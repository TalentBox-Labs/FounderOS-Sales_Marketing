"""REV-ORCH M1 — canonical revenue orchestration API on runner_api."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from revenue_os.database import SessionLocal
from revenue_os.agents.orchestration import (
    REV_ORCH_M1_WORKFLOW_KEY,
    WorkflowOrchestrator,
)
from revenue_os.services.revenue_orchestration_service import RevenueOrchestrationError
from revenue_os.services.tenant_resolution import require_tenant_context
from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/revenue", tags=["revenue-orchestration"])


class ResearchToOutreachRequest(BaseModel):
    """Optional body; organization comes from server TenantContext only."""

    organization_id: str | None = Field(
        default=None,
        description="Ignored if supplied — tenant is server-derived",
    )


@router.post("/contacts/{contact_id}/research-to-outreach")
def research_to_outreach(
    contact_id: str,
    http_request: Request,
    _: ResearchToOutreachRequest = ResearchToOutreachRequest(),
    __: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """M1 vertical slice: research → qualify → draft → ApprovalRequest (pending)."""
    tenant = require_tenant_context(http_request)
    db = SessionLocal()
    try:
        result = WorkflowOrchestrator.execute_revenue_workflow(
            REV_ORCH_M1_WORKFLOW_KEY,
            db=db,
            tenant=tenant,
            contact_id=contact_id,
        )
        return {"ok": True, **result}
    except RevenueOrchestrationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("M1 orchestration failed for contact %s", contact_id)
        raise HTTPException(status_code=500, detail="Orchestration failed") from exc
    finally:
        db.close()
