import smtplib
from email.message import EmailMessage
import logging

import resend

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_streak_reminder(email: str) -> None:
    if settings.resend_api_key:
        try:
            resend.api_key = settings.resend_api_key
            resend.Emails.send(
                {
                    "from": settings.resend_from_email,
                    "to": [email],
                    "subject": "Your reading streak needs attention",
                    "html": "<p>You missed your reading goal today. Open the app now and get back on track.</p>",
                }
            )
        except Exception as exc:
            logger.exception("Resend reminder failed for %s: %s", email, exc)
        return

    if settings.smtp_host and settings.smtp_user:
        try:
            msg = EmailMessage()
            msg["Subject"] = "Your reading streak needs attention"
            msg["From"] = settings.smtp_from_email
            msg["To"] = email
            msg.set_content(
                "You missed your reading goal today. Open the app now and get back on track.")

            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
        except Exception as exc:
            logger.exception("SMTP reminder failed for %s: %s", email, exc)
