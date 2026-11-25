"""add matricule, langue, synced_from_intermediate to users and products

Revision ID: 001
Revises: a8f3c2d1e9b5
Create Date: 2026-06-06
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = "a8f3c2d1e9b5"
branch_labels = None
depends_on = None


def _col_exists(table: str, column: str) -> bool:
    """Return True if column already exists (safe for re-running on upgraded DBs)."""
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT COUNT(1) FROM sys.columns "
        "WHERE Object_ID = Object_ID(:table) AND Name = :col"
    ), {"table": table, "col": column})
    return bool(result.scalar())


def upgrade() -> None:
    if not _col_exists("users", "matricule"):
        op.add_column("users", sa.Column("matricule", sa.String(50), nullable=True))
        # Filtered unique index: SQL Server rejects a standard UNIQUE index when
        # multiple rows have NULL (treats NULLs as duplicates). A WHERE filter
        # enforces uniqueness only on non-NULL values, which is the correct behaviour.
        op.execute(
            "CREATE UNIQUE INDEX ix_users_matricule ON users (matricule) "
            "WHERE matricule IS NOT NULL"
        )

    if not _col_exists("users", "langue"):
        op.add_column("users", sa.Column("langue", sa.String(5), nullable=False, server_default="fr"))

    if not _col_exists("users", "synced_from_intermediate"):
        op.add_column("users", sa.Column(
            "synced_from_intermediate", sa.Boolean(), nullable=False, server_default="0"
        ))

    if not _col_exists("products", "synced_from_intermediate"):
        op.add_column("products", sa.Column(
            "synced_from_intermediate", sa.Boolean(), nullable=False, server_default="0"
        ))


def downgrade() -> None:
    # Products
    if _col_exists("products", "synced_from_intermediate"):
        op.drop_column("products", "synced_from_intermediate")

    # Users
    if _col_exists("users", "synced_from_intermediate"):
        op.drop_column("users", "synced_from_intermediate")
    if _col_exists("users", "langue"):
        op.drop_column("users", "langue")
    if _col_exists("users", "matricule"):
        op.execute(
            "IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ix_users_matricule') "
            "DROP INDEX ix_users_matricule ON users"
        )
        op.drop_column("users", "matricule")
