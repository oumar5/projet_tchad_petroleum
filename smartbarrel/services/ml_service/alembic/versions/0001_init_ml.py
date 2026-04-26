"""init ml schema

Revision ID: 0001_init_ml
Revises:
Create Date: 2026-04-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_init_ml"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS ml")

    op.create_table(
        "models",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("model_type", sa.Text(), nullable=False),
        sa.Column("algorithm", sa.Text(), nullable=False),
        sa.Column("metrics", postgresql.JSONB(), nullable=False),
        sa.Column("hyperparameters", postgresql.JSONB(), nullable=False),
        sa.Column("training_dataset_id", postgresql.UUID(as_uuid=True)),
        sa.Column("blob_url", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("trained_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trained_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("name", "version"),
        schema="ml",
    )
    op.create_index("ix_models_type_active", "models", ["model_type", "is_active"], schema="ml")
    op.execute("""
        CREATE UNIQUE INDEX one_active_per_type ON ml.models (model_type)
        WHERE is_active = true
    """)

    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("job_type", sa.Text(), nullable=False),
        sa.Column("model_type", sa.Text()),
        sa.Column("algorithm", sa.Text()),
        sa.Column("status", sa.Text(), server_default="queued", nullable=False),
        sa.Column("params", postgresql.JSONB()),
        sa.Column("result", postgresql.JSONB()),
        sa.Column("error", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        schema="ml",
    )
    op.create_index("ix_jobs_status_created", "jobs", ["status", "created_at"], schema="ml")

    op.create_table(
        "predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("model_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("ml.models.id"), nullable=False),
        sa.Column("prediction_type", sa.Text(), nullable=False),
        sa.Column("input_data", postgresql.JSONB(), nullable=False),
        sa.Column("output_data", postgresql.JSONB(), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4)),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        schema="ml",
    )
    op.create_index("ix_pred_model_created", "predictions",
                    ["model_id", "created_at"], schema="ml")
    op.create_index("ix_pred_type_created", "predictions",
                    ["prediction_type", "created_at"], schema="ml")


def downgrade() -> None:
    op.drop_table("predictions", schema="ml")
    op.drop_table("jobs", schema="ml")
    op.drop_table("models", schema="ml")
