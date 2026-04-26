"""Async RabbitMQ consumer dispatching events to handlers."""
import asyncio
import logging
from typing import Any

from sqlalchemy.ext.asyncio import async_sessionmaker

from shared.messaging import EventConsumer

from ..core.settings import NotificationSettings
from ..models import SentMessage
from ..services.email_sender import send_email
from ..services.template_renderer import render

log = logging.getLogger(__name__)


WELCOME_TEMPLATE = """
<h1>Bienvenue sur SmartBarrel, {{ full_name }}</h1>
<p>Votre compte ({{ email }}) a été créé avec succès.</p>
"""

FAILURE_ALERT_TEMPLATE = """
<h2>⚠️ Alerte panne prédite — Bloc {{ block }}</h2>
<p>Probabilité de panne sous {{ horizon_days }} jours : <strong>{{ probability }}%</strong></p>
"""


async def handle_event(routing_key: str, payload: dict[str, Any],
                       settings: NotificationSettings,
                       session_factory: async_sessionmaker) -> None:
    log.info("notification.received", extra={"routing_key": routing_key})

    if routing_key == "user.created":
        body = render(WELCOME_TEMPLATE, {
            "full_name": payload.get("full_name", ""),
            "email": payload.get("email", ""),
        })
        await _send_and_record(
            session_factory, settings, channel="email",
            recipient=payload["email"], subject="Bienvenue sur SmartBarrel",
            body_html=body,
        )
    elif routing_key == "alert.failure_predicted":
        recipients = payload.get("recipients", [])
        body = render(FAILURE_ALERT_TEMPLATE, payload)
        for r in recipients:
            await _send_and_record(
                session_factory, settings, channel="email",
                recipient=r, subject="SmartBarrel — Alerte de panne",
                body_html=body,
            )


async def _send_and_record(session_factory, settings, *, channel, recipient,
                           subject, body_html) -> None:
    status = "sent"
    error: str | None = None
    try:
        await send_email(settings, to=recipient, subject=subject, body_html=body_html)
    except Exception as e:
        status = "failed"
        error = str(e)
    async with session_factory() as session:
        session.add(SentMessage(
            channel=channel, recipient=recipient, subject=subject,
            body=body_html, status=status, error=error,
        ))
        await session.commit()


async def run_consumer(settings: NotificationSettings, session_factory) -> None:
    consumer = EventConsumer(
        amqp_url=settings.rabbitmq_url,
        queue_name="notification-service",
        routing_keys=["user.*", "alert.*", "prediction.*"],
    )

    async def handler(rk: str, payload: dict[str, Any]) -> None:
        await handle_event(rk, payload, settings, session_factory)

    while True:
        try:
            await consumer.consume(handler)
        except Exception as e:
            log.exception("consumer crashed: %s", e)
            await asyncio.sleep(5)
