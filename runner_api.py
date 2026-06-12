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
import os
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from revenue_os.database import SessionLocal
from revenue_os.models.activity import (
    Activity,
    ActivityType,
    OutreachSequence,
    SequenceStep,
)
from revenue_os.models.contact import ContactStatus
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

app = FastAPI(title="WorkCrew CMS OS")
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

PROJECT_ROOT = Path(__file__).resolve().parent
PIPELINE_TIMEOUT_SEC = int(os.environ.get("RUNNER_PIPELINE_TIMEOUT_SEC", "1800"))
TAIL_CHARS = int(os.environ.get("RUNNER_LOG_TAIL_CHARS", "4000"))


def _runner_api_key() -> str:
    """Read on each auth check so tests can monkeypatch ``RUNNER_API_KEY``."""
    return os.environ.get("RUNNER_API_KEY", "").strip()


class RunRequest(BaseModel):
    """``topic`` is echoed only; pipeline selection uses ``week`` + runtime files."""

    week: str | None = Field(
        default=None,
        description="If set (e.g. W10), copies data/week_runtime/WXX.json to runtime_config.json before the pipeline.",
    )
    topic: str | None = Field(
        default=None,
        description="Optional label for operators / n8n logs; not passed to validators.",
    )


def _require_auth(authorization: str | None) -> None:
    key = _runner_api_key()
    if not key:
        return
    expected = f"Bearer {key}"
    if (authorization or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _tail(text: str) -> str:
    if len(text) <= TAIL_CHARS:
        return text
    return text[-TAIL_CHARS:]


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=PIPELINE_TIMEOUT_SEC,
    )


# ── UI helpers ─────────────────────────────────────────────────────────────

PIPELINE_STEPS = [
    ("Brief",    "01_Content_Brief.md",     "brief"),
    ("SEO Plan", "02_SEO_Plan.md",          "seo"),
    ("Research", "03_Research.md",          "research"),
    ("Draft",    "04_Draft.md",             "draft"),
    ("Final",    "05_Final.md",             "final"),
    ("Design",   "06_Design_Brief.md",      "design"),
    ("Social",   "07_Social_Posts.md",      "social"),
    ("Email",    "08_Email_Copy.md",        "email"),
    ("Checklist","09_Publish_Checklist.md", "checklist"),
]

VALIDATOR_NAMES = [
    "research_mapper",
    "draft_validator",
    "structure_checker",
    "metadata_checker",
    "publish_checklist_checker",
]


def _read_tracker() -> list[dict[str, str]]:
    tracker = PROJECT_ROOT / "tracker.csv"
    if not tracker.is_file():
        return []
    with tracker.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _load_runtime() -> dict:
    rc = PROJECT_ROOT / "data" / "runtime_config.json"
    if not rc.is_file():
        return {}
    return json.loads(rc.read_text(encoding="utf-8"))


def _last_run_summary() -> dict | None:
    p = PROJECT_ROOT / "output" / "pipeline_orchestrator_run.json"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _week_artifacts(week_id: str) -> dict[str, bool]:
    base = PROJECT_ROOT / "input" / week_id
    return {key: (base / fname).is_file() for _, fname, key in PIPELINE_STEPS}


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


def _apply_week_if_set(week: str | None) -> tuple[bool, list[dict]]:
    steps: list[dict] = []
    if not week:
        return True, steps
    week = week.strip().upper()
    r = _run([sys.executable, "-m", "src.tools.runtime_apply", week])
    steps.append({"step": "runtime_apply", "returncode": r.returncode,
                  "stdout": _tail(r.stdout or ""), "stderr": _tail(r.stderr or "")})
    return r.returncode == 0, steps


@app.post("/run")
def run_full(
    request: WeekRequest,
    authorization: str | None = Header(default=None),
) -> dict:
    """Full pipeline: optional week switch then main.py."""
    _require_auth(authorization)
    week = (request.week or "").strip().upper() or None
    ok, steps = _apply_week_if_set(week)
    if not ok:
        return {"ok": False, "week": week, "steps": steps, "stderr": steps[-1]["stderr"]}
    r = _run([sys.executable, "-m", "src.tools.pipeline_orchestrator"])
    steps.append({"step": "pipeline", "returncode": r.returncode,
                  "stdout": _tail(r.stdout or ""), "stderr": _tail(r.stderr or "")})
    return {"ok": r.returncode == 0, "week": week, "stdout": _tail(r.stdout or ""),
            "stderr": _tail(r.stderr or ""), "steps": steps}


@app.post("/validate")
def run_validate(
    request: WeekRequest,
    authorization: str | None = Header(default=None),
) -> dict:
    """Run validators only (no generation, no tracker write)."""
    _require_auth(authorization)
    week = (request.week or "").strip().upper() or None
    ok, steps = _apply_week_if_set(week)
    if not ok:
        return {"ok": False, "steps": steps}
    r = _run([sys.executable, "-m", "src.tools.pipeline_runner"])
    return {"ok": r.returncode == 0, "stdout": _tail(r.stdout or ""), "stderr": _tail(r.stderr or "")}


@app.post("/generate")
def run_generate(
    request: WeekRequest,
    authorization: str | None = Header(default=None),
) -> dict:
    """Phase 2A: generation crew."""
    _require_auth(authorization)
    week = (request.week or "").strip().upper() or None
    ok, steps = _apply_week_if_set(week)
    if not ok:
        return {"ok": False, "steps": steps}
    r = _run([sys.executable, "-m", "src.generation_crew"])
    return {"ok": r.returncode == 0, "stdout": _tail(r.stdout or ""), "stderr": _tail(r.stderr or "")}


@app.post("/edit")
def run_edit(
    request: WeekRequest,
    authorization: str | None = Header(default=None),
) -> dict:
    """Phase 2B: editor crew."""
    _require_auth(authorization)
    week = (request.week or "").strip().upper() or None
    ok, steps = _apply_week_if_set(week)
    if not ok:
        return {"ok": False, "steps": steps}
    r = _run([sys.executable, "-m", "src.editor_crew"])
    return {"ok": r.returncode == 0, "stdout": _tail(r.stdout or ""), "stderr": _tail(r.stderr or "")}


@app.post("/switch-week")
def switch_week(
    request: WeekRequest,
    authorization: str | None = Header(default=None),
) -> dict:
    """Apply a week profile to runtime_config.json."""
    _require_auth(authorization)
    week = (request.week or "").strip().upper()
    if not week:
        raise HTTPException(status_code=400, detail="week is required")
    r = _run([sys.executable, "-m", "src.tools.runtime_apply", week])
    return {"ok": r.returncode == 0, "week": week, "stdout": r.stdout, "stderr": r.stderr}


@app.post("/go-live")
def record_go_live(
    request: WeekRequest,
    authorization: str | None = Header(default=None),
) -> dict:
    """Record that a week's article is live at a URL."""
    _require_auth(authorization)
    week = (request.week or "").strip().upper()
    url  = (request.url or "").strip()
    if not week or not url:
        raise HTTPException(status_code=400, detail="week and url are required")
    ok, steps = _apply_week_if_set(week)
    if not ok:
        return {"ok": False, "steps": steps}
    r = _run([sys.executable, "-m", "src.tools.go_live_helpers",
              "record-live", "--url", url, "--i-confirmed-url-live"])
    return {"ok": r.returncode == 0, "stdout": _tail(r.stdout or ""), "stderr": _tail(r.stderr or "")}


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
    authorization: str | None = Header(default=None),
) -> HTMLResponse:
    _require_auth(authorization)
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
    authorization: str | None = Header(default=None),
) -> dict:
    _require_auth(authorization)
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
    authorization: str | None = Header(default=None),
) -> dict:
    _require_auth(authorization)
    return {
        "ok": True,
        "providers": provider_status(),
        "thresholds": prospecting_limits(),
    }


@app.post("/api/v1/prospecting/plan")
def prospecting_plan_proxy(
    req: ProspectingRequest,
    authorization: str | None = Header(default=None),
) -> dict:
    _require_auth(authorization)
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
    authorization: str | None = Header(default=None),
) -> dict:
    _require_auth(authorization)
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
    authorization: str | None = Header(default=None),
) -> dict:
    _require_auth(authorization)
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
    authorization: str | None = Header(default=None),
) -> dict:
    _require_auth(authorization)
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
    authorization: str | None = Header(default=None),
) -> dict:
    _require_auth(authorization)
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
    authorization: str | None = Header(default=None),
) -> dict:
    _require_auth(authorization)
    return {
        "supported": ["hermes", "openclaw"],
        "configured": backend_status(),
    }


@app.get("/api/v1/orchestration/logs")
def orchestration_logs_proxy(
    limit: int = 20,
    authorization: str | None = Header(default=None),
) -> dict:
    _require_auth(authorization)
    return {
        "ok": True,
        "runs": load_recent_orchestration_runs(limit=max(1, min(limit, 100))),
    }


@app.post("/api/v1/orchestration/plan")
def orchestration_plan_proxy(
    req: OrchestrationRequest,
    authorization: str | None = Header(default=None),
) -> dict:
    _require_auth(authorization)
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
    authorization: str | None = Header(default=None),
) -> dict:
    _require_auth(authorization)
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
    authorization: str | None = Header(default=None),
) -> dict:
    """Generate multi-channel marketing content via CrewAI agents."""
    _require_auth(authorization)
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
    authorization: str | None = Header(default=None),
) -> dict:
    """Preview what publish_all would post without hitting any APIs."""
    _require_auth(authorization)
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
    authorization: str | None = Header(default=None),
) -> dict:
    """Publish to all configured social channels. Requires confirmed=True."""
    _require_auth(authorization)
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


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "project_root": str(PROJECT_ROOT),
        "python": sys.executable,
    }


@app.post("/run-pipeline")
def run_pipeline(
    request: RunRequest,
    authorization: str | None = Header(default=None),
) -> dict:
    """
    Optionally apply a week profile, then run the same entrypoint as ``python main.py``.
    """
    _require_auth(authorization)

    steps: list[dict] = []
    week = (request.week or "").strip().upper() or None

    if week:
        r = _run([sys.executable, "-m", "src.tools.runtime_apply", week])
        steps.append(
            {
                "step": "runtime_apply",
                "returncode": r.returncode,
                "stdout_tail": _tail(r.stdout or ""),
                "stderr_tail": _tail(r.stderr or ""),
            }
        )
        if r.returncode != 0:
            return {
                "status": "failed",
                "week": week,
                "topic": request.topic,
                "returncode": r.returncode,
                "steps": steps,
            }

    r = _run([sys.executable, "main.py"])
    steps.append(
        {
            "step": "main.py",
            "returncode": r.returncode,
            "stdout_tail": _tail(r.stdout or ""),
            "stderr_tail": _tail(r.stderr or ""),
        }
    )

    ok = r.returncode == 0
    return {
        "status": "success" if ok else "failed",
        "week": week,
        "topic": request.topic,
        "returncode": r.returncode,
        "steps": steps,
    }
