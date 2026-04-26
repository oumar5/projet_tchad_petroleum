from datetime import date as Date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean, CheckConstraint, Date as DateCol, ForeignKey, Index, Integer,
    Numeric, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.db import Base
from shared.db.base import TimestampMixin, UUIDMixin


class Block(UUIDMixin, Base):
    __tablename__ = "blocks"
    __table_args__ = {"schema": "production"}

    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    wells: Mapped[list["Well"]] = relationship(back_populates="block")


class Well(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "wells"
    __table_args__ = (
        Index("ix_wells_block_id", "block_id"),
        {"schema": "production"},
    )

    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    block_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("production.blocks.id"), nullable=False
    )
    pump_type: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    block: Mapped[Block] = relationship(back_populates="wells")


class DailyProduction(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "daily_production"
    __table_args__ = (
        UniqueConstraint("date", "block_id", "well_id"),
        CheckConstraint("watercut_pct BETWEEN 0 AND 100"),
        CheckConstraint("oil_bbl >= 0"),
        CheckConstraint("water_bbl >= 0"),
        Index("ix_daily_date_block", "date", "block_id"),
        Index("ix_daily_block_date", "block_id", "date"),
        {"schema": "production"},
    )

    date: Mapped[Date] = mapped_column(DateCol, nullable=False)
    block_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("production.blocks.id"), nullable=False
    )
    well_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("production.wells.id")
    )
    wells_total: Mapped[int] = mapped_column(Integer, nullable=False)
    wells_active: Mapped[int] = mapped_column(Integer, nullable=False)
    oil_bbl: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    water_bbl: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    watercut_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    wor: Mapped[Decimal | None] = mapped_column(Numeric(8, 3))
    water_kbbl_day: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    source: Mapped[str] = mapped_column(Text, default="manual", nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True))
