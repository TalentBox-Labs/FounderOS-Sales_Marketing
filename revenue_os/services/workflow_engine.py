from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from revenue_os.models.automation import (
    Action,
    Trigger,
    Workflow,
    WorkflowExecution,
    WorkflowStep,
)
from revenue_os.models.task import Task, TaskPriority, TaskStatus


TRIGGER_EVENTS = {
    "contact.created",
    "contact.updated",
    "deal.created",
    "deal.stage_changed",
    "deal.updated",
    "deal.won",
    "deal.lost",
    "email.opened",
    "email.clicked",
    "email.replied",
    "scheduled.time",
}

ACTION_TYPES = {
    "create_task",
    "update_deal_stage",
    "send_email",
    "send_webhook",
    "update_contact_status",
    "score_contact",
    "add_tag",
}


def evaluate_conditions(conditions_str: Optional[str], context: dict) -> bool:
    if not conditions_str or not conditions_str.strip():
        return True
    try:
        conditions = json.loads(conditions_str)
    except (json.JSONDecodeError, TypeError):
        return True

    if not isinstance(conditions, dict):
        return True

    for field, expected in conditions.items():
        actual = context.get(field)
        if isinstance(expected, list):
            if actual not in expected:
                return False
        elif actual != expected:
            return False
    return True


def execute_action(
    db: Session,
    action: Action,
    step: WorkflowStep,
    context: dict,
    current_user_id: Optional[uuid.UUID] = None,
) -> str:
    action_type = action.action_type
    config = {}
    if action.config:
        try:
            config = json.loads(action.config)
        except (json.JSONDecodeError, TypeError):
            config = {}

    if action_type == "create_task":
        title = config.get("title", "Task from workflow").format(**context)
        assigned_to = config.get("assigned_to")
        if assigned_to and assigned_to in context:
            assigned_to = context[assigned_to]
        priority_str = config.get("priority", "none")

        try:
            priority = TaskPriority(priority_str)
        except ValueError:
            priority = TaskPriority.NONE

        task = Task(
            title=title,
            description=config.get("description", "").format(**context),
            assigned_to=uuid.UUID(assigned_to) if assigned_to and isinstance(assigned_to, str) else None,
            created_by=current_user_id or uuid.uuid4(),
            priority=priority,
            related_entity_type=config.get("related_type"),
            related_entity_id=context.get("entity_id"),
        )
        db.add(task)
        db.flush()
        return f"Created task: {task.id}"

    elif action_type == "update_deal_stage":
        from revenue_os.models.deal import Deal, DealStage

        deal_id = context.get("entity_id") or config.get("deal_id")
        if deal_id:
            deal = db.query(Deal).filter(Deal.id == deal_id).first()
            if deal:
                new_stage = config.get("stage", deal.stage.value)
                try:
                    deal.stage = DealStage(new_stage)
                except ValueError:
                    pass
                if new_stage == "closed_won":
                    deal.closed_at = datetime.utcnow()
                db.flush()
                return f"Updated deal {deal_id} to stage {new_stage}"
        return "No deal_id found in context"

    elif action_type == "update_contact_status":
        from revenue_os.models.contact import Contact, ContactStatus

        contact_id = context.get("entity_id") or config.get("contact_id")
        if contact_id:
            contact = db.query(Contact).filter(Contact.id == contact_id).first()
            if contact:
                new_status = config.get("status", "qualified")
                try:
                    contact.status = ContactStatus(new_status)
                except ValueError:
                    pass
                db.flush()
                return f"Updated contact {contact_id} status to {new_status}"
        return "No contact_id found"

    elif action_type == "add_tag":
        entity_id = context.get("entity_id")
        tag = config.get("tag", "")
        if entity_id and tag:
            from revenue_os.models.contact import Contact

            contact = db.query(Contact).filter(Contact.id == entity_id).first()
            if contact:
                existing_tags = (contact.tags or "").split(",")
                if tag not in [t.strip() for t in existing_tags]:
                    new_tags = (contact.tags + "," + tag) if contact.tags else tag
                    contact.tags = new_tags
                    db.flush()
                return f"Added tag '{tag}' to contact {entity_id}"
        return "Cannot add tag"

    elif action_type == "score_contact":
        from revenue_os.services.scoring_service import score_contact

        contact_id = context.get("entity_id")
        if contact_id:
            score_contact(db, contact_id)
            db.flush()
            return f"Re-scored contact {contact_id}"
        return "No contact_id for scoring"

    elif action_type == "send_webhook":
        import requests

        url = config.get("url", "")
        if url:
            try:
                payload = {k: context.get(k, v) for k, v in config.get("payload", {}).items()}
                requests.post(url, json=payload, timeout=10)
                return f"Webhook sent to {url}"
            except Exception as e:
                return f"Webhook failed: {e}"
        return "No webhook URL"

    return f"Unknown action type: {action_type}"


def run_workflow(
    db: Session,
    workflow_id: uuid.UUID,
    event: str,
    context: dict,
    current_user_id: Optional[uuid.UUID] = None,
) -> dict:
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        return {"status": "error", "error": "Workflow not found"}
    if not workflow.is_active:
        return {"status": "skipped", "error": "Workflow is inactive"}

    execution = WorkflowExecution(
        workflow_id=workflow_id,
        trigger_event=event,
        status="running",
    )
    db.add(execution)
    db.flush()

    steps = (
        db.query(WorkflowStep)
        .filter(WorkflowStep.workflow_id == workflow_id)
        .order_by(WorkflowStep.step_order)
        .all()
    )

    results = []
    errors = []
    try:
        for step in steps:
            if not evaluate_conditions(step.conditions, context):
                results.append(f"Step {step.step_order}: conditions not met, skipped")
                continue

            if step.step_type == "action" and step.action_id:
                action = db.query(Action).filter(Action.id == step.action_id).first()
                if action:
                    try:
                        result = execute_action(db, action, step, context, current_user_id)
                        results.append(f"Step {step.step_order}: {result}")
                    except Exception as e:
                        errors.append(f"Step {step.step_order}: {e}")
                else:
                    errors.append(f"Step {step.step_order}: action not found")
            elif step.step_type == "delay":
                import time
                delay_seconds = step.config.get("seconds", 60) if step.config else 60
                time.sleep(min(delay_seconds, 30))
                results.append(f"Step {step.step_order}: delayed {delay_seconds}s")

        execution.status = "completed" if not errors else "completed_with_errors"
        execution.result = json.dumps({"steps": results, "errors": errors})
        execution.completed_at = datetime.utcnow()
        db.commit()

        return {"status": execution.status, "results": results, "errors": errors}

    except Exception as e:
        execution.status = "failed"
        execution.error = str(e)
        execution.completed_at = datetime.utcnow()
        db.commit()
        return {"status": "failed", "error": str(e)}


def find_matching_workflows(
    db: Session, event: str, context: dict
) -> list[Workflow]:
    from sqlalchemy.orm import joinedload

    workflows = (
        db.query(Workflow)
        .options(joinedload(Workflow.steps))
        .filter(Workflow.is_active == 1)
        .all()
    )

    matching = []
    for wf in workflows:
        if wf.trigger_id:
            trigger = db.query(Trigger).filter(Trigger.id == wf.trigger_id).first()
            if trigger and trigger.trigger_type == event and trigger.is_active:
                matching.append(wf)
    return matching


def trigger_event(
    db: Session,
    event: str,
    context: dict,
    current_user_id: Optional[uuid.UUID] = None,
) -> list[dict]:
    workflows = find_matching_workflows(db, event, context)
    results = []
    for wf in workflows:
        result = run_workflow(db, wf.id, event, context, current_user_id)
        results.append({"workflow_id": str(wf.id), "workflow_name": wf.name, **result})
    return results
