from __future__ import annotations

import math
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_admin, require_admin_or_gest
from app.core.permissions import require_acheteur, require_human_user
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.order import (
    OrderBLUpdate,
    OrderCreate,
    OrderFlagUpdate,
    OrderLineResponse,
    OrderResponse,
    OrderStatusHistoryResponse,
    OrderStatusUpdate,
)
from app.services import order as order_svc

router = APIRouter(prefix="/orders", tags=["orders"], dependencies=[Depends(require_human_user)])

# Valid status machine transitions (server-enforced)
_VALID_TRANSITIONS: dict[str, list[str]] = {
    # pending = waiting for ETL (no admin validate required)
    "pending":    ["processing", "cancelled", "validated"],
    "validated":  ["processing", "cancelled"],  # legacy
    "processing": ["ready", "cancelled"],
    "ready":      ["delivered"],
    "delivered":  [],
    "cancelled":  [],
}


@router.get("", response_model=PaginatedResponse[OrderResponse])
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    society_code: Optional[str] = None,
    user_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    payment_mode: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    items, total = order_svc.list_orders(
        db, current_user, page, page_size,
        status=status, society_code=society_code,
        user_id=user_id, date_from=date_from, date_to=date_to,
        payment_mode=payment_mode,
    )
    return PaginatedResponse(
        items=items, total=total, page=page,
        page_size=page_size, pages=math.ceil(total / page_size) or 1,
    )


@router.get("/me", response_model=PaginatedResponse[OrderResponse])
def list_my_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Buyer: own orders only. Shorthand for GET /orders filtered to current user."""
    items, total = order_svc.list_orders(
        db, current_user, page, page_size, status=status, load_lines=True,
    )
    return PaginatedResponse(
        items=[order_svc.order_to_response_with_previews(db, order) for order in items],
        total=total, page=page,
        page_size=page_size, pages=math.ceil(total / page_size) or 1,
    )


@router.post("", response_model=List[OrderResponse], status_code=201)
def create_order(
    body: OrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_acheteur),
):
    orders = order_svc.create_order(db, current_user, body)
    return orders

@router.get("/deduction-salaire/report")
def deduction_salaire_report(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_gest),
):
    """Rapport mensuel des commandes en déduction sur salaire (pour RH / paie)."""
    return order_svc.deduction_salaire_monthly_report(db, current_user, year, month)


@router.get("/export")
def export_orders(
    format: str = Query("csv", pattern="^(csv|xlsx|pdf)$"),
    status: Optional[str] = None,
    society_code: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    payment_mode: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Export orders as CSV / Excel / PDF (respects filters; acheteurs get their own only)."""
    filters = dict(
        status=status, society_code=society_code,
        date_from=date_from, date_to=date_to,
        payment_mode=payment_mode,
    )
    if format == "xlsx":
        return Response(
            content=order_svc.orders_xlsx(db, current_user, **filters),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="commandes.xlsx"'},
        )
    if format == "pdf":
        return Response(
            content=order_svc.orders_pdf(db, current_user, **filters),
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="commandes.pdf"'},
        )
    return Response(
        content=order_svc.orders_csv(db, current_user, **filters),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="commandes.csv"'},
    )


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return order_svc.get_order(db, order_id, current_user)


@router.get("/{order_id}/lines", response_model=List[OrderLineResponse])
def get_order_lines(order_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    order = order_svc.get_order(db, order_id, current_user)
    return order_svc.lines_to_response(db, order.lines)


@router.get("/{order_id}/status-history", response_model=List[OrderStatusHistoryResponse])
def get_order_status_history(order_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    order = order_svc.get_order(db, order_id, current_user)
    return order.status_history


@router.get("/{order_id}/bl", response_model=OrderResponse)
def get_order_bl(order_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Return the BL-confirmed amounts for an order (owner or admin/gest)."""
    return order_svc.get_order(db, order_id, current_user)


@router.patch("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(order_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    # Acheteur may cancel own order before ETL push; admin may cancel too.
    # Gestionnaire cannot cancel.
    from app.core.exceptions import ForbiddenException
    if current_user.role == "gestionnaire":
        raise ForbiddenException("Les gestionnaires ne peuvent pas annuler de commandes")
    return order_svc.cancel_order(db, order_id, current_user)


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    body: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_gest),
):
    # Server-side transition guard
    order = order_svc.get_order(db, order_id)
    allowed = _VALID_TRANSITIONS.get(order.sorder_status, [])
    if body.status not in allowed:
        from app.core.exceptions import BadRequestException
        raise BadRequestException(
            f"Cannot transition from '{order.sorder_status}' to '{body.status}'. "
            f"Allowed: {allowed or 'none'}"
        )
    updated = order_svc.update_order_status(db, order_id, body, current_user)
    return updated


@router.patch("/{order_id}/validate", response_model=OrderResponse)
def validate_order(order_id: int, db: Session = Depends(get_db), current_user=Depends(require_admin_or_gest)):
    """Legacy only: new orders are already pending for ETL on create.

    Prefer not to use — ETL pulls pending directly. Kept for edge cases.
    """
    order = order_svc.get_order(db, order_id)
    if order.sorder_status != "pending":
        from app.core.exceptions import BadRequestException
        raise BadRequestException(
            "Only pending orders can be validated (new orders are already queued for ETL as pending)"
        )
    return order_svc.validate_order(db, order_id, current_user)


@router.patch("/{order_id}/flag", response_model=OrderResponse)
def flag_order(
    order_id: int,
    body: OrderFlagUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin_or_gest),
):
    """Admin/gestionnaire can flag or unflag an order for attention."""
    from app.models.order import Order
    order = db.get(Order, order_id)
    if not order:
        from app.core.exceptions import NotFoundException
        raise NotFoundException(f"Order {order_id} not found")
    order.is_flagged = body.is_flagged
    db.commit()
    db.refresh(order)
    return order
