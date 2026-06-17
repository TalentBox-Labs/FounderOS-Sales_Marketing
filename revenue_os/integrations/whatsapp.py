"""WhatsApp Business integration for community and brand building."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WhatsApp message types."""

    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"
    LOCATION = "location"
    TEMPLATE = "template"


class BroadcastStatus(Enum):
    """Broadcast campaign status."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class WhatsAppContact:
    """WhatsApp contact."""

    phone_number: str
    name: str
    profile_picture_url: str | None = None
    status: str = "active"  # active, blocked, opted_out
    tags: list[str] = field(default_factory=list)
    custom_fields: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_message_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "phone_number": self.phone_number,
            "name": self.name,
            "profile_picture_url": self.profile_picture_url,
            "status": self.status,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
        }


@dataclass
class MessageTemplate:
    """WhatsApp message template."""

    id: str
    name: str
    category: str  # MARKETING, UTILITY, AUTHENTICATION
    language: str = "en"  # language code
    body: str = ""
    header: str | None = None
    footer: str | None = None
    buttons: list[dict[str, Any]] = field(default_factory=list)
    variables: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    approved: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "language": self.language,
            "body": self.body,
            "header": self.header,
            "footer": self.footer,
            "buttons": self.buttons,
            "variables": self.variables,
            "approved": self.approved,
        }


@dataclass
class WhatsAppMessage:
    """Individual WhatsApp message."""

    id: str
    recipient_phone: str
    message_type: MessageType
    content: dict[str, Any]
    status: str = "pending"  # pending, sent, delivered, read, failed
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    read_at: datetime | None = None
    whatsapp_message_id: str | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "recipient_phone": self.recipient_phone,
            "message_type": self.message_type.value,
            "status": self.status,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class BroadcastCampaign:
    """WhatsApp broadcast campaign."""

    id: str
    name: str
    template_name: str
    recipient_count: int
    status: BroadcastStatus = BroadcastStatus.DRAFT
    scheduled_at: datetime | None = None
    sent_at: datetime | None = None
    completed_at: datetime | None = None
    sent_count: int = 0
    delivered_count: int = 0
    read_count: int = 0
    failed_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "template_name": self.template_name,
            "recipient_count": self.recipient_count,
            "status": self.status.value,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "sent_count": self.sent_count,
            "delivered_count": self.delivered_count,
            "read_count": self.read_count,
            "failed_count": self.failed_count,
            "engagement_rate": (self.read_count / max(self.sent_count, 1)) * 100,
        }


class WhatsAppClient:
    """WhatsApp Business API client."""

    _api_key: str | None = None
    _phone_number_id: str | None = None
    _business_account_id: str | None = None
    _contacts: dict[str, WhatsAppContact] = {}
    _templates: dict[str, MessageTemplate] = {}
    _messages: dict[str, WhatsAppMessage] = {}
    _broadcasts: dict[str, BroadcastCampaign] = {}

    @classmethod
    def configure(cls, api_key: str, phone_number_id: str, business_account_id: str) -> None:
        """Configure WhatsApp Business API."""
        cls._api_key = api_key
        cls._phone_number_id = phone_number_id
        cls._business_account_id = business_account_id
        logger.info("WhatsApp Business configured")

    @classmethod
    def add_contact(
        cls,
        phone_number: str,
        name: str,
        tags: list[str] | None = None,
        custom_fields: dict[str, Any] | None = None,
    ) -> WhatsAppContact:
        """Add contact to WhatsApp list."""
        contact = WhatsAppContact(
            phone_number=phone_number,
            name=name,
            tags=tags or [],
            custom_fields=custom_fields or {},
        )
        cls._contacts[phone_number] = contact
        logger.info(f"WhatsApp contact added: {phone_number}")
        return contact

    @classmethod
    def get_contact(cls, phone_number: str) -> WhatsAppContact | None:
        """Get contact by phone number."""
        return cls._contacts.get(phone_number)

    @classmethod
    def list_contacts(cls, tag: str | None = None) -> list[WhatsAppContact]:
        """List contacts with optional tag filter."""
        contacts = cls._contacts.values()
        if tag:
            contacts = [c for c in contacts if tag in c.tags]
        return list(contacts)

    @classmethod
    def register_template(cls, template: MessageTemplate) -> None:
        """Register message template."""
        cls._templates[template.name] = template
        logger.info(f"WhatsApp template registered: {template.name}")

    @classmethod
    def get_template(cls, template_name: str) -> MessageTemplate | None:
        """Get template by name."""
        return cls._templates.get(template_name)

    @classmethod
    def send_message(
        cls,
        recipient_phone: str,
        message_type: MessageType,
        content: dict[str, Any],
    ) -> WhatsAppMessage | None:
        """Send a WhatsApp message."""
        if not cls._api_key:
            logger.warning("WhatsApp not configured")
            return None

        try:
            message = WhatsAppMessage(
                id=str(uuid.uuid4()),
                recipient_phone=recipient_phone,
                message_type=message_type,
                content=content,
                status="pending",
            )
            cls._messages[message.id] = message

            # Update contact last message time
            contact = cls.get_contact(recipient_phone)
            if contact:
                contact.last_message_at = datetime.now(timezone.utc)

            logger.info(f"WhatsApp message queued: {message.id}")
            return message

        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {str(e)}")
            return None

    @classmethod
    def send_template_message(
        cls,
        recipient_phone: str,
        template_name: str,
        variables: dict[str, str] | None = None,
    ) -> WhatsAppMessage | None:
        """Send message using template."""
        template = cls.get_template(template_name)
        if not template:
            logger.error(f"Template not found: {template_name}")
            return None

        # Render template with variables
        body = template.body
        if variables:
            for key, value in variables.items():
                body = body.replace(f"{{{{{key}}}}}", value)

        content = {
            "template_name": template_name,
            "body": body,
            "header": template.header,
            "footer": template.footer,
            "buttons": template.buttons,
        }

        return cls.send_message(recipient_phone, MessageType.TEMPLATE, content)

    @classmethod
    def create_broadcast(
        cls,
        name: str,
        template_name: str,
        recipient_tags: list[str],
        created_by: str,
    ) -> BroadcastCampaign | None:
        """Create a broadcast campaign."""
        template = cls.get_template(template_name)
        if not template:
            logger.error(f"Template not found: {template_name}")
            return None

        # Count recipients
        recipients = []
        for contact in cls._contacts.values():
            if any(tag in contact.tags for tag in recipient_tags):
                recipients.append(contact)

        broadcast = BroadcastCampaign(
            id=str(uuid.uuid4()),
            name=name,
            template_name=template_name,
            recipient_count=len(recipients),
            created_by=created_by,
            tags=recipient_tags,
        )
        cls._broadcasts[broadcast.id] = broadcast
        logger.info(f"Broadcast created: {broadcast.id} ({len(recipients)} recipients)")
        return broadcast

    @classmethod
    def schedule_broadcast(
        cls, broadcast_id: str, scheduled_at: datetime
    ) -> bool:
        """Schedule a broadcast campaign."""
        broadcast = cls._broadcasts.get(broadcast_id)
        if broadcast:
            broadcast.status = BroadcastStatus.SCHEDULED
            broadcast.scheduled_at = scheduled_at
            logger.info(f"Broadcast scheduled: {broadcast_id}")
            return True
        return False

    @classmethod
    def send_broadcast(cls, broadcast_id: str) -> dict[str, Any]:
        """Send a broadcast campaign."""
        broadcast = cls._broadcasts.get(broadcast_id)
        if not broadcast:
            logger.error(f"Broadcast not found: {broadcast_id}")
            return {"ok": False, "error": "Broadcast not found"}

        broadcast.status = BroadcastStatus.SENDING
        broadcast.sent_at = datetime.now(timezone.utc)

        sent_count = 0
        failed_count = 0

        # Get recipients
        recipients = [
            c for c in cls._contacts.values()
            if any(tag in c.tags for tag in broadcast.tags)
        ]

        for contact in recipients:
            message = cls.send_template_message(
                contact.phone_number,
                broadcast.template_name,
            )
            if message:
                sent_count += 1
                broadcast.sent_count += 1
            else:
                failed_count += 1
                broadcast.failed_count += 1

        broadcast.status = BroadcastStatus.SENT
        broadcast.completed_at = datetime.now(timezone.utc)
        logger.info(f"Broadcast completed: {broadcast_id} ({sent_count} sent, {failed_count} failed)")

        return {
            "ok": True,
            "broadcast_id": broadcast_id,
            "sent": sent_count,
            "failed": failed_count,
        }

    @classmethod
    def get_broadcast(cls, broadcast_id: str) -> BroadcastCampaign | None:
        """Get broadcast by ID."""
        return cls._broadcasts.get(broadcast_id)

    @classmethod
    def list_broadcasts(cls, status: BroadcastStatus | None = None) -> list[BroadcastCampaign]:
        """List broadcasts with optional status filter."""
        broadcasts = cls._broadcasts.values()
        if status:
            broadcasts = [b for b in broadcasts if b.status == status]
        return list(broadcasts)

    @classmethod
    def update_message_status(
        cls, message_id: str, status: str, whatsapp_id: str | None = None
    ) -> bool:
        """Update message delivery status from webhook."""
        message = cls._messages.get(message_id)
        if message:
            message.status = status
            message.whatsapp_message_id = whatsapp_id

            if status == "sent":
                message.sent_at = datetime.now(timezone.utc)
            elif status == "delivered":
                message.delivered_at = datetime.now(timezone.utc)
            elif status == "read":
                message.read_at = datetime.now(timezone.utc)

            logger.info(f"Message status updated: {message_id} → {status}")
            return True
        return False
