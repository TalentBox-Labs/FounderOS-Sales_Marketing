from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from revenue_os.agents.recruiter_agent import match_candidate_to_job, screen_resume
from revenue_os.agents.sdr_agent import (
    generate_outreach_sequence,
    score_and_enrich_lead,
)
from revenue_os.database import get_db
from revenue_os.models.activity import Activity, ActivityType
from revenue_os.models.contact import Contact, ContactStatus
from revenue_os.models.deal import Deal, DealStage
from revenue_os.models.project import Project

router = APIRouter(prefix="/agents", tags=["agents"])


class LeadScoreRequest(BaseModel):
    company_name: str
    company_domain: Optional[str] = None
    industry: Optional[str] = None


class MatchCandidateRequest(BaseModel):
    candidate_name: str
    candidate_skills: str
    candidate_experience: str
    job_title: str
    job_requirements: str


class ScreenResumeRequest(BaseModel):
    resume_text: str
    job_requirements: str


class OutreachRequest(BaseModel):
    prospect_name: str
    company_name: str
    industry: Optional[str] = None


# ---- SDR Agent ----

@router.post("/score-lead")
def agent_score_lead(body: LeadScoreRequest):
    return score_and_enrich_lead(
        company_name=body.company_name,
        company_domain=body.company_domain,
        industry=body.industry,
    )


@router.post("/outreach-sequence")
def agent_outreach_sequence(body: OutreachRequest):
    return generate_outreach_sequence(
        prospect_name=body.prospect_name,
        company_name=body.company_name,
        industry=body.industry,
    )


# ---- Recruiter Agent ----

@router.post("/match-candidate")
def agent_match_candidate(body: MatchCandidateRequest):
    return match_candidate_to_job(
        candidate_name=body.candidate_name,
        candidate_skills=body.candidate_skills,
        candidate_experience=body.candidate_experience,
        job_title=body.job_title,
        job_requirements=body.job_requirements,
    )


@router.post("/screen-resume")
def agent_screen_resume(body: ScreenResumeRequest):
    return screen_resume(
        resume_text=body.resume_text,
        job_requirements=body.job_requirements,
    )
