from __future__ import annotations

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from revenue_os.database import get_db
from revenue_os.models.activity import Activity, ActivityType
from revenue_os.models.contact import Contact, ContactStatus
from revenue_os.models.deal import Deal, DealStage

router = APIRouter(prefix="/reports", tags=["reports"])


def _seq_name(subject: str | None) -> str:
    if not subject:
        return "Untitled"
    return subject[:60]


@router.get("/campaigns")
def campaign_list(db: Session = Depends(get_db)):
    subjects = (
        db.query(
            Activity.subject,
            func.count(Activity.id).label("sent"),
        )
        .filter(
            Activity.activity_type == ActivityType.EMAIL,
            Activity.direction == "outbound",
        )
        .group_by(Activity.subject)
        .order_by(func.count(Activity.id).desc())
        .limit(50)
        .all()
    )

    results = []
    for subject, sent in subjects:
        name = _seq_name(subject)

        opened = (
            db.query(func.count(Activity.id))
            .filter(
                Activity.activity_type == ActivityType.EMAIL_OPEN,
                Activity.subject == subject,
            )
            .scalar()
            or 0
        )

        replied = (
            db.query(func.count(Activity.id))
            .filter(
                Activity.activity_type == ActivityType.EMAIL_REPLY,
                Activity.subject == subject,
            )
            .scalar()
            or 0
        )

        open_rate = round((opened / sent * 100) if sent else 0, 1)
        reply_rate = round((replied / sent * 100) if sent else 0, 1)

        results.append(
            {
                "id": name,
                "name": name,
                "sent": sent,
                "opened": opened,
                "open_rate": open_rate,
                "replied": replied,
                "reply_rate": reply_rate,
                "deals_won": 0,
            }
        )

    return results


@router.get("/outreach-summary")
def outreach_summary(db: Session = Depends(get_db)):
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    total_sent_30d = (
        db.query(func.count(Activity.id))
        .filter(
            Activity.activity_type == ActivityType.EMAIL,
            Activity.direction == "outbound",
            Activity.performed_at >= thirty_days_ago,
        )
        .scalar()
        or 0
    )

    total_opened_30d = (
        db.query(func.count(Activity.id))
        .filter(
            Activity.activity_type == ActivityType.EMAIL_OPEN,
            Activity.performed_at >= thirty_days_ago,
        )
        .scalar()
        or 0
    )

    total_replied_30d = (
        db.query(func.count(Activity.id))
        .filter(
            Activity.activity_type == ActivityType.EMAIL_REPLY,
            Activity.performed_at >= thirty_days_ago,
        )
        .scalar()
        or 0
    )

    total_linkedin_30d = (
        db.query(func.count(Activity.id))
        .filter(
            Activity.activity_type.in_(
                [ActivityType.LINKEDIN_MESSAGE, ActivityType.LINKEDIN_CONNECT]
            ),
            Activity.performed_at >= thirty_days_ago,
        )
        .scalar()
        or 0
    )

    emails_by_day = (
        db.query(
            func.date(Activity.performed_at).label("day"),
            func.count(Activity.id).label("count"),
        )
        .filter(
            Activity.activity_type == ActivityType.EMAIL,
            Activity.direction == "outbound",
            Activity.performed_at >= thirty_days_ago,
        )
        .group_by(func.date(Activity.performed_at))
        .order_by(func.date(Activity.performed_at))
        .all()
    )

    new_contacts_30d = (
        db.query(func.count(Contact.id))
        .filter(Contact.created_at >= thirty_days_ago)
        .scalar()
        or 0
    )

    converted_contacts = (
        db.query(func.count(Contact.id))
        .filter(
            Contact.status == ContactStatus.CUSTOMER,
            Contact.created_at >= thirty_days_ago,
        )
        .scalar()
        or 0
    )

    return {
        "period_days": 30,
        "total_sent": total_sent_30d,
        "total_opened": total_opened_30d,
        "total_replied": total_replied_30d,
        "total_linkedin": total_linkedin_30d,
        "open_rate": round(
            (total_opened_30d / total_sent_30d * 100) if total_sent_30d else 0, 1
        ),
        "reply_rate": round(
            (total_replied_30d / total_sent_30d * 100) if total_sent_30d else 0, 1
        ),
        "emails_by_day": [
            {"date": str(row.day), "count": row.count} for row in emails_by_day
        ],
        "new_contacts": new_contacts_30d,
        "converted_to_customers": converted_contacts,
    }


@router.get("/hook-performance")
def hook_performance(db: Session = Depends(get_db)):
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    subjects = (
        db.query(
            Activity.subject,
            func.count(Activity.id).label("sent"),
        )
        .filter(
            Activity.activity_type == ActivityType.EMAIL,
            Activity.direction == "outbound",
            Activity.performed_at >= thirty_days_ago,
        )
        .group_by(Activity.subject)
        .order_by(func.count(Activity.id).desc())
        .limit(20)
        .all()
    )

    results = []
    for subject, sent in subjects:
        if not subject:
            continue
        opened = (
            db.query(func.count(Activity.id))
            .filter(
                Activity.activity_type == ActivityType.EMAIL_OPEN,
                Activity.subject == subject,
            )
            .scalar()
            or 0
        )
        replied = (
            db.query(func.count(Activity.id))
            .filter(
                Activity.activity_type == ActivityType.EMAIL_REPLY,
                Activity.subject == subject,
            )
            .scalar()
            or 0
        )
        results.append(
            {
                "subject": subject,
                "sent": sent,
                "opened": opened,
                "open_rate": round((opened / sent * 100) if sent else 0, 1),
                "replied": replied,
                "reply_rate": round((replied / sent * 100) if sent else 0, 1),
            }
        )

    return results


@router.get("/pipeline-funnel")
def pipeline_funnel(db: Session = Depends(get_db)):
    stages = [
        DealStage.DISCOVERY,
        DealStage.QUALIFIED,
        DealStage.PROPOSAL,
        DealStage.NEGOTIATION,
        DealStage.CLOSED_WON,
        DealStage.CLOSED_LOST,
    ]

    funnel = []
    for stage in stages:
        count = (
            db.query(func.count(Deal.id))
            .filter(Deal.stage == stage)
            .scalar()
            or 0
        )
        total_value = (
            db.query(func.coalesce(func.sum(Deal.value), 0))
            .filter(Deal.stage == stage)
            .scalar()
            or 0
        )
        funnel.append(
            {
                "stage": stage.value,
                "count": count,
                "total_value": float(total_value),
            }
        )

    return funnel


@router.get("/revenue-trend")
def revenue_trend(db: Session = Depends(get_db)):
    six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)

    won_by_month = (
        db.query(
            func.date_trunc("month", Deal.closed_at).label("month"),
            func.coalesce(func.sum(Deal.value), 0).label("revenue"),
            func.count(Deal.id).label("deals"),
        )
        .filter(
            Deal.stage == DealStage.CLOSED_WON,
            Deal.closed_at >= six_months_ago,
        )
        .group_by(func.date_trunc("month", Deal.closed_at))
        .order_by(func.date_trunc("month", Deal.closed_at))
        .all()
    )

    return [
        {
            "month": str(row.month),
            "revenue": float(row.revenue),
            "deals": row.deals,
        }
        for row in won_by_month
    ]


@router.get("/lead-sources")
def lead_sources(db: Session = Depends(get_db)):
    sources = (
        db.query(
            Contact.source,
            func.count(Contact.id).label("total"),
            func.sum(
                case(
                    (Contact.status == ContactStatus.CUSTOMER, 1),
                    else_=0,
                )
            ).label("converted"),
        )
        .group_by(Contact.source)
        .order_by(func.count(Contact.id).desc())
        .all()
    )

    return [
        {
            "source": str(row.source.value) if row.source else "unknown",
            "total": row.total,
            "converted": row.converted or 0,
            "conversion_rate": round(
                ((row.converted or 0) / row.total * 100) if row.total else 0, 1
            ),
        }
        for row in sources
    ]
