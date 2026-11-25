from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.types import UtcDateTime

from app.models.base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Optional: back-office users have an email; ETL-synced (Assabil) users have a
    # matricule instead. Uniqueness is enforced by a filtered index (email IS NOT NULL).
    email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(30))

    # admin | gestionnaire | acheteur | service
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="acheteur")

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Atomic: especes | carte | deduction_salaire
    # Combos: les_deux (=especes+carte) | comma-list e.g. especes,deduction_salaire
    payment_mode: Mapped[str] = mapped_column(String(80), nullable=False, default="especes")

    # Assabil matricule — unique among non-NULL values only (filtered index on SQL Server)
    matricule: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    # Assabil USER_LOGIN — preferred web/mobile login (unicity guaranteed côté Assabil)
    user_login: Mapped[Optional[str]] = mapped_column(String(100), index=True)

    # Preferred language — fr (default) or ar (V2)
    langue: Mapped[str] = mapped_column(String(5), nullable=False, default="fr")

    # True when this record was pushed from the intermediate DB by the ETL service
    synced_from_intermediate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Monthly spending cap (NULL = unlimited)
    plafond_mensuel: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))

    # Links user to a MADEC sales group (for order splitting)
    productsalesgroup_code: Mapped[Optional[str]] = mapped_column(String(50))

    # CDC §7.2: société de rattachement and agence de l'utilisateur
    societe: Mapped[Optional[str]] = mapped_column(String(100))
    agence: Mapped[Optional[str]] = mapped_column(String(50), default="001")
    ville: Mapped[Optional[str]] = mapped_column(String(100))

    # Firebase Cloud Messaging token for push notifications
    fcm_token: Mapped[Optional[str]] = mapped_column(String(512))

    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now, onupdate=_now)

    # ── Relationships ─────────────────────────────────────────────────────────
    reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    orders: Mapped[list["Order"]] = relationship(back_populates="user")  # type: ignore[name-defined]  # noqa
    notifications: Mapped[list["Notification"]] = relationship(  # type: ignore[name-defined]  # noqa
        back_populates="user", cascade="all, delete-orphan"
    )

    # ── Helpers ───────────────────────────────────────────────────────────────
    @property
    def full_name(self) -> str:
        parts = [self.first_name or "", self.last_name or ""]
        return " ".join(p for p in parts if p).strip() or self.email or self.matricule or ""


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now)

    user: Mapped["User"] = relationship(back_populates="reset_tokens")


class ServiceToken(Base):
    __tablename__ = "service_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(UtcDateTime())
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now)
