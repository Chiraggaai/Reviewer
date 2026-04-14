import logging
import smtplib
from email.message import EmailMessage
from typing import Literal

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_reviewer_invitation_email(
    *,
    to_email: str,
    recipient_name: str,
    username: str,
    plain_password: str,
) -> Literal["sent", "dry_run"]:
    subject = "Your Glimmora reviewer account"
    body = (
        f"Hello {recipient_name},\n\n"
        "You have been invited as a reviewer. Use the credentials below to sign in, "
        "then complete MFA and change your password if prompted.\n\n"
        f"Username: {username}\n"
        f"Temporary password: {plain_password}\n\n"
        "If you did not expect this message, you can ignore it.\n"
    )

    if settings.INVITATION_EMAIL_DRY_RUN or not settings.SMTP_HOST:
        if settings.INVITATION_EMAIL_DRY_RUN:
            logger.info(
                "[invitation email dry-run] to=%s subject=%s\n%s",
                to_email,
                subject,
                body,
            )
            return "dry_run"
        raise RuntimeError("SMTP_HOST is not configured.")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD is not None:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)
    return "sent"
