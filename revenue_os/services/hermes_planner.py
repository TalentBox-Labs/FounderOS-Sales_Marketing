"""Hermes autonomous planner: goal -> plan -> execute -> measure -> adapt.

Give Hermes a goal ("20 qualified leads", "$500K pipeline") and it:

  1. generates an executable plan from a library of proven revenue plays
  2. executes plan steps through the same services the API uses
     (scoring, qualification, deal creation) — every action audited
  3. measures progress against the goal metric on every heartbeat check
  4. marks the goal achieved when the target is reached

The planner is deliberately deterministic (rule-based) so it runs without
an LLM; emitted events (lead_qualified, deal_created) flow through the
EventBus to workflows and the n8n bridge, which is where outreach happens.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy.orm import Session

from revenue_os.database import SessionLocal
from revenue_os.models.contact import Contact, ContactStatus
from revenue_os.models.goals import Goal, GoalStep
from revenue_os.services.activity_log import log_agent_action

logger = logging.getLogger(__name__)

ACTOR = "hermes"

SUPPORTED_METRICS = ("qualified_leads", "pipeline_value", "deals_closed")

QUALIFY_SCORE_THRESHOLD = 70


# ── Progress measurement ─────────────────────────────────────────────────────


def measure_metric(db: Session, metric: str) -> float:
    """Current absolute value of a goal metric."""
    if metric == "qualified_leads":
        return float(
            db.query(Contact).filter(Contact.status == ContactStatus.QUALIFIED).count()
        )
    if metric == "pipeline_value":
        from revenue_os.services.deal_automation_service import get_pipeline_health
        return float(get_pipeline_health(db).get("total_pipeline_value", 0) or 0)
    if metric == "deals_closed":
        from revenue_os.models.deal import Deal, DealStage
        return float(db.query(Deal).filter(Deal.stage == DealStage.CLOSED_WON).count())
    raise ValueError(f"Unsupported metric: {metric}")


# ── Executable actions (the plays Hermes can run) ────────────────────────────


def action_score_unscored_leads(db: Session, params: dict) -> dict[str, Any]:
    """Score contacts that have no lead score yet."""
    from revenue_os.services.lead_scoring_service import score_contact

    limit = int(params.get("limit", 50))
    contacts = (
        db.query(Contact)
        .filter((Contact.lead_score == None) | (Contact.lead_score == 0))  # noqa: E711
        .limit(limit)
        .all()
    )
    scored = 0
    for contact in contacts:
        try:
            score_contact(db, contact)
            scored += 1
        except Exception as e:
            logger.warning(f"Hermes scoring failed for {contact.id}: {e}")
    db.commit()
    return {"scored": scored}


def action_qualify_high_scorers(db: Session, params: dict) -> dict[str, Any]:
    """Promote high-scoring leads/prospects to qualified and emit events."""
    from revenue_os.automation.events import emit_contact_qualified

    threshold = int(params.get("threshold", QUALIFY_SCORE_THRESHOLD))
    candidates = (
        db.query(Contact)
        .filter(
            Contact.lead_score >= threshold,
            Contact.status.in_([ContactStatus.LEAD, ContactStatus.PROSPECT]),
        )
        .limit(int(params.get("limit", 25)))
        .all()
    )
    qualified = []
    for contact in candidates:
        contact.status = ContactStatus.QUALIFIED
        qualified.append({
            "id": str(contact.id),
            "name": f"{contact.first_name} {contact.last_name}".strip(),
            "email": contact.email,
        })
    db.commit()

    from revenue_os.services.approvals import request_approval

    for contact in qualified:
        try:
            emit_contact_qualified(contact["id"])
        except Exception as e:
            logger.warning(f"emit_contact_qualified failed for {contact['id']}: {e}")
        # Outbound email is a risky action: propose it, let a human approve.
        try:
            request_approval(
                requested_by=ACTOR,
                action_type="send_outreach_email",
                title=f"Send intro email to {contact['name'] or contact['email']}",
                description=(
                    "Contact was auto-qualified by Hermes (score >= "
                    f"{threshold}). Approving hands the intro email to the "
                    "n8n send-email workflow."
                ),
                target_type="contact",
                target_id=contact["id"],
                payload={"contact_id": contact["id"], "name": contact["name"],
                         "email": contact["email"], "template": "intro"},
            )
            # Hand off awareness of the pending approval to the founder-facing
            # agent — the concrete example of inter-agent collaboration this
            # platform actually does, not a demo message.
            try:
                from revenue_os.agents.orchestration import AgentCoordinator

                AgentCoordinator.send_message(
                    from_agent="hermes", to_agent="copilot",
                    message=f"Qualified {contact['name'] or contact['email']} and proposed an intro email — awaiting founder approval.",
                    data={"contact_id": contact["id"], "action_type": "send_outreach_email"},
                )
            except Exception as e:
                logger.warning(f"agent handoff message failed for {contact['id']}: {e}")
        except Exception as e:
            logger.warning(f"approval request failed for {contact['id']}: {e}")
    return {"qualified": len(qualified), "threshold": threshold,
            "outreach_approvals_filed": len(qualified)}


def action_create_deals_for_qualified(db: Session, params: dict) -> dict[str, Any]:
    """Open a deal for every qualified contact that doesn't have one yet."""
    from revenue_os.services.deal_automation_service import create_deal_from_contact

    default_value = float(params.get("default_value", 5000.0))
    contacts = (
        db.query(Contact)
        .filter(Contact.status == ContactStatus.QUALIFIED)
        .limit(int(params.get("limit", 25)))
        .all()
    )
    created = 0
    for contact in contacts:
        try:
            deal = create_deal_from_contact(db, contact, value=default_value)
            if deal is not None:
                created += 1
        except Exception as e:
            logger.warning(f"Deal creation failed for {contact.id}: {e}")
    db.commit()
    return {"deals_created": created, "qualified_considered": len(contacts)}


def action_check_deals_at_risk(db: Session, params: dict) -> dict[str, Any]:
    """Surface at-risk deals so workflows/n8n can chase them."""
    from revenue_os.automation.events import emit_deal_at_risk
    from revenue_os.services.deal_automation_service import get_deals_at_risk

    at_risk = get_deals_at_risk(db)
    for deal in at_risk:
        deal_id = str(deal.get("deal_id") or deal.get("id") or "")
        try:
            emit_deal_at_risk(
                deal_id=deal_id,
                risk_score=int(deal.get("risk_score", 0)),
                days_overdue=int(deal.get("days_overdue", 0)),
            )
        except Exception:
            pass
    return {"deals_at_risk": len(at_risk)}


ACTION_REGISTRY: dict[str, Callable[[Session, dict], dict[str, Any]]] = {
    "score_unscored_leads": action_score_unscored_leads,
    "qualify_high_scorers": action_qualify_high_scorers,
    "create_deals_for_qualified": action_create_deals_for_qualified,
    "check_deals_at_risk": action_check_deals_at_risk,
}


# ── Plan generation ──────────────────────────────────────────────────────────


def generate_plan(metric: str) -> list[dict[str, Any]]:
    """Deterministic plan templates per goal metric.

    Steps with repeat=True re-run on every goal check; one-shot steps run once.
    """
    if metric == "qualified_leads":
        return [
            {"title": "Score all unscored leads", "action_type": "score_unscored_leads",
             "params": {"limit": 100}, "repeat": True},
            {"title": f"Qualify contacts scoring >= {QUALIFY_SCORE_THRESHOLD}",
             "action_type": "qualify_high_scorers",
             "params": {"threshold": QUALIFY_SCORE_THRESHOLD}, "repeat": True},
        ]
    if metric == "pipeline_value":
        return [
            {"title": "Score all unscored leads", "action_type": "score_unscored_leads",
             "params": {"limit": 100}, "repeat": True},
            {"title": "Qualify high-scoring contacts", "action_type": "qualify_high_scorers",
             "params": {"threshold": QUALIFY_SCORE_THRESHOLD}, "repeat": True},
            {"title": "Open deals for qualified contacts",
             "action_type": "create_deals_for_qualified", "params": {}, "repeat": True},
        ]
    if metric == "deals_closed":
        return [
            {"title": "Open deals for qualified contacts",
             "action_type": "create_deals_for_qualified", "params": {}, "repeat": True},
            {"title": "Flag at-risk deals for follow-up",
             "action_type": "check_deals_at_risk", "params": {}, "repeat": True},
        ]
    raise ValueError(f"Unsupported metric: {metric}. Supported: {SUPPORTED_METRICS}")


# ── Goal lifecycle ───────────────────────────────────────────────────────────


def create_goal(
    title: str,
    metric: str,
    target_value: float,
    description: str = "",
    deadline: datetime | None = None,
    agent_name: str | None = None,
) -> dict[str, Any]:
    """Create a goal, snapshot its baseline, and generate its plan."""
    if metric not in SUPPORTED_METRICS:
        raise ValueError(f"Unsupported metric: {metric}. Supported: {SUPPORTED_METRICS}")

    plan = generate_plan(metric)
    db = SessionLocal()
    try:
        baseline = measure_metric(db, metric)
        goal = Goal(
            title=title,
            description=description,
            agent_name=agent_name,
            metric=metric,
            target_value=target_value,
            baseline_value=baseline,
            current_value=baseline,
            deadline=deadline,
        )
        db.add(goal)
        db.flush()
        for i, step in enumerate(plan):
            db.add(GoalStep(
                goal_id=goal.id,
                order=i,
                title=step["title"],
                action_type=step["action_type"],
                params=step.get("params") or {},
                repeat=1 if step.get("repeat") else 0,
            ))
        db.commit()
        db.refresh(goal)
        result = goal.to_dict()
        result["plan"] = [s.to_dict() for s in _get_steps(db, goal.id)]
    finally:
        db.close()

    log_agent_action(
        actor=ACTOR, action_type="goal_created", target_type="goal",
        target_id=result["id"],
        detail={"title": title, "metric": metric, "target": target_value,
                "baseline": result["baseline_value"], "plan_steps": len(plan)},
    )
    return result


def _get_steps(db: Session, goal_id: str) -> list[GoalStep]:
    return (
        db.query(GoalStep)
        .filter(GoalStep.goal_id == goal_id)
        .order_by(GoalStep.order.asc())
        .all()
    )


def run_goal_check(goal_id: str) -> dict[str, Any]:
    """One Hermes cycle for a goal: execute due steps, measure, adapt status."""
    db = SessionLocal()
    try:
        goal = db.get(Goal, goal_id)
        if goal is None:
            raise ValueError(f"Goal not found: {goal_id}")
        if goal.status not in ("active",):
            return {"goal_id": goal_id, "status": goal.status, "skipped": True}

        executed: list[dict[str, Any]] = []
        for step in _get_steps(db, goal_id):
            due = step.status == "pending" or (step.repeat and step.status != "failed")
            if not due:
                continue
            action = ACTION_REGISTRY.get(step.action_type)
            if action is None:
                step.status = "skipped"
                step.result = {"error": f"unknown action {step.action_type}"}
                continue
            try:
                result = action(db, step.params or {})
                step.status = "completed"
                step.result = result
                executed.append({"step": step.title, **result})
            except Exception as e:
                step.status = "failed"
                step.result = {"error": str(e)}
                executed.append({"step": step.title, "error": str(e)})
                logger.error(f"Hermes step failed ({step.title}): {e}")
            step.runs += 1
            step.executed_at = datetime.now(timezone.utc)

        goal.current_value = measure_metric(db, goal.metric)
        goal.last_checked_at = datetime.now(timezone.utc)
        goal.checks += 1
        achieved = goal.current_value >= goal.target_value
        if achieved:
            goal.status = "achieved"
        db.commit()

        summary = {
            "goal_id": goal_id,
            "title": goal.title,
            "status": goal.status,
            "current_value": goal.current_value,
            "target_value": goal.target_value,
            "progress": round(goal.progress(), 3),
            "steps_executed": executed,
        }
    finally:
        db.close()

    log_agent_action(
        actor=ACTOR,
        action_type="goal_achieved" if summary["status"] == "achieved" else "goal_checked",
        target_type="goal", target_id=goal_id,
        detail=summary,
    )
    return summary


def check_all_active_goals() -> dict[str, Any]:
    """Heartbeat entrypoint: run one cycle for every active goal."""
    db = SessionLocal()
    try:
        goal_ids = [g.id for g in db.query(Goal).filter(Goal.status == "active").all()]
    finally:
        db.close()

    results = [run_goal_check(goal_id) for goal_id in goal_ids]
    return {
        "goals_checked": len(results),
        "achieved": sum(1 for r in results if r.get("status") == "achieved"),
    }
