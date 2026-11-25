"""Reference / master-data tables for catalogue hierarchy and organisation."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.types import UtcDateTime

from app.models.base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class CatalogGamme(Base):
    __tablename__ = "catalog_gammes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now, onupdate=_now)

    familles: Mapped[list["CatalogFamille"]] = relationship(back_populates="gamme", cascade="all, delete-orphan")


class CatalogFamille(Base):
    __tablename__ = "catalog_familles"
    __table_args__ = (UniqueConstraint("gamme_id", "name", name="uq_catalog_famille_gamme_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    gamme_id: Mapped[int] = mapped_column(Integer, ForeignKey("catalog_gammes.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now, onupdate=_now)

    gamme: Mapped["CatalogGamme"] = relationship(back_populates="familles")
    sous_familles: Mapped[list["CatalogSousFamille"]] = relationship(
        back_populates="famille", cascade="all, delete-orphan"
    )


class CatalogSousFamille(Base):
    __tablename__ = "catalog_sous_familles"
    __table_args__ = (UniqueConstraint("famille_id", "name", name="uq_catalog_sous_famille_famille_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    famille_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("catalog_familles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now, onupdate=_now)

    famille: Mapped["CatalogFamille"] = relationship(back_populates="sous_familles")


class CatalogCategorie(Base):
    """Mobile-app product category (independent from sync gamme/famille hierarchy)."""

    __tablename__ = "catalog_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    image_path: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now, onupdate=_now)

    sous_categories: Mapped[list["CatalogSousCategorie"]] = relationship(
        back_populates="categorie", cascade="all, delete-orphan"
    )


class CatalogSousCategorie(Base):
    __tablename__ = "catalog_sous_categories"
    __table_args__ = (UniqueConstraint("categorie_id", "name", name="uq_catalog_sous_categorie_categorie_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    categorie_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("catalog_categories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now, onupdate=_now)

    categorie: Mapped["CatalogCategorie"] = relationship(back_populates="sous_categories")
    types: Mapped[list["CatalogType"]] = relationship(
        back_populates="sous_categorie", cascade="all, delete-orphan"
    )


class CatalogType(Base):
    """Product type/variant under a mobile sous-catégorie (e.g. Flan, Mayonnaise)."""

    __tablename__ = "catalog_types"
    __table_args__ = (UniqueConstraint("sous_categorie_id", "name", name="uq_catalog_type_sous_categorie_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sous_categorie_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("catalog_sous_categories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now, onupdate=_now)

    sous_categorie: Mapped["CatalogSousCategorie"] = relationship(back_populates="types")


class OrgSociete(Base):
    __tablename__ = "org_societes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now, onupdate=_now)

    agences: Mapped[list["OrgAgence"]] = relationship(back_populates="societe", cascade="all, delete-orphan")


class OrgAgence(Base):
    __tablename__ = "org_agences"
    __table_args__ = (UniqueConstraint("societe_id", "code", name="uq_org_agence_societe_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    societe_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("org_societes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now, onupdate=_now)

    societe: Mapped["OrgSociete"] = relationship(back_populates="agences")


class OrgVille(Base):
    __tablename__ = "org_villes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=_now, onupdate=_now)
