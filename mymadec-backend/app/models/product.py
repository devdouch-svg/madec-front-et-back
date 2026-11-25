from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.types import UtcDateTime

from app.models.base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    unit: Mapped[Optional[str]] = mapped_column(String(20))
    # Free-text product type/variant (e.g. "Flan", "Mayonnaise") — distinct from
    # the ERP gamme/famille/sous_famille hierarchy, admin/gestionnaire-editable.
    type_produit: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    # Display order within categorie / sous_categorie / type (admin drag-and-drop).
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)

    # Sync catalogue hierarchy (intermediate server / ERP). `famille` and
    # `sous_famille` are back-office only. `gamme` doubles as the brand
    # (e.g. "IDEAL", "STAR") for Figma-imported products — shown on mobile —
    # alongside its ERP meaning ("Alimentaire" / "Non alimentaire") for
    # ERP-synced products.
    gamme: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    famille: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    sous_famille: Mapped[Optional[str]] = mapped_column(String(100), index=True)

    # Mobile-app display categories (managed separately)
    categorie: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    sous_categorie: Mapped[Optional[str]] = mapped_column(String(100), index=True)

    # Sales group / company that sells this product
    productsalesgroup_code: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    society_code: Mapped[Optional[str]] = mapped_column(String(50), index=True)

    # Pricing
    base_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 4))
    discount_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=0)  # percentage

    # True when the promotion should appear in the mobile Liquidations section
    is_liquidation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # Image stored at uploads/products/{product_code}.{ext}
    image_path: Mapped[Optional[str]] = mapped_column(String(500))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # True when this record was pushed from the intermediate DB by the ETL service
    synced_from_intermediate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now, onupdate=_now)

    # ── Computed helper ───────────────────────────────────────────────────────
    @property
    def final_price(self) -> Optional[float]:
        if self.base_price is None:
            return None
        rate = float(self.discount_rate or 0)
        return round(float(self.base_price) * (1 - rate / 100), 4)
