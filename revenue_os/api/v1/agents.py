"""Legacy CrewAI agent routes — quarantined REV-ORCH M0.

Production canonical API is ``runner_api:app`` (Dockerfile CMD). These routes
bypass TenantContext, ApprovalRequest, and canonical revenue orchestration.
Use ``/api/v1/agents/sales/{contact_id}/*`` on runner_api instead.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/agents", tags=["agents"])

_QUARANTINE_DETAIL = (
    "CrewAI legacy agent routes quarantined (REV-ORCH M0). "
    "Use runner_api canonical sales agent endpoints with ApprovalRequest gating."
)


def _quarantine() -> None:
    raise HTTPException(status_code=410, detail=_QUARANTINE_DETAIL)


@router.post("/score-lead")
def agent_score_lead() -> None:
    _quarantine()


@router.post("/outreach-sequence")
def agent_outreach_sequence() -> None:
    _quarantine()


@router.post("/match-candidate")
def agent_match_candidate() -> None:
    _quarantine()


@router.post("/screen-resume")
def agent_screen_resume() -> None:
    _quarantine()
