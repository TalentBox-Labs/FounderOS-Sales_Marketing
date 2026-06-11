from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from revenue_os.database import get_db
from revenue_os.models.activity import Activity
from revenue_os.models.contact import Contact, ContactStatus
from revenue_os.models.content import ContentLibrary, SocialPost
from revenue_os.models.deal import Deal, DealStage
from revenue_os.models.project import BillingRecord, Project, ProjectStatus

router = APIRouter(prefix="/command-center", tags=["command-center"])


@router.get("")
def founder_command_center(db: Session = Depends(get_db)):
    total_contacts = db.query(Contact).count()
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    new_contacts_30d = (
        db.query(Contact)
        .filter(Contact.created_at >= thirty_days_ago)
        .count()
    )

    leads = (
        db.query(Contact)
        .filter(Contact.status == ContactStatus.LEAD)
        .count()
    )
    qualified = (
        db.query(Contact)
        .filter(Contact.status == ContactStatus.QUALIFIED)
        .count()
    )
    customers = (
        db.query(Contact)
        .filter(Contact.status == ContactStatus.CUSTOMER)
        .count()
    )

    active_deals = (
        db.query(Deal)
        .filter(
            Deal.stage.notin_(
                [DealStage.CLOSED_WON, DealStage.CLOSED_LOST]
            )
        )
        .count()
    )

    won_deals = db.query(Deal).filter(
        Deal.stage == DealStage.CLOSED_WON
    ).count()
    lost_deals = db.query(Deal).filter(
        Deal.stage == DealStage.CLOSED_LOST
    ).count()
    win_rate = (
        round(won_deals / (won_deals + lost_deals) * 100, 1)
        if (won_deals + lost_deals) > 0
        else 0
    )

    pipeline_value = (
        db.query(func.coalesce(func.sum(Deal.value), 0))
        .filter(
            Deal.stage.notin_(
                [DealStage.CLOSED_WON, DealStage.CLOSED_LOST]
            )
        )
        .scalar()
    )

    weighted_pipeline = db.query(
        func.coalesce(
            func.sum(Deal.value * Deal.probability / 100), 0
        )
    ).filter(
        Deal.stage.notin_(
            [DealStage.CLOSED_WON, DealStage.CLOSED_LOST]
        )
    ).scalar()

    won_revenue = (
        db.query(func.coalesce(func.sum(Deal.value), 0))
        .filter(Deal.stage == DealStage.CLOSED_WON)
        .scalar()
    )

    active_projects = (
        db.query(Project)
        .filter(Project.status == ProjectStatus.ACTIVE)
        .count()
    )

    total_outstanding = (
        db.query(func.coalesce(func.sum(BillingRecord.amount), 0))
        .filter(BillingRecord.status == "pending")
        .scalar()
    )

    total_paid = (
        db.query(func.coalesce(func.sum(BillingRecord.amount), 0))
        .filter(BillingRecord.status == "paid")
        .scalar()
    )

    draft_content = (
        db.query(ContentLibrary)
        .filter(ContentLibrary.status == "draft")
        .count()
    )

    scheduled_posts = (
        db.query(SocialPost)
        .filter(
            SocialPost.status == "scheduled",
            SocialPost.scheduled_at.isnot(None),
        )
        .count()
    )

    recent_activities = (
        db.query(Activity)
        .order_by(Activity.performed_at.desc())
        .limit(5)
        .all()
    )

    return {
        "revenue": {
            "won_revenue": float(won_revenue),
            "pipeline_value": float(pipeline_value),
            "weighted_pipeline": float(weighted_pipeline),
            "total_outstanding": float(total_outstanding),
            "total_paid": float(total_paid),
        },
        "pipeline": {
            "active_deals": active_deals,
            "won_deals": won_deals,
            "lost_deals": lost_deals,
            "win_rate": win_rate,
        },
        "contacts": {
            "total": total_contacts,
            "new_30d": new_contacts_30d,
            "leads": leads,
            "qualified": qualified,
            "customers": customers,
        },
        "operations": {
            "active_projects": active_projects,
            "draft_content": draft_content,
            "scheduled_posts": scheduled_posts,
        },
        "recent_activity": [
            {
                "type": a.activity_type.value,
                "subject": a.subject,
                "performed_at": a.performed_at.isoformat(),
            }
            for a in recent_activities
        ],
    }
