"""Orchestration and GTM strategy endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from revenue_os.services.go_to_market_orchestrator import (
    GTMOrchestrationRequest,
    build_strategy,
    load_orchestration_run,
    load_recent_orchestration_runs,
    run_orchestration,
)
from revenue_os.services.orchestration_runtime import backend_status

from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/orchestration", tags=["orchestration"])


class OrchestrationRequest(BaseModel):
    """Request model for orchestration workflows."""

    backend: str = "hermes"
    brand: str = "workcrew"
    topic: str = ""
    keyword: str = ""
    geo_target: str = ""
    funnel_stage: str = "consideration"
    audience: str = "recruiters and hiring managers"
    channels: list[str] = Field(
        default_factory=lambda: [
            "blog",
            "linkedin",
            "instagram",
            "youtube",
            "email",
            "whatsapp",
        ]
    )
    run_content: bool = True
    run_seo: bool = True
    run_email: bool = True
    run_whatsapp: bool = True
    run_prospecting: bool = True
    run_voice_qualification: bool = True
    run_meeting_booking: bool = True


@router.get("/backends", tags=["orchestration"])
def orchestration_backends_proxy(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """List supported orchestration backends and their configuration status."""
    logger.info("Fetching orchestration backends")
    return {
        "supported": ["hermes", "openclaw"],
        "configured": backend_status(),
    }


@router.get("/logs", tags=["orchestration"])
def orchestration_logs_proxy(
    limit: int = 20,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get recent orchestration run logs."""
    logger.info("Fetching orchestration logs", extra={"limit": limit})
    return {
        "ok": True,
        "runs": load_recent_orchestration_runs(limit=max(1, min(limit, 100))),
    }


@router.post("/plan", tags=["orchestration"])
def orchestration_plan_proxy(
    req: OrchestrationRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Build and return a GTM strategy plan without executing."""
    if not req.topic or not req.keyword:
        raise HTTPException(status_code=400, detail="topic and keyword are required")

    logger.info(
        "Planning orchestration",
        extra={"backend": req.backend, "topic": req.topic, "keyword": req.keyword},
    )

    plan_req = GTMOrchestrationRequest(
        backend=req.backend,
        brand=req.brand,
        topic=req.topic,
        keyword=req.keyword,
        geo_target=req.geo_target,
        funnel_stage=req.funnel_stage,
        audience=req.audience,
        channels=req.channels,
        run_content=False,
        run_seo=False,
        run_email=False,
        run_whatsapp=False,
        run_prospecting=False,
        run_voice_qualification=False,
        run_meeting_booking=False,
    )
    return {
        "ok": True,
        "plan": build_strategy(plan_req),
    }


@router.post("/run", tags=["orchestration"])
def orchestration_run_proxy(
    req: OrchestrationRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Execute full orchestration workflow across all enabled channels."""
    if not req.topic or not req.keyword:
        raise HTTPException(status_code=400, detail="topic and keyword are required")

    logger.info(
        "Executing orchestration",
        extra={
            "backend": req.backend,
            "topic": req.topic,
            "keyword": req.keyword,
            "channels": req.channels,
        },
    )

    run_req = GTMOrchestrationRequest(
        backend=req.backend,
        brand=req.brand,
        topic=req.topic,
        keyword=req.keyword,
        geo_target=req.geo_target,
        funnel_stage=req.funnel_stage,
        audience=req.audience,
        channels=req.channels,
        run_content=req.run_content,
        run_seo=req.run_seo,
        run_email=req.run_email,
        run_whatsapp=req.run_whatsapp,
        run_prospecting=req.run_prospecting,
        run_voice_qualification=req.run_voice_qualification,
        run_meeting_booking=req.run_meeting_booking,
    )
    return {
        "ok": True,
        "result": run_orchestration(run_req),
    }
