"""add zones table and Block.zone_id

Revision ID: 0002_add_zones
Revises: 0001_init_production
Create Date: 2026-04-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_add_zones"
down_revision: Union[str, None] = "0001_init_production"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "zones",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("code", sa.Text(), unique=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text()),
        schema="production",
    )

    # Default zone: every existing block is migrated under "TCHAD".
    op.execute(
        "INSERT INTO production.zones (code, name) "
        "VALUES ('TCHAD', 'Tchad — zone par défaut')"
    )

    # Add zone_id (nullable temporarily, then back-fill, then NOT NULL).
    op.add_column(
        "blocks",
        sa.Column(
            "zone_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("production.zones.id"),
            nullable=True,
        ),
        schema="production",
    )
    op.execute(
        "UPDATE production.blocks "
        "SET zone_id = (SELECT id FROM production.zones WHERE code = 'TCHAD')"
    )
    op.alter_column("blocks", "zone_id", nullable=False, schema="production")
    op.create_index("ix_blocks_zone_id", "blocks", ["zone_id"], schema="production")


def downgrade() -> None:
    op.drop_index("ix_blocks_zone_id", "blocks", schema="production")
    op.drop_column("blocks", "zone_id", schema="production")
    op.drop_table("zones", schema="production")
