"""add is_liquidation to products

Revision ID: 006
Revises: 005
Create Date: 2026-06-18
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    return column in {col["name"] for col in inspect(bind).get_columns(table)}


def upgrade() -> None:
    if not _has_column("products", "is_liquidation"):
        op.add_column(
            "products",
            sa.Column(
                "is_liquidation",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            ),
        )
        op.create_index("ix_products_is_liquidation", "products", ["is_liquidation"])


def downgrade() -> None:
    if _has_column("products", "is_liquidation"):
        op.drop_index("ix_products_is_liquidation", table_name="products")
        op.drop_column("products", "is_liquidation")
