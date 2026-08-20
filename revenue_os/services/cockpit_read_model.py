"""Executive Cockpit read-model composition — authoritative sources only.

UI2: server-side aggregation for Jinja cockpit panels. No new SoT.
"""

from __future__ import annotations

import logging
import uuid as uuid_lib
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from revenue_os.database import SessionLocal
from revenue_os.models.automation_state import AgentActionLog
from revenue_os.models.contact import Contact, ContactStatus
from revenue_os.models.deal import Deal, DealStage
from revenue_os.scheduler import heartbeat_enabled, scheduler
from revenue_os.services.qualified_demand_service import (
    ACTION_ACCEPTED,
    ACTION_HANDOFF,
    ACTION_REJECTED,
)
from runner_api_routers.editorial import build_editorial_pending
from src.tools import publishing_engine as pe

logger = logging.getLogger(__name__)

PanelState = str  # ok | empty | error | unavailable | blocked


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _panel(
    state: PanelState,
    *,
    data: dict[str, Any] | None = None,
    message: str = "",
) -> dict[str, Any]:
    return {"state": state, "message": message, "data": data or {}}


def _org_uuid(organization_id: str | None) -> uuid_lib.UUID | None:
    if organization_id is None:
        return None
    try:
        return uuid_lib.UUID(str(organization_id))
    except ValueError:
        return None


def _load_pending_qualified_demands(
    db, *, organization_id: str | None = None
) -> list[dict[str, Any]]:  # noqa: ANN001
    org_uuid = _org_uuid(organization_id)
    if org_uuid is None:
        return []
    handoff_q = (
        db.query(AgentActionLog)
        .filter(
            AgentActionLog.action_type == ACTION_HANDOFF,
            AgentActionLog.organization_id == org_uuid,
        )
        .order_by(AgentActionLog.created_at.desc())
    )
    handoffs = handoff_q.all()
    accepted = {
        row.target_id
        for row in db.query(AgentActionLog)
        .filter(
            AgentActionLog.action_type == ACTION_ACCEPTED,
            AgentActionLog.organization_id == org_uuid,
        )
        .all()
        if row.target_id
    }
    rejected = {
        row.target_id
        for row in db.query(AgentActionLog)
        .filter(
            AgentActionLog.action_type == ACTION_REJECTED,
            AgentActionLog.organization_id == org_uuid,
        )
        .all()
        if row.target_id
    }
    pending: list[dict[str, Any]] = []
    for row in handoffs:
        demand_id = row.target_id or ""
        if not demand_id or demand_id in accepted or demand_id in rejected:
            continue
        payload = (row.detail or {}).get("payload") or {}
        person = payload.get("person") or {}
        pending.append(
            {
                "demand_id": demand_id,
                "source": payload.get("source"),
                "email": person.get("email"),
                "name": person.get("name"),
                "occurred_at": payload.get("occurred_at"),
                "requested_by": (row.detail or {}).get("requested_by"),
                "registered_at": row.created_at.isoformat() if row.created_at else None,
            }
        )
    return pending


def _load_sales_snapshot(
    db, *, organization_id: str | None = None
) -> dict[str, Any]:  # noqa: ANN001
    org_uuid = _org_uuid(organization_id)
    contact_q = db.query(Contact)
    deal_q = db.query(Deal)
    if org_uuid is not None:
        contact_q = contact_q.filter(Contact.organization_id == org_uuid)
        deal_q = deal_q.filter(Deal.organization_id == org_uuid)
    contacts = contact_q.all()
    deals = deal_q.all()
    by_status: dict[str, int] = {}
    for c in contacts:
        key = c.status.value if c.status else "unknown"
        by_status[key] = by_status.get(key, 0) + 1
    by_stage: dict[str, int] = {}
    for d in deals:
        key = d.stage.value if d.stage else "unknown"
        by_stage[key] = by_stage.get(key, 0) + 1
    high_score_review = [
        {
            "id": str(c.id),
            "name": f"{c.first_name} {c.last_name}".strip(),
            "email": c.email,
            "status": c.status.value if c.status else None,
            "lead_score": c.lead_score or 0,
        }
        for c in contacts
        if (c.lead_score or 0) >= 70
        and c.status not in (ContactStatus.QUALIFIED, ContactStatus.CUSTOMER)
    ]
    high_score_review.sort(key=lambda x: x["lead_score"], reverse=True)
    return {
        "contact_total": len(contacts),
        "contacts_by_status": by_status,
        "deal_total": len(deals),
        "deals_by_stage": by_stage,
        "high_score_review": high_score_review[:10],
    }


def build_cockpit_snapshot(*, organization_id: str | None = None) -> dict[str, Any]:
    """Compose cockpit panels from authoritative repository sources."""
    snapshot: dict[str, Any] = {
        "ok": True,
        "generated_at": _utc_now(),
        "panels": {},
        "errors": [],
    }

    # --- Attention / Decision Queue ---
    attention_items: list[dict[str, Any]] = []
    attention_state: PanelState = "ok"
    attention_message = ""
    pending_demand_count = 0

    try:
        db = SessionLocal()
        try:
            pending_demands = _load_pending_qualified_demands(
                db, organization_id=organization_id
            )
            pending_demand_count = len(pending_demands)
            for item in pending_demands:
                attention_items.append(
                    {
                        "kind": "qualified_demand",
                        "priority": "high",
                        "label": f"QualifiedDemand {item['demand_id'][:8]}…",
                        "detail": item.get("email") or item.get("name") or "—",
                        "meta": item,
                    }
                )
            sales_data = _load_sales_snapshot(db, organization_id=organization_id)
            for contact in sales_data.get("high_score_review") or []:
                attention_items.append(
                    {
                        "kind": "contact_qualification",
                        "priority": "medium",
                        "label": contact.get("name") or contact.get("email") or "Contact",
                        "detail": f"Score {contact.get('lead_score')} · status {contact.get('status')}",
                        "meta": contact,
                    }
                )
        finally:
            db.close()
    except SQLAlchemyError as exc:
        logger.warning("Cockpit attention queue DB unavailable: %s", exc)
        attention_state = "unavailable"
        attention_message = "Sales database unavailable — queue cannot be loaded"
        snapshot["errors"].append("attention_db")

    try:
        editorial = build_editorial_pending()
        if editorial.get("ok"):
            editorial_items = list(editorial.get("items") or [])
            if editorial_items:
                attention_items.append(
                    {
                        "kind": "editorial",
                        "priority": "medium",
                        "label": f"{len(editorial_items)} editorial item(s) pending",
                        "detail": "Human approval required",
                        "meta": {"count": len(editorial_items), "link": "/editorial"},
                    }
                )
        else:
            attention_items.append(
                {
                    "kind": "editorial",
                    "priority": "low",
                    "label": "Editorial pending unavailable",
                    "detail": "API returned not ok",
                    "meta": {"link": "/editorial"},
                }
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cockpit editorial pending failed: %s", exc)
        snapshot["errors"].append("editorial_pending")

    try:
        pub_queue = pe.list_queue(include_terminal=False)
        pending_pub = [j for j in pub_queue if j.get("state") == pe.STATE_PUBLISH_PENDING]
        if pending_pub:
            attention_items.append(
                {
                    "kind": "publishing",
                    "priority": "medium",
                    "label": f"{len(pending_pub)} publish job(s) pending",
                    "detail": "Human promote required",
                    "meta": {"count": len(pending_pub), "link": "/publishing"},
                }
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cockpit publishing queue failed: %s", exc)
        snapshot["errors"].append("publishing_queue")

    if attention_state == "ok" and not attention_items:
        attention_state = "empty"
        attention_message = "No items requiring founder attention"

    snapshot["panels"]["attention"] = _panel(
        attention_state,
        data={"items": attention_items, "count": len(attention_items)},
        message=attention_message,
    )

    # --- Sales Snapshot ---
    try:
        db = SessionLocal()
        try:
            sales = _load_sales_snapshot(db, organization_id=organization_id)
            snapshot["panels"]["sales"] = _panel("ok", data=sales)
        finally:
            db.close()
    except SQLAlchemyError as exc:
        logger.warning("Cockpit sales snapshot DB unavailable: %s", exc)
        snapshot["panels"]["sales"] = _panel(
            "unavailable",
            message="Sales database unavailable — counts not shown",
        )
        snapshot["errors"].append("sales_db")

    # --- Marketing / SEO Snapshot ---
    marketing_seo: dict[str, Any] = {}
    seo_state: PanelState = "ok"
    seo_message = ""
    try:
        from src.tools.seo_engine import analyze_site, analyze_technical_site

        readiness = analyze_site().to_dict()
        technical = analyze_technical_site().to_dict()
        marketing_seo["readiness"] = {
            "pages_scanned": readiness.get("pages_scanned"),
            "ready_count": readiness.get("ready_count"),
            "blocked_count": readiness.get("blocked_count"),
            "production_seo_activation": "BLOCKED",
        }
        marketing_seo["technical"] = {
            "score": technical.get("score"),
            "pass_count": technical.get("pass_count"),
            "warn_count": technical.get("warn_count"),
            "fail_count": technical.get("fail_count"),
            "production_seo_activation": "BLOCKED",
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cockpit SEO snapshot failed: %s", exc)
        seo_state = "error"
        seo_message = str(exc) or "SEO readiness unavailable"
        snapshot["errors"].append("seo")

    marketing_seo["social"] = {
        "state": "blocked",
        "message": "Social live publishing not active (FD-01 / external gates)",
    }
    marketing_seo["qualified_demand_pending"] = pending_demand_count
    snapshot["panels"]["marketing_seo"] = _panel(
        seo_state, data=marketing_seo, message=seo_message
    )

    # --- Commercial Flow ---
    sales_panel = snapshot["panels"].get("sales", {})
    sales_data = sales_panel.get("data") or {}
    flow_stages = [
        {
            "label": "Marketing QualifiedDemand",
            "state": "active" if pending_demand_count else "idle",
            "detail": "MC04.5 handoff register → Sales intake",
        },
        {
            "label": "Sales Contact (LEAD)",
            "state": "active" if sales_data.get("contact_total") else "idle",
            "detail": f"{sales_data.get('contact_total', '—')} contacts in CRM SoT",
        },
        {
            "label": "Deal Pipeline",
            "state": "active" if sales_data.get("deal_total") else "idle",
            "detail": f"{sales_data.get('deal_total', '—')} deals tracked",
        },
        {
            "label": "Revenue Outcome",
            "state": "emerging",
            "detail": "NOT YET ACTIVE — CommercialOutcome → Revenue intake not implemented",
        },
    ]
    snapshot["panels"]["commercial_flow"] = _panel("ok", data={"stages": flow_stages})

    # --- Governance / System Health ---
    hb_status = scheduler.status()
    governance = {
        "authority_remediation": "PASS",
        "ui1_1_bypasses_closed": "3/3",
        "frozen_baselines": [
            "Sales A1.5",
            "Sales A3.5",
            "Sales A4.5",
            "MC04.5",
            "SEO S1.5",
        ],
        "known_test_exceptions": [
            "test_prospecting_ui (PostgreSQL ENVIRONMENT_DEPENDENCY)",
        ],
        "heartbeat": {
            "enabled": heartbeat_enabled(),
            "jobs_registered": len(hb_status.get("jobs") or []),
            "last_runs": hb_status.get("last_runs") or {},
        },
        "integration_readiness": {
            "crm_spa": "UNMOUNTED",
            "social_live": "BLOCKED",
            "production_seo": "BLOCKED",
        },
    }
    snapshot["panels"]["governance"] = _panel("ok", data=governance)

    if snapshot["errors"]:
        snapshot["ok"] = len(snapshot["errors"]) < 3

    return snapshot
