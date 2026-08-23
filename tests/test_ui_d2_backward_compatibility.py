"""UI-D2.1 — backward-compatible rendering without mutating frozen historical tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import revenue_os.models  # noqa: F401
import runner_api_routers.identity as identity_mod
import runner_api_routers.revenue_orchestration as rev_orch_mod
import runner_api_routers.ui as ui_mod
from revenue_os.agents.orchestration import WorkflowOrchestrator
from revenue_os.auth import hash_password
from revenue_os.models.approvals import ApprovalRequest
from revenue_os.models.base import Base
from revenue_os.models.contact import Contact, ContactSource, ContactStatus
from revenue_os.models.organization import (
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationStatus,
)
from revenue_os.models.user import User
from revenue_os.services.tenant_resolution import ORGANIZATION_COOKIE
from runner_api import app

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_FUTURE_SLOT = {
    "start": (datetime.now(timezone.utc) + timedelta(days=2)).replace(microsecond=0).isoformat(),
    "end": (datetime.now(timezone.utc) + timedelta(days=2, minutes=30)).replace(microsecond=0).isoformat(),
}
_AVAILABILITY = {
    "ok": True,
    "connector": "google_calendar",
    "organization_id": str(_ORG_A),
    "duration_minutes": 30,
    "slots": [_FUTURE_SLOT],
}

_BASE_CONTACT = {
    "id": str(_CONTACT_A),
    "name": "Empty",
    "email": "e@x.com",
    "status": "lead",
    "lead_score": 0,
    "company": None,
    "phone": None,
}

_WORKFLOW = {
    "research": "pending",
    "draft": "pending",
    "approval": "pending",
    "send": "pending",
    "follow_up": "pending",
    "reply": "pending",
}


@pytest.fixture(autouse=True)
def _reset() -> None:
    identity_mod._revoked_jtis.clear()
    identity_mod._login_failures.clear()
    WorkflowOrchestrator._workflows.clear()
    WorkflowOrchestrator._executions.clear()
    WorkflowOrchestrator._revenue_workflows_seeded = False


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def tenant_db(monkeypatch: pytest.MonkeyPatch, tmp_path) -> sessionmaker:
    engine = create_engine(f"sqlite:///{tmp_path / 'ui_d2_compat.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    import revenue_os.database as db_mod
    import revenue_os.services.activity_log as al
    import revenue_os.services.approvals as approvals_mod
    import revenue_os.services.founder_ui_read_model as founder_rm
    import revenue_os.services.revenue_orchestration_service as rev_svc
    import revenue_os.services.tenant_resolution as tr

    for mod in (
        db_mod,
        tr,
        approvals_mod,
        al,
        ui_mod,
        founder_rm,
        rev_svc,
        identity_mod,
        rev_orch_mod,
    ):
        if hasattr(mod, "SessionLocal"):
            monkeypatch.setattr(mod, "SessionLocal", sf)
    monkeypatch.setenv("FOUNDER_OS_REQUIRE_LOGIN", "0")
    return sf


def _workspace(**overrides: object) -> dict:
    base: dict = {
        "generated_at": "now",
        "state": "ok",
        "message": "",
        "contact": dict(_BASE_CONTACT),
        "deals": [],
        "follow_up": {"state": "empty", "message": "No follow-up eligibility data"},
        "reply": {
            "state": "empty",
            "message": "No reply assessment yet",
            "meeting_interest": False,
            "booking_eligible": False,
        },
        "timeline": [],
        "workflow": dict(_WORKFLOW),
        "pending_approvals": [],
    }
    base.update(overrides)
    return base


def _render_contact(client: TestClient, monkeypatch: pytest.MonkeyPatch, workspace: dict):
    monkeypatch.setattr("runner_api_routers.ui.founder_login_redirect", lambda _r: None)
    with patch("runner_api_routers.ui.build_contact_workspace_snapshot", return_value=workspace):
        return client.get(f"/contacts/{_CONTACT_A}")


def test_contact_renders_when_booking_key_absent(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    r = _render_contact(client, monkeypatch, _workspace())
    assert r.status_code == 200
    assert "No deals linked" in r.text
    assert 'data-testid="contact-booking-panel"' in r.text
    assert 'data-testid="booking-not-eligible"' in r.text
    assert 'data-testid="booking-load-availability"' not in r.text


def test_contact_renders_when_booking_is_none(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    r = _render_contact(client, monkeypatch, _workspace(booking=None))
    assert r.status_code == 200
    assert 'data-testid="contact-booking-panel"' in r.text
    assert 'data-testid="booking-not-eligible"' in r.text


def test_contact_renders_incomplete_booking_shape(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    r = _render_contact(client, monkeypatch, _workspace(booking={"ui_state": "NOT_ELIGIBLE"}))
    assert r.status_code == 200
    assert 'data-testid="booking-not-eligible"' in r.text
    assert 'data-testid="booking-eligible-panel"' not in r.text


def test_historical_generic_approval_shape_renders(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("runner_api_routers.ui.founder_login_redirect", lambda _r: None)
    snapshot = {
        "generated_at": "now",
        "state": "ok",
        "message": "",
        "pending_count": 2,
        "pending": [
            {
                "id": "appr-email",
                "action_type": "send-email",
                "title": "Send follow-up email",
                "description": "Draft outreach",
                "status": "pending",
                "target_id": str(_CONTACT_A),
            },
            {
                "id": "appr-future",
                "action_type": "unknown_future_action",
                "title": "Future governed action",
                "description": None,
                "status": "pending",
            },
        ],
        "recent": [],
    }
    with patch("runner_api_routers.ui.build_approvals_snapshot", return_value=snapshot):
        r = client.get("/pending-approvals")
    assert r.status_code == 200
    assert "send-email" in r.text
    assert "Send follow-up email" in r.text
    assert "unknown_future_action" in r.text
    assert "Future governed action" in r.text
    assert "Sign in as a human operator to approve or reject" in r.text


def test_booking_approval_shape_renders(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("runner_api_routers.ui.founder_login_redirect", lambda _r: None)
    snapshot = {
        "generated_at": "now",
        "state": "ok",
        "message": "",
        "pending_count": 1,
        "pending": [
            {
                "id": "appr-book",
                "action_type": "book_meeting",
                "title": "Book meeting with Alice",
                "description": "M4 booking proposal",
                "status": "pending",
                "target_id": str(_CONTACT_A),
                "booking_display": {
                    "meeting_title": "Book meeting with Alice",
                    "slot_start_display": "Mon, Jan 01, 2026 · 10:00 AM UTC",
                    "timezone": "UTC",
                    "duration_minutes": 30,
                    "proposal_source": "AI proposal",
                },
            }
        ],
        "recent": [],
    }
    with patch("runner_api_routers.ui.build_approvals_snapshot", return_value=snapshot):
        r = client.get("/pending-approvals")
    assert r.status_code == 200
    assert "book_meeting" in r.text
    assert "Book meeting with Alice" in r.text
    assert 'data-testid="approval-booking-slot"' in r.text
    assert "Meeting booking" in r.text
    assert "Sign in as a human operator to approve or reject" in r.text


def test_historical_activity_shape_renders(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("runner_api_routers.ui.founder_login_redirect", lambda _r: None)
    snapshot = {
        "generated_at": "now",
        "state": "ok",
        "message": "",
        "events": [
            {
                "id": "evt-1",
                "label": "Reply assessed",
                "created_at": "2026-01-01T00:00:00Z",
                "actor": "system",
            }
        ],
    }
    with patch("runner_api_routers.ui.build_activity_snapshot", return_value=snapshot):
        r = client.get("/activity")
    assert r.status_code == 200
    assert "Reply assessed" in r.text


def test_booking_activity_shape_renders(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("runner_api_routers.ui.founder_login_redirect", lambda _r: None)
    snapshot = {
        "generated_at": "now",
        "state": "ok",
        "message": "",
        "events": [
            {
                "id": "evt-2",
                "label": "Booking proposal created",
                "action_type": "worker_booking_proposal",
                "created_at": "2026-01-01T00:00:00Z",
                "actor": "booking_worker",
            }
        ],
    }
    with patch("runner_api_routers.ui.build_activity_snapshot", return_value=snapshot):
        r = client.get("/activity")
    assert r.status_code == 200
    assert "Booking proposal created" in r.text
    assert "worker_booking_proposal" in r.text


def test_client_requested_by_and_decided_by_do_not_create_human_authority(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    db = tenant_db()
    try:
        db.add(Organization(id=_ORG_A, name="A", slug="org-a", status=OrganizationStatus.ACTIVE))
        owner = User(
            email="owner-a@example.com",
            hashed_password=hash_password("pass-a"),
            full_name="Krishna Founder",
            role="owner",
            is_active=1,
        )
        db.add(owner)
        db.flush()
        db.add(
            OrganizationMembership(
                user_id=owner.id,
                organization_id=_ORG_A,
                role="owner",
                status=MembershipStatus.ACTIVE,
            )
        )
        db.add(
            Contact(
                id=_CONTACT_A,
                first_name="Alice",
                last_name="A",
                email="alice@example.com",
                status=ContactStatus.LEAD,
                source=ContactSource.MANUAL,
                organization_id=_ORG_A,
            )
        )
        from revenue_os.models.activity import Activity, ActivityType
        from revenue_os.models.automation_state import AgentActionLog

        reply_act = Activity(
            contact_id=_CONTACT_A,
            activity_type=ActivityType.EMAIL_REPLY,
            subject="Meeting interest",
            body="Can we meet?",
            direction="inbound",
            status="completed",
        )
        db.add(reply_act)
        db.flush()
        db.add(
            AgentActionLog(
                organization_id=_ORG_A,
                actor="revenue_workflow_orchestrator",
                action_type="rev_orch_reply_assessment",
                target_type="contact",
                target_id=str(_CONTACT_A),
                status="completed",
                detail={
                    "activity_id": str(reply_act.id),
                    "assessment": {"reply_type": "MEETING_INTEREST", "meeting_interest": True},
                    "routing": {
                        "reply_type": "MEETING_INTEREST",
                        "booking_eligible": True,
                        "recommended_next_action": "BOOKING_ELIGIBLE",
                    },
                },
            )
        )
        db.commit()
    finally:
        db.close()

    login = client.post(
        "/api/v1/identity/login", json={"email": "owner-a@example.com", "password": "pass-a"}
    )
    assert login.status_code == 200, login.text
    client.cookies.set(ORGANIZATION_COOKIE, str(_ORG_A))
    with patch(
        "revenue_os.services.revenue_orchestration_service.get_tenant_availability",
        return_value=_AVAILABILITY,
    ):
        propose = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose",
            json={
                "selected_slot": _FUTURE_SLOT,
                "requested_by": "booking_worker",
            },
        )
    assert propose.status_code == 200, propose.text
    approval_id = propose.json()["approval_id"]
    with patch(
        "revenue_os.services.calendar_executor.create_tenant_calendar_event",
        return_value={"ok": True, "provider_event_id": "evt-auth", "connector": "google_calendar"},
    ):
        client.post(
            f"/api/v1/approvals/{approval_id}/approve",
            json={"decided_by": "booking_worker", "requested_by": "booking_worker"},
        )
    db2 = tenant_db()
    try:
        req = db2.get(ApprovalRequest, approval_id)
        assert req is not None
        assert req.requested_by != "client"
        assert req.decided_by != "booking_worker"
        assert req.decided_by not in ("booking_worker", "ai", "agent")
    finally:
        db2.close()
