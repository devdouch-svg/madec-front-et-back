"""add_missing_cdc_fields

Adds fields required by CDC v2.3 that were missing from the initial schema:
- users.societe, users.agence
- orders.agence, orders.discount_total, orders.pushed_at
- order_lines.sorder_line_code, order_lines.discount
- order_lines.quantity / bl_quantity type change: Integer → Numeric(10,3)

Revision ID: a8f3c2d1e9b5
Revises: ccff69c17e87
Create Date: 2026-06-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a8f3c2d1e9b5"
down_revision: Union[str, None] = "ccff69c17e87"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────────────────────
    op.add_column("users", sa.Column("societe", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("agence",  sa.String(length=50),  nullable=True, server_default="001"))

    # ── orders ────────────────────────────────────────────────────────────────
    op.add_column("orders", sa.Column("agence",        sa.String(length=100),          nullable=True))
    op.add_column("orders", sa.Column("discount_total", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"))
    op.add_column("orders", sa.Column("pushed_at",     sa.DateTime(timezone=True),     nullable=True))

    # ── order_lines ───────────────────────────────────────────────────────────
    op.add_column("order_lines", sa.Column("sorder_line_code", sa.Integer(), nullable=True))
    op.add_column("order_lines", sa.Column("discount",         sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"))

    # Change quantity and bl_quantity from Integer to Numeric(10,3).
    # SQLite doesn't enforce column types strictly, so alter_column is safe there.
    # For MsSQL/Postgres this is a type change — data is preserved since integers
    # are valid decimals.
    op.alter_column(
        "order_lines", "quantity",
        existing_type=sa.Integer(),
        type_=sa.Numeric(precision=10, scale=3),
        existing_nullable=False,
    )
    op.alter_column(
        "order_lines", "bl_quantity",
        existing_type=sa.Integer(),
        type_=sa.Numeric(precision=10, scale=3),
        existing_nullable=True,
    )


def downgrade() -> None:
    # Revert order_lines type changes
    op.alter_column(
        "order_lines", "bl_quantity",
        existing_type=sa.Numeric(precision=10, scale=3),
        type_=sa.Integer(),
        existing_nullable=True,
    )
    op.alter_column(
        "order_lines", "quantity",
        existing_type=sa.Numeric(precision=10, scale=3),
        type_=sa.Integer(),
        existing_nullable=False,
    )

    op.drop_column("order_lines", "discount")
    op.drop_column("order_lines", "sorder_line_code")

    op.drop_column("orders", "pushed_at")
    op.drop_column("orders", "discount_total")
    op.drop_column("orders", "agence")

    op.drop_column("users", "agence")
    op.drop_column("users", "societe")
