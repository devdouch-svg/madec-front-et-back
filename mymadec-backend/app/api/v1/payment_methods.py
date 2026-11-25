from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_admin
from app.core.payment_modes import ATOMIC_MODES, expand_payment_modes, normalize_payment_modes
from app.core.permissions import require_human_user
from app.models.user import User
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/payment-methods", tags=["payment-methods"], dependencies=[Depends(require_human_user)])

AVAILABLE_MODES = list(ATOMIC_MODES)
LEGACY_ADMIN_MODES = ["especes", "carte", "les_deux", "deduction_salaire"]


class PaymentModesBody(BaseModel):
    modes: List[str] = Field(..., min_length=1)


@router.get("", response_model=List[str])
def get_my_payment_methods(current_user=Depends(get_current_user)):
    """Return atomic payment modes available for the current user (mobile checkout)."""
    return expand_payment_modes(current_user.payment_mode)


@router.get("/all", response_model=List[str])
def get_all_payment_methods(_=Depends(require_admin)):
    return AVAILABLE_MODES


@router.patch("/{user_id}/{mode}/toggle", response_model=MessageResponse)
def toggle_user_payment_mode(
    user_id: int,
    mode: str,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Legacy: replace user modes with a single legacy preset. Prefer PUT .../modes."""
    from app.core.exceptions import BadRequestException, NotFoundException

    if mode not in LEGACY_ADMIN_MODES and mode not in AVAILABLE_MODES:
        raise BadRequestException(
            f"Mode de paiement inconnu '{mode}'. Valides : {LEGACY_ADMIN_MODES}"
        )
    user = db.get(User, user_id)
    if not user:
        raise NotFoundException(f"User {user_id} not found")
    try:
        user.payment_mode = normalize_payment_modes(expand_payment_modes(mode))
    except ValueError as exc:
        raise BadRequestException(str(exc)) from exc
    db.commit()
    return {"message": f"Payment mode for user {user_id} set to '{user.payment_mode}'"}


@router.put("/{user_id}/modes", response_model=MessageResponse)
def set_user_payment_modes(
    user_id: int,
    body: PaymentModesBody,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Set the exact set of payment modes for a user (admin checkboxes)."""
    from app.core.exceptions import BadRequestException, NotFoundException

    user = db.get(User, user_id)
    if not user:
        raise NotFoundException(f"User {user_id} not found")
    try:
        user.payment_mode = normalize_payment_modes(body.modes)
    except ValueError as exc:
        raise BadRequestException(str(exc)) from exc
    db.commit()
    return {
        "message": f"Payment modes for user {user_id}: {expand_payment_modes(user.payment_mode)}"
    }
