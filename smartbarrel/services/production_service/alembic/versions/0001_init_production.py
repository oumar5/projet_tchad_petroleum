"""init production schema

Revision ID: 0001_init_production
Revises:
Create Date: 2026-04-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_init_production"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS production")

    op.create_table(
        "blocks",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("code", sa.Text(), unique=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text()),
        schema="production",
    )

    op.create_table(
        "wells",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("code", sa.Text(), unique=True, nullable=False),
        sa.Column("block_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("production.blocks.id"), nullable=False),
        sa.Column("pump_type", sa.Text()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        schema="production",
    )
    op.create_index("ix_wells_block_id", "wells", ["block_id"], schema="production")

    op.create_table(
        "daily_production",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("block_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("production.blocks.id"), nullable=False),
        sa.Column("well_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("production.wells.id")),
        sa.Column("wells_total", sa.Integer(), nullable=False),
        sa.Column("wells_active", sa.Integer(), nullable=False),
        sa.Column("oil_bbl", sa.Numeric(12, 2), nullable=False),
        sa.Column("water_bbl", sa.Numeric(12, 2), nullable=False),
        sa.Column("watercut_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("wor", sa.Numeric(8, 3)),
        sa.Column("water_kbbl_day", sa.Numeric(10, 3)),
        sa.Column("source", sa.Text(), server_default="manual", nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("date", "block_id", "well_id"),
        sa.CheckConstraint("watercut_pct BETWEEN 0 AND 100"),
        sa.CheckConstraint("oil_bbl >= 0"),
        sa.CheckConstraint("water_bbl >= 0"),
        schema="production",
    )
    op.create_index("ix_daily_date_block", "daily_production",
                    ["date", "block_id"], schema="production")
    op.create_index("ix_daily_block_date", "daily_production",
                    ["block_id", "date"], schema="production")


def downgrade() -> None:
    op.drop_table("daily_production", schema="production")
    op.drop_table("wells", schema="production")
    op.drop_table("blocks", schema="production")
