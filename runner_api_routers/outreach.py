"""Outreach sequence endpoints — email-sequence automation.

Sequences and steps are DB-backed (OutreachSequence/SequenceStep). Enrolling
a contact schedules one TASK activity per step, spaced by each step's
delay_days — so a sequence shows up on the contact's timeline and in the
follow-up engine/Copilot exactly like any other task, with no separate
execution engine required.
"""

from __future__ import annotations

import logging
import uuid as uuid_lib
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from revenue_os.database import SessionLocal
from revenue_os.models.activity import OutreachSequence, SequenceStep
from revenue_os.models.contact import Contact
from revenue_os.services.outreach_service import schedule_contact_sequence
from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/outreach", tags=["outreach"])


def _step_dict(st: SequenceStep) -> dict[str, Any]:
    return {
        "id": str(st.id),
        "sequence_id": str(st.sequence_id),
        "step_order": st.step_order,
        "delay_days": st.delay_days,
        "subject": st.subject,
        "template": st.template,
        "action_type": st.action_type,
    }


def _sequence_dict(s: OutreachSequence, steps: list[SequenceStep] | None = None) -> dict[str, Any]:
    d = {
        "id": str(s.id),
        "name": s.name,
        "channel": s.channel,
        "steps_count": s.steps_count,
        "is_active": bool(s.is_active),
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }
    if steps is not None:
        d["steps"] = [_step_dict(st) for st in steps]
    return d


class SequenceCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    channel: str = Field(default="email", max_length=50)


class SequenceUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class StepCreateRequest(BaseModel):
    step_order: int | None = None
    delay_days: int = Field(default=1, ge=0)
    subject: str | None = Field(default=None, max_length=500)
    template: str | None = None
    action_type: str = Field(default="send_email", max_length=50)


class EnrollRequest(BaseModel):
    contact_id: str


class GenerateEmailRequest(BaseModel):
    prospect_name: str = Field(..., min_length=1, max_length=255)
    company_name: str = Field(..., min_length=1, max_length=255)
    context: str | None = None


@router.get("/sequences")
def list_sequences(
    is_active: bool | None = Query(None),
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """List outreach sequences."""
    db = SessionLocal()
    try:
        query = db.query(OutreachSequence).order_by(OutreachSequence.created_at.desc())
        if is_active is not None:
            query = query.filter(OutreachSequence.is_active == (1 if is_active else 0))
        sequences = query.all()
        return {"ok": True, "count": len(sequences), "sequences": [_sequence_dict(s) for s in sequences]}
    finally:
        db.close()


@router.post("/sequences")
def create_sequence(
    req: SequenceCreateRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        seq = OutreachSequence(name=req.name, channel=req.channel, is_active=1)
        db.add(seq)
        db.commit()
        db.refresh(seq)
        return {"ok": True, "sequence": _sequence_dict(seq, steps=[])}
    finally:
        db.close()


@router.get("/sequences/{seq_id}")
def get_sequence(
    seq_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        try:
            sid = uuid_lib.UUID(seq_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid sequence_id")
        seq = db.get(OutreachSequence, sid)
        if seq is None:
            raise HTTPException(status_code=404, detail="Sequence not found")
        steps = (
            db.query(SequenceStep)
            .filter(SequenceStep.sequence_id == sid)
            .order_by(SequenceStep.step_order)
            .all()
        )
        return {"ok": True, "sequence": _sequence_dict(seq, steps=steps)}
    finally:
        db.close()


@router.patch("/sequences/{seq_id}")
def update_sequence(
    seq_id: str,
    req: SequenceUpdateRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        try:
            sid = uuid_lib.UUID(seq_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid sequence_id")
        seq = db.get(OutreachSequence, sid)
        if seq is None:
            raise HTTPException(status_code=404, detail="Sequence not found")
        if req.name is not None:
            seq.name = req.name
        if req.is_active is not None:
            seq.is_active = 1 if req.is_active else 0
        db.add(seq)
        db.commit()
        db.refresh(seq)
        return {"ok": True, "sequence": _sequence_dict(seq)}
    finally:
        db.close()


@router.post("/sequences/{seq_id}/steps")
def create_step(
    seq_id: str,
    req: StepCreateRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        try:
            sid = uuid_lib.UUID(seq_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid sequence_id")
        seq = db.get(OutreachSequence, sid)
        if seq is None:
            raise HTTPException(status_code=404, detail="Sequence not found")

        existing_count = db.query(SequenceStep).filter(SequenceStep.sequence_id == sid).count()
        step = SequenceStep(
            sequence_id=sid,
            step_order=req.step_order or (existing_count + 1),
            delay_days=req.delay_days,
            subject=req.subject,
            template=req.template,
            action_type=req.action_type,
        )
        db.add(step)
        seq.steps_count = existing_count + 1
        db.add(seq)
        db.commit()
        db.refresh(step)
        return {"ok": True, "step": _step_dict(step)}
    finally:
        db.close()


@router.post("/sequences/{seq_id}/enroll")
def enroll_contact(
    seq_id: str,
    req: EnrollRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Enroll a contact — schedules one activity per step, spaced by delay_days.

    Same scheduling path as the prospecting-import flow
    (``revenue_os.services.outreach_service``), so a sequence behaves
    identically whether a contact is enrolled one at a time here or in bulk
    from a prospecting plan.
    """
    db = SessionLocal()
    try:
        try:
            sid = uuid_lib.UUID(seq_id)
            cid = uuid_lib.UUID(req.contact_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid id")
        seq = db.get(OutreachSequence, sid)
        if seq is None:
            raise HTTPException(status_code=404, detail="Sequence not found")
        contact = db.get(Contact, cid)
        if contact is None:
            raise HTTPException(status_code=404, detail="Contact not found")

        steps_count = (
            db.query(SequenceStep).filter(SequenceStep.sequence_id == sid).count()
        )
        if not steps_count:
            raise HTTPException(status_code=422, detail="Sequence has no steps yet")

        result = schedule_contact_sequence(db, seq, str(cid))
        db.commit()

        return {
            "ok": True,
            "enrolled": True,
            "sequence": seq.name,
            "contact": f"{contact.first_name} {contact.last_name}".strip(),
            "tasks_created": result["steps"],
        }
    finally:
        db.close()


@router.post("/generate-email")
def generate_email(
    req: GenerateEmailRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """AI-draft a cold email (falls back to a template if no OPENAI_API_KEY)."""
    from revenue_os.services.ai_service import generate_cold_email

    body = generate_cold_email(
        prospect_name=req.prospect_name,
        company_name=req.company_name,
        context=req.context,
    )
    return {"ok": True, "email_body": body}
