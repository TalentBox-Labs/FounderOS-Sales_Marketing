from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from revenue_os.database import get_db
from revenue_os.models.activity import (
    Activity,
    ActivityType,
    OutreachSequence,
    SequenceStep,
)
from revenue_os.services.ai_service import generate_cold_email
from revenue_os.services.search_service import index_activity

router = APIRouter(prefix="/outreach", tags=["outreach"])


class SequenceCreate(BaseModel):
    name: str
    channel: str = "email"


class SequenceUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[int] = None


class SequenceResponse(BaseModel):
    id: uuid.UUID
    name: str
    channel: str
    steps_count: int
    is_active: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StepCreate(BaseModel):
    step_order: int
    delay_days: int = 1
    subject: Optional[str] = None
    template: Optional[str] = None
    action_type: str = "send_email"
    conditions: Optional[str] = None


class StepResponse(BaseModel):
    id: uuid.UUID
    sequence_id: uuid.UUID
    step_order: int
    delay_days: int
    subject: Optional[str] = None
    template: Optional[str] = None
    action_type: str
    conditions: Optional[str] = None

    model_config = {"from_attributes": True}


class ActivityCreate(BaseModel):
    contact_id: str
    deal_id: Optional[str] = None
    activity_type: ActivityType
    subject: Optional[str] = None
    body: Optional[str] = None
    direction: str = "outbound"


class ActivityResponse(BaseModel):
    id: uuid.UUID
    contact_id: uuid.UUID
    deal_id: Optional[uuid.UUID] = None
    activity_type: ActivityType
    subject: Optional[str] = None
    body: Optional[str] = None
    direction: str
    status: str
    performed_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class AIEmailRequest(BaseModel):
    prospect_name: str
    company_name: str
    context: Optional[str] = None


class AIEmailResponse(BaseModel):
    email_body: str


# ---- Sequences ----

@router.post("/sequences", response_model=SequenceResponse, status_code=201)
def create_sequence(body: SequenceCreate, db: Session = Depends(get_db)):
    seq = OutreachSequence(name=body.name, channel=body.channel)
    db.add(seq)
    db.commit()
    db.refresh(seq)
    return seq


@router.get("/sequences", response_model=list[SequenceResponse])
def list_sequences(
    is_active: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(OutreachSequence)
    if is_active is not None:
        query = query.filter(OutreachSequence.is_active == is_active)
    return query.all()


@router.get("/sequences/{seq_id}", response_model=SequenceResponse)
def get_sequence(seq_id: str, db: Session = Depends(get_db)):
    seq = db.query(OutreachSequence).filter(
        OutreachSequence.id == seq_id
    ).first()
    if not seq:
        raise HTTPException(status_code=404, detail="Sequence not found")
    return seq


@router.post(
    "/sequences/{seq_id}/steps",
    response_model=StepResponse,
    status_code=201,
)
def create_step(
    seq_id: str,
    body: StepCreate,
    db: Session = Depends(get_db),
):
    seq = db.query(OutreachSequence).filter(
        OutreachSequence.id == seq_id
    ).first()
    if not seq:
        raise HTTPException(status_code=404, detail="Sequence not found")

    step = SequenceStep(
        sequence_id=uuid.UUID(seq_id),
        step_order=body.step_order,
        delay_days=body.delay_days,
        subject=body.subject,
        template=body.template,
        action_type=body.action_type,
        conditions=body.conditions,
    )
    db.add(step)
    seq.steps_count = (
        db.query(SequenceStep)
        .filter(SequenceStep.sequence_id == seq_id)
        .count()
        + 1
    )
    db.commit()
    db.refresh(step)
    return step


@router.get(
    "/sequences/{seq_id}/steps",
    response_model=list[StepResponse],
)
def list_steps(seq_id: str, db: Session = Depends(get_db)):
    return (
        db.query(SequenceStep)
        .filter(SequenceStep.sequence_id == seq_id)
        .order_by(SequenceStep.step_order)
        .all()
    )


# ---- Activities ----

@router.post("/activities", response_model=ActivityResponse, status_code=201)
def create_activity(body: ActivityCreate, db: Session = Depends(get_db)):
    activity = Activity(
        contact_id=uuid.UUID(body.contact_id),
        deal_id=uuid.UUID(body.deal_id) if body.deal_id else None,
        activity_type=body.activity_type,
        subject=body.subject,
        body=body.body,
        direction=body.direction,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    index_activity(
        activity_id=activity.id,
        subject=activity.subject,
        body=activity.body,
    )
    return activity


@router.get("/activities", response_model=list[ActivityResponse])
def list_activities(
    contact_id: Optional[str] = Query(None),
    activity_type: Optional[ActivityType] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(Activity)
    if contact_id:
        query = query.filter(Activity.contact_id == contact_id)
    if activity_type:
        query = query.filter(Activity.activity_type == activity_type)
    return query.order_by(Activity.performed_at.desc()).limit(limit).all()


# ---- AI ----

@router.post("/generate-email", response_model=AIEmailResponse)
def generate_email(body: AIEmailRequest):
    email = generate_cold_email(
        prospect_name=body.prospect_name,
        company_name=body.company_name,
        context=body.context,
    )
    return AIEmailResponse(email_body=email)
