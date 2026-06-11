from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from revenue_os.services.go_to_market_orchestrator import (
    GTMOrchestrationRequest,
    build_strategy,
    load_recent_orchestration_runs,
    run_orchestration,
)
from revenue_os.services.orchestration_runtime import backend_status

router = APIRouter(prefix="/orchestration", tags=["orchestration"])


class GTMPlanRequest(BaseModel):
    backend: str = Field(default="hermes", description="hermes | openclaw")
    brand: str = Field(default="workcrew", description="workcrew | hirestack | founder")
    topic: str
    keyword: str
    geo_target: str = ""
    funnel_stage: str = "consideration"
    audience: str = "recruiters and hiring managers"
    channels: list[str] = Field(default_factory=lambda: ["blog", "linkedin", "instagram", "youtube", "email", "whatsapp"])


class GTMRunRequest(GTMPlanRequest):
    run_content: bool = True
    run_seo: bool = True
    run_email: bool = True
    run_whatsapp: bool = True
    run_prospecting: bool = True
    run_voice_qualification: bool = True
    run_meeting_booking: bool = True


@router.get("/backends")
def orchestration_backends() -> dict:
    return {
        "supported": ["hermes", "openclaw"],
        "configured": backend_status(),
    }


@router.post("/plan")
def orchestration_plan(body: GTMPlanRequest) -> dict:
    req = GTMOrchestrationRequest(
        backend=body.backend,
        brand=body.brand,
        topic=body.topic,
        keyword=body.keyword,
        geo_target=body.geo_target,
        funnel_stage=body.funnel_stage,
        audience=body.audience,
        channels=body.channels,
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
        "plan": build_strategy(req),
    }


@router.post("/run")
def orchestration_run(body: GTMRunRequest) -> dict:
    req = GTMOrchestrationRequest(
        backend=body.backend,
        brand=body.brand,
        topic=body.topic,
        keyword=body.keyword,
        geo_target=body.geo_target,
        funnel_stage=body.funnel_stage,
        audience=body.audience,
        channels=body.channels,
        run_content=body.run_content,
        run_seo=body.run_seo,
        run_email=body.run_email,
        run_whatsapp=body.run_whatsapp,
        run_prospecting=body.run_prospecting,
        run_voice_qualification=body.run_voice_qualification,
        run_meeting_booking=body.run_meeting_booking,
    )
    return {
        "ok": True,
        "result": run_orchestration(req),
    }


@router.get("/logs")
def orchestration_logs(limit: int = 20) -> dict:
    return {
        "ok": True,
        "runs": load_recent_orchestration_runs(limit=max(1, min(limit, 100))),
    }
