"""MC04 — QualifiedDemand Marketing→Sales handoff service.

Immutable handoff payload + idempotent Sales intake + canonical Contact SoT.
Does not mutate Marketing-owned state after handoff or Revenue deal/outcome state.
"""

from __future__ import annotations

import json
import logging
import uuid as uuid_lib
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from revenue_os.models.automation_state import AgentActionLog
from revenue_os.models.contact import Company, Contact, ContactSource, ContactStatus
from revenue_os.services.mutation_authority import require_human_mutation_authority

logger = logging.getLogger(__name__)

ACTION_HANDOFF = "qualified_demand_handoff"
ACTION_ACCEPTED = "qualified_demand_accepted"
ACTION_REJECTED = "qualified_demand_rejected"

SOURCE_TO_CONTACT: dict[str, ContactSource] = {
    "web_form": ContactSource.WEB_FORM,
    "campaign": ContactSource.WEB_FORM,
    "social": ContactSource.LINKEDIN,
    "linkedin": ContactSource.LINKEDIN,
    "referral": ContactSource.REFERRAL,
    "event": ContactSource.MANUAL,
    "manual": ContactSource.MANUAL,
    "outreach": ContactSource.OUTREACH,
}


class PersonPayload(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    name: str = Field(default="", max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    linkedin_url: str | None = Field(default=None, max_length=500)


class CompanyHintPayload(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    domain: str | None = Field(default=None, max_length=255)


class QualifiedDemandPayload(BaseModel):
    """Frozen minimum payload per SALES_MARKETING_CONTRACT."""

    demand_id: str = Field(..., min_length=8, max_length=64)
    occurred_at: str = Field(..., min_length=10, max_length=64)
    source: str = Field(..., min_length=1, max_length=64)
    channel: str | None = Field(default=None, max_length=255)
    person: PersonPayload
    company_hint: CompanyHintPayload | None = None
    marketing_qualification: dict[str, Any] | None = None
    consent: dict[str, Any] | None = None
    content_attribution: dict[str, Any] | None = None

    @field_validator("demand_id")
    @classmethod
    def validate_demand_id_uuid(cls, value: str) -> str:
        try:
            uuid_lib.UUID(value)
        except ValueError as exc:
            raise ValueError("demand_id must be a valid UUID") from exc
        return value


def map_contact_source(source: str) -> ContactSource:
    key = source.strip().lower().replace("-", "_")
    return SOURCE_TO_CONTACT.get(key, ContactSource.MANUAL)


def _split_name(full_name: str) -> tuple[str, str]:
    parts = (full_name or "").strip().split(None, 1)
    if not parts:
        return "Unknown", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def _provenance_note(payload: QualifiedDemandPayload) -> str:
    record = {
        "demand_id": payload.demand_id,
        "source": payload.source,
        "channel": payload.channel,
        "marketing_qualification": payload.marketing_qualification,
        "content_attribution": payload.content_attribution,
        "consent": payload.consent,
    }
    return json.dumps(record, sort_keys=True)


def _find_audit(db: Session, action_type: str, demand_id: str) -> AgentActionLog | None:
    return (
        db.query(AgentActionLog)
        .filter(
            AgentActionLog.action_type == action_type,
            AgentActionLog.target_id == demand_id,
        )
        .first()
    )


def register_marketing_handoff(
    db: Session, payload: QualifiedDemandPayload, requested_by: str
) -> dict[str, Any]:
    """Marketing-side handoff registration — does not write Revenue CRM entities."""
    existing = _find_audit(db, ACTION_HANDOFF, payload.demand_id)
    if existing is not None:
        return {
            "ok": True,
            "idempotent": True,
            "demand_id": payload.demand_id,
            "handoff_registered": True,
            "requested_by": requested_by,
        }

    require_human_mutation_authority(
        requested_by, action="Marketing QualifiedDemand handoff"
    )

    db.add(
        AgentActionLog(
            actor=requested_by,
            action_type=ACTION_HANDOFF,
            target_type="qualified_demand",
            target_id=payload.demand_id,
            status="completed",
            detail={
                "payload": payload.model_dump(),
                "requested_by": requested_by,
                "occurred_at": payload.occurred_at,
            },
        )
    )
    db.commit()
    logger.info(
        "QualifiedDemand handoff registered",
        extra={"demand_id": payload.demand_id, "requested_by": requested_by},
    )
    return {
        "ok": True,
        "idempotent": False,
        "demand_id": payload.demand_id,
        "handoff_registered": True,
        "requested_by": requested_by,
    }


def _require_handoff(db: Session, demand_id: str) -> dict[str, Any]:
    row = _find_audit(db, ACTION_HANDOFF, demand_id)
    if row is None or not row.detail or "payload" not in row.detail:
        raise ValueError("QualifiedDemand handoff not found — register Marketing handoff first")
    return row.detail["payload"]


def accept_qualified_demand(
    db: Session, demand_id: str, requested_by: str, notes: str = ""
) -> dict[str, Any]:
    """Sales intake accept — creates or links canonical Contact; no auto-qualify or Deal."""
    prior = _find_audit(db, ACTION_ACCEPTED, demand_id)
    if prior is not None and prior.detail:
        return {
            "ok": True,
            "idempotent": True,
            "demand_id": demand_id,
            "contact_id": prior.detail.get("contact_id"),
            "created": prior.detail.get("created", False),
            "merged": prior.detail.get("merged", False),
            "requested_by": prior.detail.get("requested_by", requested_by),
        }

    require_human_mutation_authority(requested_by, action="Sales demand intake accept")

    payload_dict = _require_handoff(db, demand_id)
    payload = QualifiedDemandPayload.model_validate(payload_dict)
    email = payload.person.email.strip().lower()
    first_name, last_name = _split_name(payload.person.name)

    existing_contact = db.query(Contact).filter(Contact.email == email).first()
    created = False
    merged = False

    if existing_contact is not None:
        contact = existing_contact
        merged = True
        if payload.person.phone and not contact.phone:
            contact.phone = payload.person.phone
        if payload.person.linkedin_url and not contact.linkedin_url:
            contact.linkedin_url = payload.person.linkedin_url
        provenance = _provenance_note(payload)
        contact.notes = (contact.notes or "") + f"\n[MC04 handoff {payload.demand_id}] {provenance}"
        db.add(contact)
    else:
        contact = Contact(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=payload.person.phone,
            linkedin_url=payload.person.linkedin_url,
            source=map_contact_source(payload.source),
            status=ContactStatus.LEAD,
            notes=f"[MC04 handoff {payload.demand_id}] {_provenance_note(payload)}",
        )
        if payload.company_hint and payload.company_hint.name:
            company = (
                db.query(Company)
                .filter(Company.name == payload.company_hint.name)
                .first()
            )
            if company is None and payload.company_hint.domain:
                company = (
                    db.query(Company)
                    .filter(Company.domain == payload.company_hint.domain)
                    .first()
                )
            if company is None:
                company = Company(name=payload.company_hint.name)
                if payload.company_hint.domain:
                    company.domain = payload.company_hint.domain
                db.add(company)
                db.flush()
            contact.company_id = company.id
        db.add(contact)
        created = True

    db.flush()
    contact_id = str(contact.id)

    db.add(
        AgentActionLog(
            actor=requested_by,
            action_type=ACTION_ACCEPTED,
            target_type="qualified_demand",
            target_id=demand_id,
            status="completed",
            detail={
                "contact_id": contact_id,
                "created": created,
                "merged": merged,
                "requested_by": requested_by,
                "notes": notes or None,
                "email": email,
                "source": payload.source,
            },
        )
    )
    db.commit()
    db.refresh(contact)

    return {
        "ok": True,
        "idempotent": False,
        "demand_id": demand_id,
        "contact_id": contact_id,
        "created": created,
        "merged": merged,
        "status": contact.status.value,
        "lead_score": contact.lead_score or 0,
        "requested_by": requested_by,
        "deal_created": False,
        "commercial_outcome_emitted": False,
    }


def reject_qualified_demand(
    db: Session, demand_id: str, requested_by: str, reason: str
) -> dict[str, Any]:
    """Sales intake reject — audit only; no CRM entity."""
    prior = _find_audit(db, ACTION_REJECTED, demand_id)
    if prior is not None:
        return {
            "ok": True,
            "idempotent": True,
            "demand_id": demand_id,
            "rejected": True,
            "reason": prior.detail.get("reason") if prior.detail else reason,
        }

    require_human_mutation_authority(requested_by, action="Sales demand intake reject")

    _require_handoff(db, demand_id)

    prior_accept = _find_audit(db, ACTION_ACCEPTED, demand_id)
    if prior_accept is not None:
        raise ValueError("Demand already accepted — cannot reject")

    db.add(
        AgentActionLog(
            actor=requested_by,
            action_type=ACTION_REJECTED,
            target_type="qualified_demand",
            target_id=demand_id,
            status="completed",
            detail={
                "reason": reason.strip(),
                "requested_by": requested_by,
            },
        )
    )
    db.commit()
    return {
        "ok": True,
        "idempotent": False,
        "demand_id": demand_id,
        "rejected": True,
        "reason": reason.strip(),
        "requested_by": requested_by,
    }
