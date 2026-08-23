"""Follow-up engine — one query for "what needs a founder's attention".

Combines overdue/upcoming tasks with the existing at-risk-deal and
stalled-qualified-contact signals so Dashboard and Copilot read from the
same source instead of duplicating logic.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from revenue_os.database import SessionLocal
from revenue_os.models.activity import Activity, ActivityType
from revenue_os.models.contact import Contact, ContactStatus
from revenue_os.models.deal import Deal

UPCOMING_WINDOW_DAYS = 7


def _aware(dt: datetime | None) -> datetime | None:
    # SQLite returns naive datetimes; treat stored values as UTC.
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _task_dict(a: Activity) -> dict[str, Any]:
    return {
        "id": str(a.id),
        "subject": a.subject or "Task",
        "contact_id": str(a.contact_id) if a.contact_id else None,
        "deal_id": str(a.deal_id) if a.deal_id else None,
        "due_date": a.due_date.isoformat() if a.due_date else None,
    }


def get_open_tasks(db: Session) -> tuple[list[dict], list[dict]]:
    """Return (overdue, upcoming) open tasks, both due-date ascending."""
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(days=UPCOMING_WINDOW_DAYS)

    tasks = (
        db.query(Activity)
        .filter(Activity.activity_type == ActivityType.TASK)
        .filter(Activity.is_completed == 0)
        .all()
    )

    overdue, upcoming = [], []
    for t in tasks:
        due = _aware(t.due_date)
        if due is None:
            continue
        if due < now:
            overdue.append((due, t))
        elif due <= horizon:
            upcoming.append((due, t))

    overdue.sort(key=lambda pair: pair[0])
    upcoming.sort(key=lambda pair: pair[0])
    return (
        [_task_dict(t) for _, t in overdue],
        [_task_dict(t) for _, t in upcoming],
    )


def get_stalled_qualified_contacts(db: Session, stale_days: int = 14) -> list[dict[str, Any]]:
    """Qualified contacts with no open deal and no recent activity."""
    now = datetime.now(timezone.utc)
    with_deals = {d.contact_id for d in db.query(Deal).all() if d.contact_id}

    stalled = []
    for c in db.query(Contact).filter(Contact.status == ContactStatus.QUALIFIED).all():
        if c.id in with_deals:
            continue
        last_touch = _aware(c.last_contacted_at) or _aware(c.updated_at)
        days_stale = (now - last_touch).days if last_touch else stale_days + 1
        if days_stale >= stale_days:
            stalled.append({
                "id": str(c.id),
                "name": f"{c.first_name} {c.last_name}".strip(),
                "email": c.email,
                "lead_score": c.lead_score or 0,
                "days_stale": days_stale,
            })

    return sorted(stalled, key=lambda c: c["days_stale"], reverse=True)


def get_followups(db: Session | None = None) -> dict[str, Any]:
    """Aggregate every follow-up signal the platform can currently surface."""
    from revenue_os.services.approvals import list_requests
    from revenue_os.services.deal_automation_service import get_deals_at_risk

    owns_session = db is None
    db = db or SessionLocal()
    try:
        overdue_tasks, upcoming_tasks = get_open_tasks(db)
        stalled_contacts = get_stalled_qualified_contacts(db)
        at_risk_deals = get_deals_at_risk(db)
    finally:
        if owns_session:
            db.close()

    pending_approvals = list_requests(status="pending", limit=20)

    total = (
        len(overdue_tasks) + len(upcoming_tasks) + len(stalled_contacts)
        + len(at_risk_deals) + len(pending_approvals)
    )

    return {
        "overdue_tasks": overdue_tasks,
        "upcoming_tasks": upcoming_tasks,
        "stalled_contacts": stalled_contacts,
        "at_risk_deals": at_risk_deals,
        "pending_approvals": pending_approvals,
        "total": total,
    }
