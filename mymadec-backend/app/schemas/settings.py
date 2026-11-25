from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CashFeeRateResponse(BaseModel):
    """The espèces (cash) fee rate, as a fraction (0.25 == 25 %)."""

    rate: float


class CashFeeRateUpdate(BaseModel):
    # 0 disables the fee; upper bound guards against a fat-fingered 25 (= 2500 %).
    rate: float = Field(..., ge=0, le=1)


class DefaultPlafondResponse(BaseModel):
    """Default monthly plafond applied to new acheteurs. None = unlimited."""

    plafond_mensuel: Optional[float] = None


class DefaultPlafondUpdate(BaseModel):
    plafond_mensuel: Optional[float] = Field(None, ge=0)
