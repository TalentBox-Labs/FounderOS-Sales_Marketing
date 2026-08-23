"""Email integration for transactional and campaign messages."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EmailTemplate:
    """Email template with variables."""

    name: str
    subject: str
    html_body: str
    text_body: str
    variables: list[str]  # Variable names like {{first_name}}

    def render(self, context: dict[str, Any]) -> tuple[str, str, str]:
        """Render template with context variables."""
        subject = self.subject
        html = self.html_body
        text = self.text_body

        for key, value in context.items():
            placeholder = "{{" + key + "}}"
            subject = subject.replace(placeholder, str(value))
            html = html.replace(placeholder, str(value))
            text = text.replace(placeholder, str(value))

        return subject, html, text


class EmailNotifier:
    """Send emails via SMTP."""

    _smtp_config: dict[str, Any] | None = None
    _templates: dict[str, EmailTemplate] = {}

    @classmethod
    def configure_smtp(cls, config: dict[str, Any]) -> None:
        """Configure SMTP server."""
        cls._smtp_config = config
        logger.info("SMTP configured", extra={"host": config.get("host")})

    @classmethod
    def register_template(cls, template: EmailTemplate) -> None:
        """Register an email template."""
        cls._templates[template.name] = template
        logger.info(f"Email template registered: {template.name}")

    @classmethod
    def send_email(
        cls,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
    ) -> bool:
        """Send an email."""
        if not cls._smtp_config:
            logger.warning("SMTP not configured")
            return False

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = cls._smtp_config.get("from_email", "noreply@workcrew.ai")
            msg["To"] = to_email

            if cc:
                msg["Cc"] = ", ".join(cc)

            if text_body:
                msg.attach(MIMEText(text_body, "plain"))

            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(
                cls._smtp_config.get("host"),
                cls._smtp_config.get("port", 587),
                timeout=10,
            ) as server:
                if cls._smtp_config.get("use_tls", True):
                    server.starttls()

                if cls._smtp_config.get("username"):
                    server.login(
                        cls._smtp_config["username"],
                        cls._smtp_config["password"],
                    )

                recipients = [to_email]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)

                server.sendmail(msg["From"], recipients, msg.as_string())

            logger.info(f"Email sent to {to_email}", extra={"subject": subject})
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

    @classmethod
    def send_template_email(
        cls,
        template_name: str,
        to_email: str,
        context: dict[str, Any],
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
    ) -> bool:
        """Send email using a template."""
        template = cls._templates.get(template_name)
        if not template:
            logger.error(f"Template not found: {template_name}")
            return False

        subject, html, text = template.render(context)
        return cls.send_email(to_email, subject, html, text, cc, bcc)

    @classmethod
    def send_batch_emails(
        cls, recipients: list[tuple[str, dict[str, Any]]], template_name: str
    ) -> dict[str, Any]:
        """Send emails to multiple recipients using a template."""
        template = cls._templates.get(template_name)
        if not template:
            logger.error(f"Template not found: {template_name}")
            return {"ok": False, "sent": 0, "failed": 0}

        sent = 0
        failed = 0

        for email, context in recipients:
            if cls.send_template_email(template_name, email, context):
                sent += 1
            else:
                failed += 1

        return {
            "ok": True,
            "sent": sent,
            "failed": failed,
            "total": len(recipients),
        }


class ScheduledEmailQueue:
    """Queue for scheduled email sends."""

    _queue: list[dict[str, Any]] = []

    @classmethod
    def schedule_email(
        cls,
        to_email: str,
        template_name: str,
        context: dict[str, Any],
        send_at: datetime,
        cc: list[str] | None = None,
    ) -> bool:
        """Schedule an email to be sent at a specific time."""
        item = {
            "to_email": to_email,
            "template_name": template_name,
            "context": context,
            "send_at": send_at,
            "cc": cc or [],
            "sent": False,
            "created_at": datetime.now(timezone.utc),
        }
        cls._queue.append(item)
        logger.info(
            f"Email scheduled for {to_email}",
            extra={"send_at": send_at.isoformat()},
        )
        return True

    @classmethod
    def get_pending_emails(cls) -> list[dict[str, Any]]:
        """Get all pending emails that should be sent."""
        now = datetime.now(timezone.utc)
        pending = [item for item in cls._queue if not item["sent"] and item["send_at"] <= now]
        return pending

    @classmethod
    def process_pending_emails(cls) -> dict[str, Any]:
        """Process and send all pending emails."""
        pending = cls.get_pending_emails()
        sent = 0
        failed = 0

        for item in pending:
            if EmailNotifier.send_template_email(
                item["template_name"],
                item["to_email"],
                item["context"],
                item["cc"],
            ):
                item["sent"] = True
                sent += 1
            else:
                failed += 1

        logger.info(f"Processed scheduled emails", extra={"sent": sent, "failed": failed})
        return {"ok": True, "sent": sent, "failed": failed}
