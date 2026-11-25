from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_admin
from app.core.permissions import require_human_user
from app.schemas.settings import (
    CashFeeRateResponse,
    CashFeeRateUpdate,
    DefaultPlafondResponse,
    DefaultPlafondUpdate,
)
from app.services import app_settings

router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[Depends(require_human_user)])


@router.get("/cash-fee-rate", response_model=CashFeeRateResponse)
def get_cash_fee_rate(db: Session = Depends(get_db), _=Depends(get_current_user)):
    """Cash fee rate (always 0 — Sabile prices are used without surcharge)."""
    return CashFeeRateResponse(rate=app_settings.get_cash_fee_rate(db))


@router.put("/cash-fee-rate", response_model=CashFeeRateResponse)
def update_cash_fee_rate(
    body: CashFeeRateUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Kept for API compatibility; effective rate remains 0."""
    rate = app_settings.set_cash_fee_rate(db, body.rate)
    return CashFeeRateResponse(rate=rate)


@router.get("/default-plafond", response_model=DefaultPlafondResponse)
def get_default_plafond(db: Session = Depends(get_db), _=Depends(require_admin)):
    """Plafond applied automatically on new acheteur creation when not specified."""
    return DefaultPlafondResponse(plafond_mensuel=app_settings.get_default_plafond(db))


@router.put("/default-plafond", response_model=DefaultPlafondResponse)
def update_default_plafond(
    body: DefaultPlafondUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    try:
        value = app_settings.set_default_plafond(db, body.plafond_mensuel)
    except ValueError as exc:
        from app.core.exceptions import BadRequestException
        raise BadRequestException(str(exc)) from exc
    return DefaultPlafondResponse(plafond_mensuel=value)
