"""Automation and workflow management endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from revenue_os.automation.actions import ActionType, Action, ActionExecutor
from revenue_os.automation.events import EventBus, EventType
from revenue_os.automation.workflows import (
    Condition,
    Workflow,
    WorkflowEngine,
    create_deal_at_risk_workflow,
    create_deal_closed_workflow,
    create_lead_qualified_workflow,
    create_crew_completed_workflow,
)
from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/automation", tags=["automation"])


class ConditionRequest(BaseModel):
    """Condition specification."""

    field: str
    operator: str = Field(..., pattern="^(eq|gte|lte|gt|lt|contains|in|exists)$")
    value: Any = None


class ActionRequest(BaseModel):
    """Action specification."""

    action_type: str
    config: dict[str, Any]
    enabled: bool = True


class WorkflowRequest(BaseModel):
    """Create or update workflow."""

    name: str
    description: str = ""
    event_type: str
    conditions: list[ConditionRequest] = Field(default_factory=list)
    actions: list[ActionRequest] = Field(default_factory=list)
    enabled: bool = True


class EventResponse(BaseModel):
    """Event response."""

    event_id: str
    event_type: str
    entity_id: str
    entity_type: str
    priority: str
    timestamp: str


@router.post("/workflows", tags=["automation"])
def create_workflow(
    req: WorkflowRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Create a new workflow."""
    logger.info("Creating workflow", extra={"workflow_name": req.name, "event_type": req.event_type})

    # Validate event type
    try:
        event_type = EventType(req.event_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid event type: {req.event_type}")

    # Parse conditions
    conditions = []
    for cond_req in req.conditions:
        conditions.append(Condition(cond_req.field, cond_req.operator, cond_req.value))

    # Parse actions
    actions = []
    for action_req in req.actions:
        try:
            action_type = ActionType(action_req.action_type)
            actions.append(Action(action_type=action_type, config=action_req.config, enabled=action_req.enabled))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid action type: {action_req.action_type}")

    # Create workflow
    workflow = Workflow(
        name=req.name,
        description=req.description,
        event_type=event_type,
        conditions=conditions,
        actions=actions,
        enabled=req.enabled,
    )

    WorkflowEngine.register_workflow(workflow)

    return {"ok": True, "workflow": workflow.to_dict()}


@router.get("/workflows", tags=["automation"])
def list_workflows(
    enabled_only: bool = False,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """List all workflows."""
    logger.info("Listing workflows", extra={"enabled_only": enabled_only})

    workflows = WorkflowEngine.list_workflows(enabled_only=enabled_only)

    return {
        "ok": True,
        "count": len(workflows),
        "workflows": [w.to_dict() for w in workflows],
    }


@router.get("/workflows/{workflow_id}", tags=["automation"])
def get_workflow(
    workflow_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get a specific workflow."""
    workflow = WorkflowEngine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {"ok": True, "workflow": workflow.to_dict()}


@router.put("/workflows/{workflow_id}/toggle", tags=["automation"])
def toggle_workflow(
    workflow_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Enable/disable a workflow."""
    workflow = WorkflowEngine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow.enabled = not workflow.enabled
    WorkflowEngine.save_workflow(workflow)
    logger.info(
        f"Workflow toggled",
        extra={"workflow_id": workflow_id, "enabled": workflow.enabled},
    )

    return {"ok": True, "workflow": workflow.to_dict()}


@router.put("/workflows/{workflow_id}", tags=["automation"])
def update_workflow(
    workflow_id: str,
    req: WorkflowRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Replace a workflow's name/description/event/conditions/actions in place."""
    workflow = WorkflowEngine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    try:
        event_type = EventType(req.event_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid event type: {req.event_type}")

    conditions = [Condition(c.field, c.operator, c.value) for c in req.conditions]

    actions = []
    for action_req in req.actions:
        try:
            action_type = ActionType(action_req.action_type)
            actions.append(Action(action_type=action_type, config=action_req.config, enabled=action_req.enabled))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid action type: {action_req.action_type}")

    workflow.name = req.name
    workflow.description = req.description
    workflow.event_type = event_type
    workflow.conditions = conditions
    workflow.actions = actions
    workflow.enabled = req.enabled
    WorkflowEngine.save_workflow(workflow)

    return {"ok": True, "workflow": workflow.to_dict()}


@router.delete("/workflows/{workflow_id}", tags=["automation"])
def delete_workflow(
    workflow_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Delete a workflow."""
    WorkflowEngine.unregister_workflow(workflow_id)
    logger.info("Workflow deleted", extra={"workflow_id": workflow_id})

    return {"ok": True, "message": "Workflow deleted"}


@router.post("/workflows/presets/lead-qualified", tags=["automation"])
def create_lead_qualified_preset(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Create preset: Lead Qualified workflow."""
    workflow = create_lead_qualified_workflow()
    WorkflowEngine.register_workflow(workflow)

    return {"ok": True, "workflow": workflow.to_dict()}


@router.post("/workflows/presets/deal-at-risk", tags=["automation"])
def create_deal_at_risk_preset(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Create preset: Deal at Risk workflow."""
    workflow = create_deal_at_risk_workflow()
    WorkflowEngine.register_workflow(workflow)

    return {"ok": True, "workflow": workflow.to_dict()}


@router.post("/workflows/presets/deal-closed", tags=["automation"])
def create_deal_closed_preset(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Create preset: Deal Closed workflow."""
    workflow = create_deal_closed_workflow()
    WorkflowEngine.register_workflow(workflow)

    return {"ok": True, "workflow": workflow.to_dict()}


@router.post("/workflows/presets/crew-completed", tags=["automation"])
def create_crew_completed_preset(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Create preset: Crew Completed workflow."""
    workflow = create_crew_completed_workflow()
    WorkflowEngine.register_workflow(workflow)

    return {"ok": True, "workflow": workflow.to_dict()}


@router.get("/workflows/{workflow_id}/executions", tags=["automation"])
def get_workflow_executions(
    workflow_id: str,
    limit: int = 50,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get execution history for a workflow."""
    history = WorkflowEngine.get_execution_history(workflow_id=workflow_id, limit=limit)

    return {
        "ok": True,
        "workflow_id": workflow_id,
        "execution_count": len(history),
        "executions": history,
    }


@router.get("/events/history", tags=["automation"])
def get_event_history(
    event_type: str | None = None,
    limit: int = 50,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get recent events from event bus."""
    filter_type = None
    if event_type:
        try:
            filter_type = EventType(event_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")

    events = EventBus.get_history(event_type=filter_type, limit=limit)

    return {
        "ok": True,
        "count": len(events),
        "events": [e.to_dict() for e in events],
    }


@router.get("/actions/types", tags=["automation"])
def list_action_types(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """List available action types."""
    action_types = [
        {
            "name": at.value,
            "description": f"Action type: {at.value}",
        }
        for at in ActionType
    ]

    return {"ok": True, "action_types": action_types}


@router.get("/events/types", tags=["automation"])
def list_event_types(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """List available event types."""
    event_types = [
        {
            "name": et.value,
            "description": f"Event type: {et.value}",
        }
        for et in EventType
    ]

    return {"ok": True, "event_types": event_types}


@router.get("/health", tags=["automation"])
def automation_health(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get automation system health."""
    workflows = WorkflowEngine.list_workflows()
    enabled = len([w for w in workflows if w.enabled])

    return {
        "ok": True,
        "total_workflows": len(workflows),
        "enabled_workflows": enabled,
        "status": "healthy",
    }
