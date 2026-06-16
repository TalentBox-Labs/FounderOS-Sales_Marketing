"""Outreach sequence and activity endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from revenue_os.database import SessionLocal
from revenue_os.models.activity import OutreachSequence

from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/outreach", tags=["outreach"])


@router.get("/sequences", tags=["outreach"])
def outreach_sequences_list(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """List active outreach sequences."""
    logger.info("Listing outreach sequences")
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
