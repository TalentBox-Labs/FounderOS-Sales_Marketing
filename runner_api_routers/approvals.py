"""Approvals API — the human sign-off queue for risky autonomous actions."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from revenue_os.services.approvals import (
    EXECUTORS,
    decide,
    list_requests,
    pending_count,
    request_approval,
)
from revenue_os.services.mutation_authority import HumanAuthorityError
from revenue_os.services.tenant_resolution import (
    require_tenant_context,
    resolve_tenant_context,
)
from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])


class ApprovalCreateRequest(BaseModel):
    action_type: str = Field(..., description=f"Known executors: {sorted(EXECUTORS)}")
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(default="")
    target_type: str | None = None
    target_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class DecisionRequest(BaseModel):
    decided_by: str = Field(default="user", max_length=128)
    note: str | None = Field(default=None, max_length=2000)


def _tenant_for_approval(request: Request):
    """Prefer session tenant; fall back to legacy API-key path."""
    tenant = resolve_tenant_context(request)
    return tenant


@router.get("")
def list_approvals(
    request: Request,
    status: str | None = Query(None, description="pending | approved | rejected"),
    limit: int = Query(100, ge=1, le=500),
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    tenant = _tenant_for_approval(request)
    org_id = tenant.organization_id if tenant is not None else None
    requests = list_requests(status=status, limit=limit, organization_id=org_id)
    return {
        "ok": True,
        "count": len(requests),
        "pending": pending_count(organization_id=org_id),
        "requests": requests,
    }


@router.post("")
def create_approval(
    req: ApprovalCreateRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """File an approval request manually (agents normally do this themselves)."""
    result = request_approval(
        requested_by="api",
        action_type=req.action_type,
        title=req.title,
        description=req.description,
        target_type=req.target_type,
        target_id=req.target_id,
        payload=req.payload,
    )
    return {"ok": True, "request": result}


@router.post("/{request_id}/approve")
def approve_request(
    request_id: str,
    http_request: Request,
    req: DecisionRequest = DecisionRequest(),
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Approve — the proposed action executes immediately."""
    tenant = require_tenant_context(http_request)
    try:
        result = decide(
            request_id,
            approve=True,
            note=req.note,
            tenant=tenant,
        )
    except HumanAuthorityError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as e:
        raise HTTPException(status_code=409 if "already" in str(e) else 404, detail=str(e))
    return {"ok": True, "request": result}


@router.post("/{request_id}/reject")
def reject_request(
    request_id: str,
    http_request: Request,
    req: DecisionRequest = DecisionRequest(),
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Reject — the proposed action is archived and never runs."""
    tenant = require_tenant_context(http_request)
    try:
        result = decide(
            request_id,
            approve=False,
            note=req.note,
            tenant=tenant,
        )
    except HumanAuthorityError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as e:
        raise HTTPException(status_code=409 if "already" in str(e) else 404, detail=str(e))
    return {"ok": True, "request": result}
