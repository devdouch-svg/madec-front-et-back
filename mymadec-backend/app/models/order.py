from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.types import UtcDateTime

from app.models.base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


# Order statuses
ORDER_STATUSES = ["pending", "validated", "processing", "ready", "delivered", "cancelled"]


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # e.g. SMD_000001_GRP01
    sorder_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # If this is a sub-order (split by society), reference the parent
    parent_order_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("orders.id"))

    productsalesgroup_code: Mapped[Optional[str]] = mapped_column(String(50), index=True)

    # Client agency (populated from user's site code or ETL)
    agence: Mapped[Optional[str]] = mapped_column(String(100))

    sorder_status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending", index=True)

    # especes | carte | deduction_salaire
    payment_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="especes")

    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    discount_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    fixedtax: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    dueamount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    # BL (bon de livraison) confirmed amount (may differ if paid by card → no fixed tax)
    bl_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))

    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamp when order was successfully pushed to the ERP (set by ETL)
    pushed_at: Mapped[Optional[datetime]] = mapped_column(UtcDateTime())

    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now, onupdate=_now)

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship(back_populates="orders")  # type: ignore[name-defined]

    # ── Computed helpers (exposed by OrderResponse) ───────────────────────────
    @property
    def user_email(self) -> Optional[str]:
        return self.user.email if self.user else None

    @property
    def user_name(self) -> Optional[str]:
        return self.user.full_name if self.user else None
    lines: Mapped[list["OrderLine"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    status_history: Mapped[list["OrderStatusHistory"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", order_by="OrderStatusHistory.created_at"
    )
    sub_orders: Mapped[list["Order"]] = relationship(back_populates="parent_order")
    parent_order: Mapped[Optional["Order"]] = relationship(back_populates="sub_orders", remote_side="Order.id")


class OrderLine(Base):
    __tablename__ = "order_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    # Line position within the order: 10, 20, 30 … (incremented by 10 per CDC)
    sorder_line_code: Mapped[Optional[int]] = mapped_column(Integer)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("products.id"))
    product_code: Mapped[str] = mapped_column(String(50), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    # Decimal quantities (e.g. 1.5 kg) per CDC QUANTITE DECIMAL(10,3)
    quantity: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False, default=1)
    discount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    line_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    bl_quantity: Mapped[Optional[float]] = mapped_column(Numeric(10, 3))  # confirmed by BL

    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now)

    order: Mapped["Order"] = relationship(back_populates="lines")


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now)

    order: Mapped["Order"] = relationship(back_populates="status_history")
