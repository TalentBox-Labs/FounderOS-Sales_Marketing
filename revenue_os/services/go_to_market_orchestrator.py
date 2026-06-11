from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

from revenue_os.integrations.n8n import trigger_workflow
from revenue_os.services.orchestration_runtime import (
    TaskRequest,
    get_backend,
)


@dataclass
class GTMOrchestrationRequest:
    backend: str
    brand: str
    topic: str
    keyword: str
    geo_target: str = ""
    funnel_stage: str = "consideration"
    audience: str = "recruiters and hiring managers"
    channels: list[str] | None = None
    run_content: bool = True
    run_seo: bool = True
    run_email: bool = True
    run_whatsapp: bool = True
    run_prospecting: bool = True
    run_voice_qualification: bool = True
    run_meeting_booking: bool = True


def build_strategy(req: GTMOrchestrationRequest) -> dict[str, Any]:
    """Return a deterministic, execution-ready strategy plan."""
    channels = req.channels or ["blog", "linkedin", "instagram", "youtube", "email", "whatsapp"]
    return {
        "brand": req.brand,
        "topic": req.topic,
        "keyword": req.keyword,
        "geo_target": req.geo_target or "global",
        "funnel_stage": req.funnel_stage,
        "audience": req.audience,
        "channels": channels,
        "playbooks": {
            "content_strategy": {
                "objective": "Generate SEO/GEO/AEO long-form article and social derivatives",
                "kpis": ["organic_sessions", "impressions", "ai_citations", "ctr"],
            },
            "email_marketing": {
                "objective": "Drive qualified demo traffic via segmented sequences",
                "kpis": ["open_rate", "reply_rate", "meeting_booked_rate"],
            },
            "whatsapp_marketing": {
                "objective": "Re-engage warm leads with high-intent nudges",
                "kpis": ["response_rate", "meeting_conversion"],
            },
            "lead_prospecting": {
                "objective": "Score and prioritise ICP-fit accounts",
                "kpis": ["qualified_leads", "sql_rate"],
            },
            "voice_qualification": {
                "objective": "Automate pre-qualification and route to booking",
                "kpis": ["qualified_calls", "handoff_rate"],
            },
            "meeting_booking": {
                "objective": "Book meetings only when qualification threshold met",
                "kpis": ["booked_meetings", "show_rate"],
            },
        },
    }


def _run_marketing_crew(req: GTMOrchestrationRequest) -> dict[str, Any]:
    cmd = [
        sys.executable,
        "-m",
        "src.marketing_crew",
        "--brand",
        req.brand,
        "--topic",
        req.topic,
        "--keyword",
        req.keyword,
        "--funnel",
        req.funnel_stage,
    ]
    if req.geo_target:
        cmd += ["--geo", req.geo_target]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
    return {
        "ok": proc.returncode == 0,
        "stdout_tail": (proc.stdout or "")[-4000:],
        "stderr_tail": (proc.stderr or "")[-4000:],
        "returncode": proc.returncode,
    }


def _trigger_n8n(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Fire optional n8n automation workflow."""
    res = trigger_workflow(name, payload)
    return {
        "workflow": name,
        "triggered": res is not None,
        "result": res,
    }


def run_orchestration(req: GTMOrchestrationRequest) -> dict[str, Any]:
    backend = get_backend(req.backend)
    strategy = build_strategy(req)

    results: dict[str, Any] = {
        "backend": req.backend,
        "backend_configured": backend.is_configured(),
        "strategy": strategy,
        "executions": {},
    }

    shared_payload = {
        "brand": req.brand,
        "topic": req.topic,
        "keyword": req.keyword,
        "geo_target": req.geo_target or "global",
        "funnel_stage": req.funnel_stage,
        "audience": req.audience,
    }

    if req.run_content:
        # 1) Local marketing generation (primary path)
        results["executions"]["content_local"] = _run_marketing_crew(req)

        # 2) Optional external backend coordination
        task = TaskRequest(
            name="content_strategy_and_distribution",
            objective="Generate blog + social + metadata assets for SEO/GEO/AEO",
            payload=shared_payload,
        )
        results["executions"]["content_backend"] = backend.run_task(task)

    if req.run_seo:
        task = TaskRequest(
            name="seo_aeo_optimization",
            objective="Produce title/meta/schema and improve answer-engine citation readiness",
            payload=shared_payload,
        )
        results["executions"]["seo_backend"] = backend.run_task(task)

    if req.run_email:
        task = TaskRequest(
            name="email_campaign",
            objective="Generate segmented email sequence for TOFU/MOFU/BOFU and push to automation",
            payload=shared_payload,
        )
        results["executions"]["email_backend"] = backend.run_task(task)
        results["executions"]["email_n8n"] = _trigger_n8n("email-campaign", shared_payload)

    if req.run_whatsapp:
        task = TaskRequest(
            name="whatsapp_campaign",
            objective="Generate WhatsApp outreach messages and drip cadence for warm leads",
            payload=shared_payload,
        )
        results["executions"]["whatsapp_backend"] = backend.run_task(task)
        results["executions"]["whatsapp_n8n"] = _trigger_n8n("whatsapp-campaign", shared_payload)

    if req.run_prospecting:
        task = TaskRequest(
            name="lead_prospecting",
            objective="Find ICP-fit leads, score intent, prioritise outreach",
            payload=shared_payload,
        )
        results["executions"]["prospecting_backend"] = backend.run_task(task)
        results["executions"]["prospecting_n8n"] = _trigger_n8n("lead-prospecting", shared_payload)

    if req.run_voice_qualification:
        task = TaskRequest(
            name="voice_agent_qualification",
            objective="Run voice qualification script and classify lead quality",
            payload={
                **shared_payload,
                "voice_provider": os.getenv("VOICE_AGENT_PROVIDER", "vapi"),
            },
        )
        results["executions"]["voice_backend"] = backend.run_task(task)
        results["executions"]["voice_n8n"] = _trigger_n8n("voice-qualification", shared_payload)

    if req.run_meeting_booking:
        task = TaskRequest(
            name="meeting_booking",
            objective="Book meeting only for leads above qualification threshold",
            payload={
                **shared_payload,
                "calendar_provider": os.getenv("MEETING_PROVIDER", "calendly"),
            },
        )
        results["executions"]["booking_backend"] = backend.run_task(task)
        results["executions"]["booking_n8n"] = _trigger_n8n("meeting-booking", shared_payload)

    return results
