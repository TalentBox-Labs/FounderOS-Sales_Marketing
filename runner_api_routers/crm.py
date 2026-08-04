"""CRM REST endpoints — contacts and deals for the frontend."""

from __future__ import annotations

import logging
import uuid as uuid_lib
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field

from revenue_os.automation.events import Event, EventBus, EventType
from revenue_os.database import SessionLocal
from revenue_os.models.activity import Activity, ActivityType
from revenue_os.models.contact import Contact, ContactStatus
from revenue_os.models.deal import Deal, DealStage
from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/crm", tags=["crm"])


def _contact_dict(c: Contact) -> dict[str, Any]:
    return {
        "id": str(c.id),
        "first_name": c.first_name,
        "last_name": c.last_name,
        "name": f"{c.first_name} {c.last_name}".strip(),
        "email": c.email,
        "phone": getattr(c, "phone", None),
        "title": getattr(c, "title", None),
        "status": c.status.value if c.status else None,
        "lead_score": c.lead_score or 0,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


def _deal_dict(d: Deal, contact_name: str | None = None) -> dict[str, Any]:
    return {
        "id": str(d.id),
        "name": d.name,
        "stage": d.stage.value if d.stage else None,
        "probability": d.probability,
        "value": d.value,
        "currency": d.currency,
        "contact_id": str(d.contact_id) if d.contact_id else None,
        "contact_name": contact_name,
        "expected_close_date": d.expected_close_date.isoformat() if d.expected_close_date else None,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


def _activity_dict(a: Activity) -> dict[str, Any]:
    return {
        "id": str(a.id),
        "contact_id": str(a.contact_id) if a.contact_id else None,
        "deal_id": str(a.deal_id) if a.deal_id else None,
        "activity_type": a.activity_type.value if a.activity_type else None,
        "subject": a.subject,
        "body": a.body,
        "due_date": a.due_date.isoformat() if a.due_date else None,
        "is_completed": bool(a.is_completed),
        "completed_at": a.completed_at.isoformat() if a.completed_at else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


class ContactCreateRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(default="", max_length=100)
    email: str = Field(..., min_length=3, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    title: str | None = Field(default=None, max_length=255)
    status: str = Field(default="prospect")


class DealCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    value: float = Field(default=0.0, ge=0)
    stage: str = Field(default="discovery")
    contact_id: str | None = None


class ActivityCreateRequest(BaseModel):
    contact_id: str | None = None
    deal_id: str | None = None
    activity_type: str = Field(default="note")
    subject: str | None = Field(default=None, max_length=500)
    body: str | None = None
    due_date: str | None = None


@router.get("/contacts")
def list_contacts(
    status: str | None = Query(None),
    search: str | None = Query(None, max_length=100),
    limit: int = Query(100, ge=1, le=500),
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        query = db.query(Contact).order_by(Contact.created_at.desc())
        if status:
            try:
                query = query.filter(Contact.status == ContactStatus(status))
            except ValueError:
                raise HTTPException(status_code=422, detail=f"Invalid status: {status}")
        if search:
            like = f"%{search}%"
            query = query.filter(
                (Contact.first_name.ilike(like))
                | (Contact.last_name.ilike(like))
                | (Contact.email.ilike(like))
            )
        contacts = [_contact_dict(c) for c in query.limit(limit).all()]
        return {"ok": True, "count": len(contacts), "contacts": contacts}
    finally:
        db.close()


@router.get("/contacts/{contact_id}")
def get_contact(
    contact_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        try:
            cid = uuid_lib.UUID(contact_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid contact_id")
        contact = db.get(Contact, cid)
        if contact is None:
            raise HTTPException(status_code=404, detail="Contact not found")

        deals = db.query(Deal).filter(Deal.contact_id == cid).order_by(Deal.created_at.desc()).all()
        activities = (
            db.query(Activity)
            .filter(Activity.contact_id == cid)
            .order_by(Activity.created_at.desc())
            .limit(100).all()
        )
        result = _contact_dict(contact)
        result["deals"] = [_deal_dict(d) for d in deals]
        result["activities"] = [_activity_dict(a) for a in activities]
        return {"ok": True, "contact": result}
    finally:
        db.close()


@router.post("/contacts")
def create_contact(
    req: ContactCreateRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    try:
        status = ContactStatus(req.status)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid status: {req.status}")

    db = SessionLocal()
    try:
        if db.query(Contact).filter(Contact.email == req.email).first() is not None:
            raise HTTPException(status_code=409, detail="A contact with this email already exists")
        contact = Contact(
            first_name=req.first_name,
            last_name=req.last_name or "",
            email=req.email,
            status=status,
        )
        if req.phone and hasattr(contact, "phone"):
            contact.phone = req.phone
        if req.title and hasattr(contact, "title"):
            contact.title = req.title
        db.add(contact)
        db.commit()
        db.refresh(contact)
        result = _contact_dict(contact)
    finally:
        db.close()

    try:
        EventBus.publish(Event(
            event_type=EventType.LEAD_CREATED,
            source="crm_api",
            entity_id=result["id"],
            entity_type="contact",
            data={"email": result["email"], "name": result["name"]},
        ))
    except Exception as e:
        logger.warning(f"LEAD_CREATED publish failed: {e}")
    return {"ok": True, "contact": result}


@router.get("/deals")
def list_deals(
    stage: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        query = db.query(Deal).order_by(Deal.created_at.desc())
        if stage:
            try:
                query = query.filter(Deal.stage == DealStage(stage))
            except ValueError:
                raise HTTPException(status_code=422, detail=f"Invalid stage: {stage}")
        deals = query.limit(limit).all()

        contact_ids = {d.contact_id for d in deals if d.contact_id}
        names: dict = {}
        if contact_ids:
            for c in db.query(Contact).filter(Contact.id.in_(contact_ids)).all():
                names[c.id] = f"{c.first_name} {c.last_name}".strip()

        return {
            "ok": True,
            "count": len(deals),
            "deals": [_deal_dict(d, names.get(d.contact_id)) for d in deals],
        }
    finally:
        db.close()


@router.get("/deals/{deal_id}")
def get_deal(
    deal_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        try:
            did = uuid_lib.UUID(deal_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid deal_id")
        deal = db.get(Deal, did)
        if deal is None:
            raise HTTPException(status_code=404, detail="Deal not found")

        contact_name = None
        if deal.contact_id:
            contact = db.get(Contact, deal.contact_id)
            contact_name = f"{contact.first_name} {contact.last_name}".strip() if contact else None

        activities = (
            db.query(Activity)
            .filter(Activity.deal_id == did)
            .order_by(Activity.created_at.desc())
            .limit(100).all()
        )
        result = _deal_dict(deal, contact_name)
        result["activities"] = [_activity_dict(a) for a in activities]
        return {"ok": True, "deal": result}
    finally:
        db.close()


@router.post("/deals")
def create_deal(
    req: DealCreateRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    try:
        stage = DealStage(req.stage)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid stage: {req.stage}")

    db = SessionLocal()
    try:
        contact_id = None
        if req.contact_id:
            try:
                contact_id = uuid_lib.UUID(req.contact_id)
            except ValueError:
                raise HTTPException(status_code=422, detail="Invalid contact_id")
            if db.get(Contact, contact_id) is None:
                raise HTTPException(status_code=404, detail="Contact not found")

        from revenue_os.services.deal_automation_service import get_or_create_sales_pipeline

        pipeline = get_or_create_sales_pipeline(db)
        deal = Deal(
            name=req.name, value=req.value, stage=stage,
            contact_id=contact_id, pipeline_id=pipeline.id,
        )
        db.add(deal)
        db.commit()
        db.refresh(deal)
        result = _deal_dict(deal)
    finally:
        db.close()

    try:
        EventBus.publish(Event(
            event_type=EventType.DEAL_CREATED,
            source="crm_api",
            entity_id=result["id"],
            entity_type="deal",
            data={"value": result["value"], "stage": result["stage"]},
        ))
    except Exception as e:
        logger.warning(f"DEAL_CREATED publish failed: {e}")
    return {"ok": True, "deal": result}


@router.get("/pipeline")
def pipeline_summary(_: str | None = Depends(_verify_api_key)) -> dict[str, Any]:
    from revenue_os.services.deal_automation_service import get_pipeline_health

    db = SessionLocal()
    try:
        return {"ok": True, "pipeline": get_pipeline_health(db)}
    finally:
        db.close()


@router.get("/activities")
def list_activities(
    contact_id: str | None = Query(None),
    deal_id: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        query = db.query(Activity)
        if contact_id:
            try:
                query = query.filter(Activity.contact_id == uuid_lib.UUID(contact_id))
            except ValueError:
                raise HTTPException(status_code=422, detail="Invalid contact_id")
        if deal_id:
            try:
                query = query.filter(Activity.deal_id == uuid_lib.UUID(deal_id))
            except ValueError:
                raise HTTPException(status_code=422, detail="Invalid deal_id")
        activities = query.order_by(Activity.created_at.desc()).limit(limit).all()
        return {"ok": True, "count": len(activities), "activities": [_activity_dict(a) for a in activities]}
    finally:
        db.close()


@router.post("/activities")
def create_activity(
    req: ActivityCreateRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    try:
        activity_type = ActivityType(req.activity_type)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid activity_type: {req.activity_type}")

    if not req.contact_id and not req.deal_id:
        raise HTTPException(status_code=422, detail="contact_id or deal_id is required")

    due_date = None
    if req.due_date:
        try:
            due_date = datetime.fromisoformat(req.due_date)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid due_date — use ISO 8601")

    db = SessionLocal()
    try:
        contact_id = None
        if req.contact_id:
            try:
                contact_id = uuid_lib.UUID(req.contact_id)
            except ValueError:
                raise HTTPException(status_code=422, detail="Invalid contact_id")
            if db.get(Contact, contact_id) is None:
                raise HTTPException(status_code=404, detail="Contact not found")

        deal_id = None
        if req.deal_id:
            try:
                deal_id = uuid_lib.UUID(req.deal_id)
            except ValueError:
                raise HTTPException(status_code=422, detail="Invalid deal_id")
            if db.get(Deal, deal_id) is None:
                raise HTTPException(status_code=404, detail="Deal not found")

        activity = Activity(
            contact_id=contact_id, deal_id=deal_id,
            activity_type=activity_type, subject=req.subject, body=req.body,
            due_date=due_date, status="completed" if activity_type != ActivityType.TASK else "pending",
        )
        db.add(activity)

        if contact_id:
            contact = db.get(Contact, contact_id)
            contact.last_contacted_at = datetime.now(timezone.utc)
            db.add(contact)

        db.commit()
        db.refresh(activity)
        return {"ok": True, "activity": _activity_dict(activity)}
    finally:
        db.close()


@router.post("/activities/{activity_id}/complete")
def complete_activity(
    activity_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        try:
            aid = uuid_lib.UUID(activity_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid activity_id")
        activity = db.get(Activity, aid)
        if activity is None:
            raise HTTPException(status_code=404, detail="Activity not found")

        activity.is_completed = 1
        activity.completed_at = datetime.now(timezone.utc)
        activity.status = "completed"
        db.add(activity)
        db.commit()
        db.refresh(activity)
        return {"ok": True, "activity": _activity_dict(activity)}
    finally:
        db.close()


@router.get("/followups")
def followups(_: str | None = Depends(_verify_api_key)) -> dict[str, Any]:
    from revenue_os.services.followups import get_followups

    return {"ok": True, **get_followups()}
