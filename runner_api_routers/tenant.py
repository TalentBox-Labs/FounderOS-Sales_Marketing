"""SaaS S2 — tenant context API (server-derived organization authority)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from revenue_os.services.tenant_resolution import (
    ORGANIZATION_COOKIE,
    require_tenant_context,
    resolve_tenant_context,
    set_organization_cookie,
)

router = APIRouter(prefix="/api/v1/tenant", tags=["tenant"])


class TenantSelectBody(BaseModel):
    organization_id: str = Field(..., min_length=8, max_length=64)


@router.get("/me")
def tenant_me(request: Request) -> dict[str, Any]:
    tenant = resolve_tenant_context(request)
    if tenant is None:
        return {"ok": True, "tenant": None}
    return {"ok": True, "tenant": tenant.as_public_dict()}


@router.post("/select")
def tenant_select(body: TenantSelectBody, request: Request) -> JSONResponse:
    tenant = resolve_tenant_context(
        request, organization_id_hint=body.organization_id.strip()
    )
    if tenant is None:
        raise HTTPException(status_code=403, detail="Cannot select organization")
    response = JSONResponse({"ok": True, "tenant": tenant.as_public_dict()})
    set_organization_cookie(response, tenant.organization_id)
    return response


@router.get("/require")
def tenant_require(request: Request) -> dict[str, Any]:
    tenant = require_tenant_context(request)
    return {"ok": True, "tenant": tenant.as_public_dict()}
