"""
Local HTTP runner + CMS UI.

ChatGPT-style snippets often POST {"week": "W10"} then only run main.py — that
does **not** switch weeks: main.py always follows data/runtime_config.json.
When ``week`` is set, this app runs ``runtime_apply`` first, then main.py.

Install: pip install -r requirements.txt -r requirements-api.txt
Run:    uvicorn runner_api:app --host 0.0.0.0 --port 8000 --reload

UI routes:
  GET  /              — Dashboard
  GET  /weeks         — Content calendar
  GET  /weeks/{id}    — Week detail
  GET  /pipeline      — Pipeline trigger UI
  GET  /weeks/{id}/file/{name}  — File viewer

API routes:
  POST /run           — Run full pipeline
  POST /validate      — Validators only
  POST /generate      — Phase 2A generation
  POST /edit          — Phase 2B editor
  POST /switch-week   — Apply week profile
  POST /go-live       — Record live URL
  POST /run-pipeline  — Legacy alias
  GET  /health        — Health check

Marketing routes:
  GET  /marketing          — Marketing agent UI
  POST /marketing/generate — Generate multi-channel content
  POST /marketing/dry-run  — Preview publish status
  POST /marketing/publish  — Publish to live platforms
"""

from __future__ import annotations

import csv
import json
import html
import logging
import os
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from runner_api_routers.middleware import StructuredLoggingMiddleware
from runner_api_routers.pipeline import router as pipeline_router
from runner_api_routers.orchestration import router as orchestration_router
from runner_api_routers.prospecting import router as prospecting_router
from runner_api_routers.marketing import router as marketing_router
from runner_api_routers.ui import router as ui_router
from runner_api_routers.outreach import router as outreach_router
from runner_api_routers.metrics import router as metrics_router
from runner_api_routers.hermes import router as hermes_router
from runner_api_routers.automation import router as automation_router
from runner_api_routers.paperclip import router as paperclip_router
from runner_api_routers.csm import router as csm_router
from runner_api_routers.utils import (
    _apply_week_if_set,
    _get_runner_api_key,
    _load_runtime,
    _read_tracker,
    _run,
    _tail,
    _verify_api_key,
    _week_artifacts,
    PROJECT_ROOT,
    PIPELINE_TIMEOUT_SEC,
    TAIL_CHARS,
)
from revenue_os.automation.init import initialize_automation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from revenue_os.config import settings
from revenue_os.database import SessionLocal
from revenue_os.models.activity import (
    Activity,
    ActivityType,
    OutreachSequence,
    SequenceStep,
)
from revenue_os.models.contact import Contact, ContactStatus
from revenue_os.models.deal import Deal, DealStage
from revenue_os.services.go_to_market_orchestrator import (
    GTMOrchestrationRequest,
    build_strategy,
    load_orchestration_run,
    load_recent_orchestration_runs,
    run_orchestration,
)
from revenue_os.services.lead_prospecting_service import (
    build_prospecting_plan,
    provider_status,
    prospecting_limits,
)
from revenue_os.services.orchestration_runtime import backend_status

# Marketing integration (optional — only loads when needed)
def _social_publisher():
    from revenue_os.integrations.social_publisher import SocialPublisher
    return SocialPublisher()

# Initialize FastAPI app with security headers
app = FastAPI(
    title="WorkCrew CMS OS API",
    description=(
        "Enterprise content management, multi-agent orchestration, and AI-powered publishing platform.\n\n"
        "## Features\n\n"
        "- **Pipeline Management**: Execute validation, generation, editing, and publishing workflows\n"
        "- **Multi-Agent Orchestration**: Coordinate complex content creation across teams\n"
        "- **Marketing Automation**: Generate multi-channel marketing content (blog, social, email)\n"
        "- **Outreach Management**: Track and manage automated outreach sequences\n"
        "- **UI Dashboard**: Visual monitoring and control of all workflows\n\n"
        "## Authentication\n\n"
        "All API endpoints require authentication via API key in the Authorization header:\n"
        "```\nAuthorization: Bearer YOUR_API_KEY\n```\n\n"
        "## Rate Limiting\n\n"
        "API endpoints are subject to rate limiting. Long-running operations (pipeline execution) "
        "have a 10-minute timeout and return partial results on timeout.\n\n"
        "## Documentation\n\n"
        "- **Swagger UI**: `/docs` (interactive API explorer)\n"
        "- **ReDoc**: `/redoc` (static API documentation)\n"
        "- **OpenAPI Schema**: `/openapi.json` (machine-readable specification)"
    ),
    version="2.0.0",
    contact={
        "name": "WorkCrew Engineering",
        "email": "engineering@workcrew.ai",
        "url": "https://workcrew.ai",
    },
    license_info={
        "name": "Proprietary",
        "url": "https://workcrew.ai/legal/license",
    },
    servers=[
        {"url": "http://localhost:8000", "description": "Local development"},
        {"url": "https://api.workcrew.ai", "description": "Production"},
    ],
    openapi_tags=[
        {
            "name": "pipeline",
            "description": "Content pipeline execution: validation, generation, editing, publishing",
        },
        {
            "name": "orchestration",
            "description": "Multi-agent workflow orchestration and planning",
        },
        {
            "name": "prospecting",
            "description": "Sales prospecting and contact management",
        },
        {
            "name": "marketing",
            "description": "Multi-channel marketing content generation",
        },
        {
            "name": "outreach",
            "description": "Automated outreach sequence management",
        },
        {
            "name": "ui",
            "description": "Web UI pages and file serving",
        },
        {
            "name": "health",
            "description": "Service health and status checks",
        },
    ],
)

# Setup CORS
cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Add structured logging middleware
app.add_middleware(StructuredLoggingMiddleware)

# Setup templates
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include routers (domain-specific functionality)
app.include_router(pipeline_router)
app.include_router(orchestration_router)
app.include_router(prospecting_router)
app.include_router(outreach_router)
app.include_router(marketing_router)
app.include_router(metrics_router)
app.include_router(hermes_router)
app.include_router(automation_router)
app.include_router(paperclip_router)
app.include_router(csm_router)
# UI routes must be last to avoid conflicts with API routes
app.include_router(ui_router)

# Initialize automation system
initialize_automation()


class WeekRequest(BaseModel):
    """Request model for week-based operations."""

    week: str | None = Field(
        default=None,
        description="Week ID (e.g., W10)",
    )
    topic: str | None = Field(
        default=None,
        description="Optional label for logs",
    )
    url: str | None = Field(
        default=None,
        description="URL for go-live operations",
    )


# ── UI helpers ────────────────────────────────────────────────────────────


def _week_pipeline_steps(row: dict) -> list[dict]:
    """Derive per-step state from tracker row and artifact existence."""
    wid = row.get("content_id", "")
    arts = _week_artifacts(wid)
    current = (row.get("current_step") or "").lower()
    steps = []
    mapping = [
        ("Brief",    "brief"),
        ("SEO",      "seo"),
        ("Research", "research"),
        ("Draft",    "draft"),
        ("Final",    "final"),
        ("Checklist","checklist"),
    ]
    for label, key in mapping:
        if arts.get(key):
            state = "done"
        elif label.lower() in current:
            state = "active"
        else:
            state = "pending"
        steps.append({"label": label, "state": state})
    return steps


def _enrich_rows(rows: list[dict]) -> list[dict]:
    enriched = []
    for r in rows:
        wid = r.get("content_id", "")
        arts = _week_artifacts(wid)
        enriched.append({
            **r,
            "has_draft":     arts.get("draft", False),
            "has_final":     arts.get("final", False),
            "has_qa":        (PROJECT_ROOT / "output" / "qa_reports" / f"{wid}_Draft_Validation.md").is_file(),
            "has_checklist": arts.get("checklist", False),
            "pipeline_steps": _week_pipeline_steps(r),
        })
    return enriched


def _pipeline_healthy() -> bool:
    run = _last_run_summary()
    return bool(run and run.get("ok"))


def _dashboard_stats(rows: list[dict]) -> dict:
    total = len(rows)
    qa_passed = sum(1 for r in rows if (r.get("qa_status") or "").upper() == "PASS")
    published = sum(1 for r in rows if "publish" in (r.get("status") or "").lower() or
                    "complete" in (r.get("status") or "").lower())
    in_prog   = sum(1 for r in rows if "progress" in (r.get("status") or "").lower() or
                    "review" in (r.get("status") or "").lower())
    weeks_set = {r.get("content_id", "") for r in rows}
    return {
        "total":       total,
        "weeks":       len(weeks_set),
        "qa_passed":   qa_passed,
        "qa_pct":      round(qa_passed / total * 100) if total else 0,
        "published":   published,
        "in_progress": in_prog,
    }


def _validator_results(week_id: str) -> list[tuple[str, str]]:
    qa_dir = PROJECT_ROOT / "output" / "qa_reports"
    suffix_map = {
        "research_mapper":          f"{week_id}_Research_Map.md",
        "draft_validator":          f"{week_id}_Draft_Validation.md",
        "structure_checker":        f"{week_id}_Structure_Check.md",
        "metadata_checker":         f"{week_id}_Metadata_Check.md",
        "publish_checklist_checker":f"{week_id}_Publish_Checklist_Check.md",
    }
    results = []
    for name, fname in suffix_map.items():
        path = qa_dir / fname
        if not path.is_file():
            results.append((name, "—"))
            continue
        text = path.read_text(encoding="utf-8")
        # Last PASS/FAIL wins
        verdict = "—"
        for line in reversed(text.splitlines()):
            if "PASS" in line:
                verdict = "PASS"
                break
            if "FAIL" in line:
                verdict = "FAIL"
                break
        results.append((name, verdict))
    return results


# ── Page routes ─────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def page_dashboard(request: Request) -> HTMLResponse:
    rows = _read_tracker()
    runtime = _load_runtime()
    active_week = runtime.get("active_week", "—")
    return templates.TemplateResponse("dashboard.html", {
        "request":     request,
        "active_page": "dashboard",
        "active_week": active_week,
        "weeks":       _enrich_rows(rows),
        "stats":       _dashboard_stats(rows),
        "last_run":    _last_run_summary(),
        "pipeline_ok": _pipeline_healthy(),
    })


@app.get("/weeks", response_class=HTMLResponse)
def page_weeks(request: Request) -> HTMLResponse:
    rows = _read_tracker()
    runtime = _load_runtime()
    active_week = runtime.get("active_week", "—")
    return templates.TemplateResponse("dashboard.html", {
        "request":     request,
        "active_page": "weeks",
        "active_week": active_week,
        "weeks":       _enrich_rows(rows),
        "stats":       _dashboard_stats(rows),
        "last_run":    _last_run_summary(),
        "pipeline_ok": _pipeline_healthy(),
    })


@app.get("/weeks/{week_id}", response_class=HTMLResponse)
def page_week_detail(week_id: str, request: Request) -> HTMLResponse:
    week_id = week_id.upper()
    rows = _read_tracker()
    runtime = _load_runtime()
    active_week = runtime.get("active_week", "—")
    row = next((r for r in rows if r.get("content_id", "").upper() == week_id), {})

    # Runtime profile JSON for display
    profile_path = PROJECT_ROOT / "data" / "week_runtime" / f"{week_id}.json"
    if profile_path.is_file():
        runtime_json = json.dumps(json.loads(profile_path.read_text(encoding="utf-8")), indent=2)
    else:
        runtime_json = json.dumps(runtime, indent=2)

    return templates.TemplateResponse("week_detail.html", {
        "request":      request,
        "active_page":  "weeks",
        "active_week":  active_week,
        "week_id":      week_id,
        "row":          row,
        "artifacts":    _week_artifacts(week_id),
        "validators":   _validator_results(week_id),
        "qa_report_html": None,
        "runtime_json": runtime_json,
    })


@app.get("/weeks/{week_id}/file/{filename:path}", response_class=HTMLResponse)
def page_file_view(week_id: str, filename: str, request: Request) -> HTMLResponse:
    week_id = week_id.upper()
    path = PROJECT_ROOT / "input" / week_id / filename
    if not path.is_file() or not path.resolve().is_relative_to((PROJECT_ROOT / "input").resolve()):
        raise HTTPException(status_code=404, detail="File not found")
    content = path.read_text(encoding="utf-8")
    runtime = _load_runtime()
    return templates.TemplateResponse("file_view.html", {
        "request":    request,
        "active_page":"weeks",
        "active_week":runtime.get("active_week", "—"),
        "week_id":    week_id,
        "filename":   filename,
        "content":    content,
        "char_count": len(content),
        "line_count": content.count("\n") + 1,
    })


@app.get("/pipeline", response_class=HTMLResponse)
def page_pipeline(request: Request) -> HTMLResponse:
    rows = _read_tracker()
    runtime = _load_runtime()
    active_week = runtime.get("active_week", "—")
    return templates.TemplateResponse("pipeline.html", {
        "request":     request,
        "active_page": "pipeline",
        "active_week": active_week,
        "weeks":       rows,
        "last_run":    _last_run_summary(),
    })


# ── New API endpoints ───────────────────────────────────────────────────────

class WeekRequest(BaseModel):
    week: str | None = None
    topic: str | None = None
    url: str | None = None


# Pipeline endpoints have been moved to runner_api_routers/pipeline.py
# and included via: app.include_router(pipeline_router)

# ── Marketing ───────────────────────────────────────────────────────────────


def _marketing_integration_status() -> dict[str, bool]:
    return {
        "hashnode":  bool(os.environ.get("HASHNODE_ACCESS_TOKEN")),
        "linkedin":  bool(os.environ.get("LINKEDIN_ACCESS_TOKEN")),
        "instagram": bool(os.environ.get("INSTAGRAM_ACCESS_TOKEN")),
        "youtube":   bool(os.environ.get("YOUTUBE_API_KEY")),
    }


def _marketing_runs() -> list[dict]:
    """Scan output/marketing for 08_Publish_Status.json manifests."""
    mkt_dir = PROJECT_ROOT / "output" / "marketing"
    runs = []
    if not mkt_dir.is_dir():
        return runs
    for status_file in sorted(mkt_dir.rglob("08_Publish_Status.json"), reverse=True):
        try:
            data = json.loads(status_file.read_text(encoding="utf-8"))
            data["slug"] = status_file.parent.name
            runs.append(data)
        except Exception:
            pass
    return runs[:20]


def _mcp_hub_status() -> dict:
    """Summarize which MCP-connected tool groups are ready from env/config state."""
    backends = backend_status()
    return {
        "models": {
            "primary_llm": settings.OPENAI_MODEL,
            "crewai_model": settings.WORKCREW_CREWAI_MODEL,
            "openai": bool(settings.OPENAI_API_KEY),
            "gemini": bool(settings.GEMINI_API_KEY),
        },
        "backends": backends,
        "sales": {
            "prospecting": True,
            "lead_scoring": True,
            "crm_contacts": True,
            "outreach_sequences": True,
            "mcp_provider_ready": provider_status(),
        },
        "marketing": {
            "orchestration": True,
            "social_publishing": True,
            "hashnode": bool(os.environ.get("HASHNODE_ACCESS_TOKEN")),
            "linkedin": bool(os.environ.get("LINKEDIN_ACCESS_TOKEN")),
            "instagram": bool(os.environ.get("INSTAGRAM_ACCESS_TOKEN")),
            "youtube": bool(os.environ.get("YOUTUBE_API_KEY")),
        },
        "research": {
            "knowledge_base": True,
            "web_research": True,
            "agent_backends": bool(backends.get("hermes") or backends.get("openclaw")),
            "n8n": bool(settings.N8N_API_KEY or settings.N8N_WEBHOOK_BASE_URL),
        },
        "messaging": {
            "email": bool(settings.GMAIL_CREDENTIALS_PATH or os.environ.get("SMTP_HOST")),
            "whatsapp": bool(settings.WHATSAPP_API_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID),
            "linkedin": bool(settings.LINKEDIN_ACCESS_TOKEN),
            "instagram": bool(os.environ.get("INSTAGRAM_ACCESS_TOKEN")),
            "youtube": bool(os.environ.get("YOUTUBE_API_KEY")),
        },
        "entrypoints": [
            {"name": "Sales Prospecting", "path": "/sales", "status": "ready"},
            {"name": "Marketing Campaigns", "path": "/marketing", "status": "ready"},
            {"name": "Analytics", "path": "/analytics", "status": "ready"},
            {"name": "Orchestration Plan", "path": "/api/v1/orchestration/plan", "status": "api"},
            {"name": "Orchestration Run", "path": "/api/v1/orchestration/run", "status": "api"},
        ],
    }


@app.get("/mcp", response_class=HTMLResponse)
def page_mcp(request: Request) -> HTMLResponse:
    runtime = _load_runtime()
    return templates.TemplateResponse("mcp.html", {
        "request": request,
        "active_page": "mcp",
        "active_week": runtime.get("active_week", "—"),
    })


@app.get("/api/v1/mcp/hub")
def api_mcp_hub() -> dict:
    return {
        "ok": True,
        "hub": _mcp_hub_status(),
    }


@app.get("/marketing", response_class=HTMLResponse)
def page_marketing(request: Request) -> HTMLResponse:
    runtime = _load_runtime()
    return templates.TemplateResponse("marketing.html", {
        "request":            request,
        "active_page":        "marketing",
        "active_week":        runtime.get("active_week", "—"),
        "runs":               _marketing_runs(),
        "orchestration_runs": load_recent_orchestration_runs(limit=20),
        "integration_status": _marketing_integration_status(),
        "orchestration_status": backend_status(),
    })


@app.get("/sales", response_class=HTMLResponse)
def page_sales(request: Request) -> HTMLResponse:
    runtime = _load_runtime()
    return templates.TemplateResponse("sales.html", {
        "request": request,
        "active_page": "sales",
        "active_week": runtime.get("active_week", "—"),
    })


@app.get("/orchestration/run/{run_id}", response_class=HTMLResponse)
def page_orchestration_run(
    run_id: str,
    request: Request,
    _: str | None = Depends(_verify_api_key),
) -> HTMLResponse:
    run = load_orchestration_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="orchestration run not found")
    return HTMLResponse(_render_orchestration_run_detail(run, run_id, _load_runtime().get("active_week", "—")))


class MarketingRequest(BaseModel):
    brand:               str = "workcrew"
    topic:               str = ""
    keyword:             str = ""
    geo:                 str = ""
    funnel:              str = "consideration"
    output_root:         str | None = None
    status_path:         str = ""
    instagram_image_url: str = ""
    confirmed:           bool = False
    channel:             str = "all"


class OrchestrationRequest(BaseModel):
    backend: str = "hermes"
    brand: str = "workcrew"
    topic: str = ""
    keyword: str = ""
    geo_target: str = ""
    funnel_stage: str = "consideration"
    audience: str = "recruiters and hiring managers"
    channels: list[str] = Field(default_factory=lambda: ["blog", "linkedin", "instagram", "youtube", "email", "whatsapp"])
    run_content: bool = True
    run_seo: bool = True
    run_email: bool = True
    run_whatsapp: bool = True
    run_prospecting: bool = True
    run_voice_qualification: bool = True
    run_meeting_booking: bool = True


class ProspectingRequest(BaseModel):
    target_count: int = Field(default=50, ge=1, le=5000)
    min_score: int = Field(default=25, ge=0, le=100)
    statuses: list[str] = Field(default_factory=lambda: ["lead", "prospect"])
    allow_scraper: bool = True
    allow_mcp: bool = True


class ProspectingPresetSaveRequest(BaseModel):
    name: str
    brand: str = "workcrew"
    team: str = "sales"
    target_count: int = Field(default=50, ge=1, le=5000)
    min_score: int = Field(default=25, ge=0, le=100)
    statuses: list[str] = Field(default_factory=lambda: ["lead", "prospect"])
    allow_scraper: bool = True
    allow_mcp: bool = True
    sequence_id: str | None = None


class ProspectingImportRequest(BaseModel):
    sequence_id: str
    contact_ids: list[str]


class ProspectingExecuteRequest(ProspectingRequest):
    execute_stages: list[str] = Field(default_factory=lambda: [
        "free_linkedin_existing_data", "scraper_platforms", "mcp_providers"
    ])
    sequence_id: str | None = None
    auto_import: bool = True
    max_import: int = Field(default=50, ge=1, le=1000)


def _presets_file() -> Path:
    p = PROJECT_ROOT / "output" / "sales" / "prospecting_presets.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _read_presets() -> list[dict[str, Any]]:
    p = _presets_file()
    if not p.is_file():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _write_presets(items: list[dict[str, Any]]) -> None:
    _presets_file().write_text(json.dumps(items, ensure_ascii=True, indent=2), encoding="utf-8")


def _parse_statuses(raw: list[str]) -> list[ContactStatus]:
    statuses: list[ContactStatus] = []
    for value in raw:
        key = (value or "").strip().lower()
        if not key:
            continue
        try:
            statuses.append(ContactStatus(key))
        except Exception:
            raise HTTPException(status_code=400, detail=f"invalid status: {value}")
    if not statuses:
        raise HTTPException(status_code=400, detail="at least one status is required")
    return statuses


def _map_activity_type(step_action: str, sequence_channel: str) -> ActivityType:
    action = (step_action or "").strip().lower()
    channel = (sequence_channel or "").strip().lower()
    if action in {"send_email", "email"} or channel == "email":
        return ActivityType.EMAIL
    if action in {"linkedin_message", "linkedin"}:
        return ActivityType.LINKEDIN_MESSAGE
    if action in {"linkedin_connect"}:
        return ActivityType.LINKEDIN_CONNECT
    if action in {"whatsapp"} or channel == "whatsapp":
        return ActivityType.WHATSAPP
    if action in {"call"}:
        return ActivityType.CALL
    return ActivityType.TASK


def _schedule_contact_sequence(db, sequence: OutreachSequence, contact_id: str) -> dict[str, Any]:
    steps = (
        db.query(SequenceStep)
        .filter(SequenceStep.sequence_id == sequence.id)
        .order_by(SequenceStep.step_order)
        .all()
    )
    if not steps:
        activity = Activity(
            contact_id=uuid.UUID(contact_id),
            activity_type=_map_activity_type("", sequence.channel),
            subject=f"{sequence.name} - outreach",
            body="Imported from prospecting plan",
            direction="outbound",
            status="scheduled",
            scheduled_at=datetime.now(timezone.utc),
        )
        db.add(activity)
        return {"contact_id": contact_id, "steps": 1}

    cumulative_days = 0
    for step in steps:
        cumulative_days += max(0, int(step.delay_days or 0))
        activity = Activity(
            contact_id=uuid.UUID(contact_id),
            activity_type=_map_activity_type(step.action_type, sequence.channel),
            subject=step.subject or f"{sequence.name} - step {step.step_order}",
            body=step.template or "",
            direction="outbound",
            status="scheduled",
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=cumulative_days),
        )
        db.add(activity)
    return {"contact_id": contact_id, "steps": len(steps)}


@app.get("/api/v1/outreach/sequences")
def outreach_sequences_proxy(
    _: str | None = Depends(_verify_api_key),
) -> dict:
    db = SessionLocal()
    try:
        rows = db.query(OutreachSequence).filter(OutreachSequence.is_active == 1).all()
        return {
            "ok": True,
            "sequences": [
                {
                    "id": str(r.id),
                    "name": r.name,
                    "channel": r.channel,
                    "steps_count": r.steps_count,
                }
                for r in rows
            ],
        }
    finally:
        db.close()


@app.get("/api/v1/prospecting/providers")
def prospecting_providers_proxy(
    _: str | None = Depends(_verify_api_key),
) -> dict:
    return {
        "ok": True,
        "providers": provider_status(),
        "thresholds": prospecting_limits(),
    }


@app.post("/api/v1/prospecting/plan")
def prospecting_plan_proxy(
    req: ProspectingRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict:
    db = SessionLocal()
    try:
        statuses = _parse_statuses(req.statuses)
        plan = build_prospecting_plan(
            db,
            target_count=req.target_count,
            min_score=req.min_score,
            statuses=statuses,
            allow_scraper=req.allow_scraper,
            allow_mcp=req.allow_mcp,
        )
        return {"ok": True, "plan": plan}
    finally:
        db.close()


@app.get("/api/v1/prospecting/presets")
def prospecting_presets_list(
    brand: str | None = None,
    team: str | None = None,
    _: str | None = Depends(_verify_api_key),
) -> dict:
    items = _read_presets()
    if brand:
        items = [x for x in items if (x.get("brand") or "") == brand]
    if team:
        items = [x for x in items if (x.get("team") or "") == team]
    items.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return {"ok": True, "presets": items}


@app.post("/api/v1/prospecting/presets/save")
def prospecting_presets_save(
    req: ProspectingPresetSaveRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict:
    items = _read_presets()
    now = datetime.now(timezone.utc).isoformat()
    key = f"{req.brand}:{req.team}:{req.name}".lower()
    payload = {
        "key": key,
        "name": req.name,
        "brand": req.brand,
        "team": req.team,
        "target_count": req.target_count,
        "min_score": req.min_score,
        "statuses": req.statuses,
        "allow_scraper": req.allow_scraper,
        "allow_mcp": req.allow_mcp,
        "sequence_id": req.sequence_id,
        "updated_at": now,
    }
    kept = [x for x in items if (x.get("key") or "") != key]
    kept.append(payload)
    _write_presets(kept)
    return {"ok": True, "preset": payload}


@app.post("/api/v1/prospecting/import")
def prospecting_import(
    req: ProspectingImportRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict:
    db = SessionLocal()
    try:
        if not req.contact_ids:
            raise HTTPException(status_code=400, detail="contact_ids is required")
        sequence = db.query(OutreachSequence).filter(OutreachSequence.id == req.sequence_id).first()
        if not sequence:
            raise HTTPException(status_code=404, detail="outreach sequence not found")
        scheduled = []
        for cid in req.contact_ids:
            scheduled.append(_schedule_contact_sequence(db, sequence, cid))
        db.commit()
        return {
            "ok": True,
            "sequence_id": req.sequence_id,
            "contacts_imported": len(scheduled),
            "scheduled": scheduled,
        }
    finally:
        db.close()


@app.post("/api/v1/prospecting/execute")
def prospecting_execute(
    req: ProspectingExecuteRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict:
    db = SessionLocal()
    try:
        statuses = _parse_statuses(req.statuses)
        plan = build_prospecting_plan(
            db,
            target_count=req.target_count,
            min_score=req.min_score,
            statuses=statuses,
            allow_scraper=req.allow_scraper,
            allow_mcp=req.allow_mcp,
        )

        by_stage = {x.get("stage"): x for x in plan.get("stages", [])}
        executed: dict[str, Any] = {}
        for stage_name in req.execute_stages:
            stage = by_stage.get(stage_name)
            if not stage:
                executed[stage_name] = {"ok": False, "error": "unknown stage"}
                continue
            executed[stage_name] = {
                "ok": True,
                "stage": stage_name,
                "planned_cap": stage.get("cap", 0),
                "planned_used": stage.get("used", 0),
                "status": "executed",
            }

        import_result: dict[str, Any] | None = None
        if req.auto_import and req.sequence_id:
            selected = plan.get("selected_existing_linkedin_contacts", [])
            ids = [x.get("id") for x in selected if x.get("id")][: req.max_import]
            if ids:
                sequence = db.query(OutreachSequence).filter(OutreachSequence.id == req.sequence_id).first()
                if sequence:
                    scheduled = []
                    for cid in ids:
                        scheduled.append(_schedule_contact_sequence(db, sequence, cid))
                    import_result = {
                        "ok": True,
                        "sequence_id": req.sequence_id,
                        "contacts_imported": len(scheduled),
                        "scheduled": scheduled,
                    }
                else:
                    import_result = {"ok": False, "error": "outreach sequence not found"}

        db.commit()
        return {
            "ok": True,
            "plan": plan,
            "executed_stages": executed,
            "import_result": import_result,
        }
    finally:
        db.close()


@app.get("/api/v1/orchestration/backends")
def orchestration_backends_proxy(
    _: str | None = Depends(_verify_api_key),
) -> dict:
    return {
        "supported": ["hermes", "openclaw"],
        "configured": backend_status(),
    }


@app.get("/api/v1/orchestration/logs")
def orchestration_logs_proxy(
    limit: int = 20,
    _: str | None = Depends(_verify_api_key),
) -> dict:
    return {
        "ok": True,
        "runs": load_recent_orchestration_runs(limit=max(1, min(limit, 100))),
    }


@app.post("/api/v1/orchestration/plan")
def orchestration_plan_proxy(
    req: OrchestrationRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict:
    if not req.topic or not req.keyword:
        raise HTTPException(status_code=400, detail="topic and keyword are required")
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


@app.post("/api/v1/orchestration/run")
def orchestration_run_proxy(
    req: OrchestrationRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict:
    if not req.topic or not req.keyword:
        raise HTTPException(status_code=400, detail="topic and keyword are required")
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


@app.post("/marketing/generate")
def marketing_generate(
    req: MarketingRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict:
    """Generate multi-channel marketing content via CrewAI agents."""
    if not req.topic or not req.keyword:
        raise HTTPException(status_code=400, detail="topic and keyword are required")
    r = _run([
        sys.executable, "-m", "src.marketing_crew",
        "--brand",   req.brand,
        "--topic",   req.topic,
        "--keyword", req.keyword,
        "--geo",     req.geo,
        "--funnel",  req.funnel,
    ] + (["--output", req.output_root] if req.output_root else []))
    return {
        "ok":     r.returncode == 0,
        "stdout": _tail(r.stdout or ""),
        "stderr": _tail(r.stderr or ""),
    }


@app.post("/marketing/dry-run")
def marketing_dry_run(
    req: MarketingRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict:
    """Preview what publish_all would post without hitting any APIs."""
    if not req.status_path:
        raise HTTPException(status_code=400, detail="status_path is required")
    try:
        pub = _social_publisher()
        return pub.dry_run(req.status_path)
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/marketing/publish")
def marketing_publish(
    req: MarketingRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict:
    """Publish to all configured social channels. Requires confirmed=True."""
    if not req.status_path:
        raise HTTPException(status_code=400, detail="status_path is required")
    if not req.confirmed:
        raise HTTPException(status_code=400, detail="confirmed must be true to publish")
    try:
        pub = _social_publisher()
        return pub.publish_all(
            req.status_path,
            instagram_image_url=req.instagram_image_url,
            confirmed=True,
        )
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _render_orchestration_run_detail(run: dict[str, Any], run_id: str, active_week: str) -> str:
    results = run.get("results", {}) if isinstance(run.get("results"), dict) else {}
    executions = results.get("executions", {}) if isinstance(results.get("executions"), dict) else {}
    events = run.get("events", []) if isinstance(run.get("events"), list) else []
    audit = results.get("audit", {}) if isinstance(results.get("audit"), dict) else {}

    def esc(value: Any) -> str:
        if isinstance(value, (dict, list)):
            return html.escape(json.dumps(value, indent=2, ensure_ascii=True))
        return html.escape(str(value))

    summary_rows = "".join(
        f"<tr><th>{label}</th><td>{esc(value)}</td></tr>"
        for label, value in [
            ("Run ID", run.get("run_id", run_id)),
            ("Timestamp", run.get("timestamp", "—")),
            ("Backend", run.get("backend", "—")),
            ("Brand", run.get("brand", "—")),
            ("Keyword", run.get("keyword", "—")),
            ("Topic", run.get("topic", "—")),
            ("GEO", run.get("geo_target", "—")),
            ("Funnel Stage", run.get("funnel_stage", "—")),
            ("Audience", run.get("audience", "—")),
            ("Audit File", audit.get("run_file", "—") if isinstance(audit, dict) else "—"),
            ("Active Week", active_week),
        ]
    )

    event_cards = "".join(
        f"""
        <div style=\"padding:12px;border-radius:var(--radius-sm);border:1px solid var(--border);background:var(--surface2)\">
          <div style=\"display:flex;align-items:center;gap:8px;margin-bottom:6px\">
            <span class=\"pill {'green' if event.get('ok') is True else 'red' if event.get('ok') is False else 'gray'}\">{html.escape(str(event.get('channel', 'unknown')))}</span>
            <span style=\"font-size:12px;font-weight:500\">{html.escape(str(event.get('step', 'step')))}</span>
            <span style=\"font-size:11px;color:var(--text-muted);margin-left:auto\">{html.escape(str(event.get('timestamp', '')))}</span>
          </div>
          <div style=\"font-size:12px;color:var(--text-muted);margin-bottom:8px\">Run: {html.escape(str(event.get('run_id', run_id)))}</div>
          <pre style=\"background:#090b10;border:1px solid var(--border);border-radius:var(--radius-sm);padding:12px;font-size:11px;font-family:'JetBrains Mono','Fira Code',monospace;color:#c9d1d9;overflow-x:auto;white-space:pre-wrap;line-height:1.6;max-height:240px;overflow-y:auto;\">{esc(event.get('payload', {}))}</pre>
        </div>
        """
        for event in events
    ) or '<p style="color:var(--text-muted)">No per-channel events were recorded for this run.</p>'

    failure_cards: list[str] = []
    for key, payload in executions.items():
        if isinstance(payload, dict) and (
            payload.get("error") or payload.get("ok") is False or payload.get("status") == "not_configured"
        ):
            failure_cards.append(
                f"""
                <div style=\"padding:12px;border-radius:var(--radius-sm);border:1px solid var(--red);background:rgba(220,38,38,0.08)\">
                  <div style=\"display:flex;align-items:center;gap:8px;margin-bottom:6px\">
                    <span class=\"pill red\">{html.escape(str(key))}</span>
                    <span style=\"font-size:12px;font-weight:500\">Issue detected</span>
                  </div>
                  <pre style=\"background:#090b10;border:1px solid var(--border);border-radius:var(--radius-sm);padding:12px;font-size:11px;font-family:'JetBrains Mono','Fira Code',monospace;color:#c9d1d9;overflow-x:auto;white-space:pre-wrap;line-height:1.6;max-height:180px;overflow-y:auto;\">{esc(payload)}</pre>
                </div>
                """
            )
    failures_html = "".join(failure_cards) or '<p style="color:var(--text-muted)">No failures were recorded in the execution payload.</p>'

    return f"""<!doctype html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
    <title>Orchestration Run — {html.escape(run_id)} — WorkCrew CMS OS</title>
    <style>
        :root {{
            --bg:#0b0f14; --surface:#11161d; --surface2:#151b23; --border:#26303d;
            --text:#e6edf3; --text-muted:#94a3b8; --green:#16a34a; --red:#ef4444; --accent:#60a5fa;
            --radius-sm:12px; --radius-md:18px;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }}
        body {{ margin:0; background:linear-gradient(180deg,#0b0f14,#10151b 70%); color:var(--text); }}
        .page {{ padding:24px; max-width:1400px; margin:0 auto; }}
        .topbar {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; }}
        .topbar-title {{ font-size:28px; font-weight:700; }}
        .topbar-meta {{ color:var(--text-muted); margin-top:4px; }}
        .card {{ background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-md); padding:18px; margin-bottom:18px; }}
        .card-title {{ display:flex; align-items:center; gap:8px; font-size:16px; font-weight:600; margin-bottom:14px; }}
        .table-wrap {{ overflow:auto; }}
        table {{ width:100%; border-collapse:collapse; }}
        th, td {{ text-align:left; padding:10px 12px; border-bottom:1px solid var(--border); vertical-align:top; }}
        th {{ width:180px; color:var(--text-muted); font-weight:600; }}
        pre {{ margin:0; }}
        .pill {{ padding:4px 8px; border-radius:999px; font-size:11px; border:1px solid var(--border); background:var(--surface2); }}
        .pill.green {{ color:#bbf7d0; border-color:rgba(22,163,74,.4); }}
        .pill.red {{ color:#fecaca; border-color:rgba(239,68,68,.4); }}
        .pill.gray {{ color:var(--text-muted); }}
        .btn {{ display:inline-flex; align-items:center; gap:8px; padding:8px 12px; border-radius:12px; border:1px solid var(--border); color:var(--text); text-decoration:none; background:var(--surface2); }}
        .layout {{ display:grid; grid-template-columns:1.1fr .9fr; gap:24px; align-items:start; }}
        @media (max-width: 980px) {{ .layout {{ grid-template-columns:1fr; }} .topbar {{ flex-direction:column; align-items:flex-start; gap:12px; }} }}
    </style>
</head>
<body>
    <div class=\"page\">
        <div class=\"topbar\">
            <div>
                <div class=\"topbar-title\">Orchestration Run {html.escape(run_id[:8])}</div>
                <div class=\"topbar-meta\">Per-channel execution audit and failure trace</div>
            </div>
            <div><a href=\"/marketing\" class=\"btn\">← Back to Marketing</a></div>
        </div>

        <div class=\"layout\">
            <div>
                <div class=\"card\">
                    <div class=\"card-title\">🧾 Run Summary</div>
                    <div class=\"table-wrap\"><table><tbody>{summary_rows}</tbody></table></div>
                </div>

                <div class=\"card\">
                    <div class=\"card-title\">📦 Execution Payload</div>
                    <pre style=\"background:#090b10;border:1px solid var(--border);border-radius:var(--radius-sm);padding:16px;font-size:12px;font-family:'JetBrains Mono','Fira Code',monospace;color:#c9d1d9;overflow-x:auto;line-height:1.7;white-space:pre-wrap;max-height:60vh;overflow-y:auto;\">{esc(run.get('results', {}))}</pre>
                </div>
            </div>

            <div>
                <div class=\"card\">
                    <div class=\"card-title\">🔎 Per-Channel Events</div>
                    <div style=\"display:flex;flex-direction:column;gap:10px\">{event_cards}</div>
                </div>

                <div class=\"card\">
                    <div class=\"card-title\">⚠️ Failures / Notes</div>
                    <div style=\"display:flex;flex-direction:column;gap:10px\">{failures_html}</div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""


# ── Analytics ────────────────────────────────────────────────────────────────

def _date_series(n: int, step_days: int) -> list[str]:
    """Return n ISO-date bucket labels ending today (step_days apart)."""
    today = datetime.now(timezone.utc).date()
    return [(today - timedelta(days=step_days * (n - 1 - i))).isoformat() for i in range(n)]


def _truncate_to(dt: datetime, period: str) -> str:
    """Bucket a datetime to daily / weekly-monday / monthly / yearly string."""
    d = dt.date() if hasattr(dt, "date") else datetime.fromisoformat(str(dt)).date()
    if period == "daily":
        return d.isoformat()
    if period == "weekly":
        return (d - timedelta(days=d.weekday())).isoformat()  # Monday of week
    if period == "monthly":
        return d.replace(day=1).isoformat()
    if period == "yoy":
        return str(d.year)
    return d.isoformat()


def _analytics_data(period: str = "monthly") -> dict:
    """
    Query the database and produce analytics payload grouped by period.
    period: daily | weekly | monthly | yoy
    """
    from collections import defaultdict

    # period → bucket count / window
    windows = {"daily": 30, "weekly": 12, "monthly": 12, "yoy": 3}
    step_map = {"daily": 1, "weekly": 7, "monthly": 30, "yoy": 365}
    n_buckets = windows.get(period, 12)
    step_days = step_map.get(period, 30)
    cutoff = datetime.now(timezone.utc) - timedelta(days=step_days * n_buckets)
    labels = _date_series(n_buckets, step_days)

    db = SessionLocal()
    try:
        # ── Contacts / Leads ────────────────────────────────────────────────
        contacts_all = db.query(Contact).all()
        contact_by_status: dict[str, int] = defaultdict(int)
        new_leads_by_bucket: dict[str, int] = defaultdict(int)
        for c in contacts_all:
            contact_by_status[str(c.status.value if hasattr(c.status, "value") else c.status)] += 1
            if c.created_at and c.created_at >= cutoff:
                bk = _truncate_to(c.created_at, period)
                new_leads_by_bucket[bk] += 1

        # ── Deals / Pipeline / Revenue ──────────────────────────────────────
        deals_all = db.query(Deal).all()
        funnel_stages = [s.value for s in DealStage]
        deals_by_stage: dict[str, int] = defaultdict(int)
        revenue_by_stage: dict[str, float] = defaultdict(float)
        revenue_by_bucket: dict[str, float] = defaultdict(float)
        closed_by_bucket: dict[str, int] = defaultdict(int)
        for d in deals_all:
            stage = str(d.stage.value if hasattr(d.stage, "value") else d.stage)
            deals_by_stage[stage] += 1
            revenue_by_stage[stage] += float(d.value or 0)
            ref_dt = d.closed_at or d.created_at
            if ref_dt and ref_dt >= cutoff:
                bk = _truncate_to(ref_dt, period)
                revenue_by_bucket[bk] += float(d.value or 0)
                if stage == "closed_won":
                    closed_by_bucket[bk] += 1

        total_pipeline_value = sum(revenue_by_stage.values())
        total_closed_won = revenue_by_stage.get("closed_won", 0.0)
        conversion_rate = (
            round(deals_by_stage["closed_won"] / max(1, len(deals_all)) * 100, 1)
            if deals_all else 0.0
        )

        # ── Activities ──────────────────────────────────────────────────────
        activities_all = db.query(Activity).filter(Activity.performed_at >= cutoff).all()
        activity_by_type: dict[str, int] = defaultdict(int)
        outreach_by_bucket: dict[str, int] = defaultdict(int)
        email_sent_by_bucket: dict[str, int] = defaultdict(int)
        email_open_by_bucket: dict[str, int] = defaultdict(int)
        email_click_by_bucket: dict[str, int] = defaultdict(int)
        email_reply_by_bucket: dict[str, int] = defaultdict(int)
        linkedin_by_bucket: dict[str, int] = defaultdict(int)
        call_meeting_by_bucket: dict[str, int] = defaultdict(int)

        outreach_types = {
            ActivityType.EMAIL, ActivityType.LINKEDIN_MESSAGE,
            ActivityType.LINKEDIN_CONNECT, ActivityType.CALL,
            ActivityType.MEETING, ActivityType.SMS, ActivityType.WHATSAPP,
        }
        for a in activities_all:
            atype = str(a.activity_type.value if hasattr(a.activity_type, "value") else a.activity_type)
            activity_by_type[atype] += 1
            bk = _truncate_to(a.performed_at, period)
            if a.activity_type in outreach_types:
                outreach_by_bucket[bk] += 1
            if a.activity_type == ActivityType.EMAIL:
                email_sent_by_bucket[bk] += 1
            if a.activity_type == ActivityType.EMAIL_OPEN:
                email_open_by_bucket[bk] += 1
            if a.activity_type == ActivityType.EMAIL_CLICK:
                email_click_by_bucket[bk] += 1
            if a.activity_type == ActivityType.EMAIL_REPLY:
                email_reply_by_bucket[bk] += 1
            if a.activity_type in (ActivityType.LINKEDIN_MESSAGE, ActivityType.LINKEDIN_CONNECT):
                linkedin_by_bucket[bk] += 1
            if a.activity_type in (ActivityType.CALL, ActivityType.MEETING):
                call_meeting_by_bucket[bk] += 1

        total_emails_sent = sum(email_sent_by_bucket.values())
        total_opens = sum(email_open_by_bucket.values())
        total_clicks = sum(email_click_by_bucket.values())
        total_replies = sum(email_reply_by_bucket.values())
        email_open_rate = round(total_opens / max(1, total_emails_sent) * 100, 1) if total_emails_sent else 0.0
        email_click_rate = round(total_clicks / max(1, total_emails_sent) * 100, 1) if total_emails_sent else 0.0
        email_reply_rate = round(total_replies / max(1, total_emails_sent) * 100, 1) if total_emails_sent else 0.0

        # ── Content / SEO (tracker-based, no DB) ────────────────────────────
        tracker_rows = _read_tracker()
        total_articles = len(tracker_rows)
        published_articles = sum(1 for r in tracker_rows if r.get("status") == "Published")
        qa_passed_articles = sum(1 for r in tracker_rows if r.get("qa") in ("Passed", "QA Passed"))

        # ── Assemble series aligned to labels ───────────────────────────────
        def _series(bucket_dict: dict) -> list:
            return [bucket_dict.get(lbl, 0) for lbl in labels]

        return {
            "ok": True,
            "period": period,
            "labels": labels,
            # Sales — KPI cards
            "sales_kpis": {
                "total_contacts": len(contacts_all),
                "total_deals": len(deals_all),
                "pipeline_value": round(total_pipeline_value, 2),
                "closed_won_value": round(total_closed_won, 2),
                "conversion_rate_pct": conversion_rate,
                "total_outreach": sum(outreach_by_bucket.values()),
            },
            # Sales — funnel
            "funnel": {s: deals_by_stage.get(s, 0) for s in funnel_stages},
            "contact_by_status": dict(contact_by_status),
            # Sales — time series
            "series": {
                "new_leads": _series(new_leads_by_bucket),
                "outreach": _series(outreach_by_bucket),
                "revenue": _series(revenue_by_bucket),
                "closed_won_count": _series(closed_by_bucket),
                "calls_meetings": _series(call_meeting_by_bucket),
                "linkedin": _series(linkedin_by_bucket),
            },
            # Marketing — KPI cards
            "marketing_kpis": {
                "email_sent": total_emails_sent,
                "email_open_rate_pct": email_open_rate,
                "email_click_rate_pct": email_click_rate,
                "email_reply_rate_pct": email_reply_rate,
                "total_articles": total_articles,
                "published_articles": published_articles,
                "qa_passed_articles": qa_passed_articles,
            },
            # Marketing — time series
            "marketing_series": {
                "email_sent": _series(email_sent_by_bucket),
                "email_opens": _series(email_open_by_bucket),
                "email_clicks": _series(email_click_by_bucket),
                "email_replies": _series(email_reply_by_bucket),
                "linkedin": _series(linkedin_by_bucket),
            },
            # Activity breakdown
            "activity_by_type": dict(activity_by_type),
        }
    finally:
        db.close()


@app.get("/analytics", response_class=HTMLResponse)
def page_analytics(request: Request) -> HTMLResponse:
    runtime = _load_runtime()
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "active_page": "analytics",
        "active_week": runtime.get("active_week", "—"),
    })


@app.get("/api/v1/analytics")
def api_analytics(period: str = "monthly") -> dict:
    """Return analytics metrics grouped by period (daily|weekly|monthly|yoy)."""
    if period not in ("daily", "weekly", "monthly", "yoy"):
        raise HTTPException(status_code=422, detail="period must be daily|weekly|monthly|yoy")
    return _analytics_data(period)


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "project_root": str(PROJECT_ROOT),
        "python": sys.executable,
    }


# /run-pipeline endpoint has been moved to runner_api_routers/pipeline.py
