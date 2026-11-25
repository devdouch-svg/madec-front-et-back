from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_db, get_service_auth, require_admin
from app.core.exceptions import BadRequestException
from app.models.sync_log import SyncLog
from app.schemas.common import MessageResponse
from app.schemas.product import ProductSyncBulkRequest
from app.schemas.common import PaginatedResponse
from app.schemas.sync import (
    SyncHealthResponse, SyncLogResponse, SyncUserBulkRequest, TokenRotateResponse,
    SyncOrderResponse,
)
from app.schemas.order import OrderBLUpdate, OrderFlagUpdate, OrderStatusUpdate
from app.services import product as product_svc
from app.services.order import apply_bl_update

from app.core.rate_limits import sync_rate_limit

router = APIRouter(prefix="/sync", tags=["sync"], dependencies=[Depends(sync_rate_limit)])


# ── helpers ───────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _write_log(
    db: Session,
    *,
    entity_type: str,
    operation: str,
    status: str,
    records_processed: int = 0,
    records_failed: int = 0,
    error_message: Optional[str] = None,
    started_at: datetime,
) -> SyncLog:
    log = SyncLog(
        entity_type=entity_type,
        operation=operation,
        status=status,
        records_processed=records_processed,
        records_failed=records_failed,
        error_message=error_message,
        started_at=started_at,
        ended_at=_now(),
    )
    db.add(log)
    db.commit()
    return log


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health", response_model=SyncHealthResponse)
def sync_health(db: Session = Depends(get_db), _=Depends(get_service_auth)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"
    return SyncHealthResponse(status="ok", db=db_status, version=settings.APP_VERSION)


# ── Products ──────────────────────────────────────────────────────────────────

@router.post("/products", response_model=MessageResponse)
def sync_product(
    body: ProductSyncBulkRequest,
    db: Session = Depends(get_db),
    _=Depends(get_service_auth),
):
    return _do_sync_products(db, body, operation="sync")


@router.post("/products/bulk", response_model=MessageResponse)
def sync_products_bulk(
    body: ProductSyncBulkRequest,
    db: Session = Depends(get_db),
    _=Depends(get_service_auth),
):
    return _do_sync_products(db, body, operation="bulk_sync")


def _do_sync_products(db: Session, body: ProductSyncBulkRequest, operation: str) -> dict:
    started = _now()
    try:
        result = product_svc.sync_bulk_products(db, body.items)
        _write_log(
            db, entity_type="products", operation=operation, status="success",
            records_processed=len(body.items), started_at=started,
        )
        # CDC §3.2: new synced products arrive without a mobile category (inactive).
        # Alert staff via the header notifications so they can categorize them.
        if result.get("created"):
            from app.services.notification import notify_role_users
            missing = product_svc.count_missing_mobile_category(db)
            if missing:
                notify_role_users(
                    db, ["admin", "gestionnaire"],
                    title="Produits à catégoriser",
                    body=f"{missing} produit(s) sans catégorie mobile — cliquez pour les assigner.",
                    type="catalog",
                    data={"event": "uncategorized_products", "count": missing},
                )
        return {"message": f"Synced {len(body.items)} products: {result}"}
    except Exception as exc:
        _write_log(
            db, entity_type="products", operation=operation, status="error",
            records_failed=len(body.items), error_message=str(exc), started_at=started,
        )
        raise


# ── Users ─────────────────────────────────────────────────────────────────────

@router.post("/users", response_model=MessageResponse)
def sync_user(
    body: SyncUserBulkRequest,
    db: Session = Depends(get_db),
    _=Depends(get_service_auth),
):
    return _do_sync_users(db, body, operation="sync")


@router.post("/users/bulk", response_model=MessageResponse)
def sync_users_bulk(
    body: SyncUserBulkRequest,
    db: Session = Depends(get_db),
    _=Depends(get_service_auth),
):
    return _do_sync_users(db, body, operation="bulk_sync")


def _do_sync_users(db: Session, body: SyncUserBulkRequest, operation: str) -> dict:
    from app.models.user import User
    from app.core.security import hash_password, generate_password
    from app.services.email import send_welcome_email

    started = _now()
    created = updated = failed = 0
    last_error: Optional[str] = None

    # Match on matricule / user_login (Assabil USER_LOGIN); email is optional.
    matricules = [item.matricule for item in body.items if item.matricule]
    logins = [item.user_login for item in body.items if item.user_login]
    existing_by_mat: dict[str, User] = {
        u.matricule: u
        for u in db.query(User).filter(User.matricule.in_(matricules)).all()
    } if matricules else {}
    existing_by_login: dict[str, User] = {
        u.user_login: u
        for u in db.query(User).filter(User.user_login.in_(logins)).all()
        if u.user_login
    } if logins else {}

    for item in body.items:
        try:
            existing = None
            if item.user_login:
                existing = existing_by_login.get(item.user_login)
            if existing is None and item.matricule:
                existing = existing_by_mat.get(item.matricule)
            if existing:
                data = item.model_dump(exclude={"matricule"})
                for k, v in data.items():
                    # Allow explicit False/0 for is_active; skip None for other fields
                    if v is not None or k == "is_active":
                        setattr(existing, k, v)
                if not existing.user_login and (item.user_login or item.matricule):
                    existing.user_login = item.user_login or item.matricule
                updated += 1
            else:
                from app.services import app_settings

                plain_pw = generate_password()
                payload = item.model_dump()
                if not payload.get("user_login") and payload.get("matricule"):
                    payload["user_login"] = payload["matricule"]
                if payload.get("plafond_mensuel") is None and payload.get("role", "acheteur") == "acheteur":
                    payload["plafond_mensuel"] = app_settings.get_default_plafond(db)
                user = User(hashed_password=hash_password(plain_pw), **payload)
                db.add(user)
                db.flush()
                # Welcome email only when the synced user actually has an email.
                if user.email:
                    send_welcome_email(user.email, user.full_name, plain_pw)
                created += 1
        except Exception as exc:
            failed += 1
            last_error = str(exc)

    db.commit()
    status = "success" if not failed else ("partial" if (created + updated) else "error")
    _write_log(
        db, entity_type="users", operation=operation, status=status,
        records_processed=created + updated, records_failed=failed,
        error_message=last_error, started_at=started,
    )
    # Alert staff when new users are imported from Assabil (header notifications).
    if created:
        from app.services.notification import notify_role_users
        notify_role_users(
            db, ["admin", "gestionnaire"],
            title="Nouveaux utilisateurs",
            body=f"{created} utilisateur(s) importé(s) depuis Assabil.",
            type="users",
            data={"event": "users_synced", "count": created},
        )
    return {"message": f"Users synced — created: {created}, updated: {updated}, failed: {failed}"}


@router.patch("/users/{user_id}/deactivate", response_model=MessageResponse)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_service_auth),
):
    from app.models.user import User

    started = _now()
    user = db.get(User, user_id)
    if user:
        user.is_active = False
        db.commit()
        _write_log(db, entity_type="users", operation="deactivate", status="success",
                   records_processed=1, started_at=started)
    else:
        _write_log(db, entity_type="users", operation="deactivate", status="error",
                   records_failed=1, error_message=f"User {user_id} not found", started_at=started)
    return {"message": f"User {user_id} deactivated"}


# ── Orders ────────────────────────────────────────────────────────────────────

@router.get("/orders/pending", response_model=list[SyncOrderResponse])
def get_pending_orders(
    db: Session = Depends(get_db),
    _=Depends(get_service_auth),
):
    """ETL: return orders waiting to be pushed (pending, or legacy validated)."""
    from sqlalchemy.orm import joinedload

    from app.models.order import Order

    orders = (
        db.query(Order)
        .options(joinedload(Order.user))  # eager-load user → avoids an N+1 query
        .filter(
            Order.sorder_status.in_(("pending", "validated")),
            Order.pushed_at.is_(None),
        )
        .order_by(Order.created_at)
        .all()
    )
    result = []
    for order in orders:
        item = SyncOrderResponse.model_validate(order)
        item.user_matricule = order.user.matricule if order.user else None
        result.append(item)
    return result


@router.get("/orders/by-code", response_model=SyncOrderResponse)
def get_order_by_code(
    code: str,
    db: Session = Depends(get_db),
    _=Depends(get_service_auth),
):
    """ETL: look up an order by its SORDER_CODE."""
    from app.models.order import Order
    from app.core.exceptions import NotFoundException

    order = db.query(Order).filter(Order.sorder_code == code).first()
    if not order:
        raise NotFoundException(f"Order {code!r} not found")
    return SyncOrderResponse.model_validate(order)


@router.post("/orders/{order_id}/push", response_model=MessageResponse)
def push_order(
    order_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_service_auth),
):
    """ETL: mark order as pushed (pending/validated → processing + pushed_at)."""
    from app.models.order import Order, OrderStatusHistory
    from app.services.order import notify_buyer_order_status

    started = _now()
    order = db.get(Order, order_id)
    if order and order.sorder_status in ("pending", "validated") and order.pushed_at is None:
        order.sorder_status = "processing"
        order.pushed_at = _now()
        db.add(OrderStatusHistory(
            order_id=order_id,
            status="processing",
            notes="Prise en charge par l'ETL / envoyée à l'ERP",
        ))
        db.commit()
        db.refresh(order)
        notify_buyer_order_status(db, order)
        _write_log(db, entity_type="orders", operation="push", status="success",
                   records_processed=1, started_at=started)
    else:
        _write_log(db, entity_type="orders", operation="push", status="error",
                   records_failed=1,
                   error_message=f"Order {order_id} not found or not awaiting ETL push",
                   started_at=started)
    return {"message": f"Order {order_id} pushed to ETL"}


@router.patch("/orders/{order_id}/status", response_model=MessageResponse)
def etl_update_order_status(
    order_id: int,
    body: OrderStatusUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_service_auth),
):
    from app.models.order import Order, OrderStatusHistory
    from app.services.order import notify_buyer_order_status

    started = _now()
    order = db.get(Order, order_id)
    if order:
        order.sorder_status = body.status
        db.add(OrderStatusHistory(order_id=order_id, status=body.status, notes="ETL update"))
        db.commit()
        db.refresh(order)
        notify_buyer_order_status(db, order)

        _write_log(db, entity_type="orders", operation="status_update", status="success",
                   records_processed=1, started_at=started)
    else:
        _write_log(db, entity_type="orders", operation="status_update", status="error",
                   records_failed=1, error_message=f"Order {order_id} not found", started_at=started)
    return {"message": f"Order {order_id} status updated to {body.status}"}


@router.patch("/orders/{order_id}/bl", response_model=MessageResponse)
def etl_update_order_bl(
    order_id: int,
    body: OrderBLUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_service_auth),
):
    started = _now()
    try:
        apply_bl_update(db, order_id, body.lines, body.bl_amount)
        _write_log(db, entity_type="orders", operation="bl_update", status="success",
                   records_processed=1, started_at=started)
    except Exception as exc:
        _write_log(db, entity_type="orders", operation="bl_update", status="error",
                   records_failed=1, error_message=str(exc), started_at=started)
        raise
    return {"message": f"BL updated for order {order_id}"}


@router.patch("/orders/{order_id}/flag", response_model=MessageResponse)
def etl_flag_order(
    order_id: int,
    body: OrderFlagUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_service_auth),
):
    from app.models.order import Order

    started = _now()
    order = db.get(Order, order_id)
    if order:
        order.is_flagged = body.is_flagged
        db.commit()
        _write_log(db, entity_type="orders", operation="flag", status="success",
                   records_processed=1, started_at=started)
    else:
        _write_log(db, entity_type="orders", operation="flag", status="error",
                   records_failed=1, error_message=f"Order {order_id} not found", started_at=started)
    return {"message": f"Order {order_id} flag set to {body.is_flagged}"}


# ── Admin: sync history (web UI) ──────────────────────────────────────────────

@router.get("/logs", response_model=PaginatedResponse[SyncLogResponse])
def list_sync_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Recent ETL sync operations (admin dashboard)."""
    q = db.query(SyncLog)
    if entity_type:
        q = q.filter(SyncLog.entity_type == entity_type)
    total = q.count()
    items = (
        q.order_by(SyncLog.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) or 1,
    )


@router.get("/overview")
def sync_overview(
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """DB health + last sync per entity type (no service token required)."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    entity_types = ("products", "users", "orders")
    subq = (
        db.query(
            SyncLog.entity_type,
            func.max(SyncLog.started_at).label("max_started"),
        )
        .filter(SyncLog.entity_type.in_(entity_types))
        .group_by(SyncLog.entity_type)
        .subquery()
    )
    latest_rows = (
        db.query(SyncLog)
        .join(
            subq,
            (SyncLog.entity_type == subq.c.entity_type)
            & (SyncLog.started_at == subq.c.max_started),
        )
        .all()
    )
    last_by_type: dict = {
        row.entity_type: {
            "status": row.status,
            "operation": row.operation,
            "records_processed": row.records_processed,
            "records_failed": row.records_failed,
            "started_at": row.started_at.isoformat(),
        }
        for row in latest_rows
    }

    return {
        "db": db_status,
        "app_version": settings.APP_VERSION,
        "last_sync": last_by_type,
    }


# ── Token rotation ────────────────────────────────────────────────────────────

@router.post("/tokens/rotate", response_model=TokenRotateResponse)
def rotate_service_token(
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """
    Admin-only: deactivate all current service tokens and issue a new one.
    The new plain token is returned **once** — store it in the ETL_SERVICE_TOKEN
    environment variable immediately.
    """
    from app.models.user import ServiceToken
    from app.core.security import generate_service_token, hash_service_token

    # Deactivate all existing tokens
    db.query(ServiceToken).filter(ServiceToken.is_active == True).update(
        {"is_active": False}
    )
    db.flush()

    plain = generate_service_token()
    new_token = ServiceToken(
        name="ETL Service",
        token_hash=hash_service_token(plain),
        is_active=True,
    )
    db.add(new_token)
    db.commit()
    db.refresh(new_token)

    return TokenRotateResponse(
        message="Service token rotated. Store the new token immediately — it will not be shown again.",
        token=plain,
        token_id=new_token.id,
    )
