from __future__ import annotations

import math
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_admin, require_admin_or_gest
from app.core.exceptions import ForbiddenException
from app.core.permissions import require_human_user
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.user import (
    FCMTokenUpdate,
    PasswordSet,
    PaymentModeUpdate,
    PlafondStatus,
    PlafondUpdate,
    RoleUpdate,
    UserCreate,
    UserMeUpdate,
    UserResponse,
    UserUpdate,
)
from app.services import user as user_svc
from app.services.email import (
    send_admin_password_reset_email,
    send_password_changed_email,
    send_welcome_email,
)

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_human_user)])


# ── /me endpoints ─────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
def update_me(body: UserMeUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.patch("/me/fcm-token", response_model=MessageResponse)
def update_fcm_token(
    body: FCMTokenUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mobile app registers/clears its FCM push token."""
    current_user.fcm_token = body.fcm_token
    db.commit()
    return {"message": "FCM token updated"}


@router.get("/me/plafond", response_model=PlafondStatus)
def get_my_plafond(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return user_svc.get_plafond_status(db, current_user)


# ── Admin / gestionnaire list + read ─────────────────────────────────────────
# CDC §5.1: gestionnaire manages products only. User mutations are admin-only.
# We grant gestionnaire READ access to user list/detail so they can identify
# buyers when reviewing orders (pragmatic deviation from CDC §6.2 documented here).

@router.get("", response_model=PaginatedResponse[UserResponse])
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[Literal["admin", "gestionnaire", "acheteur", "service"]] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    societe: Optional[str] = None,
    agence: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(require_admin_or_gest),
):
    items, total = user_svc.list_users(
        db, page, page_size, role, is_active, search,
        societe=societe, agence=agence,
    )
    return PaginatedResponse(
        items=items, total=total, page=page,
        page_size=page_size, pages=math.ceil(total / page_size),
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), _=Depends(require_admin_or_gest)):
    return user_svc.get_user(db, user_id)


# ── Admin-only mutations ──────────────────────────────────────────────────────

@router.post("", response_model=UserResponse, status_code=201)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    user, plain_pw = user_svc.create_user(db, body)
    send_welcome_email(user.email, user.full_name, plain_pw)
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, body: UserUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return user_svc.update_user(db, user_id, body)


@router.patch("/{user_id}/toggle", response_model=UserResponse)
def toggle_user(user_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    return user_svc.toggle_user(db, user_id)


@router.patch("/{user_id}/reset-password", response_model=MessageResponse)
def reset_user_password(user_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    user, plain_pw = user_svc.reset_user_password(db, user_id)
    send_admin_password_reset_email(user.email, user.full_name, plain_pw)
    return {"message": f"Password reset — new credentials sent to {user.email}"}


@router.patch("/{user_id}/set-password", response_model=MessageResponse)
def set_user_password(
    user_id: int,
    body: PasswordSet,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Admin manually sets a specific password for a user."""
    user = user_svc.set_user_password(db, user_id, body.new_password)
    send_password_changed_email(user.email, user.full_name)
    return {"message": f"Mot de passe mis à jour pour {user.email}"}


@router.patch("/plafond/bulk", response_model=MessageResponse)
def bulk_update_plafond(body: PlafondUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Admin: apply the same monthly plafond to all acheteurs at once (None = unlimited)."""
    count = user_svc.bulk_set_plafond(db, body.plafond_mensuel, roles=["acheteur"])
    return {"message": f"Plafond appliqué à {count} acheteur(s)"}


@router.patch("/{user_id}/plafond", response_model=UserResponse)
def update_plafond(user_id: int, body: PlafondUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return user_svc.update_plafond(db, user_id, body.plafond_mensuel)


@router.patch("/{user_id}/payment-mode", response_model=UserResponse)
def update_payment_mode(user_id: int, body: PaymentModeUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return user_svc.update_payment_mode(
        db, user_id, mode=body.payment_mode, modes=body.modes,
    )


@router.patch("/{user_id}/role", response_model=UserResponse)
def update_role(user_id: int, body: RoleUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return user_svc.update_role(db, user_id, body.role)


# ── Plafond status (admin, gestionnaire, or own acheteur) ─────────────────────

@router.get("/{user_id}/plafond/status", response_model=PlafondStatus)
def get_user_plafond_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Admin and gestionnaire can see any user; acheteur can only see their own
    if current_user.role not in ("admin", "gestionnaire") and current_user.id != user_id:
        raise ForbiddenException("You can only view your own plafond status")
    user = user_svc.get_user(db, user_id)
    return user_svc.get_plafond_status(db, user)


# ── Orders for a user (admin and gestionnaire) ────────────────────────────────

@router.get("/{user_id}/orders")
def get_user_orders(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(require_admin_or_gest),
):
    from app.models.order import Order
    import math
    user_svc.get_user(db, user_id)
    q = db.query(Order).filter(Order.user_id == user_id)
    total = q.count()
    items = q.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=items, total=total, page=page,
        page_size=page_size, pages=math.ceil(total / page_size) or 1,
    )
