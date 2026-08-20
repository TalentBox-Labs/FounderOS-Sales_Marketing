"""COS-2 — map a marketing signal onto the frozen QualifiedDemand contract.

Does not persist. Does not create Contact. Does not mutate Contact.status or Deal.stage.
Does not invent ICP, scores, ARR, or attribution fields that were not supplied.
Callers persist only via register_marketing_handoff (MC04).
"""

from __future__ import annotations

from typing import Any

from revenue_os.services.qualified_demand_service import (
    CompanyHintPayload,
    PersonPayload,
    QualifiedDemandPayload,
)


def compose_marketing_qualified_demand(
    *,
    demand_id: str,
    occurred_at: str,
    source: str,
    person: PersonPayload | dict[str, Any],
    channel: str | None = None,
    company_hint: CompanyHintPayload | dict[str, Any] | None = None,
    marketing_qualification: dict[str, Any] | None = None,
    content_attribution: dict[str, Any] | None = None,
    consent: dict[str, Any] | None = None,
) -> QualifiedDemandPayload:
    """Compose a marketing-originated QualifiedDemand payload from supplied fields only."""
    person_model = (
        person if isinstance(person, PersonPayload) else PersonPayload.model_validate(person)
    )
    hint_model = None
    if company_hint is not None:
        hint_model = (
            company_hint
            if isinstance(company_hint, CompanyHintPayload)
            else CompanyHintPayload.model_validate(company_hint)
        )
    return QualifiedDemandPayload(
        demand_id=demand_id,
        occurred_at=occurred_at,
        source=source,
        channel=channel,
        person=person_model,
        company_hint=hint_model,
        marketing_qualification=marketing_qualification,
        consent=consent,
        content_attribution=content_attribution,
    )
