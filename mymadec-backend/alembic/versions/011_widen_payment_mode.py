"""Widen users.payment_mode for multi-select storage.

Revision ID: 011_widen_payment_mode
Revises: 010_catalog_sort_and_types
Create Date: 2026-10-28
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "011_widen_payment_mode"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "payment_mode",
        existing_type=sa.String(length=20),
        type_=sa.String(length=80),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "payment_mode",
        existing_type=sa.String(length=80),
        type_=sa.String(length=20),
        existing_nullable=False,
    )
