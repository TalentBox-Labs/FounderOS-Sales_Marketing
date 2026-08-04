"""Founder Copilot — one chat interface that reads and runs the platform.

Deterministic intent router: each intent maps a natural-language pattern to
the same services the API uses, so answers are live data and commands really
execute (and land in the audit trail as actor="copilot"). An LLM layer can
slot in front later — same handlers, same response contract.

Response contract:
    {"reply": str, "items": [{"title", "subtitle", "link"?}], "action": str|None}
"""

from __future__ import annotations

import logging
import re
from typing import Any, Callable

from revenue_os.database import SessionLocal
from revenue_os.services.activity_log import log_agent_action

logger = logging.getLogger(__name__)

ACTOR = "copilot"


def _resp(reply: str, items: list[dict] | None = None, action: str | None = None) -> dict[str, Any]:
    return {"reply": reply, "items": items or [], "action": action}


# ── Intent handlers ──────────────────────────────────────────────────────────


def _handle_followups(message: str) -> dict[str, Any]:
    """Overdue tasks + deals at risk + stalled contacts + pending approvals."""
    from revenue_os.services.followups import get_followups

    f = get_followups()
    items: list[dict] = []

    for t in f["overdue_tasks"][:5]:
        link = f"/deals/{t['deal_id']}" if t.get("deal_id") else f"/contacts/{t['contact_id']}"
        items.append({
            "title": f"Overdue task: {t['subject']}",
            "subtitle": f"was due {t['due_date']}",
            "link": link,
        })
    for d in f["at_risk_deals"][:5]:
        items.append({
            "title": f"Deal at risk: {d.get('name', d.get('deal_id', '?'))}",
            "subtitle": f"risk {d.get('risk_score', '?')} · {d.get('days_overdue', 0)} days overdue",
            "link": f"/deals/{d['deal_id']}",
        })
    for c in f["stalled_contacts"][:5]:
        items.append({
            "title": f"Qualified, no deal yet: {c['name']}",
            "subtitle": f"score {c['lead_score']} · quiet {c['days_stale']} days",
            "link": f"/contacts/{c['id']}",
        })
    for r in f["pending_approvals"][:5]:
        items.append({
            "title": f"Awaiting your approval: {r['title']}",
            "subtitle": f"proposed by {r['requested_by']}",
            "link": "/approvals",
        })

    if not items:
        return _resp("Nothing needs follow-up right now — pipeline is clean and the approvals inbox is empty.")
    return _resp(f"{len(items)} things need attention:", items)


def _handle_priorities(message: str) -> dict[str, Any]:
    """Morning-brief style summary across the platform."""
    from revenue_os.models.goals import Goal
    from revenue_os.services.deal_automation_service import get_pipeline_health
    from revenue_os.services.followups import get_followups

    db = SessionLocal()
    try:
        health = get_pipeline_health(db)
        goals = db.query(Goal).filter(Goal.status == "active").all()
        goal_items = [{
            "title": g.title,
            "subtitle": f"{g.current_value:g} / {g.target_value:g} ({round(g.progress() * 100)}%)",
            "link": "/goals",
        } for g in goals]
    finally:
        db.close()

    f = get_followups()
    pending = len(f["pending_approvals"])
    at_risk = len(f["at_risk_deals"])
    overdue = len(f["overdue_tasks"])

    from revenue_os.agents.orchestration import AgentCoordinator

    handoffs = AgentCoordinator.get_messages("copilot", unread_only=True)

    items = []
    if overdue:
        items.append({"title": f"{overdue} task(s) overdue", "subtitle": "Clear these first", "link": "/copilot"})
    if pending:
        items.append({"title": f"{pending} approval(s) waiting for you", "subtitle": "Approve or reject proposed actions", "link": "/approvals"})
    if at_risk:
        items.append({"title": f"{at_risk} deal(s) flagged at risk", "subtitle": "Review before they slip", "link": "/deals"})
    for h in handoffs[:3]:
        items.append({"title": h["message"], "subtitle": f"from {h['from']}", "link": "/agents"})
    items.extend(goal_items)

    reply = (
        f"Today: pipeline ${health.get('total_pipeline_value', 0):,.0f} across "
        f"{health.get('total_deals', 0)} open deals "
        f"(weighted forecast ${health.get('weighted_forecast', 0):,.0f}). "
        f"{overdue} tasks overdue, {pending} approvals pending, {at_risk} deals at risk, "
        f"{len(goal_items)} active goal(s)"
        + (f", {len(handoffs)} update(s) from other agents." if handoffs else ".")
    )
    return _resp(reply, items)


def _handle_pipeline(message: str) -> dict[str, Any]:
    from revenue_os.services.deal_automation_service import get_pipeline_health

    db = SessionLocal()
    try:
        health = get_pipeline_health(db)
    finally:
        db.close()
    items = [
        {"title": stage.replace("_", " ").title(),
         "subtitle": f"{m.get('count', 0)} deals · ${m.get('value', 0):,.0f}"}
        for stage, m in (health.get("by_stage") or {}).items()
    ]
    return _resp(
        f"Pipeline: ${health.get('total_pipeline_value', 0):,.0f} across "
        f"{health.get('total_deals', 0)} open deals. Weighted forecast "
        f"${health.get('weighted_forecast', 0):,.0f}.",
        items,
    )


def _handle_contacts(message: str) -> dict[str, Any]:
    from revenue_os.models.contact import Contact

    db = SessionLocal()
    try:
        contacts = (
            db.query(Contact)
            .order_by(Contact.lead_score.desc().nullslast()
                      if hasattr(Contact.lead_score, "desc") else Contact.lead_score)
            .limit(8).all()
        )
        items = [{
            "title": f"{c.first_name} {c.last_name}".strip(),
            "subtitle": f"{c.status.value if c.status else '?'} · score {c.lead_score or 0} · {c.email}",
            "link": "/contacts",
        } for c in contacts]
        total = db.query(Contact).count()
    finally:
        db.close()
    return _resp(f"{total} contacts. Top by lead score:", items)


def _handle_goals(message: str) -> dict[str, Any]:
    # "create goal 20 qualified leads" / "set a goal: 500k pipeline"
    create = None
    if re.search(r"create|new|set|add", message, re.I):
        create = re.search(
            r"([\d][\d,\.]*)\s*k?\s*(qualified|lead|pipeline|deal|close)", message, re.I,
        )

    if create:
        from revenue_os.services.hermes_planner import create_goal

        raw_num, kind = create.groups()
        target = float(raw_num.replace(",", ""))
        if re.search(rf"{re.escape(raw_num)}\s*k", message, re.I):
            target *= 1000
        metric = ("pipeline_value" if "pipeline" in kind.lower()
                  else "deals_closed" if "close" in kind.lower()
                  else "qualified_leads")
        goal = create_goal(
            title=f"Copilot goal: {target:g} {metric.replace('_', ' ')}",
            metric=metric, target_value=target,
            description=f'Created from Copilot: "{message}"',
        )
        return _resp(
            f"Goal created — Hermes snapshotted a baseline of {goal['baseline_value']:g} "
            f"and generated a {len(goal['plan'])}-step plan. It runs on every heartbeat.",
            [{"title": goal["title"], "subtitle": f"target {goal['target_value']:g}", "link": "/goals"}],
            action="goal_created",
        )

    from revenue_os.models.goals import Goal

    db = SessionLocal()
    try:
        goals = db.query(Goal).order_by(Goal.created_at.desc()).limit(8).all()
        items = [{
            "title": g.title,
            "subtitle": f"{g.status} · {g.current_value:g}/{g.target_value:g} ({round(g.progress() * 100)}%)",
            "link": "/goals",
        } for g in goals]
    finally:
        db.close()
    if not items:
        return _resp('No goals yet. Try: "create a goal: 20 qualified leads".')
    return _resp(f"{len(items)} goal(s):", items)


def _handle_run_scoring(message: str) -> dict[str, Any]:
    from revenue_os.scheduler import scheduler

    result = scheduler.run_job_now("score_new_leads")
    r = result.get("result") or {}
    return _resp(
        f"Lead scoring ran: {r.get('contacts_scored', 0)} contact(s) scored "
        f"out of {r.get('contacts_considered', 0)} considered.",
        action="job_executed",
    )


def _handle_run_goal_check(message: str) -> dict[str, Any]:
    from revenue_os.scheduler import scheduler

    result = scheduler.run_job_now("hermes_goal_check")
    r = result.get("result") or {}
    return _resp(
        f"Hermes cycle complete: {r.get('goals_checked', 0)} goal(s) checked, "
        f"{r.get('achieved', 0)} achieved. Any proposed outreach is in Approvals.",
        action="job_executed",
    )


def _handle_approvals(message: str) -> dict[str, Any]:
    from revenue_os.services.approvals import list_requests

    pending = list_requests(status="pending", limit=8)
    if not pending:
        return _resp("Approvals inbox is empty — nothing is waiting on you.")
    items = [{
        "title": r["title"],
        "subtitle": f"by {r['requested_by']} · {r['action_type']}",
        "link": "/approvals",
    } for r in pending]
    return _resp(f"{len(pending)} approval(s) pending — decide on the Approvals page:", items)


def _handle_help(message: str) -> dict[str, Any]:
    return _resp(
        "I can read and run the platform. Try:",
        [
            {"title": "What needs follow-up?", "subtitle": "at-risk deals, stalled contacts, pending approvals"},
            {"title": "Show today's priorities", "subtitle": "pipeline, approvals, goals — one brief"},
            {"title": "Show the pipeline", "subtitle": "value and deals by stage"},
            {"title": "Show contacts / goals / approvals", "subtitle": "live lists"},
            {"title": "Create a goal: 20 qualified leads", "subtitle": "Hermes plans and executes it"},
            {"title": "Run lead scoring", "subtitle": "score new contacts now"},
            {"title": "Run a goal check", "subtitle": "one Hermes cycle across active goals"},
            {"title": "Anything else — e.g. \"how do I handle a stuck deal?\"", "subtitle": "answered from your knowledge base"},
        ],
    )


# Ordered: first matching pattern wins.
INTENTS: list[tuple[str, Callable[[str], dict[str, Any]]]] = [
    (r"follow[\s-]?up|need.*attention|what.*next", _handle_followups),
    (r"priorit|today|morning|brief|summary|standup", _handle_priorities),
    (r"create|new goal|set.*goal|add.*goal", _handle_goals),
    (r"pipeline|revenue|forecast", _handle_pipeline),
    (r"run.*scor|score.*lead|scoring", _handle_run_scoring),
    (r"goal check|check.*goal|run.*hermes|hermes", _handle_run_goal_check),
    (r"approv", _handle_approvals),
    (r"goal", _handle_goals),
    (r"contact|lead(?!.*scor)", _handle_contacts),
    (r"deal", _handle_pipeline),
    (r"help|what can you", _handle_help),
]


def chat(message: str) -> dict[str, Any]:
    """Route one founder message to an intent handler. Never raises."""
    text = (message or "").strip()
    if not text:
        return _handle_help("")

    for pattern, handler in INTENTS:
        if re.search(pattern, text, re.I):
            try:
                result = handler(text)
            except Exception as e:
                logger.error(f"Copilot handler failed ({handler.__name__}): {e}")
                result = _resp(f"That hit an error ({e}). The audit trail has details.")
            log_agent_action(
                actor=ACTOR, action_type="chat",
                status="completed" if not result["reply"].startswith("That hit an error") else "failed",
                detail={"message": text[:200], "intent": handler.__name__,
                        "action": result.get("action")},
            )
            return result

    # No pattern matched — try the knowledge base + CRM before giving up.
    # This is retrieval-augmented, not a guess: it only answers from what
    # search_service actually finds, and always shows its sources.
    try:
        from revenue_os.services.rag_service import answer_question

        rag = answer_question(text, limit=4)
    except Exception as e:
        logger.error(f"Copilot RAG fallback failed: {e}")
        rag = {"answer": "", "sources": []}

    if rag.get("sources"):
        log_agent_action(actor=ACTOR, action_type="chat",
                         detail={"message": text[:200], "intent": "rag_answer"})
        items = [{
            "title": s["title"], "subtitle": f"{s['type']} · {s['snippet'][:80]}",
        } for s in rag["sources"]]
        return _resp(rag["answer"], items, action="rag_answer")

    log_agent_action(actor=ACTOR, action_type="chat",
                     detail={"message": text[:200], "intent": "unmatched"})
    fallback = _handle_help(text)
    fallback["reply"] = "I didn't recognize that yet. " + fallback["reply"]
    return fallback
