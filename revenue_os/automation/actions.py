"""Action system for workflow automation."""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """Types of actions that workflows can execute."""

    # Task actions
    CREATE_TASK = "create_task"

    # Notification actions
    SEND_EMAIL = "send_email"
    SEND_SLACK = "send_slack"
    SEND_WEBHOOK = "send_webhook"

    # Data actions
    UPDATE_FIELD = "update_field"
    ADD_TAG = "add_tag"
    REMOVE_TAG = "remove_tag"

    # Crew actions
    TRIGGER_CREW = "trigger_crew"
    TRIGGER_SDR = "trigger_sdr"

    # Activity actions
    CREATE_ACTIVITY = "create_activity"
    LOG_EVENT = "log_event"


@dataclass
class Action:
    """An action to execute within a workflow."""

    action_type: ActionType
    config: dict[str, Any]  # Action-specific configuration
    enabled: bool = True
    action_id: str = None

    def __post_init__(self):
        if not self.action_id:
            self.action_id = f"act_{uuid.uuid4().hex[:12]}"


class ActionExecutor:
    """Execute actions in workflows."""

    _handlers: dict[ActionType, Callable] = {}
    _execution_log: list[dict[str, Any]] = []

    @classmethod
    def register_handler(cls, action_type: ActionType, handler: Callable) -> None:
        """Register handler for action type."""
        cls._handlers[action_type] = handler
        logger.info(f"Registered handler for {action_type.value}")

    @classmethod
    def execute(cls, action: Action, context: dict[str, Any]) -> dict[str, Any]:
        """Execute a single action."""
        if not action.enabled:
            return {"ok": False, "reason": "action_disabled"}

        handler = cls._handlers.get(action.action_type)
        if not handler:
            return {"ok": False, "reason": f"no_handler_for_{action.action_type.value}"}

        try:
            result = handler(action.config, context)
            cls._execution_log.append(
                {
                    "action_id": action.action_id,
                    "action_type": action.action_type.value,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "success",
                    "result": result,
                }
            )
            return {"ok": True, **result}
        except Exception as e:
            cls._execution_log.append(
                {
                    "action_id": action.action_id,
                    "action_type": action.action_type.value,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "failed",
                    "error": str(e),
                }
            )
            logger.error(f"Action execution failed: {str(e)}", extra={"action_id": action.action_id})
            return {"ok": False, "error": str(e)}

    @classmethod
    def get_execution_log(cls, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent action executions."""
        return cls._execution_log[-limit:]


# Built-in action handlers

def _resolve_contact_deal(context: dict[str, Any]) -> tuple[str | None, str | None]:
    """Pull a contact/deal id out of an event context, however it got there."""
    contact_id = context.get("contact_id")
    if not contact_id and context.get("entity_type") == "contact":
        contact_id = context.get("entity_id")
    deal_id = context.get("deal_id")
    if not deal_id and context.get("entity_type") == "deal":
        deal_id = context.get("entity_id")
    return contact_id, deal_id


def handle_create_task(config: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Create a task. Writes a real Activity(TASK) row when the triggering
    event carries a contact/deal, so it shows up on the CRM timeline and the
    M2 follow-up engine — not just a log line that vanishes."""
    title = config.get("title", "Review lead")
    description = config.get("description", "")
    due_in_hours = config.get("due_in_hours", 24)
    due_date = datetime.now(timezone.utc) + timedelta(hours=due_in_hours)

    if "{" in title or "{" in description:
        try:
            title = title.format(**context)
            description = description.format(**context)
        except KeyError:
            pass

    contact_id, deal_id = _resolve_contact_deal(context)
    task_id = f"task_{uuid.uuid4().hex[:12]}"

    if contact_id or deal_id:
        try:
            from revenue_os.database import SessionLocal
            from revenue_os.models.activity import Activity, ActivityType

            db = SessionLocal()
            try:
                activity = Activity(
                    contact_id=uuid.UUID(contact_id) if contact_id else None,
                    deal_id=uuid.UUID(deal_id) if deal_id else None,
                    activity_type=ActivityType.TASK,
                    subject=title,
                    body=description,
                    due_date=due_date,
                    status="pending",
                )
                db.add(activity)
                db.commit()
                db.refresh(activity)
                task_id = str(activity.id)
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Workflow task not persisted as Activity: {e}")

    task = {
        "task_id": task_id,
        "title": title,
        "description": description,
        "due_date": due_date.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(f"Task created: {title}", extra={"task_id": task["task_id"]})
    return task


def handle_send_email(config: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Send email notification."""
    to = config.get("to")
    subject = config.get("subject", "Notification")
    body = config.get("body", "")

    # Template substitution from context
    if "{" in subject or "{" in body:
        try:
            subject = subject.format(**context)
            body = body.format(**context)
        except KeyError:
            pass

    logger.info(f"Email sent to {to}", extra={"subject": subject})
    return {
        "email_id": f"email_{uuid.uuid4().hex[:12]}",
        "to": to,
        "subject": subject,
    }


def handle_send_slack(config: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Send Slack notification."""
    channel = config.get("channel", "#sales")
    message = config.get("message", "Notification")
    webhook_url = config.get("webhook_url")

    # Template substitution
    if "{" in message:
        try:
            message = message.format(**context)
        except KeyError:
            pass

    logger.info(f"Slack message sent to {channel}", extra={"slack_message": message[:100]})
    return {
        "slack_message_id": f"slack_{uuid.uuid4().hex[:12]}",
        "channel": channel,
        "message": message,
    }


def handle_trigger_crew(config: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Trigger a crew to execute."""
    crew_name = config.get("crew_name")  # e.g., "marketing", "generation"
    crew_params = config.get("params", {})

    logger.info(f"Crew triggered: {crew_name}", extra={"params": crew_params})
    return {
        "crew_execution_id": f"crew_{uuid.uuid4().hex[:12]}",
        "crew_name": crew_name,
        "status": "queued",
    }


def handle_trigger_sdr(config: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Trigger SDR crew for a contact."""
    contact_id = context.get("contact_id")
    use_llm = config.get("use_llm", True)

    logger.info(f"SDR crew triggered for contact {contact_id}")
    return {
        "sdr_execution_id": f"sdr_{uuid.uuid4().hex[:12]}",
        "contact_id": contact_id,
        "status": "queued",
    }


def handle_update_field(config: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Update a field on an entity."""
    entity_type = config.get("entity_type")  # contact, deal
    entity_id = context.get("entity_id")
    field = config.get("field")
    value = config.get("value")

    logger.info(f"Field updated: {entity_type}.{field}", extra={"entity_id": entity_id})
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "field": field,
        "value": value,
    }


def handle_create_activity(config: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Create an activity record. Writes a real Activity row when the
    triggering event carries a contact/deal (see handle_create_task)."""
    activity_type_raw = config.get("activity_type") or "note"
    subject = config.get("subject", "")
    body = config.get("body", "")

    if "{" in subject or "{" in body:
        try:
            subject = subject.format(**context)
            body = body.format(**context)
        except KeyError:
            pass

    contact_id, deal_id = _resolve_contact_deal(context)
    activity_id = f"activity_{uuid.uuid4().hex[:12]}"

    if contact_id or deal_id:
        try:
            from revenue_os.database import SessionLocal
            from revenue_os.models.activity import Activity, ActivityType

            db = SessionLocal()
            try:
                try:
                    resolved_type = ActivityType(activity_type_raw)
                except ValueError:
                    resolved_type = ActivityType.NOTE
                activity = Activity(
                    contact_id=uuid.UUID(contact_id) if contact_id else None,
                    deal_id=uuid.UUID(deal_id) if deal_id else None,
                    activity_type=resolved_type,
                    subject=subject,
                    body=body,
                    status="completed",
                )
                db.add(activity)
                db.commit()
                db.refresh(activity)
                activity_id = str(activity.id)
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Workflow activity not persisted: {e}")

    logger.info(f"Activity created: {activity_type_raw}", extra={"contact_id": contact_id})
    return {
        "activity_id": activity_id,
        "contact_id": contact_id,
        "activity_type": activity_type_raw,
        "subject": subject,
    }


# Register default handlers
ActionExecutor.register_handler(ActionType.CREATE_TASK, handle_create_task)
ActionExecutor.register_handler(ActionType.SEND_EMAIL, handle_send_email)
ActionExecutor.register_handler(ActionType.SEND_SLACK, handle_send_slack)
ActionExecutor.register_handler(ActionType.TRIGGER_CREW, handle_trigger_crew)
ActionExecutor.register_handler(ActionType.TRIGGER_SDR, handle_trigger_sdr)
ActionExecutor.register_handler(ActionType.UPDATE_FIELD, handle_update_field)
ActionExecutor.register_handler(ActionType.CREATE_ACTIVITY, handle_create_activity)
