from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator

from app.schemas.email_types import AppEmailStr


class SyncUserItem(BaseModel):
    email: Optional[AppEmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    matricule: Optional[str] = None
    user_login: Optional[str] = None  # Assabil USER_LOGIN
    role: str = "acheteur"
    productsalesgroup_code: Optional[str] = None
    societe: Optional[str] = None
    agence: Optional[str] = "001"
    langue: str = "fr"
    plafond_mensuel: Optional[float] = None
    payment_mode: str = "especes"
    is_active: bool = True
    synced_from_intermediate: bool = True

    @field_validator("email", mode="before")
    @classmethod
    def empty_email_as_none(cls, v: object) -> object:
        """ETL may send '' when USERS.EMAIL is NULL — treat as missing."""
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return v


class SyncUserBulkRequest(BaseModel):
    items: List[SyncUserItem]


class SyncHealthResponse(BaseModel):
    status: str
    db: str
    version: str


class TokenRotateResponse(BaseModel):
    message: str
    token: str          # plain token — shown only once
    token_id: int


class SyncLogResponse(BaseModel):
    id: int
    entity_type: str
    operation: str
    status: str
    records_processed: int
    records_failed: int
    error_message: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]

    model_config = {"from_attributes": True}


class SyncOrderLineResponse(BaseModel):
    sorder_line_code: Optional[int]
    product_code: str
    product_name: str
    unit_price: float
    quantity: float
    discount: float
    line_amount: float

    model_config = {"from_attributes": True}


class SyncOrderResponse(BaseModel):
    """Richer order payload used by the ETL intermediate server."""
    id: int
    sorder_code: str
    user_id: int
    user_matricule: Optional[str] = None
    productsalesgroup_code: Optional[str]
    agence: Optional[str]
    sorder_status: str
    payment_mode: str
    amount: float
    discount_total: float
    fixedtax: float
    dueamount: float
    notes: Optional[str]
    pushed_at: Optional[datetime]
    created_at: datetime
    lines: List[SyncOrderLineResponse] = []

    model_config = {"from_attributes": True}
