"""Analytics depth — attribution, LTV, CAC, and agent productivity."""

from __future__ import annotations

import logging
import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from revenue_os.database import SessionLocal
from revenue_os.models.analytics_depth import MarketingSpendRecord
from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/analytics-depth", tags=["analytics-depth"])

_PERIOD_RE = re.compile(r"^\d{4}-\d{2}$")


class SpendCreateRequest(BaseModel):
    channel: str = Field(..., min_length=1, max_length=64)
    period: str = Field(..., description="YYYY-MM")
    amount: float = Field(..., gt=0)
    notes: str | None = None


@router.get("/attribution")
def attribution(_: str | None = Depends(_verify_api_key)) -> dict[str, Any]:
    """Contacts, qualify rate, and closed-won revenue per acquisition source."""
    from revenue_os.services.analytics_depth import compute_attribution

    db = SessionLocal()
    try:
        return {"ok": True, "attribution": compute_attribution(db)}
    finally:
        db.close()


@router.get("/ltv")
def ltv(
    top_n: int = Query(default=10, ge=1, le=50),
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Average and top customer lifetime value from closed-won deals."""
    from revenue_os.services.analytics_depth import compute_ltv

    db = SessionLocal()
    try:
        return {"ok": True, **compute_ltv(db, top_n=top_n)}
    finally:
        db.close()


@router.get("/cac")
def cac(
    period: str | None = Query(default=None, description="YYYY-MM, omit for all-time"),
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Cost per acquired customer, per channel — only channels with logged spend."""
    from revenue_os.services.analytics_depth import compute_cac

    if period and not _PERIOD_RE.match(period):
        raise HTTPException(status_code=422, detail="period must be YYYY-MM")

    db = SessionLocal()
    try:
        return {"ok": True, "period": period, "cac": compute_cac(db, period=period)}
    finally:
        db.close()


@router.get("/spend")
def list_spend(
    period: str | None = Query(default=None),
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        query = db.query(MarketingSpendRecord).order_by(MarketingSpendRecord.period.desc())
        if period:
            query = query.filter(MarketingSpendRecord.period == period)
        rows = query.all()
        return {"ok": True, "count": len(rows), "spend": [r.to_dict() for r in rows]}
    finally:
        db.close()


@router.post("/spend")
def log_spend(
    req: SpendCreateRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Log marketing spend for a channel/period — the real cost input CAC needs."""
    if not _PERIOD_RE.match(req.period):
        raise HTTPException(status_code=422, detail="period must be YYYY-MM")

    db = SessionLocal()
    try:
        row = MarketingSpendRecord(
            channel=req.channel, period=req.period, amount=req.amount, notes=req.notes,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return {"ok": True, "spend": row.to_dict()}
    finally:
        db.close()


@router.delete("/spend/{spend_id}")
def delete_spend(
    spend_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        row = db.get(MarketingSpendRecord, spend_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Spend record not found")
        db.delete(row)
        db.commit()
        return {"ok": True}
    finally:
        db.close()


@router.get("/agent-productivity")
def agent_productivity(_: str | None = Depends(_verify_api_key)) -> dict[str, Any]:
    """Actions, goals, and approvals per registered agent (see the M5 registry)."""
    from revenue_os.services.analytics_depth import compute_agent_productivity

    db = SessionLocal()
    try:
        return {"ok": True, "agents": compute_agent_productivity(db)}
    finally:
        db.close()
