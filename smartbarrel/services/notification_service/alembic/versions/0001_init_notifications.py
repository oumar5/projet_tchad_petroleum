"""init notifications schema

Revision ID: 0001_init_notifications
Revises:
Create Date: 2026-04-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_init_notifications"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS notifications")

    op.create_table(
        "templates",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column("locale", sa.Text(), server_default="fr", nullable=False),
        sa.Column("subject", sa.Text()),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("variables", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("code", "channel", "locale"),
        schema="notifications",
    )

    op.create_table(
        "preferences",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("push_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("failure_alerts", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("weekly_report", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("fcm_token", sa.Text()),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        schema="notifications",
    )

    op.create_table(
        "sent_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("template_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("notifications.templates.id")),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column("recipient", sa.Text(), nullable=False),
        sa.Column("subject", sa.Text()),
        sa.Column("body", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("error", sa.Text()),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        schema="notifications",
    )
    op.create_index("ix_sent_user_created", "sent_messages",
                    ["user_id", "created_at"], schema="notifications")
    op.create_index("ix_sent_status_created", "sent_messages",
                    ["status", "created_at"], schema="notifications")


def downgrade() -> None:
    op.drop_table("sent_messages", schema="notifications")
    op.drop_table("preferences", schema="notifications")
    op.drop_table("templates", schema="notifications")
