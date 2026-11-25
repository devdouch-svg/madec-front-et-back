"""make users.email nullable (ETL/Assabil users have a matricule, not an email)

Revision ID: 007
Revises: 006
Create Date: 2026-07-20
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the standard UNIQUE index on email — SQL Server treats multiple NULLs
    # as duplicates, so it would reject more than one user without an email.
    op.execute(
        "IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ix_users_email') "
        "DROP INDEX ix_users_email ON users"
    )

    # Make email nullable — back-office users have an email, ETL-synced users don't.
    op.alter_column(
        "users", "email",
        existing_type=sa.String(255),
        nullable=True,
    )

    # Recreate as a filtered UNIQUE index: non-NULL emails stay unique, multiple
    # NULLs are allowed (same pattern as ix_users_matricule).
    op.execute(
        "CREATE UNIQUE INDEX ix_users_email ON users (email) "
        "WHERE email IS NOT NULL"
    )


def downgrade() -> None:
    op.execute(
        "IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ix_users_email') "
        "DROP INDEX ix_users_email ON users"
    )
    op.alter_column(
        "users", "email",
        existing_type=sa.String(255),
        nullable=False,
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
