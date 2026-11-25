from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.types import UtcDateTime

from app.models.base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AppSetting(Base):
    """Global, admin-editable business settings, stored as key/value pairs.

    Keeps runtime-tunable values (e.g. the cash-payment fee rate) out of .env so
    an admin can change them from the dashboard without a redeploy.
    """

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now, onupdate=_now)
