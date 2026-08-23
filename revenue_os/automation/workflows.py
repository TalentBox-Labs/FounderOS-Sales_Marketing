"""Workflow system for automation rules and execution."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from revenue_os.automation.actions import Action, ActionExecutor, ActionType
from revenue_os.automation.events import Event, EventType

logger = logging.getLogger(__name__)


class Condition:
    """A condition that must be met to execute actions."""

    def __init__(self, field: str, operator: str, value: Any):
        """
        Create a condition.

        Args:
            field: Field to check (e.g., "score", "status", "stage")
            operator: Comparison operator (eq, gte, lte, contains, in)
            value: Value to compare against
        """
        self.field = field
        self.operator = operator
        self.value = value

    def evaluate(self, data: dict[str, Any]) -> bool:
        """Evaluate condition against data."""
        field_value = data.get(self.field)

        if self.operator == "eq":
            return field_value == self.value
        elif self.operator == "gte":
            return field_value >= self.value
        elif self.operator == "lte":
            return field_value <= self.value
        elif self.operator == "gt":
            return field_value > self.value
        elif self.operator == "lt":
            return field_value < self.value
        elif self.operator == "contains":
            return self.value in field_value if isinstance(field_value, str) else False
        elif self.operator == "in":
            return field_value in self.value if isinstance(self.value, list) else False
        elif self.operator == "exists":
            return field_value is not None
        else:
            return False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {"field": self.field, "operator": self.operator, "value": self.value}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Condition":
        return cls(field=d["field"], operator=d["operator"], value=d.get("value"))


def _action_to_dict(a: Action) -> dict[str, Any]:
    return {
        "action_id": a.action_id,
        "action_type": a.action_type.value,
        "config": a.config,
        "enabled": a.enabled,
    }


def _action_from_dict(d: dict[str, Any]) -> Action:
    return Action(
        action_type=ActionType(d["action_type"]),
        config=d.get("config") or {},
        enabled=d.get("enabled", True),
        action_id=d.get("action_id"),
    )


class Workflow:
    """A workflow that triggers actions based on events and conditions."""

    def __init__(
        self,
        name: str,
        description: str = "",
        event_type: EventType = None,
        conditions: list[Condition] = None,
        actions: list[Action] = None,
        enabled: bool = True,
    ):
        """Create a workflow."""
        self.workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
        self.name = name
        self.description = description
        self.event_type = event_type
        self.conditions = conditions or []
        self.actions = actions or []
        self.enabled = enabled
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.executions: list[dict[str, Any]] = []

    def matches(self, event: Event) -> bool:
        """Check if workflow should trigger on this event."""
        if not self.enabled:
            return False

        if self.event_type and event.event_type != self.event_type:
            return False

        # Evaluate all conditions
        condition_data = {**event.data, "event_type": event.event_type.value}
        for condition in self.conditions:
            if not condition.evaluate(condition_data):
                return False

        return True

    def execute(self, event: Event) -> dict[str, Any]:
        """Execute workflow actions."""
        logger.info(
            f"Executing workflow {self.name}",
            extra={"workflow_id": self.workflow_id, "event_id": event.event_id},
        )

        execution = {
            "execution_id": f"exec_{uuid.uuid4().hex[:12]}",
            "workflow_id": self.workflow_id,
            "event_id": event.event_id,
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            "actions_executed": [],
            "status": "completed",
        }

        # Build execution context from event
        context = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "entity_id": event.entity_id,
            "entity_type": event.entity_type,
            **event.data,
        }

        # Execute each action
        for action in self.actions:
            result = ActionExecutor.execute(action, context)
            execution["actions_executed"].append(
                {
                    "action_id": action.action_id,
                    "action_type": action.action_type.value,
                    "result": result,
                }
            )

            if not result.get("ok"):
                execution["status"] = "partial_failure"

        self.executions.append(execution)
        return execution

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "event_type": self.event_type.value if self.event_type else None,
            "conditions": [c.to_dict() for c in self.conditions],
            "actions": [_action_to_dict(a) for a in self.actions],
            "enabled": self.enabled,
            "created_at": self.created_at,
            "execution_count": len(self.executions),
        }


def _workflows_db():
    """Open a DB session for workflow persistence. Returns None if unavailable."""
    try:
        from revenue_os.database import SessionLocal
        return SessionLocal()
    except Exception:
        return None


class WorkflowEngine:
    """Manages and executes workflows.

    Workflows run from the in-memory ``_workflows`` list for speed, but every
    mutation writes through to ``WorkflowDefinitionRecord`` and the list is
    hydrated from that table once per process — otherwise every workflow a
    founder builds evaporates the moment the process restarts.
    """

    _workflows: list[Workflow] = []
    _execution_history: list[dict[str, Any]] = []
    _hydrated: bool = False

    @classmethod
    def _hydrate_from_db(cls) -> None:
        if cls._hydrated:
            return
        cls._hydrated = True
        db = _workflows_db()
        if db is None:
            return
        try:
            from revenue_os.models.automation_state import WorkflowDefinitionRecord

            known_ids = {w.workflow_id for w in cls._workflows}
            for row in db.query(WorkflowDefinitionRecord).all():
                if row.id in known_ids:
                    continue
                workflow = Workflow(
                    name=row.name,
                    description=row.description or "",
                    event_type=EventType(row.event_type) if row.event_type else None,
                    conditions=[Condition.from_dict(c) for c in (row.conditions or [])],
                    actions=[_action_from_dict(a) for a in (row.actions or [])],
                    enabled=bool(row.is_enabled),
                )
                workflow.workflow_id = row.id
                workflow.created_at = row.created_at.isoformat() if row.created_at else workflow.created_at
                cls._workflows.append(workflow)
        except Exception as e:
            logger.warning(f"Workflow hydration skipped: {e}")
        finally:
            db.close()

    @classmethod
    def _persist(cls, workflow: Workflow) -> None:
        db = _workflows_db()
        if db is None:
            return
        try:
            from revenue_os.models.automation_state import WorkflowDefinitionRecord

            row = db.get(WorkflowDefinitionRecord, workflow.workflow_id)
            if row is None:
                row = WorkflowDefinitionRecord(id=workflow.workflow_id)
                db.add(row)
            row.name = workflow.name
            row.description = workflow.description
            row.event_type = workflow.event_type.value if workflow.event_type else None
            row.conditions = [c.to_dict() for c in workflow.conditions]
            row.actions = [_action_to_dict(a) for a in workflow.actions]
            row.is_enabled = 1 if workflow.enabled else 0
            db.commit()
        except Exception as e:
            logger.warning(f"Workflow not persisted ({workflow.workflow_id}): {e}")
        finally:
            db.close()

    @classmethod
    def register_workflow(cls, workflow: Workflow) -> None:
        """Register a workflow (persisted)."""
        cls._workflows.append(workflow)
        cls._persist(workflow)
        logger.info(f"Workflow registered: {workflow.name}", extra={"workflow_id": workflow.workflow_id})

    @classmethod
    def save_workflow(cls, workflow: Workflow) -> None:
        """Persist changes to an already-registered workflow (toggle, edit)."""
        cls._persist(workflow)

    @classmethod
    def unregister_workflow(cls, workflow_id: str) -> bool:
        """Unregister a workflow by ID (persisted)."""
        cls._workflows = [w for w in cls._workflows if w.workflow_id != workflow_id]
        db = _workflows_db()
        if db is not None:
            try:
                from revenue_os.models.automation_state import WorkflowDefinitionRecord

                row = db.get(WorkflowDefinitionRecord, workflow_id)
                if row is not None:
                    db.delete(row)
                    db.commit()
            except Exception as e:
                logger.warning(f"Workflow delete not persisted ({workflow_id}): {e}")
            finally:
                db.close()
        return True

    @classmethod
    def get_workflow(cls, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID."""
        cls._hydrate_from_db()
        return next((w for w in cls._workflows if w.workflow_id == workflow_id), None)

    @classmethod
    def list_workflows(cls, enabled_only: bool = False) -> list[Workflow]:
        """List all workflows."""
        cls._hydrate_from_db()
        workflows = cls._workflows
        if enabled_only:
            workflows = [w for w in workflows if w.enabled]
        return workflows

    @classmethod
    def on_event(cls, event: Event) -> list[dict[str, Any]]:
        """Process event and execute matching workflows."""
        cls._hydrate_from_db()
        executions = []

        for workflow in cls._workflows:
            if workflow.matches(event):
                execution = workflow.execute(event)
                executions.append(execution)
                cls._execution_history.append(execution)

        if executions:
            logger.info(
                f"Event triggered {len(executions)} workflow(s)",
                extra={"event_id": event.event_id},
            )

        return executions

    @classmethod
    def get_execution_history(cls, workflow_id: Optional[str] = None, limit: int = 100) -> list[dict[str, Any]]:
        """Get workflow execution history."""
        history = cls._execution_history
        if workflow_id:
            history = [e for e in history if e.get("workflow_id") == workflow_id]
        return history[-limit:]


# Preset workflows for common scenarios

def create_lead_qualified_workflow() -> Workflow:
    """Create workflow: When lead qualifies, notify sales and trigger SDR."""
    return Workflow(
        name="Lead Qualified → Notify & Outreach",
        description="When a contact reaches QUALIFIED status, notify sales and trigger SDR crew",
        event_type=EventType.LEAD_QUALIFIED,
        conditions=[],
        actions=[
            Action(
                action_type=ActionType.SEND_SLACK,
                config={
                    "channel": "#sales",
                    "message": "🔥 Lead qualified: {entity_id} (Score: {score})",
                },
            ),
            Action(
                action_type=ActionType.CREATE_TASK,
                config={
                    "title": "Review qualified lead",
                    "description": "New qualified lead ready for outreach",
                    "due_in_hours": 4,
                },
            ),
            Action(
                action_type=ActionType.TRIGGER_SDR,
                config={"use_llm": True},
            ),
        ],
        enabled=True,
    )


def create_deal_at_risk_workflow() -> Workflow:
    """Create workflow: When deal at risk, alert manager and escalate."""
    return Workflow(
        name="Deal at Risk → Alert & Escalate",
        description="When a deal is flagged at-risk, send alert and create escalation task",
        event_type=EventType.DEAL_AT_RISK,
        conditions=[
            Condition("risk_score", "gte", 30),
        ],
        actions=[
            Action(
                action_type=ActionType.SEND_SLACK,
                config={
                    "channel": "#sales-alerts",
                    "message": "⚠️ Deal at risk: {entity_id} (Risk: {risk_score}, Days overdue: {days_overdue})",
                },
            ),
            Action(
                action_type=ActionType.CREATE_TASK,
                config={
                    "title": "Escalate at-risk deal",
                    "description": "Deal has been at-risk for {days_overdue} days. Immediate action required.",
                    "due_in_hours": 2,
                },
            ),
        ],
        enabled=True,
    )


def create_deal_closed_workflow() -> Workflow:
    """Create workflow: When deal closes, update metrics and notify team."""
    return Workflow(
        name="Deal Closed → Update & Celebrate",
        description="When deal closes, update forecast and notify team",
        event_type=EventType.DEAL_CLOSED,
        conditions=[],
        actions=[
            Action(
                action_type=ActionType.SEND_SLACK,
                config={
                    "channel": "#general",
                    "message": "🎉 Deal closed: {entity_id} (Value: ${value})",
                },
            ),
            Action(
                action_type=ActionType.CREATE_ACTIVITY,
                config={
                    "activity_type": "deal_closed",
                    "subject": "Deal Closed",
                    "body": "Deal successfully closed",
                },
            ),
        ],
        enabled=True,
    )


def create_crew_completed_workflow() -> Workflow:
    """Create workflow: When crew completes, notify relevant team."""
    return Workflow(
        name="Crew Completed → Notify Team",
        description="When content or marketing crew completes, notify team",
        event_type=EventType.CREW_COMPLETED,
        conditions=[],
        actions=[
            Action(
                action_type=ActionType.SEND_SLACK,
                config={
                    "channel": "#content",
                    "message": "✅ {crew_name} crew completed (Type: {crew_type})",
                },
            ),
        ],
        enabled=True,
    )
