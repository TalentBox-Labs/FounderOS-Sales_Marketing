"""ACP-4 pre-effect fence — CURRENT authority/tenant/pause/kill win.

PAST_ELIGIBILITY != CURRENT_AUTHORITY

Claim ownership does not satisfy approval or authority.
"""

from __future__ import annotations

import os
import uuid as uuid_lib
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from revenue_os.models.approvals import ApprovalRequest
from revenue_os.models.contact import Contact
from revenue_os.models.organization import Organization, OrganizationStatus
from revenue_os.services.acp1_autonomous_boundary import (
    BLOCKED_MISSING_TENANT,
    org_uuid_or_none,
    resolve_autonomous_organization_ids,
)
from revenue_os.services.acp2_effect_catalog import get_effect_spec
from revenue_os.services.acp2_orchestration import (
    _already_succeeded,
    autonomous_execution_enabled,
    heartbeat_pause_active,
)
from revenue_os.services.acp2_work_contract import ExecutionMode, WorkItem
from revenue_os.services.acp3_runtime_contract import ENV_RESUME_ENABLED


def _resume_enabled() -> bool:
    return os.environ.get(ENV_RESUME_ENABLED, "1") not in ("0", "false", "False")


@dataclass
class FenceResult:
    ok: bool
    reason: str | None = None
    detail: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "reason": self.reason,
            "detail": self.detail or {},
        }


def pre_effect_fence(
    db: Session,
    work: WorkItem,
    *,
    require_autonomous: bool = True,
    claim_held: bool = True,
) -> FenceResult:
    """Revalidate all runtime safety immediately before a protected effect."""
    if not claim_held:
        return FenceResult(ok=False, reason="claim_not_held")

    org_id = str(work.organization_id or "").strip()
    if not org_id:
        return FenceResult(ok=False, reason=BLOCKED_MISSING_TENANT)

    org_uuid = org_uuid_or_none(org_id)
    if org_uuid is None:
        return FenceResult(ok=False, reason="invalid_organization_id")

    org = db.get(Organization, org_uuid)
    if org is None:
        return FenceResult(ok=False, reason=BLOCKED_MISSING_TENANT)
    if org.status != OrganizationStatus.ACTIVE:
        return FenceResult(
            ok=False,
            reason="tenant_not_active",
            detail={"status": str(org.status)},
        )

    allowed = set(resolve_autonomous_organization_ids(db))
    if org_id not in allowed:
        return FenceResult(ok=False, reason="tenant_not_autonomous_eligible")

    if not autonomous_execution_enabled():
        return FenceResult(ok=False, reason="acp2_autonomous_execution_disabled")

    if heartbeat_pause_active():
        return FenceResult(ok=False, reason="heartbeat_paused")

    if not _resume_enabled() and str(work.source or "") in (
        "acp3_recovery",
        "acp4_recovery",
    ):
        return FenceResult(ok=False, reason="acp3_resume_disabled")

    # CURRENT catalog mode wins over historically recorded mode
    spec = get_effect_spec(work.work_kind)
    if spec is None:
        return FenceResult(ok=False, reason="unknown_work_kind_prohibited")
    current_mode = spec.execution_mode

    if current_mode == ExecutionMode.PROHIBITED:
        return FenceResult(ok=False, reason="effect_prohibited")

    if current_mode == ExecutionMode.HUMAN_REQUIRED:
        if require_autonomous:
            return FenceResult(
                ok=False,
                reason="authority_now_human_required",
                detail={"prior_mode": work.execution_mode.value},
            )
        approval_ok = _approval_allows_execution(db, work)
        if not approval_ok:
            return FenceResult(ok=False, reason="human_approval_required_or_invalid")

    if require_autonomous and current_mode != ExecutionMode.AUTONOMOUS:
        return FenceResult(
            ok=False,
            reason="authority_not_autonomous",
            detail={"current_mode": current_mode.value},
        )

    # Target ownership when contact-scoped
    ownership = _verify_target_ownership(db, work, org_uuid)
    if ownership is not None:
        return ownership

    if work.idempotency_key and _already_succeeded(db, work.idempotency_key):
        return FenceResult(
            ok=False,
            reason="already_succeeded",
            detail={"idempotency_key": work.idempotency_key},
        )

    return FenceResult(ok=True, reason=None, detail={"current_mode": current_mode.value})


def _approval_allows_execution(db: Session, work: WorkItem) -> bool:
    """Approval evidence must be approved AND tenant-bound to work.organization_id."""
    approval_id = work.approval_id or (work.detail or {}).get("approval_id")
    if not approval_id:
        return False
    org_id = str(work.organization_id or "").strip()
    if not org_id:
        return False
    row = db.get(ApprovalRequest, str(approval_id))
    if row is None:
        return False
    status = str(getattr(row, "status", "") or "").lower()
    if status != "approved":
        return False
    payload = row.payload or {}
    payload_org = payload.get("organization_id")
    if payload_org is not None:
        return str(payload_org) == org_id
    if row.target_type == "contact" and row.target_id:
        try:
            cid = uuid_lib.UUID(str(row.target_id))
        except ValueError:
            return False
        contact = db.get(Contact, cid)
        if contact is None or contact.organization_id is None:
            return False
        return str(contact.organization_id) == org_id
    return False


def _verify_target_ownership(
    db: Session, work: WorkItem, org_uuid: Any
) -> FenceResult | None:
    if work.target_type != "contact" or not work.target_id:
        return None
    try:
        cid = uuid_lib.UUID(str(work.target_id))
    except ValueError:
        return FenceResult(ok=False, reason="invalid_target_id")
    contact = db.get(Contact, cid)
    if contact is None:
        return FenceResult(ok=False, reason="target_not_found")
    if contact.organization_id != org_uuid:
        return FenceResult(ok=False, reason="cross_tenant_target")
    return None
