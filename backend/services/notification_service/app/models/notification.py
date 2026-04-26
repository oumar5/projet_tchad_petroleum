from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.db import Base
from shared.db.base import TimestampMixin, UUIDMixin


class Template(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "templates"
    __table_args__ = (
        UniqueConstraint("code", "channel", "locale"),
        {"schema": "notifications"},
    )

    code: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    locale: Mapped[str] = mapped_column(Text, default="fr", nullable=False)
    subject: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[dict | None] = mapped_column(JSONB)


class Preference(Base):
    __tablename__ = "preferences"
    __table_args__ = {"schema": "notifications"}

    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    failure_alerts: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    weekly_report: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fcm_token: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )


class SentMessage(UUIDMixin, Base):
    __tablename__ = "sent_messages"
    __table_args__ = (
        Index("ix_sent_user_created", "user_id", "created_at"),
        Index("ix_sent_status_created", "status", "created_at"),
        {"schema": "notifications"},
    )

    user_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True))
    template_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("notifications.templates.id")
    )
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    recipient: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    error: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
