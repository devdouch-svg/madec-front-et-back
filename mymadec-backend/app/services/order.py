from __future__ import annotations

import logging
import random
from datetime import date, datetime, timezone
from typing import List, Optional

from sqlalchemy import cast, extract, func, Date
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException, PlafondExceededException
from app.models.order import Order, OrderLine, OrderStatusHistory
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate, OrderLinePreview, OrderLineResponse, OrderResponse, OrderStatusUpdate

logger = logging.getLogger(__name__)


ORDER_STATUS_LABELS_FR: dict[str, str] = {
    "pending": "En attente",
    "validated": "En attente",  # ETL queue (same UX as pending)
    "processing": "Traitement en cours",
    "ready": "Commande prête à récupérer",
    "delivered": "Commande récupérée",
    "cancelled": "Commande annulée",
}


def _status_label(status: str) -> str:
    return ORDER_STATUS_LABELS_FR.get(status, status)


def notify_buyer_order_status(db: Session, order: Order) -> None:
    """In-app + push + email to the buyer after any order status change."""
    try:
        from app.services.email import send_order_status_email
        from app.services.notification import create_notification

        buyer = db.get(User, order.user_id)
        if not buyer:
            return

        status = order.sorder_status
        if status == "ready":
            title = "Commande prête à récupérer"
            body = (
                f"Votre commande {order.sorder_code} est prête. "
                "Présentez-vous pour la récupérer ou procédez au paiement par carte."
            )
        else:
            label = _status_label(status)
            title = "Mise à jour de commande"
            body = f"Votre commande {order.sorder_code} est maintenant : {label}"

        create_notification(
            db,
            user_id=buyer.id,
            title=title,
            body=body,
            type="order_status",
            data={"order_id": order.id, "status": status},
            fcm_token=buyer.fcm_token,
        )
        send_order_status_email(
            buyer.email,
            buyer.full_name,
            order.sorder_code,
            _status_label(status),
            ready=(status == "ready"),
        )
    except Exception:
        logger.exception(
            "notify_buyer_order_status failed for order %s (status=%s)",
            order.id,
            order.sorder_status,
        )


def notify_staff_new_order(db: Session, order: Order, buyer: User) -> None:
    """Notify admin and gestionnaire when a new order is placed."""
    try:
        from app.services.notification import notify_role_users

        amount = float(order.dueamount or 0)
        notify_role_users(
            db,
            ["admin", "gestionnaire"],
            title="Nouvelle commande",
            body=(
                f"{buyer.full_name} a passé la commande {order.sorder_code} "
                f"({amount:.2f} DH)."
            ),
            type="order_status",
            data={"order_id": order.id, "event": "created", "buyer_id": buyer.id},
        )
    except Exception:
        logger.exception("notify_staff_new_order failed for order %s", order.id)


# ── SORDER_CODE generation ────────────────────────────────────────────────────

def _next_sequence(db: Session) -> int:
    max_seq = db.query(func.count(Order.id)).scalar() or 0
    return max_seq + 1


def _generate_sorder_code(db: Session, psg_code: Optional[str]) -> str:
    seq = _next_sequence(db)
    suffix = psg_code or "GEN"
    code = f"SMD_{seq:06d}_{suffix}"
    # Ensure uniqueness
    while db.query(Order).filter(Order.sorder_code == code).first():
        seq += random.randint(1, 99)
        code = f"SMD_{seq:06d}_{suffix}"
    return code


# ── Plafond check ─────────────────────────────────────────────────────────────

def _check_plafond(db: Session, user: User, order_total: float) -> None:
    if user.plafond_mensuel is None:
        return  # unlimited

    now = datetime.now(timezone.utc)
    spent = (
        db.query(func.sum(Order.dueamount))
        .filter(
            Order.user_id == user.id,
            Order.sorder_status.notin_(["cancelled"]),
            extract("year",  Order.created_at) == now.year,
            extract("month", Order.created_at) == now.month,
        )
        .scalar()
        or 0.0
    )
    remaining = float(user.plafond_mensuel) - float(spent)
    if order_total > remaining:
        raise PlafondExceededException(available=remaining, requested=order_total)


# ── Order creation ────────────────────────────────────────────────────────────

def _build_lines(db: Session, line_requests: list) -> tuple[List[tuple], float, float]:
    """Resolve product codes → order lines. Returns (line_data[], total_amount, discount_total)."""
    codes = [lr.product_code for lr in line_requests]
    products = (
        db.query(Product)
        .filter(Product.product_code.in_(codes), Product.is_active == True)
        .all()
    )
    by_code = {p.product_code: p for p in products}

    lines_data = []
    total = 0.0
    discount_total = 0.0
    for lr in line_requests:
        product = by_code.get(lr.product_code)
        if not product:
            raise BadRequestException(f"Product {lr.product_code!r} not found or inactive")
        base = float(product.base_price or 0.0)
        rate = float(product.discount_rate or 0.0)
        price = product.final_price or 0.0
        discount_per_unit = round(base * rate / 100, 4)
        discount = round(discount_per_unit * lr.quantity, 2)
        amount = round(price * lr.quantity, 2)
        total += amount
        discount_total += discount
        lines_data.append((product, lr.quantity, price, discount, amount))
    return lines_data, total, discount_total


def _calculate_amounts(total: float, payment_mode: str, rate: Optional[float] = None) -> tuple[float, float, float]:
    """
    Returns (amount, fixedtax, dueamount).

    Prices come from Sabile as-is: no cash fee / fixedtax is applied on top.
    ``payment_mode`` and ``rate`` are kept for call-site compatibility.
    """
    _ = payment_mode, rate
    amount = total
    fixedtax = 0.0
    dueamount = round(amount, 2)
    return amount, fixedtax, dueamount


def compute_bl_amount(amount: float, payment_mode: str, rate: Optional[float] = None) -> float:
    """BL amount equals the Sabile order amount (no added cash fee)."""
    _, _, dueamount = _calculate_amounts(amount, payment_mode, rate)
    return dueamount


def _reload_order_with_user(db: Session, order_id: int) -> Order:
    order = (
        db.query(Order)
        .options(joinedload(Order.user))
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise NotFoundException(f"Order {order_id} not found")
    return order


def order_to_response(order: Order) -> OrderResponse:
    """Serialize an order for API responses (user relationship must be loaded)."""
    return OrderResponse.model_validate(order)


def _sort_order_lines(lines: list[OrderLine]) -> list[OrderLine]:
    return sorted(lines, key=lambda line: (line.sorder_line_code or 0, line.id))


def product_images_by_code(db: Session, codes: list[str]) -> dict[str, Optional[str]]:
    if not codes:
        return {}
    rows = (
        db.query(Product.product_code, Product.image_path)
        .filter(Product.product_code.in_(codes))
        .all()
    )
    return {code: path for code, path in rows}


def lines_to_response(db: Session, lines: list[OrderLine]) -> list[OrderLineResponse]:
    sorted_lines = _sort_order_lines(lines)
    images = product_images_by_code(db, [line.product_code for line in sorted_lines])
    return [
        OrderLineResponse.model_validate(line).model_copy(
            update={"image_path": images.get(line.product_code)}
        )
        for line in sorted_lines
    ]


def order_to_response_with_previews(db: Session, order: Order) -> OrderResponse:
    """Order payload for mobile list: includes first line previews with product images."""
    base = OrderResponse.model_validate(order)
    sorted_lines = _sort_order_lines(order.lines)
    if not sorted_lines:
        return base.model_copy(update={"line_count": 0, "lines": []})

    images = product_images_by_code(db, [line.product_code for line in sorted_lines])
    previews = [
        OrderLinePreview(
            product_code=line.product_code,
            product_name=line.product_name,
            image_path=images.get(line.product_code),
        )
        for line in sorted_lines[:2]
    ]
    return base.model_copy(update={"line_count": len(sorted_lines), "lines": previews})


def create_order(db: Session, user: User, data: OrderCreate) -> List[OrderResponse]:
    """
    Create order(s). Products spanning multiple productsalesgroup_codes are
    automatically split into sub-orders. Returns one Order per sales group.
    """
    if user.role != "acheteur":
        raise ForbiddenException("Only buyer accounts can place orders")

    # Resolve payment mode from the user's allowed set (multi-select)
    from app.core.payment_modes import expand_payment_modes

    allowed = expand_payment_modes(user.payment_mode)
    if len(allowed) == 1:
        chosen_mode = allowed[0]
    elif data.payment_mode and data.payment_mode in allowed:
        chosen_mode = data.payment_mode
    else:
        raise BadRequestException(
            "Votre compte autorise plusieurs modes de paiement — "
            f"veuillez choisir parmi : {', '.join(allowed)}."
        )

    lines_data, total, _ = _build_lines(db, data.lines)
    _check_plafond(db, user, total)

    # Group lines by productsalesgroup_code
    groups: dict[str, list] = {}
    for item in lines_data:
        grp = item[0].productsalesgroup_code or "DEFAULT"
        groups.setdefault(grp, []).append(item)

    created_orders = []
    for psg_code, group_lines in groups.items():
        group_total = sum(a for _, _, _, _, a in group_lines)
        group_discount = sum(d for _, _, _, d, _ in group_lines)
        amount, fixedtax, dueamount = _calculate_amounts(group_total, chosen_mode)

        sorder_code = _generate_sorder_code(db, psg_code)

        # No admin validation: new orders are pending → GET /sync/orders/pending → ETL.
        # Legacy "validated" remains accepted by sync for older rows only.
        order = Order(
            sorder_code=sorder_code,
            user_id=user.id,
            agence=user.agence,
            productsalesgroup_code=psg_code,
            sorder_status="pending",
            payment_mode=chosen_mode,
            amount=amount,
            discount_total=round(group_discount, 2),
            fixedtax=fixedtax,
            dueamount=dueamount,
            notes=data.notes,
        )
        db.add(order)
        db.flush()  # get order.id

        for line_pos, (product, qty, price, discount, amt) in enumerate(group_lines):
            line = OrderLine(
                order_id=order.id,
                sorder_line_code=(line_pos + 1) * 10,
                product_id=product.id,
                product_code=product.product_code,
                product_name=product.name,
                unit_price=price,
                quantity=qty,
                discount=discount,
                line_amount=amt,
            )
            db.add(line)

        _add_status_history(
            db,
            order.id,
            "pending",
            user.id,
            notes="Commande créée — en attente de prise en charge ETL",
        )
        created_orders.append(order)

    db.commit()

    responses: List[OrderResponse] = []
    for o in created_orders:
        notify_staff_new_order(db, o, user)
        reloaded = _reload_order_with_user(db, o.id)
        responses.append(order_to_response(reloaded))
    return responses


def _add_status_history(db: Session, order_id: int, status: str,
                        changed_by_id: Optional[int] = None, notes: Optional[str] = None) -> None:
    db.add(OrderStatusHistory(
        order_id=order_id,
        status=status,
        changed_by_id=changed_by_id,
        notes=notes,
    ))


def list_orders(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    society_code: Optional[str] = None,
    user_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    payment_mode: Optional[str] = None,
    load_lines: bool = False,
) -> tuple[List[Order], int]:
    q = db.query(Order)
    # Buyers can only see their own orders
    if user.role == "acheteur":
        q = q.filter(Order.user_id == user.id)
    elif user_id:
        q = q.filter(Order.user_id == user_id)
    if status:
        q = q.filter(Order.sorder_status == status)
    if society_code:
        q = q.filter(Order.productsalesgroup_code == society_code)
    if payment_mode:
        q = q.filter(Order.payment_mode == payment_mode)
    if date_from:
        q = q.filter(cast(Order.created_at, Date) >= date_from)
    if date_to:
        q = q.filter(cast(Order.created_at, Date) <= date_to)
    total = q.count()
    q = q.options(joinedload(Order.user))
    if load_lines:
        q = q.options(joinedload(Order.lines))
    items = (
        q.order_by(Order.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


_EXPORT_HEADERS = [
    "Code", "Statut", "Matricule", "Agence", "Societe", "Paiement",
    "Montant", "Montant du", "Frais fixes", "Remise", "Montant BL", "Date",
]


def _orders_for_export(
    db: Session,
    user: User,
    *,
    status: Optional[str] = None,
    society_code: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    payment_mode: Optional[str] = None,
) -> List[Order]:
    """Orders matching the same filters/scope as the list view (no pagination)."""
    q = db.query(Order)
    if user.role == "acheteur":
        q = q.filter(Order.user_id == user.id)
    if status:
        q = q.filter(Order.sorder_status == status)
    if society_code:
        q = q.filter(Order.productsalesgroup_code == society_code)
    if payment_mode:
        q = q.filter(Order.payment_mode == payment_mode)
    if date_from:
        q = q.filter(cast(Order.created_at, Date) >= date_from)
    if date_to:
        q = q.filter(cast(Order.created_at, Date) <= date_to)
    return q.options(joinedload(Order.user)).order_by(Order.created_at.desc()).all()


def deduction_salaire_monthly_report(
    db: Session,
    user: User,
    year: int,
    month: int,
) -> dict:
    """Aggregate salary-deduction orders for RH export (admin/gest)."""
    from calendar import monthrange

    if user.role not in ("admin", "gestionnaire"):
        raise ForbiddenException("Réservé à l'administration")
    if month < 1 or month > 12:
        raise BadRequestException("Mois invalide (1–12)")

    start = date(year, month, 1)
    end = date(year, month, monthrange(year, month)[1])
    orders = (
        db.query(Order)
        .options(joinedload(Order.user))
        .filter(
            Order.payment_mode == "deduction_salaire",
            Order.sorder_status.notin_(["cancelled"]),
            cast(Order.created_at, Date) >= start,
            cast(Order.created_at, Date) <= end,
        )
        .order_by(Order.created_at)
        .all()
    )

    by_user: dict[int, dict] = {}
    for o in orders:
        uid = o.user_id
        if uid not in by_user:
            by_user[uid] = {
                "user_id": uid,
                "matricule": (o.user.matricule if o.user else None) or "",
                "email": (o.user.email if o.user else None) or "",
                "full_name": (
                    " ".join(
                        p for p in [
                            o.user.first_name if o.user else None,
                            o.user.last_name if o.user else None,
                        ] if p
                    ).strip()
                ),
                "orders_count": 0,
                "total_dueamount": 0.0,
                "total_bl_amount": 0.0,
            }
        row = by_user[uid]
        row["orders_count"] += 1
        due = float(o.bl_amount) if o.bl_amount is not None else float(o.dueamount or 0)
        row["total_dueamount"] += float(o.dueamount or 0)
        row["total_bl_amount"] += due if o.bl_amount is not None else float(o.dueamount or 0)

    employees = sorted(by_user.values(), key=lambda r: (r["matricule"], r["email"]))
    return {
        "year": year,
        "month": month,
        "payment_mode": "deduction_salaire",
        "orders_count": len(orders),
        "employees_count": len(employees),
        "total_dueamount": round(sum(e["total_dueamount"] for e in employees), 2),
        "total_to_deduct": round(sum(e["total_bl_amount"] for e in employees), 2),
        "note": (
            "total_to_deduct utilise bl_amount si présent, sinon dueamount. "
            "À transmettre à la RH / paie — MyMadec ne stocke pas les salaires."
        ),
        "employees": employees,
    }


def _order_row(o: Order) -> list:
    return [
        o.sorder_code,
        o.sorder_status,
        (o.user.matricule if o.user else "") or "",
        o.agence or "",
        o.productsalesgroup_code or "",
        o.payment_mode,
        float(o.amount or 0),
        float(o.dueamount or 0),
        float(o.fixedtax or 0),
        float(o.discount_total or 0),
        float(o.bl_amount) if o.bl_amount is not None else "",
        o.created_at.strftime("%Y-%m-%d %H:%M") if o.created_at else "",
    ]


def orders_csv(db: Session, user: User, **filters) -> str:
    """CSV export of orders."""
    import csv
    import io

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(_EXPORT_HEADERS)
    for o in _orders_for_export(db, user, **filters):
        writer.writerow(_order_row(o))
    return buf.getvalue()


def orders_xlsx(db: Session, user: User, **filters) -> bytes:
    """Excel (.xlsx) export of orders."""
    import io
    from openpyxl import Workbook
    from openpyxl.styles import Font

    wb = Workbook()
    ws = wb.active
    ws.title = "Commandes"
    ws.append(_EXPORT_HEADERS)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for o in _orders_for_export(db, user, **filters):
        ws.append(_order_row(o))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def orders_pdf(db: Session, user: User, **filters) -> bytes:
    """PDF export of orders (landscape summary table)."""
    import io
    from datetime import datetime as _dt

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    orders = _orders_for_export(db, user, **filters)

    pdf_headers = ["Code", "Statut", "Matricule", "Societe", "Paiement", "Montant du", "Montant BL", "Date"]
    def pdf_row(o: Order) -> list:
        return [
            o.sorder_code,
            o.sorder_status,
            (o.user.matricule if o.user else "") or "",
            o.productsalesgroup_code or "",
            o.payment_mode,
            f"{float(o.dueamount or 0):.2f}",
            f"{float(o.bl_amount):.2f}" if o.bl_amount is not None else "",
            o.created_at.strftime("%Y-%m-%d") if o.created_at else "",
        ]

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=10 * mm, rightMargin=10 * mm, topMargin=12 * mm, bottomMargin=12 * mm,
    )
    styles = getSampleStyleSheet()
    elems = [
        Paragraph("Commandes — My Madec", styles["Title"]),
        Paragraph(f"{len(orders)} commande(s) — {_dt.now():%Y-%m-%d %H:%M}", styles["Normal"]),
        Spacer(1, 6 * mm),
    ]
    data = [pdf_headers] + [[str(c) for c in pdf_row(o)] for o in orders]
    col_widths = [40 * mm, 28 * mm, 30 * mm, 45 * mm, 28 * mm, 30 * mm, 30 * mm, 28 * mm]
    table = Table(data, repeatRows=1, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    elems.append(table)
    doc.build(elems)
    return buf.getvalue()


def get_order(db: Session, order_id: int, user: Optional[User] = None) -> Order:
    order = db.get(Order, order_id)
    if not order:
        raise NotFoundException(f"Order {order_id} not found")
    if user and user.role == "acheteur" and order.user_id != user.id:
        raise NotFoundException(f"Order {order_id} not found")
    return order


def cancel_order(db: Session, order_id: int, user: User) -> Order:
    order = get_order(db, order_id, user)
    # Buyers may cancel before ETL push (pending, or legacy validated not yet pushed).
    cancellable = order.sorder_status == "pending" or (
        order.sorder_status == "validated" and order.pushed_at is None
    )
    if not cancellable:
        raise BadRequestException(
            "Only orders not yet sent to ERP (pending/validated, not pushed) can be cancelled here"
        )
    order.sorder_status = "cancelled"
    _add_status_history(db, order_id, "cancelled", user.id)
    db.commit()
    db.refresh(order)
    notify_buyer_order_status(db, order)
    return order


def update_order_status(db: Session, order_id: int, data: OrderStatusUpdate, actor: User) -> Order:
    order = db.get(Order, order_id)
    if not order:
        raise NotFoundException(f"Order {order_id} not found")
    order.sorder_status = data.status
    _add_status_history(db, order_id, data.status, actor.id, data.notes)
    db.commit()
    db.refresh(order)
    notify_buyer_order_status(db, order)
    return order


def validate_order(db: Session, order_id: int, actor: User) -> Order:
    """Admin validates a cash-payment order."""
    return update_order_status(
        db, order_id,
        OrderStatusUpdate(status="validated", notes="Validated by admin"),
        actor,
    )


# ── ETL BL update ─────────────────────────────────────────────────────────────

def apply_bl_update(db: Session, order_id: int, lines: list, bl_amount: float) -> Order:
    order = db.get(Order, order_id)
    if not order:
        raise NotFoundException(f"Order {order_id} not found")
    for line_data in lines:
        code = line_data.get("product_code")
        qty = line_data.get("bl_quantity")
        line = next((l for l in order.lines if l.product_code == code), None)
        if line and qty is not None:
            line.bl_quantity = float(qty)
    order.bl_amount = bl_amount
    db.commit()
    db.refresh(order)
    return order
