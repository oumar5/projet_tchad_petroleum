"""init etl schema

Revision ID: 0001_init_etl
Revises:
Create Date: 2026-04-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_init_etl"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS etl")

    op.create_table(
        "snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("label", sa.Text(), unique=True, nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("source_uri", sa.Text()),
        sa.Column("row_counts", postgresql.JSONB()),
        sa.Column("file_hash", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        schema="etl",
    )

    op.create_table(
        "runs",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("etl.snapshots.id")),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("rows_processed", sa.Integer()),
        sa.Column("rows_skipped", sa.Integer()),
        sa.Column("rows_failed", sa.Integer()),
        sa.Column("error_message", sa.Text()),
        sa.Column("metadata", postgresql.JSONB()),
        schema="etl",
    )
    op.create_index("ix_runs_status_started", "runs",
                    ["status", "started_at"], schema="etl")

    op.create_table(
        "migration_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("phase", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("rows_processed", sa.Integer()),
        sa.Column("error_message", sa.Text()),
        sa.Column("metadata", postgresql.JSONB()),
        schema="etl",
    )


def downgrade() -> None:
    op.drop_table("migration_runs", schema="etl")
    op.drop_table("runs", schema="etl")
    op.drop_table("snapshots", schema="etl")
