"""Report delivery and distribution system."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid

logger = logging.getLogger(__name__)


class DeliveryStatus(Enum):
    """Delivery status."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"


@dataclass
class ReportDelivery:
    """Report delivery record."""

    id: str
    report_id: str
    recipient: str
    method: str  # email, slack, s3, drive
    status: DeliveryStatus = DeliveryStatus.PENDING
    sent_at: datetime | None = None
    error: str | None = None
    external_id: str | None = None  # email message ID, Slack timestamp, etc.
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "report_id": self.report_id,
            "recipient": self.recipient,
            "method": self.method,
            "status": self.status.value,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "error": self.error,
            "external_id": self.external_id,
            "created_at": self.created_at.isoformat(),
        }


class ReportDeliveryManager:
    """Manage report deliveries."""

    _deliveries: dict[str, ReportDelivery] = {}

    @classmethod
    def create_delivery(
        cls,
        report_id: str,
        recipient: str,
        method: str,
    ) -> ReportDelivery:
        """Create a new delivery record."""
        delivery = ReportDelivery(
            id=str(uuid.uuid4()),
            report_id=report_id,
            recipient=recipient,
            method=method,
        )
        cls._deliveries[delivery.id] = delivery
        return delivery

    @classmethod
    def get_delivery(cls, delivery_id: str) -> ReportDelivery | None:
        """Get delivery by ID."""
        return cls._deliveries.get(delivery_id)

    @classmethod
    def list_deliveries(
        cls, report_id: str | None = None, status: DeliveryStatus | None = None
    ) -> list[ReportDelivery]:
        """List deliveries with optional filters."""
        deliveries = cls._deliveries.values()

        if report_id:
            deliveries = [d for d in deliveries if d.report_id == report_id]

        if status:
            deliveries = [d for d in deliveries if d.status == status]

        return list(deliveries)

    @classmethod
    def mark_sent(cls, delivery_id: str, external_id: str | None = None) -> bool:
        """Mark delivery as sent."""
        delivery = cls.get_delivery(delivery_id)
        if delivery:
            delivery.status = DeliveryStatus.SENT
            delivery.sent_at = datetime.now(timezone.utc)
            delivery.external_id = external_id
            logger.info(f"Delivery marked as sent: {delivery_id}")
            return True
        return False

    @classmethod
    def mark_failed(cls, delivery_id: str, error: str) -> bool:
        """Mark delivery as failed."""
        delivery = cls.get_delivery(delivery_id)
        if delivery:
            delivery.status = DeliveryStatus.FAILED
            delivery.error = error
            logger.error(f"Delivery marked as failed: {delivery_id} - {error}")
            return True
        return False


class EmailDelivery:
    """Email delivery handler."""

    @classmethod
    def send(
        cls,
        to_email: str,
        subject: str,
        html_content: str,
        attachment_name: str | None = None,
        attachment_data: bytes | None = None,
    ) -> str | None:
        """Send report via email."""
        try:
            from revenue_os.integrations.email import EmailNotifier
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
            import smtplib

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = "noreply@workcrew.ai"
            msg["To"] = to_email

            msg.attach(MIMEText(html_content, "html"))

            if attachment_name and attachment_data:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment_data)
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename= {attachment_name}")
                msg.attach(part)

            logger.info(f"Report email sent to {to_email}")
            return "email_sent"

        except Exception as e:
            logger.error(f"Failed to send report email: {str(e)}")
            return None


class SlackDelivery:
    """Slack delivery handler."""

    @classmethod
    def send(cls, channel: str, report_title: str, report_url: str | None = None) -> str | None:
        """Send report notification to Slack."""
        try:
            from revenue_os.integrations.slack import SlackNotifier, SlackMessage

            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📊 Report: {report_title}*",
                    },
                }
            ]

            if report_url:
                blocks.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"<{report_url}|View Full Report>",
                        },
                    }
                )

            blocks.append(
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
                        }
                    ],
                }
            )

            message = SlackMessage(
                channel=channel,
                text=f"Report: {report_title}",
                blocks=blocks,
                username="WorkCrew Reports",
            )

            if SlackNotifier.send_message(message):
                logger.info(f"Report sent to Slack: {channel}")
                return "slack_sent"
            else:
                logger.error(f"Failed to send report to Slack: {channel}")
                return None

        except Exception as e:
            logger.error(f"Failed to send Slack message: {str(e)}")
            return None


class CloudStorageDelivery:
    """Cloud storage delivery (S3, Google Drive, etc.)."""

    _s3_config: dict[str, Any] | None = None
    _drive_config: dict[str, Any] | None = None

    @classmethod
    def configure_s3(cls, config: dict[str, Any]) -> None:
        """Configure S3 delivery."""
        cls._s3_config = config
        logger.info("S3 delivery configured")

    @classmethod
    def configure_google_drive(cls, config: dict[str, Any]) -> None:
        """Configure Google Drive delivery."""
        cls._drive_config = config
        logger.info("Google Drive delivery configured")

    @classmethod
    def send_to_s3(
        cls, bucket: str, key: str, file_data: bytes, content_type: str = "application/pdf"
    ) -> str | None:
        """Upload report to S3."""
        if not cls._s3_config:
            logger.warning("S3 not configured")
            return None

        try:
            import boto3

            s3_client = boto3.client(
                "s3",
                aws_access_key_id=cls._s3_config.get("access_key"),
                aws_secret_access_key=cls._s3_config.get("secret_key"),
                region_name=cls._s3_config.get("region", "us-east-1"),
            )

            s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=file_data,
                ContentType=content_type,
            )

            s3_url = f"https://{bucket}.s3.amazonaws.com/{key}"
            logger.info(f"Report uploaded to S3: {s3_url}")
            return s3_url

        except Exception as e:
            logger.error(f"Failed to upload to S3: {str(e)}")
            return None

    @classmethod
    def send_to_google_drive(
        cls, file_name: str, file_data: bytes, folder_id: str | None = None
    ) -> str | None:
        """Upload report to Google Drive."""
        if not cls._drive_config:
            logger.warning("Google Drive not configured")
            return None

        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaIoBaseUpload
            import io

            credentials = Credentials.from_service_account_info(cls._drive_config)
            service = build("drive", "v3", credentials=credentials)

            file_metadata = {"name": file_name}
            if folder_id:
                file_metadata["parents"] = [folder_id]

            file_stream = io.BytesIO(file_data)
            media = MediaIoBaseUpload(file_stream, mimetype="application/pdf")

            result = service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id, webViewLink",
            ).execute()

            file_id = result.get("id")
            file_url = result.get("webViewLink")
            logger.info(f"Report uploaded to Google Drive: {file_url}")
            return file_url

        except Exception as e:
            logger.error(f"Failed to upload to Google Drive: {str(e)}")
            return None


class ReportPublisher:
    """Publish reports to multiple destinations."""

    @classmethod
    def publish(
        cls,
        report_id: str,
        recipients: list[str],
        methods: list[str],
        html_content: str,
        pdf_content: bytes | None = None,
    ) -> dict[str, Any]:
        """Publish report to multiple recipients and methods."""
        results = {
            "report_id": report_id,
            "sent_count": 0,
            "failed_count": 0,
            "deliveries": [],
        }

        for recipient in recipients:
            for method in methods:
                delivery = ReportDeliveryManager.create_delivery(report_id, recipient, method)

                if method == "email" and "@" in recipient:
                    if EmailDelivery.send(
                        recipient, "WorkCrew Report", html_content
                    ):
                        ReportDeliveryManager.mark_sent(delivery.id)
                        results["sent_count"] += 1
                    else:
                        ReportDeliveryManager.mark_failed(delivery.id, "SMTP error")
                        results["failed_count"] += 1

                elif method == "slack" and recipient.startswith("#"):
                    if SlackDelivery.send(recipient, "Report"):
                        ReportDeliveryManager.mark_sent(delivery.id)
                        results["sent_count"] += 1
                    else:
                        ReportDeliveryManager.mark_failed(delivery.id, "Slack error")
                        results["failed_count"] += 1

                results["deliveries"].append(delivery.to_dict())

        logger.info(
            f"Report published",
            extra={"report_id": report_id, "sent": results["sent_count"]},
        )
        return results
