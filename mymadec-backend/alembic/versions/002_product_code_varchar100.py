"""resize product_code from VARCHAR(50) to VARCHAR(100) per CDC §7.2

Revision ID: 002
Revises: 001
Create Date: 2026-06-06
"""
from __future__ import annotations

from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None

_INDEX = "ix_products_product_code"


def upgrade() -> None:
    # Unique index on product_code blocks ALTER COLUMN on SQL Server.
    with op.get_context().autocommit_block():
        op.drop_index(_INDEX, table_name="products")
        op.execute(
            "ALTER TABLE products ALTER COLUMN product_code NVARCHAR(100) NOT NULL"
        )
        op.create_index(_INDEX, "products", ["product_code"], unique=True)


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index(_INDEX, table_name="products")
        op.execute(
            "ALTER TABLE products ALTER COLUMN product_code NVARCHAR(50) NOT NULL"
        )
        op.create_index(_INDEX, "products", ["product_code"], unique=True)
