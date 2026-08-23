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
from revenue_os.models.contact import Company, Contact, ContactStatus, Industry
from revenue_os.models.deal import Deal, DealStage
from revenue_os.services.deal_automation_service import apply_deal_stage_update
from revenue_os.services.lead_scoring_service import (
    apply_contact_status_update,
    score_contact,
)
from revenue_os.services.tenant_mutation_guard import (
    assign_new_deal_org,
    crm_tenant_org_id,
    optional_tenant_mutation,
    resolve_crm_tenant_read,
    scoped_contact,
    scoped_deal,
)
from revenue_os.services.tenant_scoped_access import (
    apply_contact_org_filter,
    apply_deal_org_filter,
    stamp_new_contact_org,
    verify_activity_in_tenant,
)
from runner_api_routers.utils import _verify_api_key
from src.tools.editorial_approval import is_human_approver

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
        "title": c.designation,
        "designation": c.designation,
        "linkedin_url": c.linkedin_url,
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
        "closed_at": d.closed_at.isoformat() if d.closed_at else None,
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
        "status": a.status,
        "scheduled_at": a.scheduled_at.isoformat() if a.scheduled_at else None,
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
    linkedin_url: str | None = Field(default=None, max_length=500)
    status: str = Field(default="prospect")


class EnrichRequest(BaseModel):
    linkedin_url: str | None = Field(default=None, max_length=500)


class DealCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    value: float = Field(default=0.0, ge=0)
    stage: str = Field(default="discovery")
    contact_id: str | None = None


class DealStageUpdateRequest(BaseModel):
    """SALES A3 — human-gated runner deal stage update."""

    stage: str = Field(..., min_length=1, max_length=64)
    requested_by: str = Field(..., min_length=2, max_length=200, description="Human requester name")
    notes: str = Field(default="", max_length=2000)


class ContactStatusUpdateRequest(BaseModel):
    """SALES A4 — human-gated runner contact status update."""

    status: str = Field(..., min_length=1, max_length=64)
    requested_by: str = Field(..., min_length=2, max_length=200, description="Human requester name")
    notes: str = Field(default="", max_length=2000)


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
    tenant = resolve_crm_tenant_read()
    org_id = crm_tenant_org_id(tenant)
    db = SessionLocal()
    try:
        query = apply_contact_org_filter(
            db.query(Contact).order_by(Contact.created_at.desc()), org_id
        )
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
    tenant = resolve_crm_tenant_read()
    org_id = crm_tenant_org_id(tenant)
    db = SessionLocal()
    try:
        contact = scoped_contact(db, tenant, contact_id)
        cid = contact.id

        deals = apply_deal_org_filter(
            db.query(Deal).filter(Deal.contact_id == cid).order_by(Deal.created_at.desc()),
            org_id,
        ).all()
        activities = (
            db.query(Activity)
            .filter(Activity.contact_id == cid)
            .order_by(Activity.created_at.desc())
            .limit(100)
            .all()
        )
        if org_id is not None:
            activities = [a for a in activities if verify_activity_in_tenant(db, org_id, a)]
        result = _contact_dict(contact)
        result["deals"] = [_deal_dict(d) for d in deals]
        result["activities"] = [_activity_dict(a) for a in activities]
        return {"ok": True, "contact": result}
    finally:
        db.close()


@router.post("/contacts/{contact_id}/enrich")
def enrich_contact(
    contact_id: str,
    req: EnrichRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Enrich a contact (and their company) from LinkedIn via Proxycurl.

    Updates real fields from a licensed data provider — never guesses.
    Logs the result to the contact's timeline either way.
    """
    from revenue_os.services.linkedin_enrichment import (
        enrich_company,
        enrich_person,
        map_industry,
        score_icp_fit,
    )

    tenant = optional_tenant_mutation()
    org_id = crm_tenant_org_id(tenant)
    db = SessionLocal()
    try:
        contact = scoped_contact(db, tenant, contact_id)
        cid = contact.id

        linkedin_url = req.linkedin_url or contact.linkedin_url
        if not linkedin_url:
            raise HTTPException(
                status_code=422,
                detail="No LinkedIn URL on this contact — pass one or set it on the contact first",
            )
        if req.linkedin_url and req.linkedin_url != contact.linkedin_url:
            contact.linkedin_url = req.linkedin_url

        person = enrich_person(linkedin_url, organization_id=org_id)
        if not person.get("configured"):
            return {"ok": False, "configured": False, "reason": person.get("reason")}
        if not person.get("ok"):
            return {"ok": False, "configured": True, "reason": person.get("reason")}

        profile = person["profile"]
        if profile.get("occupation"):
            contact.designation = str(profile["occupation"])[:255]

        icp = None
        company_dict = None
        experiences = profile.get("experiences") or []
        current_exp = next((e for e in experiences if not e.get("ends_at")), experiences[0] if experiences else None)
        company_linkedin_url = (current_exp or {}).get("company_linkedin_profile_url")

        if company_linkedin_url:
            company_res = enrich_company(company_linkedin_url, organization_id=org_id)
            if company_res.get("ok"):
                c_profile = company_res["profile"]
                industry = map_industry(c_profile.get("industry"))
                employee_count = None
                size = c_profile.get("company_size")
                if isinstance(size, list) and len(size) == 2 and size[1]:
                    employee_count = size[1]

                company = contact.company
                if company is None:
                    company = Company(name=c_profile.get("name") or (current_exp or {}).get("company") or "Unknown")
                    db.add(company)
                    db.flush()
                    contact.company_id = company.id
                company.industry = Industry(industry)
                if employee_count:
                    company.employee_count = employee_count
                if c_profile.get("description"):
                    company.description = str(c_profile["description"])[:2000]
                if c_profile.get("website"):
                    company.website_url = c_profile["website"]
                company.linkedin_url = company_linkedin_url
                db.add(company)

                icp = score_icp_fit(industry, employee_count)
                company_dict = {
                    "name": company.name, "industry": industry, "employee_count": employee_count,
                }

        db.add(contact)
        db.commit()
        db.refresh(contact)

        note_body = f"Enriched from LinkedIn — {icp['fit']} ICP fit ({icp['score']}/100)." if icp else \
            "Enriched from LinkedIn (person profile only — no current employer match on LinkedIn)."
        db.add(Activity(
            contact_id=cid, activity_type=ActivityType.NOTE,
            subject="LinkedIn enrichment", body=note_body, status="completed",
        ))
        db.commit()

        result = _contact_dict(contact)
    finally:
        db.close()

    return {
        "ok": True, "configured": True,
        "contact": result,
        "headline": profile.get("headline"),
        "company": company_dict,
        "icp_fit": icp,
    }


@router.post("/contacts")
def create_contact(
    req: ContactCreateRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    try:
        status = ContactStatus(req.status)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid status: {req.status}")

    tenant = optional_tenant_mutation()
    org_id = crm_tenant_org_id(tenant)
    db = SessionLocal()
    try:
        email_q = apply_contact_org_filter(db.query(Contact).filter(Contact.email == req.email), org_id)
        if email_q.first() is not None:
            raise HTTPException(status_code=409, detail="A contact with this email already exists")
        contact = Contact(
            first_name=req.first_name,
            last_name=req.last_name or "",
            email=req.email,
            status=status,
        )
        stamp_new_contact_org(contact, org_id)
        if req.phone:
            contact.phone = req.phone
        if req.title:
            contact.designation = req.title
        if req.linkedin_url:
            contact.linkedin_url = req.linkedin_url
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

    try:
        from revenue_os.services.search_service import index_contact

        index_contact(
            uuid_lib.UUID(result["id"]), req.first_name, req.last_name or "",
            email=req.email, designation=req.title,
        )
    except Exception as e:
        logger.warning(f"Contact search-index failed: {e}")

    return {"ok": True, "contact": result}


@router.post("/contacts/{contact_id}/score")
def score_contact_endpoint(
    contact_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """SALES A4: score a contact without mutating Contact.status."""
    tenant = resolve_crm_tenant_read()
    db = SessionLocal()
    try:
        contact = scoped_contact(db, tenant, contact_id)
        payload = score_contact(db, contact)
        db.commit()
        db.refresh(contact)
        contact_payload = _contact_dict(contact)
    finally:
        db.close()

    try:
        EventBus.publish(
            Event(
                event_type=EventType.LEAD_SCORED,
                source="crm_api",
                entity_id=contact_payload["id"],
                entity_type="contact",
                data={
                    "score": payload["score"],
                    "old_score": payload["old_score"],
                    "suggested_status": payload["suggested_status"],
                    "status": payload["status"],
                    "status_changed": False,
                },
            )
        )
    except Exception as e:
        logger.warning(f"LEAD_SCORED publish failed: {e}")

    return {
        "ok": True,
        "score": payload["score"],
        "old_score": payload["old_score"],
        "suggested_status": payload["suggested_status"],
        "status_changed": False,
        "contact": contact_payload,
    }


@router.patch("/contacts/{contact_id}/status")
def update_contact_status_endpoint(
    contact_id: str,
    req: ContactStatusUpdateRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """SALES A4: human-gated Contact.status update."""
    if not is_human_approver(req.requested_by):
        raise HTTPException(
            status_code=403,
            detail=(
                "Human requester required for contact status changes. "
                "AI/automation identities cannot qualify leads."
            ),
        )

    try:
        new_status = ContactStatus(req.status.strip().lower())
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid status: {req.status}")

    tenant = optional_tenant_mutation()
    db = SessionLocal()
    try:
        contact = scoped_contact(db, tenant, contact_id)
        result = apply_contact_status_update(
            db, contact, new_status, requested_by=req.requested_by.strip()
        )
        contact_payload = _contact_dict(contact)
    finally:
        db.close()

    if result["changed"]:
        try:
            EventBus.publish(
                Event(
                    event_type=EventType.CONTACT_STATUS_CHANGED,
                    source="crm_api",
                    entity_id=contact_payload["id"],
                    entity_type="contact",
                    data={
                        "old_status": result["old_status"],
                        "new_status": result["new_status"],
                        "requested_by": req.requested_by.strip(),
                        "notes": (req.notes or "").strip() or None,
                        "lead_score": result["lead_score"],
                    },
                )
            )
        except Exception as e:
            logger.warning(f"CONTACT_STATUS_CHANGED publish failed: {e}")

    return {
        "ok": True,
        "changed": result["changed"],
        "requested_by": req.requested_by.strip(),
        "old_status": result["old_status"],
        "new_status": result["new_status"],
        "contact": contact_payload,
    }


@router.get("/deals")
def list_deals(
    stage: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    tenant = resolve_crm_tenant_read()
    org_id = crm_tenant_org_id(tenant)
    db = SessionLocal()
    try:
        query = apply_deal_org_filter(
            db.query(Deal).order_by(Deal.created_at.desc()), org_id
        )
        if stage:
            try:
                query = query.filter(Deal.stage == DealStage(stage))
            except ValueError:
                raise HTTPException(status_code=422, detail=f"Invalid stage: {stage}")
        deals = query.limit(limit).all()

        contact_ids = {d.contact_id for d in deals if d.contact_id}
        names: dict = {}
        if contact_ids:
            contact_q = apply_contact_org_filter(
                db.query(Contact).filter(Contact.id.in_(contact_ids)), org_id
            )
            for c in contact_q.all():
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
    tenant = resolve_crm_tenant_read()
    org_id = crm_tenant_org_id(tenant)
    db = SessionLocal()
    try:
        deal = scoped_deal(db, tenant, deal_id)
        did = deal.id

        contact_name = None
        if deal.contact_id:
            contact = scoped_contact(db, tenant, str(deal.contact_id))
            contact_name = f"{contact.first_name} {contact.last_name}".strip()

        activities = (
            db.query(Activity)
            .filter(Activity.deal_id == did)
            .order_by(Activity.created_at.desc())
            .limit(100)
            .all()
        )
        if org_id is not None:
            activities = [a for a in activities if verify_activity_in_tenant(db, org_id, a)]
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

    tenant = optional_tenant_mutation()
    org_id = crm_tenant_org_id(tenant)
    db = SessionLocal()
    try:
        contact_id = None
        if req.contact_id:
            contact = scoped_contact(db, tenant, req.contact_id)
            contact_id = contact.id

        from revenue_os.services.deal_automation_service import get_or_create_sales_pipeline

        pipeline = get_or_create_sales_pipeline(db)
        deal = Deal(
            name=req.name, value=req.value, stage=stage,
            contact_id=contact_id, pipeline_id=pipeline.id,
        )
        assign_new_deal_org(deal, tenant)
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

    try:
        from revenue_os.services.search_service import index_deal

        index_deal(uuid_lib.UUID(result["id"]), req.name)
    except Exception as e:
        logger.warning(f"Deal search-index failed: {e}")

    return {"ok": True, "deal": result}


@router.patch("/deals/{deal_id}/stage")
def update_deal_stage(
    deal_id: str,
    req: DealStageUpdateRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """SALES A3: human-gated deal stage update via ``advance_deal_stage``.

    Does not emit CommercialOutcome or call external webhooks.
    """
    if not is_human_approver(req.requested_by):
        raise HTTPException(
            status_code=403,
            detail=(
                "Human requester required for deal stage changes. "
                "AI/automation identities cannot advance deals."
            ),
        )

    try:
        new_stage = DealStage(req.stage.strip().lower())
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid stage: {req.stage}")

    tenant = optional_tenant_mutation()
    db = SessionLocal()
    try:
        deal = scoped_deal(db, tenant, deal_id)
        try:
            result = apply_deal_stage_update(
                db, deal, new_stage, requested_by=req.requested_by.strip()
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        deal_payload = _deal_dict(deal)
    finally:
        db.close()

    try:
        EventBus.publish(
            Event(
                event_type=EventType.DEAL_STAGE_CHANGED,
                source="crm_api",
                entity_id=deal_payload["id"],
                entity_type="deal",
                data={
                    "old_stage": result["old_stage"],
                    "new_stage": result["new_stage"],
                    "probability": result["probability"],
                    "changed": result["changed"],
                    "requested_by": req.requested_by.strip(),
                    "notes": (req.notes or "").strip() or None,
                    "commercial_outcome_emitted": False,
                },
            )
        )
    except Exception as e:
        logger.warning(f"DEAL_STAGE_CHANGED publish failed: {e}")

    return {
        "ok": True,
        "changed": result["changed"],
        "requested_by": req.requested_by.strip(),
        "old_stage": result["old_stage"],
        "new_stage": result["new_stage"],
        "commercial_outcome_emitted": False,
        "deal": deal_payload,
    }


@router.get("/pipeline")
def pipeline_summary(_: str | None = Depends(_verify_api_key)) -> dict[str, Any]:
    from revenue_os.services.deal_automation_service import get_pipeline_health

    tenant = resolve_crm_tenant_read()
    org_id = crm_tenant_org_id(tenant)
    db = SessionLocal()
    try:
        return {"ok": True, "pipeline": get_pipeline_health(db, organization_id=org_id)}
    finally:
        db.close()


@router.get("/activities")
def list_activities(
    contact_id: str | None = Query(None),
    deal_id: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    tenant = resolve_crm_tenant_read()
    org_id = crm_tenant_org_id(tenant)
    db = SessionLocal()
    try:
        query = db.query(Activity)
        if contact_id:
            scoped_contact(db, tenant, contact_id)
            query = query.filter(Activity.contact_id == uuid_lib.UUID(contact_id))
        if deal_id:
            scoped_deal(db, tenant, deal_id)
            query = query.filter(Activity.deal_id == uuid_lib.UUID(deal_id))
        activities = query.order_by(Activity.created_at.desc()).limit(limit).all()
        if org_id is not None and not contact_id and not deal_id:
            activities = [
                a for a in activities if verify_activity_in_tenant(db, org_id, a)
            ]
        elif org_id is not None:
            activities = [
                a for a in activities if verify_activity_in_tenant(db, org_id, a)
            ]
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

    tenant = optional_tenant_mutation()
    org_id = crm_tenant_org_id(tenant)
    db = SessionLocal()
    try:
        contact_id = None
        if req.contact_id:
            contact = scoped_contact(db, tenant, req.contact_id)
            contact_id = contact.id

        deal_id = None
        if req.deal_id:
            deal = scoped_deal(db, tenant, req.deal_id)
            deal_id = deal.id

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
        result = _activity_dict(activity)
    finally:
        db.close()

    try:
        from revenue_os.services.search_service import index_activity

        index_activity(activity.id, subject=req.subject, body=req.body)
    except Exception as e:
        logger.warning(f"Activity search-index failed: {e}")

    return {"ok": True, "activity": result}


@router.post("/activities/{activity_id}/complete")
def complete_activity(
    activity_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    tenant = optional_tenant_mutation()
    org_id = crm_tenant_org_id(tenant)
    db = SessionLocal()
    try:
        try:
            aid = uuid_lib.UUID(activity_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid activity_id")
        activity = db.get(Activity, aid)
        if activity is None:
            raise HTTPException(status_code=404, detail="Activity not found")
        if org_id is not None and not verify_activity_in_tenant(db, org_id, activity):
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

    tenant = resolve_crm_tenant_read()
    org_id = crm_tenant_org_id(tenant)
    return {"ok": True, **get_followups(organization_id=org_id)}
