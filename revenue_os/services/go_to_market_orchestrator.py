from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

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


def _audit_dir() -> Path:
    root = os.getenv("ORCHESTRATION_AUDIT_DIR", "").strip()
    if root:
        return Path(root)
    return Path("output") / "marketing" / "orchestration_audit"


def _event_ok(payload: Any) -> bool | None:
    if not isinstance(payload, dict):
        return None
    if "ok" in payload and isinstance(payload["ok"], bool):
        return payload["ok"]
    if "status" in payload and isinstance(payload["status"], str):
        return payload["status"].lower() == "ok"
    if "triggered" in payload and isinstance(payload["triggered"], bool):
        return payload["triggered"]
    return None


def _channel_from_key(key: str) -> str:
    mapping = {
        "content": "content",
        "seo": "seo",
        "email": "email",
        "whatsapp": "whatsapp",
        "prospecting": "prospecting",
        "voice": "voice_qualification",
        "booking": "meeting_booking",
    }
    prefix = (key or "").split("_", 1)[0]
    return mapping.get(prefix, prefix or "unknown")


def _persist_audit(req: GTMOrchestrationRequest, results: dict[str, Any]) -> dict[str, Any]:
    run_id = uuid4().hex
    ts = datetime.now(timezone.utc).isoformat()
    audit_dir = _audit_dir()
    audit_dir.mkdir(parents=True, exist_ok=True)

    executions = results.get("executions", {})
    events = []
    for key, payload in executions.items():
        events.append(
            {
                "run_id": run_id,
                "timestamp": ts,
                "channel": _channel_from_key(key),
                "step": key,
                "ok": _event_ok(payload),
                "payload": payload,
            }
        )

    run_record = {
        "run_id": run_id,
        "timestamp": ts,
        "backend": req.backend,
        "brand": req.brand,
        "topic": req.topic,
        "keyword": req.keyword,
        "geo_target": req.geo_target or "global",
        "funnel_stage": req.funnel_stage,
        "audience": req.audience,
        "results": results,
        "events": events,
    }

    run_file = audit_dir / f"{run_id}.json"
    runs_jsonl = audit_dir / "runs.jsonl"
    channels_jsonl = audit_dir / "channels.jsonl"

    run_file.write_text(json.dumps(run_record, ensure_ascii=True, indent=2), encoding="utf-8")
    with runs_jsonl.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "run_id": run_id,
            "timestamp": ts,
            "backend": req.backend,
            "brand": req.brand,
            "keyword": req.keyword,
            "geo_target": req.geo_target or "global",
            "funnel_stage": req.funnel_stage,
            "event_count": len(events),
            "run_file": str(run_file),
        }, ensure_ascii=True) + "\n")
    with channels_jsonl.open("a", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev, ensure_ascii=True) + "\n")

    return {
        "run_id": run_id,
        "timestamp": ts,
        "run_file": str(run_file),
        "events_file": str(channels_jsonl),
    }


def load_recent_orchestration_runs(limit: int = 20) -> list[dict[str, Any]]:
    runs_jsonl = _audit_dir() / "runs.jsonl"
    if not runs_jsonl.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in runs_jsonl.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    rows.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return rows[:limit]


def load_orchestration_run(run_id: str) -> dict[str, Any] | None:
    run_id = (run_id or "").strip()
    if not run_id:
        return None
    run_file = _audit_dir() / f"{run_id}.json"
    if not run_file.is_file():
        return None
    try:
        return json.loads(run_file.read_text(encoding="utf-8"))
    except Exception:
        return None


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

    try:
        results["audit"] = _persist_audit(req, results)
    except Exception as exc:
        results["audit"] = {
            "error": str(exc),
        }

    return results
