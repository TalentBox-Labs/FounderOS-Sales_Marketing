from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from revenue_os.auth import get_current_user
from revenue_os.database import get_db
from revenue_os.models.automation import (
    Action,
    Trigger,
    Workflow,
    WorkflowExecution,
    WorkflowStep,
)
from revenue_os.models.user import User
from revenue_os.services.workflow_engine import (
    ACTION_TYPES,
    TRIGGER_EVENTS,
    run_workflow,
    trigger_event,
)

router = APIRouter(prefix="/automation", tags=["automation"])


# ── Schemas ──

class TriggerCreate(BaseModel):
    name: str
    trigger_type: str
    config: Optional[str] = None


class TriggerUpdate(BaseModel):
    name: Optional[str] = None
    trigger_type: Optional[str] = None
    config: Optional[str] = None
    is_active: Optional[int] = None


class TriggerResponse(BaseModel):
    id: uuid.UUID
    name: str
    trigger_type: str
    config: Optional[str] = None
    is_active: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class ActionCreate(BaseModel):
    name: str
    action_type: str
    config: Optional[str] = None


class ActionUpdate(BaseModel):
    name: Optional[str] = None
    action_type: Optional[str] = None
    config: Optional[str] = None


class ActionResponse(BaseModel):
    id: uuid.UUID
    name: str
    action_type: str
    config: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_id: Optional[str] = None
    is_template: int = 0


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_id: Optional[str] = None
    is_active: Optional[int] = None
    is_template: Optional[int] = None


class WorkflowResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    trigger_id: Optional[uuid.UUID] = None
    is_active: int
    is_template: int
    steps: list["WorkflowStepResponse"] = []
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class WorkflowStepResponse(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    action_id: Optional[uuid.UUID] = None
    step_order: int
    step_type: str
    config: Optional[str] = None
    conditions: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class WorkflowStepCreate(BaseModel):
    action_id: Optional[str] = None
    step_order: int
    step_type: str = "action"
    config: Optional[str] = None
    conditions: Optional[str] = None


class WorkflowExecutionResponse(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    trigger_event: Optional[str] = None
    status: str
    result: Optional[str] = None
    error: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class TriggerEventBody(BaseModel):
    event: str
    context: dict[str, Any] = {}
    entity_id: Optional[str] = None


# ── Triggers ──

@router.get("/triggers", response_model=list[TriggerResponse])
def list_triggers(db: Session = Depends(get_db)):
    return db.query(Trigger).order_by(Trigger.name).all()


@router.post("/triggers", response_model=TriggerResponse, status_code=201)
def create_trigger(body: TriggerCreate, db: Session = Depends(get_db)):
    if body.trigger_type not in TRIGGER_EVENTS:
        raise HTTPException(status_code=400, detail=f"Invalid trigger type. Valid: {', '.join(sorted(TRIGGER_EVENTS))}")
    trigger = Trigger(name=body.name, trigger_type=body.trigger_type, config=body.config)
    db.add(trigger)
    db.commit()
    db.refresh(trigger)
    return trigger


@router.put("/triggers/{trigger_id}", response_model=TriggerResponse)
def update_trigger(trigger_id: str, body: TriggerUpdate, db: Session = Depends(get_db)):
    trigger = db.query(Trigger).filter(Trigger.id == trigger_id).first()
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    update_data = body.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        if v is not None:
            setattr(trigger, k, v)
    db.commit()
    db.refresh(trigger)
    return trigger


@router.delete("/triggers/{trigger_id}", status_code=204)
def delete_trigger(trigger_id: str, db: Session = Depends(get_db)):
    trigger = db.query(Trigger).filter(Trigger.id == trigger_id).first()
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    db.delete(trigger)
    db.commit()


# ── Actions ──

@router.get("/actions", response_model=list[ActionResponse])
def list_actions(db: Session = Depends(get_db)):
    return db.query(Action).order_by(Action.name).all()


@router.post("/actions", response_model=ActionResponse, status_code=201)
def create_action(body: ActionCreate, db: Session = Depends(get_db)):
    if body.action_type not in ACTION_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid action type. Valid: {', '.join(sorted(ACTION_TYPES))}")
    action = Action(name=body.name, action_type=body.action_type, config=body.config)
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


@router.put("/actions/{action_id}", response_model=ActionResponse)
def update_action(action_id: str, body: ActionUpdate, db: Session = Depends(get_db)):
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    update_data = body.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        if v is not None:
            setattr(action, k, v)
    db.commit()
    db.refresh(action)
    return action


@router.delete("/actions/{action_id}", status_code=204)
def delete_action(action_id: str, db: Session = Depends(get_db)):
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    db.delete(action)
    db.commit()


# ── Workflows ──

@router.get("/workflows", response_model=list[WorkflowResponse])
def list_workflows(db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    workflows = db.query(Workflow).options(joinedload(Workflow.steps)).order_by(Workflow.name).all()
    return [
        WorkflowResponse(
            id=w.id, name=w.name, description=w.description,
            trigger_id=w.trigger_id, is_active=w.is_active, is_template=w.is_template,
            steps=[WorkflowStepResponse.model_validate(s) for s in w.steps],
            created_at=w.created_at, updated_at=w.updated_at,
        ) for w in workflows
    ]


@router.post("/workflows", response_model=WorkflowResponse, status_code=201)
def create_workflow(body: WorkflowCreate, db: Session = Depends(get_db)):
    trigger_uuid = uuid.UUID(body.trigger_id) if body.trigger_id else None
    workflow = Workflow(
        name=body.name, description=body.description,
        trigger_id=trigger_uuid, is_template=body.is_template,
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return WorkflowResponse(
        id=workflow.id, name=workflow.name, description=workflow.description,
        trigger_id=workflow.trigger_id, is_active=workflow.is_active,
        is_template=workflow.is_template, steps=[], created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    w = db.query(Workflow).options(joinedload(Workflow.steps)).filter(Workflow.id == workflow_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return WorkflowResponse(
        id=w.id, name=w.name, description=w.description,
        trigger_id=w.trigger_id, is_active=w.is_active, is_template=w.is_template,
        steps=[WorkflowStepResponse.model_validate(s) for s in w.steps],
        created_at=w.created_at, updated_at=w.updated_at,
    )


@router.put("/workflows/{workflow_id}", response_model=WorkflowResponse)
def update_workflow(workflow_id: str, body: WorkflowUpdate, db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    w = db.query(Workflow).options(joinedload(Workflow.steps)).filter(Workflow.id == workflow_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Workflow not found")
    update_data = body.model_dump(exclude_unset=True)
    if "trigger_id" in update_data:
        update_data["trigger_id"] = uuid.UUID(body.trigger_id) if body.trigger_id else None
    for k, v in update_data.items():
        if v is not None:
            setattr(w, k, v)
    db.commit()
    db.refresh(w)
    return WorkflowResponse(
        id=w.id, name=w.name, description=w.description,
        trigger_id=w.trigger_id, is_active=w.is_active, is_template=w.is_template,
        steps=[WorkflowStepResponse.model_validate(s) for s in w.steps],
        created_at=w.created_at, updated_at=w.updated_at,
    )


@router.delete("/workflows/{workflow_id}", status_code=204)
def delete_workflow(workflow_id: str, db: Session = Depends(get_db)):
    w = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Workflow not found")
    db.query(WorkflowStep).filter(WorkflowStep.workflow_id == w.id).delete()
    db.query(WorkflowExecution).filter(WorkflowExecution.workflow_id == w.id).delete()
    db.delete(w)
    db.commit()


# ── Workflow Steps ──

@router.post("/workflows/{workflow_id}/steps", response_model=WorkflowStepResponse, status_code=201)
def add_workflow_step(workflow_id: str, body: WorkflowStepCreate, db: Session = Depends(get_db)):
    w = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if body.action_id:
        action = db.query(Action).filter(Action.id == body.action_id).first()
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")
    step = WorkflowStep(
        workflow_id=uuid.UUID(workflow_id),
        action_id=uuid.UUID(body.action_id) if body.action_id else None,
        step_order=body.step_order,
        step_type=body.step_type,
        config=body.config,
        conditions=body.conditions,
    )
    db.add(step)
    db.commit()
    db.refresh(step)
    return step


@router.delete("/workflows/{workflow_id}/steps/{step_id}", status_code=204)
def delete_workflow_step(workflow_id: str, step_id: str, db: Session = Depends(get_db)):
    step = db.query(WorkflowStep).filter(WorkflowStep.id == step_id, WorkflowStep.workflow_id == workflow_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    db.delete(step)
    db.commit()


# ── Executions ──

@router.get("/workflows/{workflow_id}/executions", response_model=list[WorkflowExecutionResponse])
def list_executions(workflow_id: str, db: Session = Depends(get_db)):
    return (
        db.query(WorkflowExecution)
        .filter(WorkflowExecution.workflow_id == workflow_id)
        .order_by(WorkflowExecution.started_at.desc())
        .limit(50)
        .all()
    )


@router.post("/trigger", status_code=200)
def trigger(body: TriggerEventBody, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    context = body.context
    if body.entity_id:
        context["entity_id"] = uuid.UUID(body.entity_id)
    results = trigger_event(db, body.event, context, current_user.id)
    return {"triggered": len(results), "results": results}


@router.get("/events")
def list_events():
    return {"trigger_events": sorted(TRIGGER_EVENTS), "action_types": sorted(ACTION_TYPES)}
