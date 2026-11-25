from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    body: str
    type: str
    data: Optional[str]
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationSend(BaseModel):
    user_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=2000)
    type: Literal["general", "order_status", "promo"] = "general"
    data: Optional[dict] = None
