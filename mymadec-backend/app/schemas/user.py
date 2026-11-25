from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.auth import _validate_password_strength
from app.schemas.email_types import AppEmailStr

PaymentMode = Literal["especes", "carte", "les_deux", "deduction_salaire"]
# Multi-select body (admin): any non-empty subset of atomic modes
AtomicPaymentMode = Literal["especes", "carte", "deduction_salaire"]


class PasswordSet(BaseModel):
    """Admin manually sets a user's password."""

    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class UserCreate(BaseModel):
    email: AppEmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    matricule: Optional[str] = None
    user_login: Optional[str] = None
    role: Literal["admin", "gestionnaire", "acheteur", "service"] = "acheteur"
    payment_mode: PaymentMode = "especes"
    plafond_mensuel: Optional[float] = None
    productsalesgroup_code: Optional[str] = None
    societe: Optional[str] = None
    agence: Optional[str] = "001"
    ville: Optional[str] = None
    langue: str = "fr"


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    matricule: Optional[str] = None
    user_login: Optional[str] = None
    productsalesgroup_code: Optional[str] = None
    societe: Optional[str] = None
    agence: Optional[str] = None
    ville: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: Optional[str] = None
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    matricule: Optional[str]
    user_login: Optional[str] = None
    role: str
    is_active: bool
    payment_mode: str
    plafond_mensuel: Optional[float]
    productsalesgroup_code: Optional[str]
    societe: Optional[str]
    agence: Optional[str]
    ville: Optional[str]
    langue: str
    synced_from_intermediate: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserMeUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    langue: Optional[Literal["fr", "ar"]] = None
    # FCM token has its own dedicated endpoint: PATCH /users/me/fcm-token


class FCMTokenUpdate(BaseModel):
    fcm_token: Optional[str] = None


class PlafondUpdate(BaseModel):
    plafond_mensuel: Optional[float] = None  # None = unlimited


class PaymentModeUpdate(BaseModel):
    """Set one legacy value OR a list of atomic modes (preferred)."""

    payment_mode: Optional[str] = None
    modes: Optional[list[AtomicPaymentMode]] = None

    @field_validator("modes")
    @classmethod
    def at_least_one_mode(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is not None and len(v) == 0:
            raise ValueError("Au moins un mode de paiement est requis")
        return v


class RoleUpdate(BaseModel):
    role: Literal["admin", "gestionnaire", "acheteur", "service"]


class PlafondStatus(BaseModel):
    plafond_mensuel: Optional[float]
    spent_this_month: float
    remaining: Optional[float]  # None if unlimited


class AnnuaireEntry(BaseModel):
    id: int
    email: Optional[str] = None
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    matricule: Optional[str]
    role: str
    societe: Optional[str]
    agence: Optional[str]
    ville: Optional[str]

    model_config = {"from_attributes": True}
