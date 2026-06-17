"""WhatsApp Business integration API endpoints."""

from __future__ import annotations

import logging
from typing import Any
from datetime import datetime

from fastapi import APIRouter, Depends
from revenue_os.database import SessionLocal
from revenue_os.integrations.whatsapp import (
    WhatsAppClient,
    MessageTemplate,
    MessageType,
    BroadcastStatus,
)
from revenue_os.integrations.whatsapp_community import (
    CommunityManager,
    BrandContentStrategy,
    CommunityPurpose,
    CommunityRole,
)

from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/whatsapp", tags=["whatsapp"])


@router.post("/configure", tags=["whatsapp"])
def configure_whatsapp(
    config: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Configure WhatsApp Business API."""
    logger.info("Configuring WhatsApp Business API")

    try:
        WhatsAppClient.configure(
            api_key=config.get("api_key", ""),
            phone_number_id=config.get("phone_number_id", ""),
            business_account_id=config.get("business_account_id", ""),
        )
        return {"ok": True, "message": "WhatsApp configured successfully"}
    except Exception as e:
        logger.error(f"Failed to configure WhatsApp: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/contacts", tags=["whatsapp"])
def add_contact(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Add contact to WhatsApp."""
    logger.info(f"Adding WhatsApp contact: {payload.get('phone_number')}")

    try:
        contact = WhatsAppClient.add_contact(
            phone_number=payload["phone_number"],
            name=payload["name"],
            tags=payload.get("tags", []),
            custom_fields=payload.get("custom_fields", {}),
        )
        return {"ok": True, "contact": contact.to_dict()}
    except Exception as e:
        logger.error(f"Failed to add contact: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.get("/contacts", tags=["whatsapp"])
def list_contacts(
    tag: str | None = None,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """List WhatsApp contacts."""
    logger.info("Listing WhatsApp contacts")

    try:
        contacts = WhatsAppClient.list_contacts(tag=tag)
        return {
            "ok": True,
            "count": len(contacts),
            "contacts": [c.to_dict() for c in contacts],
        }
    except Exception as e:
        logger.error(f"Failed to list contacts: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/templates", tags=["whatsapp"])
def register_template(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Register message template."""
    logger.info(f"Registering template: {payload.get('name')}")

    try:
        template = MessageTemplate(
            id=str(payload.get("id", "tpl_" + str(hash(payload.get("name"))))),
            name=payload["name"],
            category=payload.get("category", "MARKETING"),
            language=payload.get("language", "en"),
            body=payload.get("body", ""),
            header=payload.get("header"),
            footer=payload.get("footer"),
            buttons=payload.get("buttons", []),
            variables=payload.get("variables", []),
        )
        WhatsAppClient.register_template(template)
        return {"ok": True, "template": template.to_dict()}
    except Exception as e:
        logger.error(f"Failed to register template: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/messages/send", tags=["whatsapp"])
def send_message(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Send a WhatsApp message."""
    logger.info(f"Sending WhatsApp message to {payload.get('recipient_phone')}")

    try:
        message_type = MessageType(payload.get("message_type", "text"))
        message = WhatsAppClient.send_message(
            recipient_phone=payload["recipient_phone"],
            message_type=message_type,
            content=payload.get("content", {}),
        )
        return {
            "ok": message is not None,
            "message": message.to_dict() if message else None,
        }
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/messages/template-send", tags=["whatsapp"])
def send_template_message(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Send message using template."""
    logger.info(f"Sending template message: {payload.get('template_name')}")

    try:
        message = WhatsAppClient.send_template_message(
            recipient_phone=payload["recipient_phone"],
            template_name=payload["template_name"],
            variables=payload.get("variables", {}),
        )
        return {
            "ok": message is not None,
            "message": message.to_dict() if message else None,
        }
    except Exception as e:
        logger.error(f"Failed to send template message: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/broadcasts", tags=["whatsapp"])
def create_broadcast(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Create broadcast campaign."""
    logger.info(f"Creating broadcast: {payload.get('name')}")

    try:
        broadcast = WhatsAppClient.create_broadcast(
            name=payload["name"],
            template_name=payload["template_name"],
            recipient_tags=payload.get("recipient_tags", []),
            created_by=payload.get("created_by", "system"),
        )
        return {
            "ok": broadcast is not None,
            "broadcast": broadcast.to_dict() if broadcast else None,
        }
    except Exception as e:
        logger.error(f"Failed to create broadcast: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/broadcasts/{broadcast_id}/schedule", tags=["whatsapp"])
def schedule_broadcast(
    broadcast_id: str,
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Schedule broadcast campaign."""
    logger.info(f"Scheduling broadcast: {broadcast_id}")

    try:
        scheduled_at = datetime.fromisoformat(payload["scheduled_at"])
        success = WhatsAppClient.schedule_broadcast(broadcast_id, scheduled_at)
        return {"ok": success, "message": "Broadcast scheduled" if success else "Broadcast not found"}
    except Exception as e:
        logger.error(f"Failed to schedule broadcast: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/broadcasts/{broadcast_id}/send", tags=["whatsapp"])
def send_broadcast(
    broadcast_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Send broadcast campaign."""
    logger.info(f"Sending broadcast: {broadcast_id}")

    try:
        result = WhatsAppClient.send_broadcast(broadcast_id)
        return result
    except Exception as e:
        logger.error(f"Failed to send broadcast: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.get("/broadcasts", tags=["whatsapp"])
def list_broadcasts(
    status: str | None = None,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """List broadcast campaigns."""
    logger.info("Listing broadcasts")

    try:
        status_enum = BroadcastStatus(status) if status else None
        broadcasts = WhatsAppClient.list_broadcasts(status=status_enum)
        return {
            "ok": True,
            "count": len(broadcasts),
            "broadcasts": [b.to_dict() for b in broadcasts],
        }
    except Exception as e:
        logger.error(f"Failed to list broadcasts: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/communities", tags=["whatsapp"])
def create_community(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Create WhatsApp community."""
    logger.info(f"Creating community: {payload.get('name')}")

    try:
        purpose = CommunityPurpose(payload.get("purpose", "user_community"))
        community = CommunityManager.create_community(
            name=payload["name"],
            description=payload["description"],
            purpose=purpose,
            welcome_message=payload.get("welcome_message", ""),
            rules=payload.get("rules", []),
        )
        return {"ok": True, "community": community.to_dict()}
    except Exception as e:
        logger.error(f"Failed to create community: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/communities/{community_id}/members", tags=["whatsapp"])
def add_community_member(
    community_id: str,
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Add member to community."""
    logger.info(f"Adding member to community: {community_id}")

    try:
        role = CommunityRole(payload.get("role", "member"))
        member = CommunityManager.add_member(
            community_id=community_id,
            phone_number=payload["phone_number"],
            name=payload["name"],
            role=role,
            invitation_source=payload.get("invitation_source", ""),
        )
        return {
            "ok": member is not None,
            "member": member.to_dict() if member else None,
        }
    except Exception as e:
        logger.error(f"Failed to add member: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.get("/communities/{community_id}/stats", tags=["whatsapp"])
def get_community_stats(
    community_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get community statistics."""
    logger.info(f"Getting community stats: {community_id}")

    try:
        stats = CommunityManager.get_community_stats(community_id)
        return {"ok": bool(stats), "stats": stats}
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/content/schedule-founder-post", tags=["whatsapp"])
def schedule_founder_post(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Schedule founder thought leadership post."""
    logger.info(f"Scheduling founder post: {payload.get('founder_name')}")

    try:
        scheduled_date = datetime.fromisoformat(payload["scheduled_date"])
        post_id = BrandContentStrategy.schedule_founder_post(
            founder_name=payload["founder_name"],
            content=payload["content"],
            scheduled_date=scheduled_date,
            communities=payload.get("communities", []),
            content_type=payload.get("content_type", "thought_leadership"),
        )
        return {"ok": True, "post_id": post_id}
    except Exception as e:
        logger.error(f"Failed to schedule post: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/content/case-study", tags=["whatsapp"])
def add_case_study(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Add case study for distribution."""
    logger.info(f"Adding case study: {payload.get('title')}")

    try:
        case_study_id = BrandContentStrategy.add_case_study(
            title=payload["title"],
            customer_name=payload["customer_name"],
            results=payload["results"],
            media_urls=payload.get("media_urls", []),
        )
        return {"ok": True, "case_study_id": case_study_id}
    except Exception as e:
        logger.error(f"Failed to add case study: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.get("/health", tags=["whatsapp"])
def whatsapp_health(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get WhatsApp system health."""
    logger.info("Checking WhatsApp health")

    contacts_count = len(WhatsAppClient.list_contacts())
    broadcasts_count = len(WhatsAppClient.list_broadcasts())
    communities_count = len(CommunityManager.list_communities())

    return {
        "ok": True,
        "contacts": contacts_count,
        "broadcasts": broadcasts_count,
        "communities": communities_count,
        "status": "healthy",
    }
