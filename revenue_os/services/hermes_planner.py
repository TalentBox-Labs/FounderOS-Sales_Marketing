"""Hermes autonomous planner: goal -> plan -> execute -> measure -> adapt.

Give Hermes a goal ("20 qualified leads", "$500K pipeline") and it:

  1. generates an executable plan from a library of proven revenue plays
  2. executes plan steps through the same services the API uses
     (scoring, qualification) — every action audited
  3. measures progress against the goal metric on every heartbeat check
  4. marks the goal achieved when the target is reached

ACP-1: commercial actions require explicit organization_id. Autonomous Deal
creation (create_deals_for_qualified) is PROHIBITED regardless of org.
Contact.organization_id is ownership validation only — never tenant activation.

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
from revenue_os.services.acp1_autonomous_boundary import (
    BLOCKED_HERMES_DEAL,
    BLOCKED_MISSING_TENANT,
    assert_contact_org,
    hermes_action_allowed,
    log_autonomous_blocked,
    org_uuid_or_none,
    require_organization_id,
)

logger = logging.getLogger(__name__)

ACTOR = "hermes"

SUPPORTED_METRICS = ("qualified_leads", "pipeline_value", "deals_closed")

QUALIFY_SCORE_THRESHOLD = 70


# ── Progress measurement ─────────────────────────────────────────────────────


def measure_metric(
    db: Session, metric: str, *, organization_id: str | None = None
) -> float:
    """Current absolute value of a goal metric.

    When organization_id is provided, counts are org-scoped. Autonomous
    callers must pass organization_id (ACP-1).
    """
    org_uuid = org_uuid_or_none(organization_id) if organization_id else None
    if metric == "qualified_leads":
        q = db.query(Contact).filter(Contact.status == ContactStatus.QUALIFIED)
        if org_uuid is not None:
            q = q.filter(Contact.organization_id == org_uuid)
        return float(q.count())
    if metric == "pipeline_value":
        from revenue_os.services.deal_automation_service import get_pipeline_health

        return float(
            get_pipeline_health(db, organization_id=organization_id).get(
                "total_pipeline_value", 0
            )
            or 0
        )
    if metric == "deals_closed":
        from revenue_os.models.deal import Deal, DealStage

        q = db.query(Deal).filter(Deal.stage == DealStage.CLOSED_WON)
        if org_uuid is not None:
            q = q.filter(Deal.organization_id == org_uuid)
        return float(q.count())
    raise ValueError(f"Unsupported metric: {metric}")


# ── Executable actions (the plays Hermes can run) ────────────────────────────


def action_score_unscored_leads(db: Session, params: dict) -> dict[str, Any]:
    """Score contacts that have no lead score yet — org-scoped (ACP-1/ACP-4).

    Each contact score is routed through orchestrate_claimed so Hermes cannot
    bypass ACP-4 claim/fence (same logical identity as scheduler: unscored).
    """
    from revenue_os.services.acp2_work_contract import WORK_LEAD_SCORE, WorkState
    from revenue_os.services.acp4_production_runtime import orchestrate_claimed
    from revenue_os.services.lead_scoring_service import score_contact

    organization_id = require_organization_id(params)
    if organization_id is None:
        return log_autonomous_blocked(
            actor=ACTOR,
            action_type="hermes_score_blocked",
            reason=BLOCKED_MISSING_TENANT,
            detail={"action": "score_unscored_leads"},
        )

    org_uuid = org_uuid_or_none(organization_id)
    if org_uuid is None:
        return log_autonomous_blocked(
            actor=ACTOR,
            action_type="hermes_score_blocked",
            reason=BLOCKED_MISSING_TENANT,
            detail={"action": "score_unscored_leads", "invalid_org": True},
        )

    limit = int(params.get("limit", 50))
    contacts = (
        db.query(Contact)
        .filter(Contact.organization_id == org_uuid)
        .filter((Contact.lead_score == None) | (Contact.lead_score == 0))  # noqa: E711
        .limit(limit)
        .all()
    )
    scored = 0
    skipped = 0
    for contact in contacts:
        if not assert_contact_org(contact, organization_id):
            continue

        def _exec(work, c=contact):  # noqa: ANN001
            payload = score_contact(db, c)
            log_agent_action(
                actor=ACTOR,
                action_type="lead_scored",
                target_type="contact",
                target_id=str(c.id),
                organization_id=organization_id,
                detail={"source": "hermes", "work_id": work.work_id, "score": payload["score"]},
            )
            return {"score": payload["score"]}

        work = orchestrate_claimed(
            db,
            work_kind=WORK_LEAD_SCORE,
            organization_id=organization_id,
            source="hermes",
            actor=ACTOR,
            executor=_exec,
            target_type="contact",
            target_id=str(contact.id),
            logical_key="unscored",
        )
        if work.state == WorkState.SUCCEEDED and not (work.result or {}).get("deduplicated"):
            scored += 1
        elif work.state == WorkState.CANCELLED:
            skipped += 1
        elif work.state != WorkState.SUCCEEDED:
            skipped += 1
    db.commit()
    return {
        "ok": True,
        "scored": scored,
        "skipped": skipped,
        "organization_id": organization_id,
        "orchestrated": True,
        "acp4_claimed": True,
    }


def action_qualify_high_scorers(db: Session, params: dict) -> dict[str, Any]:
    """Identify high-scoring leads/prospects eligible for human qualification.

    SALES A4: does not mutate Contact.status — human gate required via CRM API.
    ACP-1: org-scoped read/recommend only.
    """
    organization_id = require_organization_id(params)
    if organization_id is None:
        return log_autonomous_blocked(
            actor=ACTOR,
            action_type="hermes_qualify_blocked",
            reason=BLOCKED_MISSING_TENANT,
            detail={"action": "qualify_high_scorers"},
        )

    org_uuid = org_uuid_or_none(organization_id)
    if org_uuid is None:
        return log_autonomous_blocked(
            actor=ACTOR,
            action_type="hermes_qualify_blocked",
            reason=BLOCKED_MISSING_TENANT,
            detail={"action": "qualify_high_scorers", "invalid_org": True},
        )

    threshold = int(params.get("threshold", QUALIFY_SCORE_THRESHOLD))
    candidates = (
        db.query(Contact)
        .filter(Contact.organization_id == org_uuid)
        .filter(
            Contact.lead_score >= threshold,
            Contact.status.in_([ContactStatus.LEAD, ContactStatus.PROSPECT]),
        )
        .limit(int(params.get("limit", 25)))
        .all()
    )
    eligible = [
        {
            "id": str(contact.id),
            "name": f"{contact.first_name} {contact.last_name}".strip(),
            "email": contact.email,
            "lead_score": contact.lead_score,
            "status": contact.status.value,
            "suggested_status": ContactStatus.QUALIFIED.value,
        }
        for contact in candidates
        if assert_contact_org(contact, organization_id)
    ]

    log_agent_action(
        actor=ACTOR,
        action_type="qualify_high_scorers_recommendation",
        target_type="contact_batch",
        organization_id=organization_id,
        detail={
            "threshold": threshold,
            "eligible_count": len(eligible),
            "status_mutated": False,
        },
    )

    return {
        "ok": True,
        "eligible": eligible,
        "qualified": 0,
        "status_mutated": False,
        "organization_id": organization_id,
    }


def action_create_deals_for_qualified(db: Session, params: dict) -> dict[str, Any]:
    """ACP-1/ACP-2: Hermes autonomous Deal creation is PROHIBITED.

    Routes through ACP-2 orchestration so planner output cannot grant authority.
    Preserves ACP-1 blocked provenance action_type for freeze compatibility.
    """
    from revenue_os.services.acp2_orchestration import orchestrate
    from revenue_os.services.acp2_work_contract import WORK_HERMES_DEAL_CREATE

    organization_id = require_organization_id(params)

    def _never(_work):  # noqa: ANN001
        raise RuntimeError("hermes_deal_create_executor_must_not_run")

    work = orchestrate(
        db,
        work_kind=WORK_HERMES_DEAL_CREATE,
        organization_id=organization_id,
        source="hermes",
        actor=ACTOR,
        executor=_never,
        target_type="deal_batch",
        logical_key="qualified",
    )
    # ACP-1 freeze-compatible provenance (in addition to acp2_work_blocked)
    log_autonomous_blocked(
        actor=ACTOR,
        action_type="hermes_deal_create_blocked",
        reason=work.failure_reason or BLOCKED_HERMES_DEAL,
        organization_id=organization_id,
        detail={
            "action": "create_deals_for_qualified",
            "deals_created": 0,
            "work_id": work.work_id,
            "note": "Hermes may not create Deals under ACP-1/ACP-2",
        },
    )
    return {
        "ok": False,
        "blocked": True,
        "blocked_reason": work.failure_reason or BLOCKED_HERMES_DEAL,
        "deals_created": 0,
        "work": work.to_dict(),
    }


def action_check_deals_at_risk(db: Session, params: dict) -> dict[str, Any]:
    """Surface at-risk deals — org-scoped via ACP-4 claimed WorkItems."""
    from datetime import datetime, timezone

    from revenue_os.automation.events import emit_deal_at_risk
    from revenue_os.services.acp2_work_contract import WORK_DEAL_AT_RISK, WorkState
    from revenue_os.services.acp4_production_runtime import orchestrate_claimed
    from revenue_os.services.deal_automation_service import get_deals_at_risk

    organization_id = require_organization_id(params)
    if organization_id is None:
        return log_autonomous_blocked(
            actor=ACTOR,
            action_type="hermes_deal_risk_blocked",
            reason=BLOCKED_MISSING_TENANT,
            detail={"action": "check_deals_at_risk"},
        )

    day_key = datetime.now(timezone.utc).strftime("%Y%m%d")
    at_risk = get_deals_at_risk(db, organization_id=organization_id)
    flagged = 0
    skipped = 0
    for deal in at_risk:
        deal_id = str(deal.get("deal_id") or deal.get("id") or "")

        def _exec(work, d=deal, did=deal_id, oid=organization_id):  # noqa: ANN001
            try:
                emit_deal_at_risk(
                    deal_id=did,
                    risk_score=int(d.get("risk_score", 0)),
                    days_overdue=int(d.get("days_overdue", 0)),
                )
            except Exception:
                pass
            log_agent_action(
                actor=ACTOR,
                action_type="deal_at_risk_flagged",
                target_type="deal",
                target_id=did,
                organization_id=oid,
                detail={**d, "work_id": work.work_id, "source": "hermes"},
            )
            return {"ok": True, "deal_id": did}

        work = orchestrate_claimed(
            db,
            work_kind=WORK_DEAL_AT_RISK,
            organization_id=organization_id,
            source="hermes",
            actor=ACTOR,
            executor=_exec,
            target_type="deal",
            target_id=deal_id,
            logical_key=day_key,
        )
        if work.state == WorkState.SUCCEEDED and not (work.result or {}).get("deduplicated"):
            flagged += 1
        else:
            skipped += 1
    return {
        "ok": True,
        "deals_at_risk": flagged,
        "skipped": skipped,
        "organization_id": organization_id,
        "orchestrated": True,
        "acp4_claimed": True,
    }


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


def run_goal_check(
    goal_id: str, *, organization_id: str | None = None
) -> dict[str, Any]:
    """One Hermes cycle for a goal: execute due steps, measure, adapt status.

    Autonomous callers must supply organization_id (ACP-1).
    """
    db = SessionLocal()
    try:
        goal = db.get(Goal, goal_id)
        if goal is None:
            raise ValueError(f"Goal not found: {goal_id}")
        if goal.status not in ("active",):
            return {"goal_id": goal_id, "status": goal.status, "skipped": True}

        if organization_id is None:
            blocked = log_autonomous_blocked(
                actor=ACTOR,
                action_type="hermes_goal_blocked",
                reason=BLOCKED_MISSING_TENANT,
                target_type="goal",
                target_id=goal_id,
                detail={"title": goal.title},
            )
            return {**blocked, "goal_id": goal_id, "steps_executed": []}

        executed: list[dict[str, Any]] = []
        for step in _get_steps(db, goal_id):
            due = step.status == "pending" or (step.repeat and step.status != "failed")
            if not due:
                continue
            if not hermes_action_allowed(step.action_type):
                result = action_create_deals_for_qualified(
                    db, {**(step.params or {}), "organization_id": organization_id}
                )
                step.status = "blocked"
                step.result = result
                executed.append({"step": step.title, **result})
                step.runs += 1
                step.executed_at = datetime.now(timezone.utc)
                continue
            action = ACTION_REGISTRY.get(step.action_type)
            if action is None:
                step.status = "skipped"
                step.result = {"error": f"unknown action {step.action_type}"}
                continue
            try:
                params = dict(step.params or {})
                params["organization_id"] = organization_id
                result = action(db, params)
                step.status = (
                    "completed"
                    if result.get("ok", True) and not result.get("blocked")
                    else "blocked"
                )
                step.result = result
                executed.append({"step": step.title, **result})
            except Exception as e:
                step.status = "failed"
                step.result = {"error": str(e)}
                executed.append({"step": step.title, "error": str(e)})
                logger.error(f"Hermes step failed ({step.title}): {e}")
            step.runs += 1
            step.executed_at = datetime.now(timezone.utc)

        goal.current_value = measure_metric(
            db, goal.metric, organization_id=organization_id
        )
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
            "organization_id": organization_id,
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
        target_type="goal",
        target_id=goal_id,
        organization_id=organization_id,
        detail=summary,
    )
    return summary


def check_all_active_goals(
    *, organization_ids: list[str] | None = None
) -> dict[str, Any]:
    """Heartbeat entrypoint: run one cycle per active goal per authorized org."""
    if not organization_ids:
        return log_autonomous_blocked(
            actor=ACTOR,
            action_type="hermes_goal_blocked",
            reason=BLOCKED_MISSING_TENANT,
            detail={"note": "check_all_active_goals requires explicit organization_ids"},
        )

    db = SessionLocal()
    try:
        goal_ids = [g.id for g in db.query(Goal).filter(Goal.status == "active").all()]
    finally:
        db.close()

    results: list[dict[str, Any]] = []
    for organization_id in organization_ids:
        for goal_id in goal_ids:
            results.append(
                run_goal_check(goal_id, organization_id=organization_id)
            )
    return {
        "ok": True,
        "goals_checked": len(results),
        "organizations": list(organization_ids),
        "achieved": sum(1 for r in results if r.get("status") == "achieved"),
        "blocked": sum(1 for r in results if r.get("blocked")),
    }
