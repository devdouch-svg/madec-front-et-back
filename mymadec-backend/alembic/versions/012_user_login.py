"""Add users.user_login for Assabil USER_LOGIN.

Revision ID: 012_user_login
Revises: 011_widen_payment_mode
Create Date: 2026-11-02
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "012_user_login"
down_revision = "011_widen_payment_mode"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("user_login", sa.String(length=100), nullable=True))
    op.create_index("ix_users_user_login", "users", ["user_login"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_users_user_login", table_name="users")
    op.drop_column("users", "user_login")
