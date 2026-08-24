"""Research → outreach proposal eligibility (policy before scheduled M1).

Deterministic scan/evaluate for cold research-to-outreach proposals.
Does not research, draft, file ApprovalRequest, or send outbound.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from revenue_os.models.activity import Activity, ActivityType
from revenue_os.models.approvals import ApprovalRequest
from revenue_os.models.contact import Contact
from revenue_os.services.acp1_autonomous_boundary import assert_contact_org
from revenue_os.services.follow_up_eligibility import contact_has_stop_tags

STATE_ELIGIBLE = "RESEARCH_OUTREACH_ELIGIBLE"
STATE_STOPPED = "RESEARCH_OUTREACH_STOPPED"
STATE_PENDING = "RESEARCH_OUTREACH_APPROVAL_PENDING"
STATE_ALREADY_OUTREACHED = "RESEARCH_OUTREACH_ALREADY_SENT"
STATE_MISSING_EMAIL = "RESEARCH_OUTREACH_MISSING_EMAIL"
STATE_TENANT = "RESEARCH_OUTREACH_TENANT_INVALID"

# RESEARCH_FRESHNESS_POLICY = UNDEFINED — no repository TTL; revalidate at execute.


def research_outreach_idempotency_key(organization_id: str, contact_id: str) -> str:
    """Stable proposal identity for claim/logical_key (not the per-run send key)."""
    return f"rev-orch-m1:propose:{organization_id}:{contact_id}"


def _pending_outreach_approval(db: Session, contact_id: str) -> ApprovalRequest | None:
    return (
        db.query(ApprovalRequest)
        .filter(
            ApprovalRequest.status == "pending",
            ApprovalRequest.action_type == "send_outreach_email",
            ApprovalRequest.target_id == contact_id,
        )
        .first()
    )


def _has_completed_outbound_email(db: Session, contact_id: uuid.UUID) -> bool:
    row = (
        db.query(Activity.id)
        .filter(
            Activity.contact_id == contact_id,
            Activity.activity_type == ActivityType.EMAIL,
            Activity.direction == "outbound",
            Activity.status == "completed",
        )
        .first()
    )
    return row is not None


def evaluate_research_outreach_eligibility(
    db: Session,
    contact: Contact,
    organization_id: str,
) -> dict[str, Any]:
    """Deterministic eligibility — AI must not override a negative result."""
    contact_id = str(contact.id)
    org_id = str(organization_id)

    if contact.organization_id is None:
        return {
            "eligible": False,
            "state": STATE_TENANT,
            "reason": "Contact missing tenant organization",
            "organization_id": org_id,
            "contact_id": contact_id,
        }

    if str(contact.organization_id) != org_id:
        return {
            "eligible": False,
            "state": STATE_TENANT,
            "reason": "Contact not owned by organization",
            "organization_id": org_id,
            "contact_id": contact_id,
        }

    if contact_has_stop_tags(contact):
        return {
            "eligible": False,
            "state": STATE_STOPPED,
            "reason": "Contact has do-not-contact / unsubscribe tag",
            "organization_id": org_id,
            "contact_id": contact_id,
        }

    if not (contact.email and str(contact.email).strip()):
        return {
            "eligible": False,
            "state": STATE_MISSING_EMAIL,
            "reason": "Contact has no email address",
            "organization_id": org_id,
            "contact_id": contact_id,
        }

    if _has_completed_outbound_email(db, contact.id):
        return {
            "eligible": False,
            "state": STATE_ALREADY_OUTREACHED,
            "reason": "Completed outbound email already exists (cold research-outreach not due)",
            "organization_id": org_id,
            "contact_id": contact_id,
        }

    pending = _pending_outreach_approval(db, contact_id)
    if pending is not None:
        return {
            "eligible": False,
            "state": STATE_PENDING,
            "reason": "Duplicate pending send_outreach_email ApprovalRequest",
            "organization_id": org_id,
            "contact_id": contact_id,
            "pending_approval_id": str(pending.id),
        }

    return {
        "eligible": True,
        "state": STATE_ELIGIBLE,
        "reason": "Policy permits research-to-outreach proposal",
        "organization_id": org_id,
        "contact_id": contact_id,
        "idempotency_key": research_outreach_idempotency_key(org_id, contact_id),
    }


def scan_eligible_research_outreach(
    db: Session,
    *,
    organization_id: str,
    limit: int = 25,
) -> list[dict[str, str]]:
    """Scheduler scan — mandatory organization scope (ACP-1)."""
    try:
        org_uuid = uuid.UUID(str(organization_id))
    except ValueError:
        return []

    contacts = (
        db.query(Contact)
        .filter(Contact.organization_id == org_uuid, Contact.email.isnot(None))
        .limit(limit * 4)
        .all()
    )
    eligible: list[dict[str, str]] = []
    for contact in contacts:
        if len(eligible) >= limit:
            break
        if not assert_contact_org(contact, organization_id):
            continue
        result = evaluate_research_outreach_eligibility(db, contact, organization_id)
        if result.get("eligible"):
            eligible.append(
                {
                    "organization_id": str(contact.organization_id),
                    "contact_id": str(contact.id),
                    "idempotency_key": str(result.get("idempotency_key") or ""),
                }
            )
    return eligible
