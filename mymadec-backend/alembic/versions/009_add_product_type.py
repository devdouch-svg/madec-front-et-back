"""add type_produit to products

Revision ID: 009
Revises: 008
Create Date: 2026-09-01
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    return column in {col["name"] for col in inspect(bind).get_columns(table)}


def upgrade() -> None:
    if not _has_column("products", "type_produit"):
        op.add_column("products", sa.Column("type_produit", sa.String(length=100), nullable=True))


def downgrade() -> None:
    if _has_column("products", "type_produit"):
        op.drop_column("products", "type_produit")
