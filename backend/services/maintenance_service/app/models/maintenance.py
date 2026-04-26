from datetime import date as Date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint, Date as DateCol, DateTime, ForeignKey, Index, Integer,
    Numeric, Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.db import Base
from shared.db.base import TimestampMixin, UUIDMixin


class Equipment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "equipment"
    __table_args__ = {"schema": "maintenance"}

    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    well_code: Mapped[str | None] = mapped_column(Text)
    install_date: Mapped[Date | None] = mapped_column(DateCol)
    status: Mapped[str] = mapped_column(Text, default="active", nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSONB)


class Failure(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "failures"
    __table_args__ = (
        CheckConstraint("severity IN ('low','medium','high','critical')"),
        Index("ix_failures_notif_date", "notification_date"),
        Index("ix_failures_block_date", "block", "notification_date"),
        {"schema": "maintenance"},
    )

    notification_date: Mapped[Date] = mapped_column(DateCol, nullable=False)
    block: Mapped[str] = mapped_column(Text, nullable=False)
    equipment_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("maintenance.equipment.id")
    )
    failure_type: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    estimated_duration_h: Mapped[int | None] = mapped_column(Integer)
    repair_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    parts_replaced: Mapped[dict | None] = mapped_column(JSONB)
    reported_by: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSONB)


class Intervention(UUIDMixin, Base):
    __tablename__ = "interventions"
    __table_args__ = (
        Index("ix_interv_date", "intervention_date"),
        {"schema": "maintenance"},
    )

    failure_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("maintenance.failures.id")
    )
    intervention_date: Mapped[Date] = mapped_column(DateCol, nullable=False)
    intervention_type: Mapped[str] = mapped_column(Text, nullable=False)
    duration_h: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    personnel: Mapped[dict | None] = mapped_column(JSONB)
    result: Mapped[str | None] = mapped_column(Text)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    notes: Mapped[str | None] = mapped_column(Text)
    performed_by: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
