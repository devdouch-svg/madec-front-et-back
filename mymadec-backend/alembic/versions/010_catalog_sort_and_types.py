"""catalog types + product sort_order

Revision ID: 010
Revises: 009
Create Date: 2026-09-03
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def _insp():
    return inspect(op.get_bind())


def _has_table(table: str) -> bool:
    return _insp().has_table(table)


def _has_column(table: str, column: str) -> bool:
    if not _has_table(table):
        return False
    return column in {col["name"] for col in _insp().get_columns(table)}


def upgrade() -> None:
    if not _has_table("catalog_types"):
        op.create_table(
            "catalog_types",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("sous_categorie_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["sous_categorie_id"], ["catalog_sous_categories.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "sous_categorie_id", "name", name="uq_catalog_type_sous_categorie_name"
            ),
        )
        op.create_index("ix_catalog_types_sous_categorie_id", "catalog_types", ["sous_categorie_id"])
        op.create_index("ix_catalog_types_name", "catalog_types", ["name"])

    if not _has_column("products", "sort_order"):
        op.add_column(
            "products",
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        )
        op.create_index("ix_products_sort_order", "products", ["sort_order"])

    if _has_column("products", "type_produit"):
        bind = op.get_bind()
        existing = {idx["name"] for idx in _insp().get_indexes("products")}
        if "ix_products_type_produit" not in existing:
            op.create_index("ix_products_type_produit", "products", ["type_produit"])

    conn = op.get_bind()
    # Seed types from existing product labels (idempotent).
    conn.execute(
        text(
            """
            INSERT INTO catalog_types (sous_categorie_id, name, is_active, sort_order, created_at, updated_at)
            SELECT sc.id, p.type_produit, 1, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            FROM (
                SELECT DISTINCT categorie, sous_categorie, type_produit
                FROM products
                WHERE type_produit IS NOT NULL AND type_produit <> ''
                  AND sous_categorie IS NOT NULL AND sous_categorie <> ''
                  AND categorie IS NOT NULL AND categorie <> ''
            ) p
            INNER JOIN catalog_categories c ON LOWER(c.name) = LOWER(p.categorie)
            INNER JOIN catalog_sous_categories sc
                ON sc.categorie_id = c.id AND LOWER(sc.name) = LOWER(p.sous_categorie)
            WHERE NOT EXISTS (
                SELECT 1 FROM catalog_types t
                WHERE t.sous_categorie_id = sc.id AND LOWER(t.name) = LOWER(p.type_produit)
            )
            """
        )
    )

    # Preserve current alphabetical order as the initial custom order.
    dialect = conn.dialect.name
    if dialect == "mssql":
        conn.execute(
            text(
                """
                WITH ranked AS (
                    SELECT id,
                           ROW_NUMBER() OVER (
                               PARTITION BY ISNULL(categorie, ''), ISNULL(sous_categorie, ''), ISNULL(type_produit, '')
                               ORDER BY name, id
                           ) AS rn
                    FROM products
                )
                UPDATE p
                SET sort_order = r.rn * 10
                FROM products p
                INNER JOIN ranked r ON p.id = r.id
                WHERE p.sort_order = 0
                """
            )
        )
    else:
        conn.execute(
            text(
                """
                UPDATE products
                SET sort_order = ranked.rn * 10
                FROM (
                    SELECT id,
                           ROW_NUMBER() OVER (
                               PARTITION BY COALESCE(categorie, ''), COALESCE(sous_categorie, ''), COALESCE(type_produit, '')
                               ORDER BY name, id
                           ) AS rn
                    FROM products
                ) ranked
                WHERE products.id = ranked.id AND products.sort_order = 0
                """
            )
        )


def downgrade() -> None:
    if _has_column("products", "sort_order"):
        op.drop_index("ix_products_sort_order", table_name="products")
        op.drop_column("products", "sort_order")
    if _has_table("catalog_types"):
        op.drop_index("ix_catalog_types_name", table_name="catalog_types")
        op.drop_index("ix_catalog_types_sous_categorie_id", table_name="catalog_types")
        op.drop_table("catalog_types")
