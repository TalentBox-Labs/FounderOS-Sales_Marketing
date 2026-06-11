from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from revenue_os.models.activity import Activity
from revenue_os.models.contact import Contact, ContactStatus
from revenue_os.models.deal import Deal


def get_dashboard_stats(db: Session) -> dict:
    total_contacts = db.query(Contact).count()
    total_companies = (
        db.query(Contact.company_id)
        .distinct()
        .count()
    )
    total_deals = db.query(Deal).count()

    active_deals = (
        db.query(Deal)
        .filter(
            Deal.stage.notin_(["closed_won", "closed_lost"])
        )
        .count()
    )

    won_deals_value = (
        db.query(func.coalesce(func.sum(Deal.value), 0))
        .filter(Deal.stage == "closed_won")
        .scalar()
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

    recent_activities = (
        db.query(Activity)
        .order_by(Activity.performed_at.desc())
        .limit(10)
        .all()
    )

    return {
        "total_contacts": total_contacts,
        "total_companies": total_companies,
        "total_deals": total_deals,
        "active_deals": active_deals,
        "won_deals_value": float(won_deals_value),
        "leads": leads,
        "qualified": qualified,
        "customers": customers,
        "recent_activities": [
            {
                "id": str(a.id),
                "type": a.activity_type.value,
                "subject": a.subject,
                "performed_at": a.performed_at.isoformat(),
            }
            for a in recent_activities
        ],
    }
