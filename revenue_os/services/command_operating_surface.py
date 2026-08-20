"""COS-5 — Founder Command operating surface (presentation / composition only).

Attaches governed execution modes to existing COS-3 decision items.
Does not mutate CRM, approvals, or bookings. Does not invent mutation authority.
Inline actions must call existing require-tenant / human-gated endpoints.
"""

from __future__ import annotations

from typing import Any

# Execution modes — presentation only.
EXEC_INLINE_GOVERNED = "INLINE_GOVERNED"
EXEC_NAVIGATE_GOVERNED = "NAVIGATE_GOVERNED"
EXEC_INFORMATION_ONLY = "INFORMATION_ONLY"

# Existing production endpoints reused by Command (not duplicated).
ENDPOINT_QD_ACCEPT = "/api/v1/operator/actions/qualified-demand/accept"
ENDPOINT_QD_REJECT = "/api/v1/operator/actions/qualified-demand/reject"
ENDPOINT_APPROVAL_APPROVE = "/api/v1/approvals/{request_id}/approve"
ENDPOINT_APPROVAL_REJECT = "/api/v1/approvals/{request_id}/reject"


def _action(
    *,
    key: str,
    label: str,
    action_type: str,
    execution_mode: str,
    subject_id: str | None,
    reason: str,
    endpoint: str | None = None,
    href: str | None = None,
    method: str | None = None,
    body_hint: dict[str, Any] | None = None,
    requires_reason: bool = False,
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "action_type": action_type,
        "execution_mode": execution_mode,
        "execution_mode_label": _mode_label(execution_mode),
        "subject_id": subject_id,
        "reason": reason,
        "endpoint": endpoint,
        "href": href,
        "method": method,
        "body_hint": body_hint or {},
        "requires_reason": requires_reason,
    }


def _mode_label(mode: str) -> str:
    if mode == EXEC_INLINE_GOVERNED:
        return "Decide here"
    if mode == EXEC_NAVIGATE_GOVERNED:
        return "Continue on governed surface"
    return "For awareness"


def actions_for_decision_item(item: dict[str, Any]) -> list[dict[str, Any]]:
    """Map a COS-3 decision item to COS-5 command actions (eligibility-gated)."""
    kind = str(item.get("kind") or "")
    provenance = item.get("provenance") if isinstance(item.get("provenance"), dict) else {}
    subject = provenance.get("subject_id")
    href = item.get("href")

    if kind == "qualified_demand":
        demand_id = str(subject or "")
        if not demand_id:
            return []
        return [
            _action(
                key=f"qd_accept:{demand_id}",
                label="Accept demand",
                action_type="qualified_demand_accept",
                execution_mode=EXEC_INLINE_GOVERNED,
                subject_id=demand_id,
                reason="Adds this person to your organization through the existing intake path.",
                endpoint=ENDPOINT_QD_ACCEPT,
                method="POST",
                body_hint={"demand_id": demand_id},
            ),
            _action(
                key=f"qd_reject:{demand_id}",
                label="Reject demand",
                action_type="qualified_demand_reject",
                execution_mode=EXEC_INLINE_GOVERNED,
                subject_id=demand_id,
                reason="Records your decision only — does not create a person.",
                endpoint=ENDPOINT_QD_REJECT,
                method="POST",
                body_hint={"demand_id": demand_id},
                requires_reason=True,
            ),
        ]

    if kind == "approval":
        request_id = str(subject or "")
        if not request_id:
            return []
        return [
            _action(
                key=f"approval_approve:{request_id}",
                label="Approve",
                action_type="approval_approve",
                execution_mode=EXEC_INLINE_GOVERNED,
                subject_id=request_id,
                reason="Approves the proposal. The existing approval path runs the governed action.",
                endpoint=ENDPOINT_APPROVAL_APPROVE.format(request_id=request_id),
                method="POST",
                body_hint={},
            ),
            _action(
                key=f"approval_reject:{request_id}",
                label="Reject",
                action_type="approval_reject",
                execution_mode=EXEC_INLINE_GOVERNED,
                subject_id=request_id,
                reason="Rejects the proposal. Nothing is sent or booked.",
                endpoint=ENDPOINT_APPROVAL_REJECT.format(request_id=request_id),
                method="POST",
                body_hint={},
            ),
        ]

    if kind == "meeting_interest":
        contact_id = str(subject or "")
        nav = f"/contacts/{contact_id}#contact-booking-panel" if contact_id else "/demand"
        return [
            _action(
                key=f"booking_nav:{contact_id or 'none'}",
                label="Review meeting options",
                action_type="booking_navigate",
                execution_mode=EXEC_NAVIGATE_GOVERNED,
                subject_id=contact_id or None,
                reason="Meeting booking stays proposal-only. Review times on the person workspace.",
                href=nav,
            )
        ]

    if kind == "follow_up":
        contact_id = str(subject or "")
        nav = f"/contacts/{contact_id}" if contact_id else "/demand"
        return [
            _action(
                key=f"followup_nav:{contact_id or 'none'}",
                label="Open person for follow-up",
                action_type="follow_up_navigate",
                execution_mode=EXEC_NAVIGATE_GOVERNED,
                subject_id=contact_id or None,
                reason="Propose follow-up from the person workspace. Sending still needs approval.",
                href=nav,
            )
        ]

    if kind == "outcome":
        return [
            _action(
                key=f"outcome_info:{item.get('item_id')}",
                label="View activity",
                action_type="outcome_information",
                execution_mode=EXEC_INFORMATION_ONLY,
                subject_id=str(subject) if subject else None,
                reason="This decision is already recorded on the commercial spine.",
                href=href or "/activity",
            )
        ]

    # Unknown kinds — never invent inline mutation.
    if href:
        return [
            _action(
                key=f"nav:{item.get('item_id')}",
                label="Open related surface",
                action_type="navigate",
                execution_mode=EXEC_NAVIGATE_GOVERNED,
                subject_id=str(subject) if subject else None,
                reason="Continue on the existing governed surface.",
                href=str(href),
            )
        ]
    return []


def attach_command_actions(
    decision_items: list[dict[str, Any]] | None,
    *,
    organization_id: str | None,
) -> list[dict[str, Any]]:
    """Attach command_actions to decision items. Fail closed without org."""
    if organization_id is None or not str(organization_id).strip():
        return []
    enriched: list[dict[str, Any]] = []
    for item in decision_items or []:
        row = dict(item)
        row["command_actions"] = actions_for_decision_item(row)
        enriched.append(row)
    return enriched


def summarize_command_actions(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Counts by execution mode — derived from attached actions only."""
    inline = 0
    navigate = 0
    info = 0
    for item in items:
        for action in item.get("command_actions") or []:
            mode = action.get("execution_mode")
            if mode == EXEC_INLINE_GOVERNED:
                inline += 1
            elif mode == EXEC_NAVIGATE_GOVERNED:
                navigate += 1
            else:
                info += 1
    return {
        "inline_governed": inline,
        "navigate_governed": navigate,
        "information_only": info,
        "total": inline + navigate + info,
    }


def assert_no_inline_for_optional_tenant_kinds() -> frozenset[str]:
    """Kinds that must never receive INLINE_GOVERNED in COS-5 v1."""
    return frozenset(
        {
            "deal_stage",
            "contact_status",
            "commercial_outcome",
            "outbound_send",
            "booking_execute",
            "follow_up_send",
        }
    )
