"""ACP-1 — autonomous commercial boundary (authority & tenant hardening).

Hardens existing heartbeat/Hermes/self-wake paths. Does not introduce an agent
runtime, new SoT, or widened outbound/booking authority.

Tenant enumeration (binding):
  1. Explicit env allowlist ACP1_AUTONOMOUS_ORGANIZATION_IDS (or alias
     HEARTBEAT_ORGANIZATION_IDS) when set — intersected with ACTIVE Organization.
  2. Otherwise ACTIVE Organization rows only.
Contact.organization_id is never an authorization source for tenant activation.
"""

from __future__ import annotations

import os
import uuid as uuid_lib
from typing import Any

from sqlalchemy.orm import Session

from revenue_os.services.activity_log import log_agent_action

# Effect classes — documentation + guard vocabulary (not a generic policy engine).
EFFECT_READ = "READ"
EFFECT_PROPOSE = "PROPOSE"
EFFECT_EXECUTE_GOVERNED = "EXECUTE_GOVERNED"
EFFECT_HUMAN_REQUIRED = "HUMAN_REQUIRED"
EFFECT_PROHIBITED = "PROHIBITED"

BLOCKED_MISSING_TENANT = "missing_tenant"
BLOCKED_TENANT_MISMATCH = "tenant_entity_mismatch"
BLOCKED_HERMES_DEAL = "hermes_deal_creation_prohibited"
BLOCKED_PROHIBITED_EFFECT = "effect_prohibited_for_autonomous"

ENV_ALLOWLIST_PRIMARY = "ACP1_AUTONOMOUS_ORGANIZATION_IDS"
ENV_ALLOWLIST_ALIAS = "HEARTBEAT_ORGANIZATION_IDS"

# Autonomous callers must never invoke optional_tenant mutation surfaces.
AUTONOMOUS_ACTORS = frozenset({"heartbeat", "hermes"})

HERMES_PROHIBITED_ACTIONS = frozenset({"create_deals_for_qualified"})


def _parse_uuid(value: str) -> str | None:
    try:
        return str(uuid_lib.UUID(str(value).strip()))
    except (ValueError, AttributeError, TypeError):
        return None


def parse_autonomous_organization_allowlist() -> list[str] | None:
    """Return parsed allowlist when env is set; None when unset (use Organizations).

    Empty / whitespace-only env value → empty list (fail closed).
    """
    raw = os.environ.get(ENV_ALLOWLIST_PRIMARY)
    if raw is None:
        raw = os.environ.get(ENV_ALLOWLIST_ALIAS)
    if raw is None:
        return None
    if not str(raw).strip():
        return []
    out: list[str] = []
    seen: set[str] = set()
    for part in str(raw).split(","):
        oid = _parse_uuid(part)
        if oid and oid not in seen:
            seen.add(oid)
            out.append(oid)
    return out


def active_organization_ids(db: Session) -> list[str]:
    """Canonical autonomous-eligible tenants: ACTIVE Organization records only."""
    from revenue_os.models.organization import Organization, OrganizationStatus

    rows = (
        db.query(Organization.id)
        .filter(Organization.status == OrganizationStatus.ACTIVE)
        .all()
    )
    return [str(row[0]) for row in rows]


def resolve_autonomous_organization_ids(db: Session) -> list[str]:
    """Resolve tenants authorized for autonomous commercial work.

    Never enumerates from Contact.organization_id.
    """
    active = set(active_organization_ids(db))
    allowlist = parse_autonomous_organization_allowlist()
    if allowlist is not None:
        return [oid for oid in allowlist if oid in active]
    return sorted(active)


def blocked_result(
    reason: str,
    *,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": False,
        "blocked": True,
        "blocked_reason": reason,
    }
    if detail:
        payload["detail"] = detail
    return payload


def log_autonomous_blocked(
    *,
    actor: str,
    action_type: str,
    reason: str,
    organization_id: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record a fail-closed autonomous decision with attributable provenance."""
    result = blocked_result(reason, detail=detail)
    log_agent_action(
        actor=actor,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        status="blocked",
        organization_id=organization_id,
        detail={"blocked_reason": reason, **(detail or {})},
    )
    return result


def require_organization_id(params: dict[str, Any] | None) -> str | None:
    raw = (params or {}).get("organization_id")
    if raw is None or str(raw).strip() == "":
        return None
    return _parse_uuid(str(raw))


def assert_contact_org(contact: Any, organization_id: str) -> bool:
    """True when contact is owned by organization_id."""
    owned = getattr(contact, "organization_id", None)
    if owned is None:
        return False
    return str(owned) == str(organization_id)


def assert_deal_org(deal: Any, organization_id: str) -> bool:
    owned = getattr(deal, "organization_id", None)
    if owned is None:
        return False
    return str(owned) == str(organization_id)


def hermes_action_allowed(action_type: str) -> bool:
    """Hermes autonomous deal creation is always prohibited in ACP-1."""
    return action_type not in HERMES_PROHIBITED_ACTIONS


def org_uuid_or_none(organization_id: str) -> uuid_lib.UUID | None:
    try:
        return uuid_lib.UUID(str(organization_id))
    except ValueError:
        return None
