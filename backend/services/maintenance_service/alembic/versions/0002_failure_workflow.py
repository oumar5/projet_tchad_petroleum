"""failures workflow + attachments

Revision ID: 0002_failure_workflow
Revises: 0001_init_maintenance
Create Date: 2026-04-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_failure_workflow"
down_revision: Union[str, None] = "0001_init_maintenance"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- failures: status, assigned_to, well_code, last_updated_by ---
    op.add_column(
        "failures",
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default="pending",
        ),
        schema="maintenance",
    )
    op.create_check_constraint(
        "failures_status_check",
        "failures",
        "status IN ('pending','in_progress','resolved','cancelled')",
        schema="maintenance",
    )
    op.add_column(
        "failures",
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True)),
        schema="maintenance",
    )
    op.add_column(
        "failures",
        sa.Column("well_code", sa.Text()),
        schema="maintenance",
    )
    op.add_column(
        "failures",
        sa.Column("last_updated_by", postgresql.UUID(as_uuid=True)),
        schema="maintenance",
    )
    op.create_index(
        "ix_failures_status",
        "failures",
        ["status"],
        schema="maintenance",
    )

    # Backfill: failures with resolved_at → status='resolved'
    op.execute(
        """
        UPDATE maintenance.failures
        SET status = 'resolved'
        WHERE resolved_at IS NOT NULL
        """
    )

    # --- attachments table ---
    op.create_table(
        "attachments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "failure_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("maintenance.failures.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "intervention_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("maintenance.interventions.id", ondelete="CASCADE"),
        ),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(failure_id IS NOT NULL)::int + (intervention_id IS NOT NULL)::int = 1",
            name="attachments_one_parent",
        ),
        schema="maintenance",
    )
    op.create_index(
        "ix_attachments_failure",
        "attachments",
        ["failure_id"],
        schema="maintenance",
    )
    op.create_index(
        "ix_attachments_intervention",
        "attachments",
        ["intervention_id"],
        schema="maintenance",
    )


def downgrade() -> None:
    op.drop_index("ix_attachments_intervention", "attachments", schema="maintenance")
    op.drop_index("ix_attachments_failure", "attachments", schema="maintenance")
    op.drop_table("attachments", schema="maintenance")

    op.drop_index("ix_failures_status", "failures", schema="maintenance")
    op.drop_column("failures", "last_updated_by", schema="maintenance")
    op.drop_column("failures", "well_code", schema="maintenance")
    op.drop_column("failures", "assigned_to", schema="maintenance")
    op.drop_constraint("failures_status_check", "failures", schema="maintenance")
    op.drop_column("failures", "status", schema="maintenance")
