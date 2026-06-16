"""UI page routes and templates."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from runner_api_routers.utils import (
    _last_run_summary,
    _load_runtime,
    _read_tracker,
    _validate_week_id,
    _week_artifacts,
    PROJECT_ROOT,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["ui"])

# Setup templates
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _week_pipeline_steps(row: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive per-step state from tracker row and artifact existence."""
    wid = row.get("content_id", "")
    arts = _week_artifacts(wid)
    current = (row.get("current_step") or "").lower()
    steps = []
    mapping = [
        ("Brief", "brief"),
        ("SEO", "seo"),
        ("Research", "research"),
        ("Draft", "draft"),
        ("Final", "final"),
        ("Checklist", "checklist"),
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


def _enrich_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Enrich tracker rows with artifact and pipeline state information."""
    enriched = []
    for r in rows:
        wid = r.get("content_id", "")
        arts = _week_artifacts(wid)
        enriched.append(
            {
                **r,
                "has_draft": arts.get("draft", False),
                "has_final": arts.get("final", False),
                "has_qa": (
                    PROJECT_ROOT / "output" / "qa_reports" / f"{wid}_Draft_Validation.md"
                ).is_file(),
                "has_checklist": arts.get("checklist", False),
                "pipeline_steps": _week_pipeline_steps(r),
            }
        )
    return enriched


def _dashboard_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate dashboard statistics from tracker rows."""
    total = len(rows)
    qa_passed = sum(1 for r in rows if (r.get("qa_status") or "").upper() == "PASS")
    published = sum(
        1
        for r in rows
        if "publish" in (r.get("status") or "").lower()
        or "complete" in (r.get("status") or "").lower()
    )
    in_prog = sum(
        1
        for r in rows
        if "progress" in (r.get("status") or "").lower()
        or "review" in (r.get("status") or "").lower()
    )
    weeks_set = {r.get("content_id", "") for r in rows}
    return {
        "total": total,
        "weeks": len(weeks_set),
        "qa_passed": qa_passed,
        "qa_pct": round(qa_passed / total * 100) if total else 0,
        "published": published,
        "in_progress": in_prog,
    }


@router.get("/", response_class=HTMLResponse)
def page_dashboard(request: Request) -> HTMLResponse:
    """Dashboard home page."""
    logger.info("Loading dashboard page")
    rows = _read_tracker()
    enriched = _enrich_rows(rows)
    runtime = _load_runtime()
    last_run = _last_run_summary()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "active_page": "dashboard",
            "active_week": runtime.get("active_week", "—"),
            "stats": _dashboard_stats(enriched),
            "weeks": enriched,
            "last_run": last_run,
        },
    )


@router.get("/weeks", response_class=HTMLResponse)
def page_weeks(request: Request) -> HTMLResponse:
    """Content calendar page."""
    logger.info("Loading weeks page")
    rows = _read_tracker()
    enriched = _enrich_rows(rows)
    runtime = _load_runtime()

    return templates.TemplateResponse(
        "weeks.html",
        {
            "request": request,
            "active_page": "weeks",
            "active_week": runtime.get("active_week", "—"),
            "weeks": enriched,
        },
    )


@router.get("/weeks/{week_id}", response_class=HTMLResponse)
def page_week_detail(week_id: str, request: Request) -> HTMLResponse:
    """Week detail page."""
    _validate_week_id(week_id)
    logger.info("Loading week detail", extra={"week_id": week_id})

    rows = _read_tracker()
    row = next((r for r in rows if r.get("content_id") == week_id), None)
    if not row:
        raise HTTPException(status_code=404, detail="Week not found")

    enriched_rows = _enrich_rows([row])
    enriched = enriched_rows[0] if enriched_rows else row

    runtime = _load_runtime()

    return templates.TemplateResponse(
        "week_detail.html",
        {
            "request": request,
            "active_page": "week_detail",
            "active_week": runtime.get("active_week", "—"),
            "week": enriched,
            "week_id": week_id,
        },
    )


@router.get("/weeks/{week_id}/file/{filename:path}", response_class=HTMLResponse)
def page_file_view(
    week_id: str, filename: str, request: Request
) -> HTMLResponse:
    """File viewer page."""
    _validate_week_id(week_id)
    logger.info("Loading file view", extra={"week_id": week_id, "filename": filename})

    file_path = PROJECT_ROOT / "input" / week_id / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    content = file_path.read_text(encoding="utf-8")
    runtime = _load_runtime()

    return templates.TemplateResponse(
        "file_view.html",
        {
            "request": request,
            "active_page": "file_view",
            "active_week": runtime.get("active_week", "—"),
            "week_id": week_id,
            "filename": filename,
            "content": content,
            "char_count": len(content),
            "line_count": content.count("\n") + 1,
        },
    )


@router.get("/pipeline", response_class=HTMLResponse)
def page_pipeline(request: Request) -> HTMLResponse:
    """Pipeline trigger UI page."""
    logger.info("Loading pipeline page")
    rows = _read_tracker()
    runtime = _load_runtime()
    active_week = runtime.get("active_week", "—")

    return templates.TemplateResponse(
        "pipeline.html",
        {
            "request": request,
            "active_page": "pipeline",
            "active_week": active_week,
            "weeks": rows,
            "last_run": _last_run_summary(),
        },
    )


@router.get("/mcp", response_class=HTMLResponse)
def page_mcp(request: Request) -> HTMLResponse:
    """MCP hub configuration page."""
    logger.info("Loading MCP page")
    runtime = _load_runtime()

    return templates.TemplateResponse(
        "mcp.html",
        {
            "request": request,
            "active_page": "mcp",
            "active_week": runtime.get("active_week", "—"),
        },
    )


@router.get("/marketing", response_class=HTMLResponse)
def page_marketing(request: Request) -> HTMLResponse:
    """Marketing agent UI page."""
    logger.info("Loading marketing page")
    runtime = _load_runtime()

    # Import here to avoid circular dependencies
    from revenue_os.services.orchestration_runtime import backend_status
    from revenue_os.services.go_to_market_orchestrator import (
        load_recent_orchestration_runs,
    )

    return templates.TemplateResponse(
        "marketing.html",
        {
            "request": request,
            "active_page": "marketing",
            "active_week": runtime.get("active_week", "—"),
            "orchestration_runs": load_recent_orchestration_runs(limit=20),
            "orchestration_status": backend_status(),
        },
    )


@router.get("/sales", response_class=HTMLResponse)
def page_sales(request: Request) -> HTMLResponse:
    """Sales prospecting UI page."""
    logger.info("Loading sales page")
    runtime = _load_runtime()

    return templates.TemplateResponse(
        "sales.html",
        {
            "request": request,
            "active_page": "sales",
            "active_week": runtime.get("active_week", "—"),
        },
    )


@router.get("/analytics", response_class=HTMLResponse)
def page_analytics(request: Request) -> HTMLResponse:
    """Analytics dashboard page."""
    logger.info("Loading analytics page")
    runtime = _load_runtime()

    return templates.TemplateResponse(
        "analytics.html",
        {
            "request": request,
            "active_page": "analytics",
            "active_week": runtime.get("active_week", "—"),
        },
    )


@router.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "WorkCrew CMS OS"}


@router.get("/api/v1/health")
def api_health() -> dict[str, str]:
    """API health check endpoint."""
    return {"status": "ok", "service": "WorkCrew CMS OS API"}
