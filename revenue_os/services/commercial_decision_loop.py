"""COS-3 — Founder commercial decision loop composition (no persistence).

Composes existing Command Center / AgentActionLog / ApprovalRequest presentation
state into one Founder-facing decision representation. Does not write CRM entities,
approvals, bookings, or outbound communication.
"""

from __future__ import annotations

from typing import Any

# Authority bands — deterministic, repository-backed (not scored).
AUTHORITY_REQUIRES_FOUNDER = "requires_founder"
AUTHORITY_READY = "ready"
AUTHORITY_COMPLETED = "completed"
AUTHORITY_INFORMATIONAL = "informational"

_BAND_ORDER = {
    AUTHORITY_REQUIRES_FOUNDER: 0,
    AUTHORITY_READY: 1,
    AUTHORITY_COMPLETED: 2,
    AUTHORITY_INFORMATIONAL: 3,
}

_COMPLETED_ACTION_TYPES = frozenset(
    {
        "qualified_demand_accepted",
        "qualified_demand_rejected",
        "commercial_outcome_accepted",
        "commercial_outcome_rejected",
        "approval_approved",
        "approval_rejected",
    }
)


def _item(
    *,
    item_id: str,
    kind: str,
    commercial_source: str,
    decision_type: str,
    title: str,
    reason: str | None,
    person_label: str | None,
    company_label: str | None,
    proposed_action: str | None,
    authority_state: str,
    status: str,
    outcome: str | None,
    provenance: dict[str, Any],
    occurred_at: str | None,
    href: str | None,
) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "kind": kind,
        "commercial_source": commercial_source,
        "decision_type": decision_type,
        "title": title,
        "reason": reason,
        "person_label": person_label,
        "company_label": company_label,
        "proposed_action": proposed_action,
        "authority_state": authority_state,
        "authority_state_label": _authority_label(authority_state),
        "status": status,
        "outcome": outcome,
        "provenance": provenance,
        "occurred_at": occurred_at,
        "href": href,
    }


def _authority_label(state: str) -> str:
    if state == AUTHORITY_REQUIRES_FOUNDER:
        return "Needs your decision"
    if state == AUTHORITY_READY:
        return "Ready — governed action available"
    if state == AUTHORITY_COMPLETED:
        return "Resolved"
    if state == AUTHORITY_INFORMATIONAL:
        return "For awareness"
    return state


def _from_pending_demand(row: dict[str, Any]) -> dict[str, Any]:
    demand_id = str(row.get("demand_id") or "")
    title = str(row.get("name") or row.get("email") or "Qualified demand")
    return _item(
        item_id=f"qualified_demand:{demand_id}",
        kind="qualified_demand",
        commercial_source="marketing",
        decision_type="intake",
        title=title,
        reason=row.get("why_it_matters") or row.get("qualification_reason"),
        person_label=row.get("name") or row.get("email"),
        company_label=row.get("company_hint_name"),
        proposed_action=row.get("what_happens_next")
        or "Accept or reject on People. Accept adds this person; reject records the decision only.",
        authority_state=AUTHORITY_REQUIRES_FOUNDER,
        status=str(row.get("human_decision_state") or "awaiting_intake"),
        outcome=None,
        provenance={
            "evidence_type": "agent_action_log",
            "action_type": "qualified_demand_handoff",
            "authority_class": row.get("authority_class") or "SYSTEM_RECOMMENDED",
            "subject_id": demand_id or None,
        },
        occurred_at=row.get("registered_at") or row.get("occurred_at"),
        href="/demand",
    )


def _from_pending_approval(row: dict[str, Any]) -> dict[str, Any]:
    request_id = str(row.get("id") or row.get("request_id") or "")
    action_type = str(row.get("action_type") or "")
    target_id = row.get("target_id")
    title = str(row.get("title") or row.get("action_label") or "Approval request")
    href = "/pending-approvals"
    if target_id:
        href = f"/contacts/{target_id}"
    return _item(
        item_id=f"approval:{request_id or action_type}:{target_id or 'none'}",
        kind="approval",
        commercial_source="governance",
        decision_type=action_type or "approval",
        title=title,
        reason="An AI or system proposal is waiting. Nothing executes until you approve or reject.",
        person_label=None,
        company_label=None,
        proposed_action=str(
            row.get("action_label") or "Review in Approvals — approve or reject."
        ),
        authority_state=AUTHORITY_REQUIRES_FOUNDER,
        status="pending_approval",
        outcome=None,
        provenance={
            "evidence_type": "approval_request",
            "action_type": action_type or None,
            "authority_class": "HUMAN_DECIDED",
            "subject_id": request_id or None,
            "target_id": str(target_id) if target_id else None,
        },
        occurred_at=row.get("created_at"),
        href=href,
    )


def _from_meeting_interest(row: dict[str, Any]) -> dict[str, Any]:
    contact_id = str(row.get("contact_id") or "")
    eligible = row.get("booking_status") == "eligible" or bool(row.get("booking_eligible"))
    return _item(
        item_id=f"meeting_interest:{contact_id}",
        kind="meeting_interest",
        commercial_source="sales",
        decision_type="booking_eligibility",
        title="Meeting interest detected",
        reason=(
            "This person showed meeting interest. Booking stays proposal-only until you approve."
            if eligible
            else "Meeting interest was recorded. Eligibility is advisory until you act."
        ),
        person_label=None,
        company_label=None,
        proposed_action=(
            "Open the person workspace to review times and submit a governed proposal."
            if eligible
            else "Open the person workspace to review the reply."
        ),
        authority_state=AUTHORITY_READY if eligible else AUTHORITY_INFORMATIONAL,
        status=str(row.get("booking_status") or "interest_detected"),
        outcome=None,
        provenance={
            "evidence_type": "agent_action_log",
            "action_type": "rev_orch_reply_assessment",
            "authority_class": "SYSTEM_RECOMMENDED",
            "subject_id": contact_id or None,
        },
        occurred_at=None,
        href=f"/contacts/{contact_id}" if contact_id else "/demand",
    )


def _from_follow_up(row: dict[str, Any]) -> dict[str, Any]:
    contact_id = str(row.get("contact_id") or "")
    eligible = bool(row.get("eligible"))
    return _item(
        item_id=f"follow_up:{contact_id}",
        kind="follow_up",
        commercial_source="sales",
        decision_type="follow_up",
        title=str(row.get("name") or "Follow-up signal"),
        reason=row.get("reason") or "Follow-up may be due for this person.",
        person_label=row.get("name"),
        company_label=None,
        proposed_action=(
            "Propose a follow-up from the person workspace. Sending still requires approval."
            if eligible
            else None
        ),
        authority_state=AUTHORITY_READY if eligible else AUTHORITY_INFORMATIONAL,
        status=str(row.get("state") or ("eligible" if eligible else "signal")),
        outcome=None,
        provenance={
            "evidence_type": "follow_up_eligibility",
            "action_type": "rev_orch_followup_eligibility",
            "authority_class": "SYSTEM_RECOMMENDED",
            "subject_id": contact_id or None,
        },
        occurred_at=None,
        href=f"/contacts/{contact_id}" if contact_id else "/demand",
    )


def _from_completed_activity(row: dict[str, Any]) -> dict[str, Any] | None:
    action_type = str(row.get("action_type") or "")
    if action_type not in _COMPLETED_ACTION_TYPES:
        return None
    target_id = row.get("target_id")
    label = str(row.get("label") or action_type)
    commercial_source = "marketing"
    if action_type.startswith("commercial_outcome"):
        commercial_source = "revenue"
    elif action_type.startswith("approval_"):
        commercial_source = "governance"
    href = "/activity"
    if target_id and action_type.startswith("qualified_demand"):
        href = "/demand"
    elif target_id and not action_type.startswith("qualified_demand"):
        href = f"/contacts/{target_id}"
    return _item(
        item_id=f"outcome:{action_type}:{row.get('id') or target_id or 'unknown'}",
        kind="outcome",
        commercial_source=commercial_source,
        decision_type=action_type,
        title=label,
        reason="Recorded on the commercial spine after a governed decision or action.",
        person_label=None,
        company_label=None,
        proposed_action=None,
        authority_state=AUTHORITY_COMPLETED,
        status="resolved",
        outcome=label,
        provenance={
            "evidence_type": "agent_action_log",
            "action_type": action_type,
            "authority_class": row.get("authority_class") or "HUMAN_DECIDED",
            "subject_id": str(target_id) if target_id else None,
            "actor": row.get("actor"),
        },
        occurred_at=row.get("created_at"),
        href=href,
    )


def compose_commercial_decision_items(
    *,
    pending_demands: list[dict[str, Any]] | None = None,
    pending_approvals: list[dict[str, Any]] | None = None,
    meeting_interest: list[dict[str, Any]] | None = None,
    follow_up_signals: list[dict[str, Any]] | None = None,
    recent_activity: list[dict[str, Any]] | None = None,
    organization_id: str | None = None,
) -> list[dict[str, Any]]:
    """Compose Founder decision items from already-loaded, preferably org-scoped fragments.

    Returns [] when organization_id is missing (fail closed). Does not query the database.
    Does not invent scores, confidence, or revenue estimates.
    """
    if organization_id is None or not str(organization_id).strip():
        return []

    items: list[dict[str, Any]] = []
    seen: set[str] = set()

    for row in pending_approvals or []:
        item = _from_pending_approval(row)
        if item["item_id"] not in seen:
            seen.add(item["item_id"])
            items.append(item)

    for row in pending_demands or []:
        item = _from_pending_demand(row)
        if item["item_id"] not in seen:
            seen.add(item["item_id"])
            items.append(item)

    for row in meeting_interest or []:
        item = _from_meeting_interest(row)
        if item["item_id"] not in seen:
            seen.add(item["item_id"])
            items.append(item)

    for row in follow_up_signals or []:
        item = _from_follow_up(row)
        if item["item_id"] not in seen:
            seen.add(item["item_id"])
            items.append(item)

    for row in recent_activity or []:
        item = _from_completed_activity(row)
        if item is None:
            continue
        if item["item_id"] not in seen:
            seen.add(item["item_id"])
            items.append(item)

    items.sort(
        key=lambda i: (
            _BAND_ORDER.get(str(i.get("authority_state")), 99),
            str(i.get("occurred_at") or ""),
        )
    )
    # Within requires_founder / ready, prefer newest first when timestamps exist.
    requires = [i for i in items if i["authority_state"] == AUTHORITY_REQUIRES_FOUNDER]
    ready = [i for i in items if i["authority_state"] == AUTHORITY_READY]
    completed = [i for i in items if i["authority_state"] == AUTHORITY_COMPLETED]
    info = [i for i in items if i["authority_state"] == AUTHORITY_INFORMATIONAL]
    completed.sort(key=lambda i: str(i.get("occurred_at") or ""), reverse=True)
    return requires + ready + completed[:8] + info


def summarize_decision_loop(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Counts by authority band — derived only from composed items."""
    counts = {
        AUTHORITY_REQUIRES_FOUNDER: 0,
        AUTHORITY_READY: 0,
        AUTHORITY_COMPLETED: 0,
        AUTHORITY_INFORMATIONAL: 0,
    }
    for item in items:
        band = str(item.get("authority_state") or "")
        if band in counts:
            counts[band] += 1
    return {
        "total": len(items),
        "requires_founder": counts[AUTHORITY_REQUIRES_FOUNDER],
        "ready": counts[AUTHORITY_READY],
        "completed": counts[AUTHORITY_COMPLETED],
        "informational": counts[AUTHORITY_INFORMATIONAL],
    }
