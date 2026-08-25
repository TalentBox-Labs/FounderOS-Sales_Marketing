"""Command Center V2 I3 — Decisions Queue + Decision Detail (projection only).

Composes founder-facing judgment surfaces from existing ApprovalRequest /
COS decision truth. Does not persist, mint Situation IDs, or expand authority.
"""

from __future__ import annotations

from typing import Any

from revenue_os.services.command_operating_surface import (
    ENDPOINT_APPROVAL_APPROVE,
    ENDPOINT_APPROVAL_REJECT,
    EXEC_INLINE_GOVERNED,
    EXEC_NAVIGATE_GOVERNED,
)

# Known action families for presentation labels only — unknown types still render.
_ACTION_CATEGORY: dict[str, str] = {
    "book_meeting": "Meeting booking",
    "send_outreach_email": "Outreach",
    "send_reply_email": "Reply",
    "send_linkedin_message": "LinkedIn",
    "create_deal": "Deal",
}

_KNOWN_CONSEQUENCE_APPROVE: dict[str, str] = {
    "book_meeting": (
        "If approved, the existing booking executor attempts to schedule the "
        "proposed meeting through the governed calendar path."
    ),
    "send_outreach_email": (
        "If approved, the existing outreach path may send the prepared message."
    ),
    "send_reply_email": (
        "If approved, the existing reply path may send the prepared message."
    ),
    "send_linkedin_message": (
        "If approved, the existing LinkedIn path may deliver the prepared message."
    ),
    "create_deal": (
        "If approved, the existing deal path may create the proposed deal record."
    ),
}

_REJECT_CONSEQUENCE = (
    "If rejected, nothing is sent or booked. The proposal is archived without effect."
)


def _norm(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _humanize_action(action_type: str | None) -> str:
    token = _norm(action_type) or "unknown"
    if token in _ACTION_CATEGORY:
        return _ACTION_CATEGORY[token]
    return token.replace("_", " ").title()


def _category_for(action_type: str | None) -> str:
    token = _norm(action_type)
    if token and token in _ACTION_CATEGORY:
        return _ACTION_CATEGORY[token]
    if token:
        return "Governed proposal"
    return "Governed proposal"


def _empty_queue(*, organization_id: str | None, reason: str) -> dict[str, Any]:
    return {
        "organization_id": organization_id,
        "source": "command_v2_decisions",
        "persistent": False,
        "fail_closed_reason": reason,
        "items": [],
        "count": 0,
    }


def compose_decisions_queue(
    *,
    organization_id: str | None,
    pending_approvals: list[Any] | None = None,
    decision_items: list[Any] | None = None,
) -> dict[str, Any]:
    """Build the Decisions Queue from existing pending ApprovalRequests (+ QD intake).

    Dedupes ApprovalRequest rows by canonical ApprovalRequest.id across sources.
    Never invents approvals. Never groups across tenants.
    """
    org = _norm(organization_id)
    if not org:
        return _empty_queue(organization_id=None, reason="missing_organization_id")

    pending = pending_approvals if isinstance(pending_approvals, list) else []
    decisions = decision_items if isinstance(decision_items, list) else []

    seen_approvals: set[str] = set()
    items: list[dict[str, Any]] = []

    for raw in pending:
        if not isinstance(raw, dict):
            continue
        # Tenant fence — never accept foreign org rows.
        row_org = _norm(raw.get("organization_id"))
        if row_org and row_org != org:
            continue
        request_id = _norm(raw.get("id") or raw.get("request_id"))
        if not request_id:
            continue
        if request_id in seen_approvals:
            continue
        seen_approvals.add(request_id)
        action_type = _norm(raw.get("action_type"))
        items.append(
            {
                "decision_key": f"approval:{request_id}",
                "kind": "approval",
                "approval_request_id": request_id,
                "organization_id": org,
                "title": str(raw.get("title") or "Approval request"),
                "category": _category_for(action_type),
                "action_type": action_type,
                "action_label": str(
                    raw.get("action_label") or _humanize_action(action_type)
                ),
                "state": "pending",
                "state_label": "Needs your judgment",
                "why_judgment": (
                    str(raw.get("description") or "").strip()
                    or "An AI or system proposal is waiting. Nothing executes until you approve or reject."
                ),
                "proposed_by_label": str(
                    raw.get("proposal_source_label")
                    or raw.get("requested_by_label")
                    or "Proposal"
                ),
                "requested_by": _norm(raw.get("requested_by")),
                "target_id": _norm(raw.get("target_id")),
                "target_type": _norm(raw.get("target_type")),
                "occurred_at": _norm(raw.get("created_at")),
                "evidence_available": bool(
                    (raw.get("description") or "").strip()
                    or raw.get("booking_display")
                    or raw.get("payload")
                ),
                "href_detail": f"/decisions/{request_id}",
                "href_context": (
                    f"/contacts/{raw.get('target_id')}"
                    if raw.get("target_id")
                    else "/pending-approvals"
                ),
                # Presentation adjacency only — not Situation / domain identity.
                "presentation_subject_key": f"approval_request:{request_id}",
                "next_move": "HUMAN_DECISION_REQUIRED",
            }
        )

    # Qualified demand intake already in COS-3 — not an ApprovalRequest.
    for raw in decisions:
        if not isinstance(raw, dict):
            continue
        if _norm(raw.get("kind")) != "qualified_demand":
            continue
        if _norm(raw.get("authority_state")) != "requires_founder":
            continue
        provenance = raw.get("provenance") if isinstance(raw.get("provenance"), dict) else {}
        demand_id = _norm(provenance.get("subject_id")) or _norm(raw.get("item_id"))
        if not demand_id:
            continue
        dedupe = f"demand:{demand_id}"
        if any(i.get("decision_key") == dedupe for i in items):
            continue
        items.append(
            {
                "decision_key": dedupe,
                "kind": "qualified_demand",
                "approval_request_id": None,
                "demand_id": demand_id,
                "organization_id": org,
                "title": str(raw.get("title") or "Demand intake"),
                "category": "Demand intake",
                "action_type": "qualified_demand_intake",
                "action_label": str(raw.get("proposed_action") or "Accept or reject demand"),
                "state": "requires_founder",
                "state_label": "Needs your judgment",
                "why_judgment": str(
                    raw.get("reason")
                    or "This demand is awaiting founder intake."
                ),
                "proposed_by_label": "Marketing / demand",
                "requested_by": None,
                "target_id": None,
                "target_type": "demand",
                "occurred_at": _norm(raw.get("occurred_at")),
                "evidence_available": bool(raw.get("reason")),
                "href_detail": "/demand",
                "href_context": "/demand",
                "presentation_subject_key": f"demand:{demand_id}",
                "next_move": "HUMAN_DECISION_REQUIRED",
            }
        )

    items.sort(
        key=lambda row: (
            0 if row.get("occurred_at") else 1,
            str(row.get("occurred_at") or ""),
            str(row.get("decision_key") or ""),
        ),
        reverse=False,
    )
    # Newest first when timestamps exist
    with_ts = [i for i in items if i.get("occurred_at")]
    without = [i for i in items if not i.get("occurred_at")]
    with_ts.sort(key=lambda i: str(i.get("occurred_at")), reverse=True)
    items = with_ts + without

    return {
        "organization_id": org,
        "source": "command_v2_decisions",
        "persistent": False,
        "fail_closed_reason": None,
        "items": items,
        "count": len(items),
    }


def compose_decision_detail(
    *,
    organization_id: str | None,
    approval: dict[str, Any] | None,
) -> dict[str, Any]:
    """Compose Decision Detail for one ApprovalRequest. Fail closed on mismatch."""
    org = _norm(organization_id)
    if not org:
        return {
            "organization_id": None,
            "source": "command_v2_decisions",
            "persistent": False,
            "fail_closed_reason": "missing_organization_id",
            "available": False,
            "actions": [],
        }
    if not isinstance(approval, dict):
        return {
            "organization_id": org,
            "source": "command_v2_decisions",
            "persistent": False,
            "fail_closed_reason": "missing_approval",
            "available": False,
            "actions": [],
        }

    row_org = _norm(approval.get("organization_id"))
    if row_org and row_org != org:
        return {
            "organization_id": org,
            "source": "command_v2_decisions",
            "persistent": False,
            "fail_closed_reason": "organization_mismatch",
            "available": False,
            "actions": [],
        }

    request_id = _norm(approval.get("id") or approval.get("request_id"))
    if not request_id:
        return {
            "organization_id": org,
            "source": "command_v2_decisions",
            "persistent": False,
            "fail_closed_reason": "missing_approval_identity",
            "available": False,
            "actions": [],
        }

    action_type = _norm(approval.get("action_type"))
    status = _norm(approval.get("status")) or "pending"
    description = str(approval.get("description") or "").strip()
    booking_display = (
        approval.get("booking_display")
        if isinstance(approval.get("booking_display"), dict)
        else None
    )
    payload = approval.get("payload") if isinstance(approval.get("payload"), dict) else None

    evidence_items: list[dict[str, str]] = []
    if description:
        evidence_items.append({"label": "Proposal description", "value": description})
    if booking_display:
        slot = booking_display.get("slot_start_display")
        if slot:
            evidence_items.append({"label": "Suggested time", "value": str(slot)})
        tz = booking_display.get("timezone")
        if tz:
            evidence_items.append({"label": "Timezone", "value": str(tz)})
        purpose = booking_display.get("purpose")
        if purpose:
            evidence_items.append({"label": "Purpose", "value": str(purpose)[:240]})
    # Do not dump raw payload secrets — only non-sensitive display keys if present.
    if payload:
        for key in ("template", "workflow_kind", "purpose"):
            if payload.get(key):
                evidence_items.append(
                    {"label": key.replace("_", " ").title(), "value": str(payload.get(key))[:240]}
                )

    evidence_available = bool(evidence_items)
    approve_consequence = _KNOWN_CONSEQUENCE_APPROVE.get(action_type or "")
    if not approve_consequence:
        approve_consequence = (
            "If approved, the existing governed approval executor for this "
            "action type runs (when registered). This page does not grant new authority."
        )

    actions: list[dict[str, Any]] = []
    if status == "pending":
        actions = [
            {
                "key": f"approval_approve:{request_id}",
                "label": "Approve",
                "action_type": "approval_approve",
                "execution_mode": EXEC_INLINE_GOVERNED,
                "endpoint": ENDPOINT_APPROVAL_APPROVE.format(request_id=request_id),
                "method": "POST",
                "reason": "Runs the existing approval path. Confirmation required.",
            },
            {
                "key": f"approval_reject:{request_id}",
                "label": "Reject",
                "action_type": "approval_reject",
                "execution_mode": EXEC_INLINE_GOVERNED,
                "endpoint": ENDPOINT_APPROVAL_REJECT.format(request_id=request_id),
                "method": "POST",
                "reason": "Archives the proposal. Nothing is sent or booked.",
            },
        ]
        target = _norm(approval.get("target_id"))
        if target:
            actions.append(
                {
                    "key": f"view_context:{target}",
                    "label": "View context",
                    "action_type": "navigate",
                    "execution_mode": EXEC_NAVIGATE_GOVERNED,
                    "href": f"/contacts/{target}",
                    "reason": "Open the related person workspace.",
                }
            )

    return {
        "organization_id": org,
        "source": "command_v2_decisions",
        "persistent": False,
        "fail_closed_reason": None,
        "available": True,
        "approval_request_id": request_id,
        "kind": "approval",
        "title": str(approval.get("title") or "Approval request"),
        "category": _category_for(action_type),
        "action_type": action_type,
        "action_label": str(
            approval.get("action_label") or _humanize_action(action_type)
        ),
        "status": status,
        "state_label": (
            "Needs your judgment"
            if status == "pending"
            else status.replace("_", " ").title()
        ),
        "proposal": {
            "summary": str(approval.get("title") or "Approval request"),
            "action_label": str(
                approval.get("action_label") or _humanize_action(action_type)
            ),
            "description": description or None,
        },
        "why": {
            "text": description
            or "This proposal requires founder judgment before any governed effect runs.",
            "requires_human": True,
        },
        "evidence": {
            "available": evidence_available,
            "items": evidence_items,
            "unavailable_message": (
                None
                if evidence_available
                else "Evidence is unavailable for this proposal."
            ),
        },
        "consequence": {
            "on_approve": approve_consequence,
            "on_reject": _REJECT_CONSEQUENCE,
            "unavailable": False,
        },
        "provenance": {
            "requested_by": _norm(approval.get("requested_by")),
            "proposed_by_label": str(
                approval.get("proposal_source_label")
                or approval.get("requested_by_label")
                or "Proposal"
            ),
            "approval_family": _norm(approval.get("approval_family")),
            "logical_key": _norm(approval.get("logical_key")),
            "created_at": _norm(approval.get("created_at")),
            "decided_at": _norm(approval.get("decided_at")),
            "decided_by": _norm(approval.get("decided_by")),
            "target_type": _norm(approval.get("target_type")),
            "target_id": _norm(approval.get("target_id")),
        },
        "authority": {
            "exists": [
                "Founder may approve or reject via the existing ApprovalRequest path.",
                "Tenant-scoped decision only.",
            ],
            "does_not_exist": [
                "Viewing this page does not approve or execute anything.",
                "Presentation does not grant booking, outbound, or agent authority.",
                "next_move is not an executable command.",
            ],
        },
        "actions": actions,
        "presentation_subject_key": f"approval_request:{request_id}",
        "next_move": "HUMAN_DECISION_REQUIRED" if status == "pending" else None,
        "href_queue": "/pending-approvals",
    }
