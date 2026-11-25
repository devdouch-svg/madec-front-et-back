"""add reference catalog tables and users.ville

Revision ID: 003
Revises: 002
Create Date: 2026-06-08
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "catalog_gammes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_catalog_gammes_name", "catalog_gammes", ["name"])

    op.create_table(
        "catalog_familles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("gamme_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["gamme_id"], ["catalog_gammes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("gamme_id", "name", name="uq_catalog_famille_gamme_name"),
    )
    op.create_index("ix_catalog_familles_gamme_id", "catalog_familles", ["gamme_id"])
    op.create_index("ix_catalog_familles_name", "catalog_familles", ["name"])

    op.create_table(
        "catalog_sous_familles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("famille_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["famille_id"], ["catalog_familles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("famille_id", "name", name="uq_catalog_sous_famille_famille_name"),
    )
    op.create_index("ix_catalog_sous_familles_famille_id", "catalog_sous_familles", ["famille_id"])
    op.create_index("ix_catalog_sous_familles_name", "catalog_sous_familles", ["name"])

    op.create_table(
        "org_societes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_org_societes_code", "org_societes", ["code"])

    op.create_table(
        "org_agences",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("societe_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["societe_id"], ["org_societes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("societe_id", "code", name="uq_org_agence_societe_code"),
    )
    op.create_index("ix_org_agences_societe_id", "org_agences", ["societe_id"])
    op.create_index("ix_org_agences_code", "org_agences", ["code"])

    op.create_table(
        "org_villes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_org_villes_code", "org_villes", ["code"])

    op.add_column("users", sa.Column("ville", sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "ville")
    op.drop_table("org_villes")
    op.drop_table("org_agences")
    op.drop_table("org_societes")
    op.drop_table("catalog_sous_familles")
    op.drop_table("catalog_familles")
    op.drop_table("catalog_gammes")
