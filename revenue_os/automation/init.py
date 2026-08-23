"""Initialize automation system with event subscriptions."""

from __future__ import annotations

import logging

from revenue_os.automation.events import EventBus, Event
from revenue_os.automation.workflows import WorkflowEngine

logger = logging.getLogger(__name__)


def initialize_automation():
    """Initialize automation system with default subscriptions."""
    # Subscribe WorkflowEngine to all events
    EventBus.subscribe_all(_on_event)
    logger.info("Automation system initialized")


def _on_event(event: Event) -> None:
    """Handle incoming events by executing matching workflows."""
    executions = WorkflowEngine.on_event(event)
    if executions:
        logger.info(
            f"Event triggered {len(executions)} workflow executions",
            extra={"event_id": event.event_id},
        )
