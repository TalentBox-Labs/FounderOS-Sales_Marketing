from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from revenue_os.database import get_db
from revenue_os.models.activity import (
    Activity,
    ActivityType,
    OutreachSequence,
    SequenceStep,
)
from revenue_os.services.ai_service import generate_cold_email
from revenue_os.services.email_composer import compose as compose_email
from revenue_os.services.enrichment_service import build_prospect_profile
from revenue_os.services.gmail_client import (
    inject_tracking,
    send_email as gmail_send,
)
from revenue_os.services.search_service import index_activity
from revenue_os.config import settings

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


# ---- Send ----

class SendEmailRequest(BaseModel):
    contact_id: str
    angle: Optional[str] = None
    product_description: Optional[str] = None
    sequence_step_id: Optional[str] = None


class SendEmailResponse(BaseModel):
    activity_id: str
    message_id: str
    thread_id: str
    subject: str
    body_preview: str


@router.post("/send", response_model=SendEmailResponse)
def send_personalized_email(
    body: SendEmailRequest,
    db: Session = Depends(get_db),
):
    profile = build_prospect_profile(db, body.contact_id)
    if "error" in profile:
        raise HTTPException(status_code=404, detail=profile["error"])

    composed = compose_email(
        profile,
        angle=body.angle,
        product_description=body.product_description,
    )

    contact = profile.get("contact", {})
    to_email = contact.get("email")
    if not to_email:
        raise HTTPException(
            status_code=400, detail="Contact has no email address"
        )

    body_text = f"{composed.get('hook', '')}\n\n{composed.get('body', '')}"
    body_html = body_text.replace("\n", "<br>\n")

    activity = Activity(
        contact_id=uuid.UUID(body.contact_id),
        activity_type=ActivityType.EMAIL,
        subject=composed.get("subject", ""),
        body=body_text,
        direction="outbound",
        status="sending",
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)

    domain = settings.TRACKING_DOMAIN.rstrip("/")
    body_html = inject_tracking(body_html, str(activity.id), domain)

    try:
        result = gmail_send(
            to=to_email,
            subject=composed.get("subject", ""),
            body_text=body_text,
            body_html=body_html,
        )
        activity.status = "sent"
    except Exception as e:
        activity.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=502,
            detail=f"Failed to send email: {e}",
        )

    from revenue_os.models.activity import EmailActivity

    email_activity = EmailActivity(
        activity_id=activity.id,
        message_id=result.get("message_id"),
        from_address=result.get("from_address", ""),
        to_addresses=to_email,
    )
    db.add(email_activity)
    db.commit()
    db.refresh(activity)

    index_activity(
        activity_id=activity.id,
        subject=activity.subject,
        body=activity.body,
    )

    return SendEmailResponse(
        activity_id=str(activity.id),
        message_id=result.get("message_id", ""),
        thread_id=result.get("thread_id", ""),
        subject=composed.get("subject", ""),
        body_preview=composed.get("hook", "")[:100],
    )


class BatchSendRequest(BaseModel):
    contact_ids: list[str] = Field(..., min_length=1, max_length=50)
    angle: Optional[str] = None
    product_description: Optional[str] = None


class BatchSendResponse(BaseModel):
    sent: int
    failed: int
    results: list[dict]


@router.post("/send-batch", response_model=BatchSendResponse)
def send_batch_emails(
    body: BatchSendRequest,
    db: Session = Depends(get_db),
):
    from revenue_os.tasks.outreach import send_personalized_email_task

    sent = 0
    failed = 0
    results = []

    for cid in body.contact_ids:
        try:
            profile = build_prospect_profile(db, cid)
            if "error" in profile:
                failed += 1
                results.append(
                    {"contact_id": cid, "status": "error", "detail": profile["error"]}
                )
                continue

            composed = compose_email(
                profile,
                angle=body.angle,
                product_description=body.product_description,
            )
            to_email = profile.get("contact", {}).get("email")
            if not to_email:
                failed += 1
                results.append(
                    {"contact_id": cid, "status": "error", "detail": "No email"}
                )
                continue

            activity = Activity(
                contact_id=uuid.UUID(cid),
                activity_type=ActivityType.EMAIL,
                subject=composed.get("subject", ""),
                body=f"{composed.get('hook', '')}\n\n{composed.get('body', '')}",
                direction="outbound",
                status="queued",
            )
            db.add(activity)
            db.commit()
            db.refresh(activity)

            send_personalized_email_task.delay(
                contact_id=cid,
                subject=composed.get("subject", ""),
                body_text=f"{composed.get('hook', '')}\n\n{composed.get('body', '')}",
                activity_id=str(activity.id),
            )
            sent += 1
            results.append(
                {"contact_id": cid, "status": "queued", "activity_id": str(activity.id)}
            )
        except Exception as e:
            failed += 1
            results.append(
                {"contact_id": cid, "status": "error", "detail": str(e)}
            )

    return BatchSendResponse(
        sent=sent, failed=failed, results=results
    )


# ---- Tracking (public, no auth) ----


tracking_router = APIRouter(prefix="/track", tags=["tracking"])


@tracking_router.get("/open/{activity_id}.png")
def track_open(activity_id: str, db: Session = Depends(get_db)):
    try:
        aid = uuid.UUID(activity_id)
        activity = db.query(Activity).filter(Activity.id == aid).first()
        if activity:
            activity.status = "opened"
            from revenue_os.models.activity import EmailActivity

            ea = (
                db.query(EmailActivity)
                .filter(EmailActivity.activity_id == aid)
                .first()
            )
            if ea and not ea.opened_at:
                ea.opened_at = datetime.now(timezone.utc)

                open_activity = Activity(
                    contact_id=activity.contact_id,
                    activity_type=ActivityType.EMAIL_OPEN,
                    subject=activity.subject,
                    direction="inbound",
                    status="tracked",
                )
                db.add(open_activity)

            db.commit()
    except Exception:
        db.rollback()

    return Response(
        content=(
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00"
            b"\x80\x00\x00\xff\xff\xff\x00\x00\x00"
            b"\x21\xf9\x04\x00\x00\x00\x00\x00"
            b"\x2c\x00\x00\x00\x00\x01\x00\x01\x00"
            b"\x00\x02\x02\x44\x01\x00\x3b"
        ),
        media_type="image/gif",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@tracking_router.get("/click/{activity_id}")
def track_click(activity_id: str, url: str = Query(...), db: Session = Depends(get_db)):
    try:
        aid = uuid.UUID(activity_id)
        activity = db.query(Activity).filter(Activity.id == aid).first()
        if activity:
            from revenue_os.models.activity import EmailActivity

            ea = (
                db.query(EmailActivity)
                .filter(EmailActivity.activity_id == aid)
                .first()
            )
            if ea and not ea.clicked_at:
                ea.clicked_at = datetime.now(timezone.utc)

            click_activity = Activity(
                contact_id=activity.contact_id,
                activity_type=ActivityType.EMAIL_CLICK,
                subject=activity.subject,
                body=url,
                direction="inbound",
                status="tracked",
            )
            db.add(click_activity)
            db.commit()
    except Exception:
        db.rollback()

    from urllib.parse import urlparse

    if urlparse(url).scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Invalid redirect URL")

    return RedirectResponse(url=url)


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


# ---- Enroll ----

class EnrollRequest(BaseModel):
    contact_ids: list[str] = Field(..., min_length=1, max_length=100)


class EnrollResponse(BaseModel):
    enrolled: int
    already_active: int
    results: list[dict]


@router.post("/sequences/{seq_id}/enroll", response_model=EnrollResponse)
def enroll_contacts(
    seq_id: str,
    body: EnrollRequest,
    db: Session = Depends(get_db),
):
    from revenue_os.models.sequence_enrollment import SequenceEnrollment

    seq = (
        db.query(OutreachSequence)
        .filter(OutreachSequence.id == seq_id)
        .first()
    )
    if not seq:
        raise HTTPException(status_code=404, detail="Sequence not found")

    enrolled = 0
    already_active = 0
    results = []

    for cid in body.contact_ids:
        contact_uuid = uuid.UUID(cid)
        existing = (
            db.query(SequenceEnrollment)
            .filter(
                SequenceEnrollment.sequence_id == uuid.UUID(seq_id),
                SequenceEnrollment.contact_id == contact_uuid,
                SequenceEnrollment.status == "active",
            )
            .first()
        )
        if existing:
            already_active += 1
            results.append(
                {"contact_id": cid, "status": "already_active"}
            )
            continue

        enrollment = SequenceEnrollment(
            sequence_id=uuid.UUID(seq_id),
            contact_id=contact_uuid,
            current_step=1,
            status="active",
            channel=seq.channel,
        )
        db.add(enrollment)
        enrolled += 1
        results.append({"contact_id": cid, "status": "enrolled"})

    db.commit()
    return EnrollResponse(
        enrolled=enrolled,
        already_active=already_active,
        results=results,
    )


@router.get("/sequences/{seq_id}/enrollments")
def list_enrollments(
    seq_id: str,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    from revenue_os.models.sequence_enrollment import SequenceEnrollment
    from revenue_os.models.contact import Contact

    query = (
        db.query(SequenceEnrollment)
        .join(Contact, SequenceEnrollment.contact_id == Contact.id)
        .filter(SequenceEnrollment.sequence_id == uuid.UUID(seq_id))
    )
    if status:
        query = query.filter(SequenceEnrollment.status == status)

    enrollments = query.order_by(SequenceEnrollment.started_at.desc()).all()
    return [
        {
            "id": str(e.id),
            "contact_id": str(e.contact_id),
            "contact_name": e.contact.full_name if e.contact else None,
            "contact_email": e.contact.email if e.contact else None,
            "contact_status": e.contact.status.value if e.contact else None,
            "current_step": e.current_step,
            "status": e.status,
            "channel": e.channel,
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "updated_at": e.updated_at.isoformat() if e.updated_at else None,
        }
        for e in enrollments
    ]


# ---- Preview ----

class PreviewRequest(BaseModel):
    contact_id: str
    angle: Optional[str] = None
    product_description: Optional[str] = None


class PreviewResponse(BaseModel):
    subject: str
    hook: str
    body: str
    cta: str
    angle_used: str
    profile_summary: dict


@router.post("/preview", response_model=PreviewResponse)
def preview_email(body: PreviewRequest, db: Session = Depends(get_db)):
    profile = build_prospect_profile(db, body.contact_id)
    if "error" in profile:
        raise HTTPException(status_code=404, detail=profile["error"])

    composed = compose_email(
        profile,
        angle=body.angle,
        product_description=body.product_description,
    )

    contact = profile.get("contact", {})
    company = profile.get("company") or {}

    return PreviewResponse(
        subject=composed.get("subject", ""),
        hook=composed.get("hook", ""),
        body=composed.get("body", ""),
        cta=composed.get("cta", ""),
        angle_used=composed.get("angle_used", body.angle or "auto"),
        profile_summary={
            "name": contact.get("full_name", ""),
            "title": contact.get("title", ""),
            "company": company.get("name", ""),
            "industry": company.get("industry", ""),
            "signals": profile.get("signals", {}),
        },
    )


# ---- AI ----

@router.post("/generate-email", response_model=AIEmailResponse)
def generate_email(body: AIEmailRequest):
    email = generate_cold_email(
        prospect_name=body.prospect_name,
        company_name=body.company_name,
        context=body.context,
    )
    return AIEmailResponse(email_body=email)
