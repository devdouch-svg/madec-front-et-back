from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BannerUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    link_url: Optional[str] = None
    position: Optional[int] = None


class BannerResponse(BaseModel):
    id: int
    title: Optional[str]
    subtitle: Optional[str]
    image_path: Optional[str]
    link_url: Optional[str]
    position: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
