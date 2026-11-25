from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class OrderLineCreate(BaseModel):
    product_code: str = Field(..., min_length=1, max_length=50)
    quantity: float = Field(..., gt=0, le=9999)


class OrderCreate(BaseModel):
    lines: List[OrderLineCreate] = Field(..., min_length=1, max_length=200)
    notes: Optional[str] = Field(None, max_length=2000)
    # Required when the user has payment_mode="les_deux" — must be especes or carte.
    # Ignored for users with a single assigned mode (their mode is used automatically).
    payment_mode: Optional[Literal["especes", "carte", "deduction_salaire"]] = None


class OrderLinePreview(BaseModel):
    product_code: str
    product_name: str
    image_path: Optional[str] = None


class OrderLineResponse(BaseModel):
    id: int
    sorder_line_code: Optional[int]
    product_code: str
    product_name: str
    unit_price: float
    quantity: float
    discount: float
    line_amount: float
    bl_quantity: Optional[float]
    image_path: Optional[str] = None

    model_config = {"from_attributes": True}


class OrderStatusHistoryResponse(BaseModel):
    id: int
    status: str
    changed_by_id: Optional[int]
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: int
    sorder_code: str
    user_id: int
    user_email: Optional[str] = None   # populated from the user relationship
    user_name: Optional[str] = None    # populated from the user relationship
    parent_order_id: Optional[int]
    productsalesgroup_code: Optional[str]
    agence: Optional[str]
    sorder_status: str
    payment_mode: str
    amount: float
    discount_total: float
    fixedtax: float
    dueamount: float
    bl_amount: Optional[float]
    is_flagged: bool
    notes: Optional[str]
    pushed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    line_count: Optional[int] = None
    lines: Optional[List[OrderLinePreview]] = None

    model_config = {"from_attributes": True}

    @field_validator("lines", mode="before")
    @classmethod
    def ignore_orm_order_lines(cls, value):
        if isinstance(value, list) and value and hasattr(value[0], "unit_price"):
            return None
        return value


class OrderStatusUpdate(BaseModel):
    status: Literal["pending", "validated", "processing", "ready", "delivered", "cancelled"]
    notes: Optional[str] = None


class OrderBLUpdate(BaseModel):
    """Payload from ETL updating BL quantities and amount."""
    lines: List[dict]   # [{product_code, bl_quantity}]
    bl_amount: float


class OrderFlagUpdate(BaseModel):
    is_flagged: bool


class SyncOrderPush(BaseModel):
    order_id: int
