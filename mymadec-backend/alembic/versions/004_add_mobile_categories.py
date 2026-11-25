"""add mobile categories and product categorie fields

Revision ID: 004
Revises: 003
Create Date: 2026-06-09
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "catalog_categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_catalog_categories_name", "catalog_categories", ["name"])

    op.create_table(
        "catalog_sous_categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("categorie_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["categorie_id"], ["catalog_categories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("categorie_id", "name", name="uq_catalog_sous_categorie_categorie_name"),
    )
    op.create_index("ix_catalog_sous_categories_categorie_id", "catalog_sous_categories", ["categorie_id"])
    op.create_index("ix_catalog_sous_categories_name", "catalog_sous_categories", ["name"])

    op.add_column("products", sa.Column("categorie", sa.String(length=100), nullable=True))
    op.add_column("products", sa.Column("sous_categorie", sa.String(length=100), nullable=True))
    op.create_index("ix_products_categorie", "products", ["categorie"])
    op.create_index("ix_products_sous_categorie", "products", ["sous_categorie"])


def downgrade() -> None:
    op.drop_index("ix_products_sous_categorie", table_name="products")
    op.drop_index("ix_products_categorie", table_name="products")
    op.drop_column("products", "sous_categorie")
    op.drop_column("products", "categorie")
    op.drop_table("catalog_sous_categories")
    op.drop_table("catalog_categories")
