"""Integration management API endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from revenue_os.database import SessionLocal
from revenue_os.integrations.email import EmailNotifier, ScheduledEmailQueue, EmailTemplate
from revenue_os.integrations.webhooks import WebhookManager, WebhookEventType
from revenue_os.integrations.calendar import GoogleCalendarClient, OutlookCalendarClient, CalendarEvent
from revenue_os.integrations.slack import SlackNotifier

from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


@router.post("/email/configure", tags=["integrations"])
def configure_email(
    config: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Configure email (SMTP) settings."""
    logger.info("Configuring email settings")

    try:
        EmailNotifier.configure_smtp(config)
        return {"ok": True, "message": "Email configured successfully"}
    except Exception as e:
        logger.error(f"Failed to configure email: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/email/templates", tags=["integrations"])
def register_email_template(
    template: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Register an email template."""
    logger.info(f"Registering email template: {template.get('name')}")

    try:
        email_template = EmailTemplate(
            name=template["name"],
            subject=template["subject"],
            html_body=template["html_body"],
            text_body=template.get("text_body", ""),
            variables=template.get("variables", []),
        )
        EmailNotifier.register_template(email_template)
        return {"ok": True, "message": f"Template '{email_template.name}' registered"}
    except Exception as e:
        logger.error(f"Failed to register email template: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/email/send", tags=["integrations"])
def send_email(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Send an email."""
    logger.info(f"Sending email to {payload.get('to_email')}")

    try:
        success = EmailNotifier.send_email(
            to_email=payload["to_email"],
            subject=payload["subject"],
            html_body=payload["html_body"],
            text_body=payload.get("text_body"),
            cc=payload.get("cc"),
            bcc=payload.get("bcc"),
        )
        return {"ok": success, "message": "Email sent" if success else "Failed to send email"}
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/email/template-send", tags=["integrations"])
def send_template_email(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Send email using a template."""
    logger.info(f"Sending template email: {payload.get('template_name')}")

    try:
        success = EmailNotifier.send_template_email(
            template_name=payload["template_name"],
            to_email=payload["to_email"],
            context=payload.get("context", {}),
            cc=payload.get("cc"),
            bcc=payload.get("bcc"),
        )
        return {"ok": success, "message": "Email sent" if success else "Template not found"}
    except Exception as e:
        logger.error(f"Failed to send template email: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/email/schedule", tags=["integrations"])
def schedule_email(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Schedule an email for future send."""
    logger.info(f"Scheduling email for {payload.get('to_email')}")

    try:
        from datetime import datetime as dt

        send_at = dt.fromisoformat(payload["send_at"])
        success = ScheduledEmailQueue.schedule_email(
            to_email=payload["to_email"],
            template_name=payload["template_name"],
            context=payload.get("context", {}),
            send_at=send_at,
            cc=payload.get("cc"),
        )
        return {"ok": success, "message": "Email scheduled"}
    except Exception as e:
        logger.error(f"Failed to schedule email: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/email/process-scheduled", tags=["integrations"])
def process_scheduled_emails(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Process and send all pending scheduled emails."""
    logger.info("Processing scheduled emails")

    try:
        result = ScheduledEmailQueue.process_pending_emails()
        return result
    except Exception as e:
        logger.error(f"Failed to process scheduled emails: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/webhooks/subscribe", tags=["integrations"])
def create_webhook_subscription(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Create a webhook subscription."""
    logger.info(f"Creating webhook subscription for {payload.get('url')}")

    try:
        events = [WebhookEventType(e) for e in payload.get("events", [])]
        subscription = WebhookManager.create_subscription(
            url=payload["url"],
            events=events,
            metadata=payload.get("metadata", {}),
        )
        return {
            "ok": True,
            "subscription": subscription.to_dict(),
        }
    except Exception as e:
        logger.error(f"Failed to create webhook subscription: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.get("/webhooks/subscriptions", tags=["integrations"])
def list_webhook_subscriptions(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """List all webhook subscriptions."""
    logger.info("Listing webhook subscriptions")

    try:
        subscriptions = WebhookManager.list_subscriptions(active_only=False)
        return {
            "ok": True,
            "count": len(subscriptions),
            "subscriptions": [s.to_dict() for s in subscriptions],
        }
    except Exception as e:
        logger.error(f"Failed to list webhook subscriptions: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.delete("/webhooks/subscriptions/{subscription_id}", tags=["integrations"])
def delete_webhook_subscription(
    subscription_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Delete a webhook subscription."""
    logger.info(f"Deleting webhook subscription: {subscription_id}")

    try:
        success = WebhookManager.delete_subscription(subscription_id)
        return {"ok": success, "message": "Subscription deleted" if success else "Not found"}
    except Exception as e:
        logger.error(f"Failed to delete webhook subscription: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/slack/configure", tags=["integrations"])
def configure_slack(
    config: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Configure Slack webhook URL."""
    logger.info("Configuring Slack")

    try:
        SlackNotifier.set_webhook_url(config.get("webhook_url", ""))
        return {"ok": True, "message": "Slack configured successfully"}
    except Exception as e:
        logger.error(f"Failed to configure Slack: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/slack/send", tags=["integrations"])
def send_slack_message(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Send a message to Slack."""
    logger.info(f"Sending Slack message to {payload.get('channel')}")

    try:
        from revenue_os.integrations.slack import SlackMessage

        message = SlackMessage(
            channel=payload["channel"],
            text=payload["text"],
            blocks=payload.get("blocks"),
            thread_ts=payload.get("thread_ts"),
            icon_emoji=payload.get("icon_emoji"),
            username=payload.get("username", "WorkCrew"),
        )
        success = SlackNotifier.send_message(message)
        return {"ok": success, "message": "Message sent" if success else "Failed to send"}
    except Exception as e:
        logger.error(f"Failed to send Slack message: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/slack/alert", tags=["integrations"])
def send_slack_alert(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Send an alert to Slack."""
    logger.info(f"Sending Slack alert to {payload.get('channel')}")

    try:
        success = SlackNotifier.send_alert(
            channel=payload["channel"],
            title=payload["title"],
            message=payload["message"],
            severity=payload.get("severity", "info"),
            fields=payload.get("fields"),
        )
        return {"ok": success, "message": "Alert sent" if success else "Failed to send"}
    except Exception as e:
        logger.error(f"Failed to send Slack alert: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/google-calendar/configure", tags=["integrations"])
def configure_google_calendar(
    config: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Configure Google Calendar."""
    logger.info("Configuring Google Calendar")

    try:
        GoogleCalendarClient.configure(config.get("credentials", {}))
        return {"ok": True, "message": "Google Calendar configured successfully"}
    except Exception as e:
        logger.error(f"Failed to configure Google Calendar: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/google-calendar/events", tags=["integrations"])
def create_google_calendar_event(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Create an event on Google Calendar."""
    logger.info("Creating Google Calendar event")

    try:
        from datetime import datetime as dt

        event = CalendarEvent(
            title=payload["title"],
            description=payload.get("description", ""),
            start_time=dt.fromisoformat(payload["start_time"]),
            end_time=dt.fromisoformat(payload["end_time"]),
            attendees=payload.get("attendees", []),
            location=payload.get("location"),
            calendar_id=payload.get("calendar_id"),
        )
        event_id = GoogleCalendarClient.create_event(event)
        return {
            "ok": event_id is not None,
            "event_id": event_id,
            "message": "Event created" if event_id else "Failed to create event",
        }
    except Exception as e:
        logger.error(f"Failed to create Google Calendar event: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/outlook-calendar/configure", tags=["integrations"])
def configure_outlook_calendar(
    config: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Configure Outlook Calendar."""
    logger.info("Configuring Outlook Calendar")

    try:
        OutlookCalendarClient.configure(
            tenant_id=config.get("tenant_id", ""),
            access_token=config.get("access_token", ""),
        )
        return {"ok": True, "message": "Outlook Calendar configured successfully"}
    except Exception as e:
        logger.error(f"Failed to configure Outlook Calendar: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/outlook-calendar/events", tags=["integrations"])
def create_outlook_calendar_event(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Create an event on Outlook Calendar."""
    logger.info("Creating Outlook Calendar event")

    try:
        from datetime import datetime as dt

        event = CalendarEvent(
            title=payload["title"],
            description=payload.get("description", ""),
            start_time=dt.fromisoformat(payload["start_time"]),
            end_time=dt.fromisoformat(payload["end_time"]),
            attendees=payload.get("attendees", []),
            location=payload.get("location"),
        )
        event_id = OutlookCalendarClient.create_event(event)
        return {
            "ok": event_id is not None,
            "event_id": event_id,
            "message": "Event created" if event_id else "Failed to create event",
        }
    except Exception as e:
        logger.error(f"Failed to create Outlook Calendar event: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.get("/health", tags=["integrations"])
def integrations_health(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get integration system health."""
    logger.info("Checking integrations health")

    subscriptions = len(WebhookManager.list_subscriptions())

    return {
        "ok": True,
        "integrations": {
            "email": "ready",
            "webhooks": "ready",
            "slack": "ready",
            "google_calendar": "ready",
            "outlook_calendar": "ready",
        },
        "webhook_subscriptions": subscriptions,
        "status": "healthy",
    }
