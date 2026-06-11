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
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from revenue_os.services.go_to_market_orchestrator import (
    GTMOrchestrationRequest,
    build_strategy,
    load_recent_orchestration_runs,
    run_orchestration,
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
