"""MDG1 — Manual Founder Demand Registration trusted proxy.

CONNECT_EXISTING: composes frozen MC04.5 register_marketing_handoff.
Client-supplied requested_by is never trusted.
No new persistent SoT — AgentActionLog remains the handoff store.
No public/anonymous ingress.
"""

from __future__ import annotations

import logging
import uuid as uuid_lib
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from revenue_os.database import SessionLocal
from revenue_os.services.mutation_authority import HumanAuthorityError
from revenue_os.services.qualified_demand_service import (
    SOURCE_TO_CONTACT,
    CompanyHintPayload,
    PersonPayload,
    QualifiedDemandPayload,
    register_marketing_handoff,
)
from revenue_os.services.tenant_mutation_guard import require_tenant_mutation
from runner_api_routers.cockpit import _trusted_cockpit_operator
from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/mdg", tags=["mdg1-manual-demand"])

# Manually asserted origin — not fabricated campaign/UTM capture.
ALLOWED_MANUAL_SOURCES = frozenset(SOURCE_TO_CONTACT.keys())


class ManualDemandRegisterBody(BaseModel):
    """Ephemeral form model — maps onto frozen QualifiedDemandPayload."""

    email: str = Field(..., min_length=3, max_length=255)
    name: str = Field(default="", max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    company_name: str | None = Field(default=None, max_length=255)
    company_domain: str | None = Field(default=None, max_length=255)
    source: str = Field(default="manual", max_length=64)
    source_detail: str = Field(default="", max_length=500)
    context_note: str = Field(default="", max_length=2000)
    demand_id: str | None = Field(
        default=None,
        max_length=64,
        description="Optional UUID for idempotent retry; server generates if omitted",
    )

    @field_validator("email")
    @classmethod
    def email_has_at(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if "@" not in cleaned or "." not in cleaned.split("@")[-1]:
            raise ValueError("email must look like a valid address")
        return cleaned

    @field_validator("source")
    @classmethod
    def source_allowed(cls, value: str) -> str:
        key = value.strip().lower().replace("-", "_")
        if key not in ALLOWED_MANUAL_SOURCES:
            raise ValueError(
                f"source must be one of: {', '.join(sorted(ALLOWED_MANUAL_SOURCES))}"
            )
        return key


def _service_http(exc: Exception) -> HTTPException:
    if isinstance(exc, HumanAuthorityError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=500, detail="Manual demand registration failed")


@router.post("/manual-demand/register")
def register_manual_demand(
    body: ManualDemandRegisterBody,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Trusted-human manual registration → MC04.5 handoff (no Contact/Deal yet)."""
    tenant = require_tenant_mutation()
    operator = _trusted_cockpit_operator()

    if body.demand_id:
        try:
            uuid_lib.UUID(body.demand_id.strip())
            demand_id = body.demand_id.strip()
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="demand_id must be a valid UUID") from exc
    else:
        demand_id = str(uuid_lib.uuid4())

    occurred_at = datetime.now(timezone.utc).isoformat()

    company_hint = None
    if body.company_name or body.company_domain:
        company_hint = CompanyHintPayload(
            name=(body.company_name or None),
            domain=(body.company_domain or None),
        )

    # Truthful provenance: manually supplied via Founder OS UI — never invent UTM/campaign.
    content_attribution: dict[str, Any] = {
        "registration_mode": "manual_founder_ui",
        "registration_surface": "/operator/demand/register",
        "manually_supplied": True,
    }
    if body.source_detail.strip():
        content_attribution["source_detail"] = body.source_detail.strip()

    marketing_qualification: dict[str, Any] | None = None
    if body.context_note.strip():
        marketing_qualification = {
            "notes": body.context_note.strip(),
            "qualification_mode": "manual_founder_asserted",
        }

    try:
        payload = QualifiedDemandPayload(
            demand_id=demand_id,
            occurred_at=occurred_at,
            source=body.source,
            channel="manual_founder_registration",
            person=PersonPayload(
                email=body.email,
                name=body.name.strip(),
                phone=body.phone.strip() if body.phone else None,
            ),
            company_hint=company_hint,
            marketing_qualification=marketing_qualification,
            consent=None,
            content_attribution=content_attribution,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    db = SessionLocal()
    try:
        try:
            result = register_marketing_handoff(
                db,
                payload,
                operator,
                organization_id=tenant.organization_id,
            )
        except (HumanAuthorityError, ValueError) as exc:
            raise _service_http(exc) from exc
    finally:
        db.close()

    return {
        "ok": True,
        "operator": operator,
        "action": "manual_demand_register",
        "contact_created": False,
        "deal_created": False,
        "revenue_mutated": False,
        "public_capture": False,
        "next_step": "Accept or reject on /operator (MC04.5 Sales intake)",
        **result,
    }
