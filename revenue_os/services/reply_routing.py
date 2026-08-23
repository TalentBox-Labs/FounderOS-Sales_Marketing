"""REV-ORCH M3 — deterministic inbound-reply routing (policy after AI).

AI classification is an input. This module decides routing. It does not send,
approve, book, accept QualifiedDemand, or change Deal.stage / Contact.status.
"""

from __future__ import annotations

from typing import Any

REPLY_TYPES = (
    "INTERESTED",
    "NEEDS_INFO",
    "OBJECTION",
    "NOT_NOW",
    "NOT_INTERESTED",
    "OPT_OUT",
    "MEETING_INTEREST",
    "UNKNOWN",
)

OBJECTION_CATEGORIES = (
    "PRICE",
    "TIMING",
    "AUTHORITY",
    "NEED",
    "COMPETITOR",
    "TRUST",
    "IMPLEMENTATION",
    "OTHER",
)

LOW_CONFIDENCE = 0.4

# Contact.tags tokens reused from M2.5 stop contract
OPT_OUT_TAG = "unsubscribed"


def route_reply_assessment(assessment: dict[str, Any]) -> dict[str, Any]:
    """Map a structured assessment to a deterministic next-action policy."""
    reply_type = str(assessment.get("reply_type") or "UNKNOWN").upper()
    if reply_type not in REPLY_TYPES:
        reply_type = "UNKNOWN"
    try:
        confidence = float(assessment.get("confidence") or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0

    if not assessment.get("ok"):
        reply_type = "UNKNOWN"
        confidence = 0.0

    if confidence < LOW_CONFIDENCE and reply_type not in {"OPT_OUT"}:
        # Opt-out remains high-priority even if model is uncertain once policy
        # already classified OPT_OUT; otherwise fail closed to human review.
        if reply_type != "OPT_OUT":
            reply_type = "UNKNOWN"

    meeting_interest = bool(assessment.get("meeting_interest")) or reply_type == "MEETING_INTEREST"
    objection = assessment.get("objection_category")
    if objection and str(objection).upper() not in OBJECTION_CATEGORIES:
        objection = "OTHER"
    elif objection:
        objection = str(objection).upper()

    routing: dict[str, Any] = {
        "reply_type": reply_type,
        "confidence": confidence,
        "meeting_interest": meeting_interest,
        "booking_eligible": False,
        "qualification_recommendation": None,
        "suggested_contact_status": None,
        "suggested_deal_stage": None,
        "apply_opt_out_tag": False,
        "follow_up_stopped": False,
        "requires_human_review": False,
        "recommended_next_action": "HUMAN_REVIEW",
        "human_gate_required": True,
        "contact_status_changed": False,
        "deal_stage_changed": False,
        "qualified_demand_accepted": False,
        "booking_created": False,
        "outbound_sent": False,
    }

    if reply_type == "OPT_OUT":
        routing.update(
            {
                "recommended_next_action": "SUPPRESS",
                "apply_opt_out_tag": True,
                "follow_up_stopped": True,
                "requires_human_review": False,
            }
        )
    elif reply_type == "NOT_INTERESTED":
        routing.update(
            {
                "recommended_next_action": "DISQUALIFY",
                "suggested_contact_status": "churned",
                "follow_up_stopped": True,
            }
        )
    elif reply_type == "NOT_NOW":
        routing.update(
            {
                "recommended_next_action": "PAUSE",
                "follow_up_stopped": True,
            }
        )
    elif reply_type == "NEEDS_INFO":
        routing.update(
            {
                "recommended_next_action": "DRAFT_INFO_RESPONSE",
            }
        )
    elif reply_type == "OBJECTION":
        routing.update(
            {
                "recommended_next_action": "HANDLE_OBJECTION",
                "objection_category": objection or "OTHER",
            }
        )
    elif reply_type == "INTERESTED":
        routing.update(
            {
                "recommended_next_action": "QUALIFY",
                "qualification_recommendation": "QUALIFY",
                "suggested_contact_status": "qualified",
            }
        )
    elif reply_type == "MEETING_INTEREST":
        routing.update(
            {
                "recommended_next_action": "BOOKING_ELIGIBLE",
                "booking_eligible": True,
                "meeting_interest": True,
                "qualification_recommendation": "QUALIFY",
                "suggested_contact_status": "qualified",
            }
        )
    else:
        routing.update(
            {
                "recommended_next_action": "HUMAN_REVIEW",
                "requires_human_review": True,
                "reply_type": "UNKNOWN",
            }
        )

    return routing


def merge_opt_out_tag(existing_tags: str | None) -> str:
    raw = (existing_tags or "").strip()
    tokens = {t.strip().lower() for t in raw.replace(",", " ").split() if t.strip()}
    tokens.add(OPT_OUT_TAG)
    return " ".join(sorted(tokens))
