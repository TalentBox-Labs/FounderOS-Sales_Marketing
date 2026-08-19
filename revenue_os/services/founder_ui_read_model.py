"""UI-D1 — founder-facing read-model composition (no new SoT).

Server-side aggregation for Jinja demo surfaces. Composes frozen APIs/services only.
"""

from __future__ import annotations

import json
import logging
import uuid as uuid_lib
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from revenue_os.database import SessionLocal
from revenue_os.models.activity import Activity, ActivityType, MeetingActivity
from revenue_os.models.automation_state import AgentActionLog
from revenue_os.models.contact import Contact
from revenue_os.models.deal import Deal
from revenue_os.services.approvals import list_requests, pending_count
from revenue_os.services.booking_eligibility import (
    STATE_ALREADY_BOOKED,
    STATE_ELIGIBLE,
    STATE_NO_MEETING_INTEREST,
    STATE_PENDING,
    STATE_STOPPED,
)
from revenue_os.services.calendar_executor import CONNECTOR_OUTLOOK, resolve_calendar_connector
from revenue_os.services.operator_flow_read_model import build_operator_flow_snapshot
from revenue_os.services.revenue_orchestration_service import (
    RevenueOrchestrationError,
    inspect_booking_eligibility,
    inspect_follow_up_eligibility,
    inspect_latest_reply_assessment,
)
from revenue_os.services.tenant_context import TenantContext
from revenue_os.services.tenant_scoped_access import TenantAccessError, get_contact_for_tenant

logger = logging.getLogger(__name__)

ACTION_LABELS: dict[str, str] = {
    "qualified_demand_handoff": "Demand registered",
    "qualified_demand_accepted": "Contact accepted",
    "qualified_demand_rejected": "Demand rejected",
    "rev_orch_research_to_outreach": "Research completed",
    "rev_orch_followup_eligibility": "Follow-up eligibility checked",
    "worker_followup_proposal": "Follow-up draft created",
    "rev_orch_reply_assessment": "Reply assessed",
    "worker_reply_analysis": "Reply analyzed",
    "commercial_outcome_handoff": "Outcome handoff registered",
    "commercial_outcome_accepted": "Outcome accepted",
    "commercial_outcome_rejected": "Outcome rejected",
    "contact_status_updated": "Contact status updated",
    "deal_stage_updated": "Deal stage updated",
    "rev_orch_booking_eligibility": "Booking eligibility checked",
    "worker_booking_proposal": "Booking proposal created",
    "approval_approved": "Approval granted",
    "approval_rejected": "Approval rejected",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _org_uuid(organization_id: str | None) -> uuid_lib.UUID | None:
    if organization_id is None:
        return None
    try:
        return uuid_lib.UUID(str(organization_id))
    except ValueError:
        return None


def _human_action(action_type: str) -> str:
    if action_type in ACTION_LABELS:
        return ACTION_LABELS[action_type]
    if action_type == "book_meeting":
        return "Meeting booking"
    return action_type.replace("_", " ").title()


def _format_slot_display(iso: str | None, *, tz_label: str = "UTC") -> str:
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(timezone.utc)
        return dt.strftime(f"%a, %b %d, %Y · %I:%M %p {tz_label}")
    except ValueError:
        return str(iso)[:24]


def _latest_booked_meeting(db, contact_id: uuid_lib.UUID) -> dict[str, Any] | None:  # noqa: ANN001
    activity = (
        db.query(Activity)
        .filter(
            Activity.contact_id == contact_id,
            Activity.activity_type == ActivityType.MEETING,
            Activity.status == "completed",
            Activity.direction == "outbound",
        )
        .order_by(Activity.performed_at.desc())
        .first()
    )
    if activity is None:
        return None
    body: dict[str, Any] = {}
    if activity.body:
        try:
            body = json.loads(activity.body)
        except (json.JSONDecodeError, TypeError):
            body = {}
    meeting_row = (
        db.query(MeetingActivity).filter(MeetingActivity.activity_id == activity.id).first()
    )
    return {
        "activity_id": str(activity.id),
        "title": activity.subject or "Booked meeting",
        "slot_start": body.get("selected_slot_start"),
        "slot_end": body.get("selected_slot_end"),
        "slot_start_display": _format_slot_display(body.get("selected_slot_start")),
        "slot_end_display": _format_slot_display(body.get("selected_slot_end")),
        "provider_event_id": body.get("provider_event_id"),
        "connector": body.get("connector"),
        "meeting_url": meeting_row.meeting_url if meeting_row else None,
        "performed_at": activity.performed_at.isoformat() if activity.performed_at else None,
    }


_SAFE_BOOKING_DEFAULTS: dict[str, Any] = {
    "ui_state": "NOT_ELIGIBLE",
    "backend_state": None,
    "eligible": False,
    "message": "",
    "timezone": "UTC",
    "duration_minutes": 30,
    "connector": None,
    "candidate_slots": [],
    "selected_slot": None,
    "approval": None,
    "confirmation": None,
    "pending_approval": None,
    "booked_meeting": None,
}


def ensure_booking_presentation(booking: Any) -> dict[str, Any]:
    """Safe booking presentation shape for templates (not a SoT, not eligibility)."""
    panel = dict(_SAFE_BOOKING_DEFAULTS)
    if not isinstance(booking, dict):
        return panel
    panel.update(booking)
    if panel.get("approval") is None:
        panel["approval"] = panel.get("pending_approval")
    if panel.get("confirmation") is None:
        panel["confirmation"] = panel.get("booked_meeting")
    if not panel.get("timezone"):
        panel["timezone"] = "UTC"
    if not panel.get("duration_minutes"):
        panel["duration_minutes"] = 30
    if not panel.get("ui_state"):
        panel["ui_state"] = "NOT_ELIGIBLE"
    if panel.get("candidate_slots") is None:
        panel["candidate_slots"] = []
    return panel


def attach_safe_booking(workspace: Any) -> Any:
    """Guarantee workspace.booking is a renderable dict. Never invents eligibility."""
    if not isinstance(workspace, dict):
        return workspace
    out = dict(workspace)
    out["booking"] = ensure_booking_presentation(out.get("booking"))
    return out


def _enrich_book_meeting_approval(item: dict[str, Any]) -> dict[str, Any]:
    if item.get("action_type") != "book_meeting":
        return item
    payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
    tz = str(payload.get("timezone") or "UTC")
    enriched = dict(item)
    enriched["booking_display"] = {
        "meeting_title": payload.get("meeting_title") or item.get("title"),
        "slot_start": payload.get("selected_slot_start"),
        "slot_end": payload.get("selected_slot_end"),
        "slot_start_display": _format_slot_display(payload.get("selected_slot_start"), tz_label=tz),
        "slot_end_display": _format_slot_display(payload.get("selected_slot_end"), tz_label=tz),
        "timezone": tz,
        "duration_minutes": payload.get("duration_minutes"),
        "purpose": payload.get("meeting_notes") or item.get("description"),
        "proposal_source": (
            "AI proposal" if item.get("requested_by") == "booking_worker" else "Proposal"
        ),
        "requested_by_label": (
            "AI proposal" if item.get("requested_by") == "booking_worker" else "Proposal"
        ),
    }
    return enriched


def _build_booking_panel(
    db,  # noqa: ANN001
    tenant: TenantContext,
    contact: Contact,
    organization_id: str,
    contact_approvals: list[dict[str, Any]],
) -> dict[str, Any]:
    """Server-authoritative booking presentation state (not SoT)."""
    panel: dict[str, Any] = dict(_SAFE_BOOKING_DEFAULTS)
    try:
        eligibility = inspect_booking_eligibility(db, tenant, str(contact.id))
    except RevenueOrchestrationError as exc:
        panel["ui_state"] = "ERROR"
        panel["message"] = str(exc)
        return ensure_booking_presentation(panel)

    backend_state = eligibility.get("state")
    panel["backend_state"] = backend_state
    panel["eligible"] = bool(eligibility.get("eligible"))
    panel["duration_minutes"] = int(eligibility.get("duration_minutes") or 30)
    panel["timezone"] = str(eligibility.get("timezone") or "UTC")

    if backend_state == STATE_ALREADY_BOOKED:
        panel["ui_state"] = "BOOKED"
        panel["booked_meeting"] = _latest_booked_meeting(db, contact.id)
        panel["message"] = "Meeting booked"
        panel["confirmation"] = panel["booked_meeting"]
        return ensure_booking_presentation(panel)

    if backend_state == STATE_PENDING:
        approval_id = eligibility.get("approval_id")
        pending = next((a for a in contact_approvals if a.get("id") == approval_id), None)
        if pending is None and approval_id:
            all_pending = list_requests(status="pending", limit=50, organization_id=organization_id)
            pending = next((a for a in all_pending if a.get("id") == approval_id), None)
        panel["ui_state"] = "APPROVAL_PENDING"
        panel["message"] = "Booking approval required before the meeting is scheduled"
        if pending:
            panel["pending_approval"] = _enrich_book_meeting_approval(pending)
            panel["approval"] = panel["pending_approval"]
        return ensure_booking_presentation(panel)

    if backend_state == STATE_ELIGIBLE:
        resolved = resolve_calendar_connector(organization_id)
        if resolved is None:
            panel["ui_state"] = "NO_CONNECTOR"
            panel["message"] = "Connect a Google Calendar for this workspace to view availability"
            return ensure_booking_presentation(panel)
        connector_name, _config = resolved
        panel["connector"] = connector_name
        if connector_name == CONNECTOR_OUTLOOK:
            panel["ui_state"] = "CONNECTOR_UNAVAILABLE"
            panel["message"] = (
                "Availability is not available for this calendar connection yet."
            )
            return ensure_booking_presentation(panel)
        panel["ui_state"] = "BOOKING_ELIGIBLE"
        panel["message"] = "View tenant-safe availability and submit a booking for approval"
        return ensure_booking_presentation(panel)

    if backend_state in (STATE_NO_MEETING_INTEREST, STATE_STOPPED):
        panel["ui_state"] = "NOT_ELIGIBLE"
        panel["message"] = eligibility.get("reason") or "Not eligible for booking"
        return ensure_booking_presentation(panel)

    panel["ui_state"] = "NOT_ELIGIBLE"
    panel["message"] = eligibility.get("reason") or "Not eligible for booking"
    return ensure_booking_presentation(panel)


def _tenant_from_org(organization_id: str | None) -> TenantContext | None:
    if not organization_id:
        return None
    from revenue_os.services.identity_context import anonymous_identity

    return TenantContext(
        identity=anonymous_identity(),
        organization_id=str(organization_id),
        organization_name="",
        organization_slug="",
        membership_id="",
        membership_role="owner",
        membership_status="active",
    )


def _org_scoped_actions(
    db, *, organization_id: str | None, limit: int = 50
) -> list[dict[str, Any]]:  # noqa: ANN001
    org_uuid = _org_uuid(organization_id)
    query = db.query(AgentActionLog).order_by(AgentActionLog.created_at.desc())
    if org_uuid is not None:
        query = query.filter(AgentActionLog.organization_id == org_uuid)
    rows = query.limit(min(limit, 200)).all()
    events: list[dict[str, Any]] = []
    for row in rows:
        events.append(
            {
                "id": str(row.id) if row.id else None,
                "label": _human_action(row.action_type or ""),
                "action_type": row.action_type,
                "actor": row.actor,
                "target_type": row.target_type,
                "target_id": row.target_id,
                "status": row.status,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "detail": row.detail or {},
            }
        )
    return events


def _reply_summary_from_assessment(assessment_payload: dict[str, Any] | None) -> dict[str, Any]:
    if not assessment_payload:
        return {
            "state": "empty",
            "message": "No reply assessment yet",
            "reply_type": None,
            "summary": None,
            "recommended_next_action": None,
            "meeting_interest": False,
            "booking_eligible": False,
            "booking_status": "none",
        }
    detail = assessment_payload if isinstance(assessment_payload, dict) else {}
    inner = detail.get("assessment") if isinstance(detail.get("assessment"), dict) else {}
    routing = detail.get("routing") if isinstance(detail.get("routing"), dict) else {}
    reply_type = routing.get("reply_type") or inner.get("reply_type")
    meeting_interest = bool(routing.get("meeting_interest") or inner.get("meeting_interest"))
    booking_eligible = bool(routing.get("booking_eligible"))
    recommended = routing.get("recommended_next_action")
    booking_status = "none"
    if meeting_interest or reply_type == "MEETING_INTEREST":
        booking_status = "eligible" if booking_eligible else "interest_detected"
    return {
        "state": "ok",
        "message": "",
        "reply_type": reply_type,
        "summary": inner.get("summary"),
        "confidence": inner.get("confidence") or routing.get("confidence"),
        "recommended_next_action": recommended,
        "meeting_interest": meeting_interest,
        "booking_eligible": booking_eligible,
        "booking_status": booking_status,
        "requires_human_review": bool(routing.get("requires_human_review")),
    }


def build_command_center_snapshot(*, organization_id: str | None = None) -> dict[str, Any]:
    """Founder Command Center — attention-oriented read composition."""
    snapshot: dict[str, Any] = {
        "generated_at": _utc_now(),
        "state": "ok",
        "message": "",
        "pending_approvals": [],
        "pending_approval_count": 0,
        "pending_demands": [],
        "pending_demand_count": 0,
        "pipeline": {"contacts": 0, "deals": 0, "deals_by_stage": {}},
        "recent_replies": [],
        "meeting_interest": [],
        "meeting_booking_pending": [],
        "follow_up_signals": [],
        "recent_activity": [],
        "errors": [],
    }
    flow_contacts: list[dict[str, Any]] = []
    try:
        flow = build_operator_flow_snapshot(organization_id=organization_id)
        flow_contacts = flow.get("contacts") or []
        snapshot["pending_demands"] = flow.get("pending_demands") or []
        snapshot["pending_demand_count"] = len(snapshot["pending_demands"])
        deals = flow.get("deals") or []
        snapshot["pipeline"]["contacts"] = len(flow_contacts)
        snapshot["pipeline"]["deals"] = len(deals)
        by_stage: dict[str, int] = {}
        for d in deals:
            stage = d.get("stage") or "unknown"
            by_stage[stage] = by_stage.get(stage, 0) + 1
        snapshot["pipeline"]["deals_by_stage"] = by_stage
    except Exception as exc:  # noqa: BLE001
        logger.warning("Command center operator flow unavailable: %s", exc)
        snapshot["errors"].append("operator_flow")
        snapshot["state"] = "partial"

    try:
        pending = list_requests(status="pending", limit=20, organization_id=organization_id)
        snapshot["pending_approvals"] = pending
        snapshot["pending_approval_count"] = pending_count(organization_id=organization_id)
        snapshot["meeting_booking_pending"] = [
            _enrich_book_meeting_approval(a)
            for a in pending
            if a.get("action_type") == "book_meeting"
        ]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Command center approvals unavailable: %s", exc)
        snapshot["errors"].append("approvals")

    tenant = _tenant_from_org(organization_id)
    db = SessionLocal()
    try:
        snapshot["recent_activity"] = _org_scoped_actions(
            db, organization_id=organization_id, limit=12
        )
        org_uuid = _org_uuid(organization_id)
        reply_q = db.query(AgentActionLog).filter(
            AgentActionLog.action_type == "rev_orch_reply_assessment"
        )
        if org_uuid is not None:
            reply_q = reply_q.filter(AgentActionLog.organization_id == org_uuid)
        reply_logs = reply_q.order_by(AgentActionLog.created_at.desc()).limit(8).all()
        for log in reply_logs:
            summary = _reply_summary_from_assessment(log.detail or {})
            snapshot["recent_replies"].append(
                {
                    "contact_id": log.target_id,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                    **summary,
                }
            )
            if summary.get("meeting_interest") or summary.get("booking_eligible"):
                snapshot["meeting_interest"].append(
                    {
                        "contact_id": log.target_id,
                        "reply_type": summary.get("reply_type"),
                        "booking_status": summary.get("booking_status"),
                        "recommended_next_action": summary.get("recommended_next_action"),
                    }
                )

        if tenant is not None and flow_contacts:
            for c in flow_contacts[:5]:
                cid = c.get("id")
                if not cid:
                    continue
                try:
                    elig = inspect_follow_up_eligibility(db, tenant, str(cid))
                    if elig.get("eligible") or elig.get("state") not in (None, "IDLE"):
                        snapshot["follow_up_signals"].append(
                            {
                                "contact_id": cid,
                                "name": c.get("name") or c.get("email"),
                                "state": elig.get("state"),
                                "eligible": elig.get("eligible"),
                                "reason": elig.get("reason"),
                            }
                        )
                except RevenueOrchestrationError:
                    continue
    except SQLAlchemyError as exc:
        logger.warning("Command center DB unavailable: %s", exc)
        snapshot["errors"].append("database")
        snapshot["state"] = "partial"
    finally:
        db.close()

    return snapshot


def build_demand_contacts_snapshot(*, organization_id: str | None = None) -> dict[str, Any]:
    """Demand + contacts list for founder demo."""
    try:
        flow = build_operator_flow_snapshot(organization_id=organization_id)
        return {
            "generated_at": _utc_now(),
            "state": "ok",
            "pending_demands": flow.get("pending_demands") or [],
            "contacts": flow.get("contacts") or [],
            "message": "",
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Demand/contacts snapshot unavailable: %s", exc)
        return {
            "generated_at": _utc_now(),
            "state": "unavailable",
            "pending_demands": [],
            "contacts": [],
            "message": "Demand and contact sources unavailable",
        }


def build_contact_workspace_snapshot(
    *,
    organization_id: str | None,
    contact_id: str,
) -> dict[str, Any]:
    """Unified contact revenue workspace."""
    empty: dict[str, Any] = {
        "generated_at": _utc_now(),
        "state": "unavailable",
        "message": "Contact not available",
        "contact": None,
        "deals": [],
        "follow_up": {"state": "empty", "message": "No follow-up data"},
        "reply": _reply_summary_from_assessment(None),
        "booking": ensure_booking_presentation(
            {"ui_state": "NOT_ELIGIBLE", "message": "Organization context required"}
        ),
        "timeline": [],
        "workflow": {
            "research": "unknown",
            "draft": "unknown",
            "approval": "unknown",
            "send": "unknown",
            "follow_up": "unknown",
            "reply": "unknown",
        },
    }
    if not organization_id:
        empty["message"] = "Organization context required"
        return empty

    tenant = _tenant_from_org(organization_id)
    if tenant is None:
        return empty

    db = SessionLocal()
    try:
        try:
            contact = get_contact_for_tenant(db, organization_id, contact_id)
        except TenantAccessError:
            empty["state"] = "not_found"
            empty["message"] = "Contact not found in your organization"
            return empty

        org_uuid = _org_uuid(organization_id)
        deals_q = db.query(Deal).filter(Deal.contact_id == contact.id)
        if org_uuid is not None:
            deals_q = deals_q.filter(Deal.organization_id == org_uuid)
        deals = [
            {
                "id": str(d.id),
                "name": d.name,
                "stage": d.stage.value if d.stage else None,
                "value": float(d.value or 0),
                "currency": d.currency or "USD",
            }
            for d in deals_q.all()
        ]

        follow_up: dict[str, Any] = {"state": "empty", "message": "No follow-up eligibility data"}
        reply = _reply_summary_from_assessment(None)
        try:
            follow_up = inspect_follow_up_eligibility(db, tenant, str(contact.id))
            follow_up["state"] = "ok"
        except RevenueOrchestrationError as exc:
            follow_up = {"state": "unavailable", "message": str(exc)}

        try:
            assessment_payload = inspect_latest_reply_assessment(db, tenant, str(contact.id))
            reply = _reply_summary_from_assessment(assessment_payload.get("assessment"))
            if assessment_payload.get("assessment"):
                reply["raw"] = assessment_payload.get("assessment")
        except RevenueOrchestrationError as exc:
            reply = {"state": "unavailable", "message": str(exc)}

        timeline_q = db.query(AgentActionLog).filter(AgentActionLog.target_id == str(contact.id))
        if org_uuid is not None:
            timeline_q = timeline_q.filter(AgentActionLog.organization_id == org_uuid)
        timeline = [
            {
                "label": _human_action(row.action_type or ""),
                "action_type": row.action_type,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "actor": row.actor,
            }
            for row in timeline_q.order_by(AgentActionLog.created_at.desc()).limit(30).all()
        ]

        pending = list_requests(status="pending", limit=50, organization_id=organization_id)
        contact_approvals = [a for a in pending if a.get("target_id") == str(contact.id)]

        booking = _build_booking_panel(db, tenant, contact, organization_id, contact_approvals)

        workflow = _workflow_stages(timeline, contact_approvals, reply, follow_up)

        return attach_safe_booking({
            "generated_at": _utc_now(),
            "state": "ok",
            "message": "",
            "contact": {
                "id": str(contact.id),
                "name": f"{contact.first_name or ''} {contact.last_name or ''}".strip()
                or contact.email,
                "email": contact.email,
                "status": contact.status.value if contact.status else None,
                "lead_score": contact.lead_score or 0,
                "company": contact.company,
                "phone": contact.phone,
            },
            "deals": deals,
            "follow_up": follow_up,
            "reply": reply,
            "booking": booking,
            "timeline": timeline,
            "pending_approvals": [_enrich_book_meeting_approval(a) for a in contact_approvals],
            "workflow": workflow,
        })
    finally:
        db.close()


def _workflow_stages(
    timeline: list[dict[str, Any]],
    pending_approvals: list[dict[str, Any]],
    reply: dict[str, Any],
    follow_up: dict[str, Any],
) -> dict[str, str]:
    types = {t.get("action_type") for t in timeline}
    stages = {
        "research": "pending",
        "draft": "pending",
        "approval": "pending",
        "send": "pending",
        "follow_up": "pending",
        "reply": "pending",
    }
    if any(t in types for t in ("rev_orch_research_to_outreach",)):
        stages["research"] = "done"
    if pending_approvals:
        stages["draft"] = "active"
        stages["approval"] = "active"
    elif any(t in types for t in ("worker_followup_proposal",)):
        stages["draft"] = "done"
        stages["approval"] = "done"
    if follow_up.get("eligible"):
        stages["follow_up"] = "active"
    elif follow_up.get("state") not in (None, "empty", "unavailable"):
        stages["follow_up"] = "done"
    if reply.get("state") == "ok":
        stages["reply"] = "done"
    return stages


def build_approvals_snapshot(*, organization_id: str | None = None) -> dict[str, Any]:
    """Governed approval inbox."""
    try:
        pending = list_requests(status="pending", limit=100, organization_id=organization_id)
        recent = list_requests(status=None, limit=30, organization_id=organization_id)
        pending = [_enrich_book_meeting_approval(a) for a in pending]
        recent = [_enrich_book_meeting_approval(a) for a in recent]
        meeting_pending = [a for a in pending if a.get("action_type") == "book_meeting"]
        return {
            "generated_at": _utc_now(),
            "state": "ok",
            "message": "",
            "pending": pending,
            "recent": recent,
            "pending_count": len(pending),
            "meeting_pending_count": len(meeting_pending),
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Approvals snapshot unavailable: %s", exc)
        return {
            "generated_at": _utc_now(),
            "state": "unavailable",
            "message": "Approval queue unavailable",
            "pending": [],
            "recent": [],
            "pending_count": 0,
        }


def build_activity_snapshot(
    *, organization_id: str | None = None, limit: int = 50
) -> dict[str, Any]:
    """Founder-facing activity / provenance timeline."""
    db = SessionLocal()
    try:
        events = _org_scoped_actions(db, organization_id=organization_id, limit=limit)
        return {
            "generated_at": _utc_now(),
            "state": "ok" if events else "empty",
            "message": "No activity recorded yet" if not events else "",
            "events": events,
        }
    except SQLAlchemyError as exc:
        logger.warning("Activity snapshot DB unavailable: %s", exc)
        return {
            "generated_at": _utc_now(),
            "state": "unavailable",
            "message": "Activity sources unavailable",
            "events": [],
        }
    finally:
        db.close()
