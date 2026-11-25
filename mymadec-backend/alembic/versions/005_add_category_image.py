"""add image_path to catalog_categories

Revision ID: 005
Revises: 004
Create Date: 2026-06-16
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    return column in {col["name"] for col in inspect(bind).get_columns(table)}


def upgrade() -> None:
    if not _has_column("catalog_categories", "image_path"):
        op.add_column(
            "catalog_categories",
            sa.Column("image_path", sa.String(length=500), nullable=True),
        )


def downgrade() -> None:
    if _has_column("catalog_categories", "image_path"):
        op.drop_column("catalog_categories", "image_path")
