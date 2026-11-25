from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.types import UtcDateTime

from app.models.base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # products | users | orders
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    # create | update | deactivate | push
    operation: Mapped[str] = mapped_column(String(30), nullable=False)
    # success | error | partial
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False, default=_now)
    ended_at: Mapped[Optional[datetime]] = mapped_column(UtcDateTime())
