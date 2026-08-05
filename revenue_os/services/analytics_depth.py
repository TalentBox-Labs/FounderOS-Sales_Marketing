"""Attribution, LTV, CAC, and agent-productivity analytics.

Every number here comes from data the platform actually has — Contact.source
for attribution, closed-won Deal.value for LTV, logged MarketingSpendRecord
for CAC (never fabricated — a channel with no logged spend reports CAC as
unavailable, not zero or guessed), and AgentActionLog/Goal/ApprovalRequest
for agent productivity (see the M5 agent registry).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session


def compute_attribution(db: Session) -> list[dict[str, Any]]:
    """Contacts, qualify rate, and closed-won revenue per acquisition source."""
    from revenue_os.models.contact import Contact, ContactStatus
    from revenue_os.models.deal import Deal, DealStage

    contacts = db.query(Contact).all()
    by_source: dict[str, dict[str, Any]] = {}

    def _row(key: str) -> dict[str, Any]:
        return by_source.setdefault(key, {
            "source": key, "contacts": 0, "qualified": 0, "won_deals": 0, "won_value": 0.0,
        })

    for c in contacts:
        key = c.source.value if c.source else "unknown"
        row = _row(key)
        row["contacts"] += 1
        if c.status in (ContactStatus.QUALIFIED, ContactStatus.CUSTOMER):
            row["qualified"] += 1

    contact_source = {c.id: (c.source.value if c.source else "unknown") for c in contacts}
    won_deals = db.query(Deal).filter(Deal.stage == DealStage.CLOSED_WON).all()
    for d in won_deals:
        key = contact_source.get(d.contact_id, "unknown")
        row = _row(key)
        row["won_deals"] += 1
        row["won_value"] += d.value or 0.0

    for row in by_source.values():
        row["qualify_rate"] = round(row["qualified"] / row["contacts"], 3) if row["contacts"] else 0.0

    return sorted(by_source.values(), key=lambda r: r["won_value"], reverse=True)


def compute_ltv(db: Session, top_n: int = 10) -> dict[str, Any]:
    """Average and top customer lifetime value from closed-won deals."""
    from revenue_os.models.contact import Contact
    from revenue_os.models.deal import Deal, DealStage

    won_deals = (
        db.query(Deal)
        .filter(Deal.stage == DealStage.CLOSED_WON, Deal.contact_id.isnot(None))
        .all()
    )
    by_contact: dict[Any, dict[str, Any]] = {}
    for d in won_deals:
        agg = by_contact.setdefault(d.contact_id, {"deals": 0, "value": 0.0})
        agg["deals"] += 1
        agg["value"] += d.value or 0.0

    if not by_contact:
        return {"avg_ltv": None, "customers_with_revenue": 0, "top_customers": []}

    contacts = {c.id: c for c in db.query(Contact).filter(Contact.id.in_(by_contact.keys())).all()}
    ranked = sorted(by_contact.items(), key=lambda kv: kv[1]["value"], reverse=True)
    top = []
    for contact_id, agg in ranked[:top_n]:
        c = contacts.get(contact_id)
        top.append({
            "contact_id": str(contact_id),
            "name": f"{c.first_name} {c.last_name}".strip() if c else "Unknown",
            "deals": agg["deals"],
            "total_value": round(agg["value"], 2),
        })

    avg = sum(v["value"] for v in by_contact.values()) / len(by_contact)
    return {"avg_ltv": round(avg, 2), "customers_with_revenue": len(by_contact), "top_customers": top}


def compute_cac(db: Session, period: str | None = None) -> list[dict[str, Any]]:
    """Cost per acquired customer, per channel — only channels with logged spend."""
    from revenue_os.models.analytics_depth import MarketingSpendRecord
    from revenue_os.models.contact import Contact, ContactStatus

    spend_query = db.query(MarketingSpendRecord)
    if period:
        spend_query = spend_query.filter(MarketingSpendRecord.period == period)
    spend_by_channel: dict[str, float] = {}
    for row in spend_query.all():
        spend_by_channel[row.channel] = spend_by_channel.get(row.channel, 0.0) + row.amount

    if not spend_by_channel:
        return []

    acquired_by_channel: dict[str, int] = {}
    for c in db.query(Contact).all():
        if c.status not in (ContactStatus.QUALIFIED, ContactStatus.CUSTOMER):
            continue
        if period and (not c.created_at or c.created_at.strftime("%Y-%m") != period):
            continue
        key = c.source.value if c.source else "unknown"
        acquired_by_channel[key] = acquired_by_channel.get(key, 0) + 1

    results = []
    for channel, spend in spend_by_channel.items():
        acquired = acquired_by_channel.get(channel, 0)
        results.append({
            "channel": channel,
            "period": period,
            "spend": round(spend, 2),
            "customers_acquired": acquired,
            "cac": round(spend / acquired, 2) if acquired else None,
        })
    return sorted(results, key=lambda r: r["spend"], reverse=True)


def compute_agent_productivity(db: Session) -> list[dict[str, Any]]:
    """Actions, goals, and approvals per registered agent (see the M5 registry)."""
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.models.approvals import ApprovalRequest
    from revenue_os.models.automation_state import AgentActionLog
    from revenue_os.models.goals import Goal

    agents = AgentCoordinator.list_agents()
    results = []
    for agent in agents:
        name = agent["name"]

        actions = db.query(AgentActionLog).filter(AgentActionLog.actor == name).all()
        completed = sum(1 for a in actions if a.status == "completed")
        failed = sum(1 for a in actions if a.status == "failed")

        goals = db.query(Goal).filter(Goal.agent_name == name).all()
        goals_achieved = sum(1 for g in goals if g.status == "achieved")

        approvals = db.query(ApprovalRequest).filter(ApprovalRequest.requested_by == name).all()
        approvals_approved = sum(1 for a in approvals if a.status == "approved")
        approvals_rejected = sum(1 for a in approvals if a.status == "rejected")

        results.append({
            "name": name, "type": agent.get("type"),
            "actions_total": len(actions), "actions_completed": completed, "actions_failed": failed,
            "goals_owned": len(goals), "goals_achieved": goals_achieved,
            "approvals_requested": len(approvals),
            "approvals_approved": approvals_approved, "approvals_rejected": approvals_rejected,
        })

    return sorted(results, key=lambda r: r["actions_total"], reverse=True)
