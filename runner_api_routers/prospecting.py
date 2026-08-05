"""Lead prospecting and sequencing endpoints."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from revenue_os.database import SessionLocal
from revenue_os.models.activity import Activity, ActivityType, OutreachSequence
from revenue_os.models.contact import ContactStatus
from revenue_os.services.lead_prospecting_service import (
    build_prospecting_plan,
    provider_status,
    prospecting_limits,
)

from runner_api_routers.utils import PROJECT_ROOT, _verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/prospecting", tags=["prospecting"])


class ProspectingRequest(BaseModel):
    """Lead prospecting parameters."""

    target_count: int = Field(default=50, ge=1, le=5000)
    min_score: int = Field(default=25, ge=0, le=100)
    statuses: list[str] = Field(default_factory=lambda: ["lead", "prospect"])
    allow_scraper: bool = True
    allow_mcp: bool = True


class ProspectingExecuteRequest(ProspectingRequest):
    """Extended request for prospecting execution with import options."""

    execute_stages: list[str] = Field(
        default_factory=lambda: [
            "free_linkedin_existing_data",
            "scraper_platforms",
            "mcp_providers",
        ]
    )
    sequence_id: str | None = None
    auto_import: bool = True
    max_import: int = Field(default=50, ge=1, le=1000)


class ProspectingPresetSaveRequest(BaseModel):
    """Save a prospecting preset configuration."""

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
    """Import prospects into an outreach sequence."""

    sequence_id: str
    contact_ids: list[str]


def _presets_file():
    """Get path to prospecting presets file."""
    p = PROJECT_ROOT / "output" / "sales" / "prospecting_presets.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _read_presets() -> list[dict[str, Any]]:
    """Read saved prospecting presets."""
    import json

    p = _presets_file()
    if not p.is_file():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _write_presets(items: list[dict[str, Any]]) -> None:
    """Save prospecting presets."""
    import json

    _presets_file().write_text(json.dumps(items, ensure_ascii=True, indent=2), encoding="utf-8")


def _parse_statuses(raw: list[str]) -> list[ContactStatus]:
    """Parse and validate contact statuses."""
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
    """Map sequence action to activity type."""
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


@router.get("/providers", tags=["prospecting"])
def prospecting_providers_proxy(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get available prospecting providers and their limits."""
    logger.info("Fetching prospecting providers")
    return {
        "ok": True,
        "providers": provider_status(),
        "thresholds": prospecting_limits(),
    }


@router.post("/plan", tags=["prospecting"])
def prospecting_plan_proxy(
    req: ProspectingRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Build a prospecting plan with available leads."""
    logger.info(
        "Building prospecting plan",
        extra={"target_count": req.target_count, "statuses": req.statuses},
    )
    db = SessionLocal()
    try:
        statuses = _parse_statuses(req.statuses)
        return {
            "ok": True,
            "plan": build_prospecting_plan(
                db,
                target_count=req.target_count,
                min_score=req.min_score,
                statuses=statuses,
                allow_scraper=req.allow_scraper,
                allow_mcp=req.allow_mcp,
            ),
        }
    finally:
        db.close()


@router.post("/execute", tags=["prospecting"])
def prospecting_execute(
    req: ProspectingExecuteRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Execute prospecting plan across multiple sources."""
    logger.info(
        "Executing prospecting plan",
        extra={
            "target_count": req.target_count,
            "execute_stages": req.execute_stages,
            "auto_import": req.auto_import,
        },
    )
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
                sequence = (
                    db.query(OutreachSequence)
                    .filter(OutreachSequence.id == req.sequence_id)
                    .first()
                )
                if sequence:
                    scheduled = []
                    for cid in ids:
                        activity = Activity(
                            contact_id=uuid.UUID(cid),
                            activity_type=_map_activity_type("", sequence.channel),
                            subject=f"{sequence.name} - imported",
                            body="Imported from prospecting plan",
                            direction="outbound",
                            status="scheduled",
                            scheduled_at=datetime.now(timezone.utc),
                        )
                        db.add(activity)
                        scheduled.append({"contact_id": cid})
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


@router.get("/presets", tags=["prospecting"])
def prospecting_presets_list(
    brand: str | None = None,
    team: str | None = None,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """List saved prospecting presets."""
    logger.info("Listing prospecting presets", extra={"brand": brand, "team": team})
    items = _read_presets()
    if brand:
        items = [x for x in items if (x.get("brand") or "") == brand]
    if team:
        items = [x for x in items if (x.get("team") or "") == team]
    items.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return {"ok": True, "presets": items}


@router.post("/presets/save", tags=["prospecting"])
def prospecting_presets_save(
    req: ProspectingPresetSaveRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Save a prospecting preset configuration."""
    logger.info(
        "Saving prospecting preset",
        extra={"preset_name": req.name, "brand": req.brand, "team": req.team},
    )
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


@router.post("/import", tags=["prospecting"])
def prospecting_import(
    req: ProspectingImportRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Import prospects into an outreach sequence."""
    logger.info(
        "Importing prospects",
        extra={"sequence_id": req.sequence_id, "contact_count": len(req.contact_ids)},
    )
    db = SessionLocal()
    try:
        if not req.contact_ids:
            raise HTTPException(status_code=400, detail="contact_ids is required")
        sequence = (
            db.query(OutreachSequence)
            .filter(OutreachSequence.id == req.sequence_id)
            .first()
        )
        if not sequence:
            raise HTTPException(status_code=404, detail="outreach sequence not found")

        scheduled = []
        for cid in req.contact_ids:
            activity = Activity(
                contact_id=uuid.UUID(cid),
                activity_type=_map_activity_type("", sequence.channel),
                subject=f"{sequence.name} - imported",
                body="Imported from prospecting",
                direction="outbound",
                status="scheduled",
                scheduled_at=datetime.now(timezone.utc),
            )
            db.add(activity)
            scheduled.append({"contact_id": cid})

        db.commit()
        logger.info(
            "Import successful",
            extra={"sequence_id": req.sequence_id, "imported_count": len(scheduled)},
        )
        return {
            "ok": True,
            "sequence_id": req.sequence_id,
            "contacts_imported": len(scheduled),
            "scheduled": scheduled,
        }
    finally:
        db.close()
