"""Pluggable mail delivery (Prompt 3).

A tiny provider-agnostic mail interface so lead-capture emails can go out via SMTP today and
a provider like Postmark/SES can be swapped in later without touching callers. Selection is
by ``MAIL_PROVIDER`` env (smtp | console | none):

- ``smtp``    — real SMTP send (STARTTLS by default).
- ``console`` — logs the email instead of sending (dev / no credentials). DEFAULT.
- ``none``    — silently drops (score still returned; no delivery).

Callers depend only on the ``Mailer`` protocol (``send(message) -> bool``), so tests inject a
fake and never touch the network.
"""

from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import List, Optional, Protocol

from saas.app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class MailMessage:
    to: List[str]
    subject: str
    html: str
    text: str = ""
    reply_to: Optional[str] = None
    from_addr: Optional[str] = None

    def build(self, default_from: str) -> EmailMessage:
        msg = EmailMessage()
        msg["From"] = self.from_addr or default_from
        msg["To"] = ", ".join(self.to)
        msg["Subject"] = self.subject
        if self.reply_to:
            msg["Reply-To"] = self.reply_to
        msg.set_content(self.text or "This email requires an HTML-capable client.")
        msg.add_alternative(self.html, subtype="html")
        return msg


class Mailer(Protocol):
    def send(self, message: MailMessage) -> bool:  # pragma: no cover - protocol
        ...


@dataclass
class ConsoleMailer:
    """Logs emails instead of sending — the safe default when no SMTP creds are set."""
    from_addr: str = settings.mail_from
    sent: list = field(default_factory=list)

    def send(self, message: MailMessage) -> bool:
        self.sent.append(message)
        logger.info("[ConsoleMailer] to=%s subject=%r (%d chars html)",
                    message.to, message.subject, len(message.html))
        return True


@dataclass
class NullMailer:
    """Drops everything (MAIL_PROVIDER=none)."""
    def send(self, message: MailMessage) -> bool:
        return False


@dataclass
class SMTPMailer:
    host: str
    port: int
    user: str
    password: str
    use_tls: bool = True
    from_addr: str = settings.mail_from

    def send(self, message: MailMessage) -> bool:
        try:
            msg = message.build(self.from_addr)
            with smtplib.SMTP(self.host, self.port, timeout=20) as server:
                if self.use_tls:
                    server.starttls()
                if self.user:
                    server.login(self.user, self.password)
                server.send_message(msg)
            return True
        except Exception as exc:  # never raise into the request path
            logger.warning("SMTP send failed: %s", exc)
            return False


def get_mailer() -> Mailer:
    """Build the configured mailer. Falls back to ConsoleMailer if SMTP is selected but
    unconfigured, so a missing credential degrades to a logged email, not a crash."""
    provider = (settings.mail_provider or "console").strip().lower()
    if provider == "none":
        return NullMailer()
    if provider == "smtp" and settings.smtp_host:
        return SMTPMailer(
            host=settings.smtp_host, port=settings.smtp_port,
            user=settings.smtp_user, password=settings.smtp_password,
            use_tls=settings.smtp_use_tls, from_addr=settings.mail_from,
        )
    return ConsoleMailer(from_addr=settings.mail_from)
