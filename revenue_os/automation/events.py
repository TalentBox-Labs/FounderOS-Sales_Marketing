"""Event and trigger system for workflow automation."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types of events that can trigger workflows."""

    # Lead events
    LEAD_CREATED = "lead_created"
    LEAD_SCORED = "lead_scored"
    LEAD_QUALIFIED = "lead_qualified"

    # Contact events
    CONTACT_STATUS_CHANGED = "contact_status_changed"
    CONTACT_IMPORTED = "contact_imported"
    CONTACT_ENRICHED = "contact_enriched"

    # Deal events
    DEAL_CREATED = "deal_created"
    DEAL_STAGE_CHANGED = "deal_stage_changed"
    DEAL_AT_RISK = "deal_at_risk"
    DEAL_CLOSED = "deal_closed"

    # Commercial outcome events (MC06 — not DEAL_CLOSED; no finance workflows)
    COMMERCIAL_OUTCOME_HANDED_OFF = "commercial_outcome_handed_off"
    COMMERCIAL_OUTCOME_ACCEPTED = "commercial_outcome_accepted"
    COMMERCIAL_OUTCOME_REJECTED = "commercial_outcome_rejected"

    # Crew events
    CREW_STARTED = "crew_started"
    CREW_COMPLETED = "crew_completed"
    CREW_FAILED = "crew_failed"

    # Marketing events
    CONTENT_GENERATED = "content_generated"
    CONTENT_PUBLISHED = "content_published"

    # Outreach events
    OUTREACH_STARTED = "outreach_started"
    OUTREACH_COMPLETED = "outreach_completed"


class EventPriority(str, Enum):
    """Priority levels for events."""

    CRITICAL = "critical"  # Immediate action (deal closed, major failure)
    HIGH = "high"  # Within 1 hour (lead qualified, deal at risk)
    MEDIUM = "medium"  # Within 4 hours (lead scored, contact imported)
    LOW = "low"  # Within 24 hours (routine updates)


@dataclass
class Event:
    """An event that occurred in the system."""

    event_type: EventType
    source: str  # Where event came from (lead_scoring, deal_creation, etc)
    entity_id: str  # ID of entity that triggered event (contact_id, deal_id, etc)
    entity_type: str  # Type of entity (contact, deal, crew, etc)
    priority: EventPriority = EventPriority.MEDIUM
    data: dict[str, Any] = field(default_factory=dict)  # Additional context
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_id: str = field(default_factory=lambda: f"evt_{datetime.now(timezone.utc).timestamp()}")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            **asdict(self),
            "event_type": self.event_type.value,
            "priority": self.priority.value,
        }


class EventBus:
    """Publish and subscribe to events."""

    _subscribers: dict[EventType, list[Callable]] = {}
    _event_history: list[Event] = []
    _max_history = 1000

    @classmethod
    def subscribe(cls, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Subscribe handler to event type."""
        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []
        cls._subscribers[event_type].append(handler)
        logger.info(f"Subscribed to {event_type.value}")

    @classmethod
    def subscribe_all(cls, handler: Callable[[Event], None]) -> None:
        """Subscribe handler to all events."""
        for event_type in EventType:
            cls.subscribe(event_type, handler)

    @classmethod
    def publish(cls, event: Event) -> None:
        """Publish event to all subscribers."""
        logger.info(
            f"Publishing event {event.event_type.value}",
            extra={
                "event_id": event.event_id,
                "entity": f"{event.entity_type}:{event.entity_id}",
                "priority": event.priority.value,
            },
        )

        # Store in history
        cls._event_history.append(event)
        if len(cls._event_history) > cls._max_history:
            cls._event_history = cls._event_history[-cls._max_history :]

        # Notify subscribers
        if event.event_type in cls._subscribers:
            for handler in cls._subscribers[event.event_type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Event handler failed: {str(e)}", extra={"event_id": event.event_id})

    @classmethod
    def get_history(cls, event_type: Optional[EventType] = None, limit: int = 100) -> list[Event]:
        """Get recent events, optionally filtered by type."""
        history = cls._event_history
        if event_type:
            history = [e for e in history if e.event_type == event_type]
        return history[-limit:]


def emit_lead_scored(contact_id: str, score: int, old_score: int, status: str) -> None:
    """Emit lead scored event."""
    event = Event(
        event_type=EventType.LEAD_SCORED,
        source="lead_scoring_service",
        entity_id=contact_id,
        entity_type="contact",
        priority=EventPriority.HIGH if score >= 70 else EventPriority.MEDIUM,
        data={
            "score": score,
            "old_score": old_score,
            "status": status,
            "score_change": score - old_score,
        },
    )
    EventBus.publish(event)


def emit_contact_qualified(contact_id: str, company_id: str | None = None) -> None:
    """Emit contact qualified event."""
    event = Event(
        event_type=EventType.LEAD_QUALIFIED,
        source="lead_scoring_service",
        entity_id=contact_id,
        entity_type="contact",
        priority=EventPriority.HIGH,
        data={"company_id": company_id},
    )
    EventBus.publish(event)


def emit_deal_created(deal_id: str, contact_id: str, value: float) -> None:
    """Emit deal created event."""
    event = Event(
        event_type=EventType.DEAL_CREATED,
        source="deal_automation_service",
        entity_id=deal_id,
        entity_type="deal",
        priority=EventPriority.HIGH,
        data={"contact_id": contact_id, "value": value},
    )
    EventBus.publish(event)


def emit_deal_stage_changed(deal_id: str, old_stage: str, new_stage: str, probability: int) -> None:
    """Emit deal stage changed event."""
    event = Event(
        event_type=EventType.DEAL_STAGE_CHANGED,
        source="deal_automation_service",
        entity_id=deal_id,
        entity_type="deal",
        priority=EventPriority.MEDIUM,
        data={
            "old_stage": old_stage,
            "new_stage": new_stage,
            "probability": probability,
        },
    )
    EventBus.publish(event)


def emit_deal_at_risk(deal_id: str, risk_score: int, days_overdue: int) -> None:
    """Emit deal at risk event."""
    event = Event(
        event_type=EventType.DEAL_AT_RISK,
        source="deal_automation_service",
        entity_id=deal_id,
        entity_type="deal",
        priority=EventPriority.HIGH,
        data={"risk_score": risk_score, "days_overdue": days_overdue},
    )
    EventBus.publish(event)


def emit_crew_completed(crew_name: str, crew_type: str, week_id: str | None = None) -> None:
    """Emit crew completed event."""
    event = Event(
        event_type=EventType.CREW_COMPLETED,
        source=crew_name,
        entity_id=f"{crew_name}_{week_id or 'general'}",
        entity_type="crew",
        priority=EventPriority.MEDIUM,
        data={"crew_name": crew_name, "crew_type": crew_type, "week_id": week_id},
    )
    EventBus.publish(event)


def emit_contact_status_changed(
    contact_id: str, old_status: str, new_status: str, reason: str = ""
) -> None:
    """Emit contact status changed event."""
    event = Event(
        event_type=EventType.CONTACT_STATUS_CHANGED,
        source="contact_management",
        entity_id=contact_id,
        entity_type="contact",
        priority=EventPriority.MEDIUM,
        data={"old_status": old_status, "new_status": new_status, "reason": reason},
    )
    EventBus.publish(event)
