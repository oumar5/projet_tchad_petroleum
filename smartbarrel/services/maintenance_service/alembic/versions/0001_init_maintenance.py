"""init maintenance schema

Revision ID: 0001_init_maintenance
Revises:
Create Date: 2026-04-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_init_maintenance"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS maintenance")

    op.create_table(
        "equipment",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("code", sa.Text(), unique=True, nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("well_code", sa.Text()),
        sa.Column("install_date", sa.Date()),
        sa.Column("status", sa.Text(), server_default="active", nullable=False),
        sa.Column("metadata", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        schema="maintenance",
    )

    op.create_table(
        "failures",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("notification_date", sa.Date(), nullable=False),
        sa.Column("block", sa.Text(), nullable=False),
        sa.Column("equipment_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("maintenance.equipment.id")),
        sa.Column("failure_type", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("estimated_duration_h", sa.Integer()),
        sa.Column("repair_cost", sa.Numeric(12, 2)),
        sa.Column("parts_replaced", postgresql.JSONB()),
        sa.Column("reported_by", postgresql.UUID(as_uuid=True)),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("metadata", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("severity IN ('low','medium','high','critical')"),
        schema="maintenance",
    )
    op.create_index("ix_failures_notif_date", "failures",
                    ["notification_date"], schema="maintenance")
    op.create_index("ix_failures_block_date", "failures",
                    ["block", "notification_date"], schema="maintenance")

    op.create_table(
        "interventions",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("failure_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("maintenance.failures.id")),
        sa.Column("intervention_date", sa.Date(), nullable=False),
        sa.Column("intervention_type", sa.Text(), nullable=False),
        sa.Column("duration_h", sa.Numeric(6, 2)),
        sa.Column("personnel", postgresql.JSONB()),
        sa.Column("result", sa.Text()),
        sa.Column("cost", sa.Numeric(12, 2)),
        sa.Column("notes", sa.Text()),
        sa.Column("performed_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        schema="maintenance",
    )
    op.create_index("ix_interv_date", "interventions",
                    ["intervention_date"], schema="maintenance")


def downgrade() -> None:
    op.drop_table("interventions", schema="maintenance")
    op.drop_table("failures", schema="maintenance")
    op.drop_table("equipment", schema="maintenance")
