"""Async SMTP sender via aiosmtplib."""
from email.message import EmailMessage

import aiosmtplib

from ..core.settings import NotificationSettings


async def send_email(
    settings: NotificationSettings,
    *,
    to: str,
    subject: str,
    body_html: str,
    body_text: str | None = None,
) -> None:
    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg["Subject"] = subject
    if body_text:
        msg.set_content(body_text)
        msg.add_alternative(body_html, subtype="html")
    else:
        msg.set_content(body_html, subtype="html")

    await aiosmtplib.send(
        msg, hostname=settings.smtp_host, port=settings.smtp_port,
        username=settings.smtp_user or None,
        password=settings.smtp_password or None,
        start_tls=settings.smtp_port == 587,
    )
