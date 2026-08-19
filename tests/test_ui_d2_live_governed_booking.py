"""UI-D2 — live governed booking demo integration tests."""

from __future__ import annotations

import json
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
from revenue_os.models.activity import Activity, ActivityType, MeetingActivity
from revenue_os.models.approvals import ApprovalRequest
from revenue_os.models.automation_state import AgentActionLog
from revenue_os.models.base import Base
from revenue_os.models.contact import Contact, ContactSource, ContactStatus
from revenue_os.models.deal import Deal, DealStage, Pipeline, PipelineType
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
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_OPERATOR = "Krishna Founder"
_DEAL_A = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
_PIPELINE_A = uuid.UUID("11111111-1111-1111-1111-111111111112")

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
    engine = create_engine(f"sqlite:///{tmp_path / 'ui_d2.db'}")
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


def _seed(
    db_factory: sessionmaker,
    *,
    booking_eligible: bool = True,
    with_deal: bool = False,
) -> None:
    db = db_factory()
    try:
        db.add_all([
            Organization(id=_ORG_A, name="A", slug="org-a", status=OrganizationStatus.ACTIVE),
            Organization(id=_ORG_B, name="B", slug="org-b", status=OrganizationStatus.ACTIVE),
        ])
        owner_a = User(
            email="owner-a@example.com",
            hashed_password=hash_password("pass-a"),
            full_name=_OPERATOR,
            role="owner",
            is_active=1,
        )
        owner_b = User(
            email="owner-b@example.com",
            hashed_password=hash_password("pass-b"),
            full_name="Owner B",
            role="owner",
            is_active=1,
        )
        db.add_all([owner_a, owner_b])
        db.flush()
        db.add_all([
            OrganizationMembership(user_id=owner_a.id, organization_id=_ORG_A, role="owner", status=MembershipStatus.ACTIVE),
            OrganizationMembership(user_id=owner_b.id, organization_id=_ORG_B, role="owner", status=MembershipStatus.ACTIVE),
            Contact(
                id=_CONTACT_A,
                first_name="Alice",
                last_name="A",
                email="alice@example.com",
                status=ContactStatus.LEAD,
                source=ContactSource.MANUAL,
                organization_id=_ORG_A,
            ),
            Contact(
                id=_CONTACT_B,
                first_name="Bob",
                last_name="B",
                email="bob@example.com",
                status=ContactStatus.LEAD,
                source=ContactSource.MANUAL,
                organization_id=_ORG_B,
            ),
        ])
        if with_deal:
            db.add(
                Pipeline(
                    id=_PIPELINE_A,
                    name="Sales",
                    pipeline_type=PipelineType.SALES,
                )
            )
            db.flush()
            db.add(
                Deal(
                    id=_DEAL_A,
                    pipeline_id=_PIPELINE_A,
                    name="Alice deal",
                    contact_id=_CONTACT_A,
                    organization_id=_ORG_A,
                    stage=DealStage.QUALIFIED,
                    value=5000,
                )
            )
        if booking_eligible:
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


def _login(client: TestClient, email: str, password: str, org_id: str) -> None:
    r = client.post("/api/v1/identity/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    client.cookies.set(ORGANIZATION_COOKIE, org_id)


def _google_connector():
    return ("google_calendar", {"client_id": "x", "client_secret": "y", "refresh_token": "z"})


# --- Contact workspace booking panel ---


def test_ui_d2_booking_eligible_shows_panel(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    with patch("revenue_os.services.founder_ui_read_model.resolve_calendar_connector", return_value=_google_connector()):
        r = client.get(f"/contacts/{_CONTACT_A}")
    assert r.status_code == 200
    assert 'data-testid="contact-booking-panel"' in r.text
    assert 'data-testid="booking-eligible-panel"' in r.text
    assert 'data-testid="booking-load-availability"' in r.text
    assert "Approval required" in r.text or "you approve" in r.text


def test_ui_d2_noneligible_no_active_booking(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db, booking_eligible=False)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    r = client.get(f"/contacts/{_CONTACT_A}")
    assert r.status_code == 200
    assert 'data-testid="booking-not-eligible"' in r.text
    assert 'data-testid="booking-load-availability"' not in r.text


def test_ui_d2_availability_renders_via_api(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    with patch("revenue_os.services.revenue_orchestration_service.get_tenant_availability", return_value=_AVAILABILITY):
        r = client.get(f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/availability")
    assert r.status_code == 200
    body = r.json()
    assert body["availability"]["ok"] is True
    assert body["availability"]["slots"]
    assert "UTC" in body["availability"]["slots"][0]["start"] or "T" in body["availability"]["slots"][0]["start"]


def test_ui_d2_timezone_in_booking_panel(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    with patch("revenue_os.services.founder_ui_read_model.resolve_calendar_connector", return_value=_google_connector()):
        r = client.get(f"/contacts/{_CONTACT_A}")
    assert "UTC" in r.text


def test_ui_d2_slot_selection_and_proposal(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    with patch("revenue_os.services.revenue_orchestration_service.get_tenant_availability", return_value=_AVAILABILITY):
        r = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose",
            json={"selected_slot": _FUTURE_SLOT},
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["approval_id"]
    assert body["approval_status"] == "pending"


def test_ui_d2_book_meeting_approval_in_inbox(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    with patch("revenue_os.services.revenue_orchestration_service.get_tenant_availability", return_value=_AVAILABILITY):
        propose = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose",
            json={"selected_slot": _FUTURE_SLOT},
        )
    assert propose.status_code == 200
    r = client.get("/pending-approvals")
    assert r.status_code == 200
    assert "Meeting booking" in r.text
    assert 'data-testid="approval-booking-slot"' in r.text
    assert "Approve booking" in r.text


def test_ui_d2_pending_cannot_execute(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    with patch("revenue_os.services.revenue_orchestration_service.get_tenant_availability", return_value=_AVAILABILITY):
        body = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose",
            json={"selected_slot": _FUTURE_SLOT},
        ).json()
    db = tenant_db()
    try:
        req = db.get(ApprovalRequest, body["approval_id"])
        assert req.status == "pending"
    finally:
        db.close()
    with patch("revenue_os.services.calendar_executor.create_tenant_calendar_event") as mock_create:
        db2 = tenant_db()
        try:
            assert db2.query(Activity).filter(Activity.activity_type == ActivityType.MEETING).count() == 0
        finally:
            db2.close()
        mock_create.assert_not_called()


def test_ui_d2_rejected_cannot_execute(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    with patch("revenue_os.services.revenue_orchestration_service.get_tenant_availability", return_value=_AVAILABILITY):
        body = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose",
            json={"selected_slot": _FUTURE_SLOT},
        ).json()
    client.post(f"/api/v1/approvals/{body['approval_id']}/reject", json={})
    with patch("revenue_os.services.calendar_executor.create_tenant_calendar_event") as mock_create:
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        assert r.status_code in (409, 422)
        mock_create.assert_not_called()


def test_ui_d2_approved_booking_executes(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    with patch("revenue_os.services.revenue_orchestration_service.get_tenant_availability", return_value=_AVAILABILITY):
        body = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose",
            json={"selected_slot": _FUTURE_SLOT},
        ).json()
    calendar_result = {
        "ok": True,
        "provider_event_id": "evt-ui-d2",
        "connector": "google_calendar",
        "meeting_url": "https://meet.example.com/abc",
    }
    with patch("revenue_os.services.calendar_executor.create_tenant_calendar_event", return_value=calendar_result):
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
    assert r.status_code == 200
    exec_result = r.json().get("request", {}).get("execution_result") or {}
    assert exec_result.get("executed") is True


def test_ui_d2_confirmation_renders(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    with patch("revenue_os.services.revenue_orchestration_service.get_tenant_availability", return_value=_AVAILABILITY):
        body = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose",
            json={"selected_slot": _FUTURE_SLOT},
        ).json()
    calendar_result = {
        "ok": True,
        "provider_event_id": "evt-confirm",
        "connector": "google_calendar",
        "meeting_url": "https://meet.example.com/xyz",
    }
    with patch("revenue_os.services.calendar_executor.create_tenant_calendar_event", return_value=calendar_result):
        client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
    r = client.get(f"/contacts/{_CONTACT_A}")
    assert 'data-testid="booking-confirmation"' in r.text
    assert "Booked" in r.text


def test_ui_d2_booking_activity_renders(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    with patch("revenue_os.services.revenue_orchestration_service.get_tenant_availability", return_value=_AVAILABILITY):
        body = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose",
            json={"selected_slot": _FUTURE_SLOT},
        ).json()
    with patch(
        "revenue_os.services.calendar_executor.create_tenant_calendar_event",
        return_value={"ok": True, "provider_event_id": "evt-act", "connector": "google_calendar"},
    ):
        client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
    r = client.get("/activity")
    assert r.status_code == 200
    assert "Booking proposal created" in r.text or "Booking Proposal" in r.text or "Approval granted" in r.text


def test_ui_d2_stale_slot_error(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    past = {
        "start": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        "end": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
    }
    with patch(
        "revenue_os.services.revenue_orchestration_service.get_tenant_availability",
        return_value={**_AVAILABILITY, "slots": [past]},
    ):
        body = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose",
            json={"selected_slot": past},
        ).json()
    with patch("revenue_os.services.calendar_executor.create_tenant_calendar_event") as mock_create:
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        exec_result = r.json().get("request", {}).get("execution_result") or {}
        assert exec_result.get("executed") is False or "past" in str(exec_result).lower()
        mock_create.assert_not_called()


def test_ui_d2_duplicate_proposal_deduplicated(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    with patch("revenue_os.services.revenue_orchestration_service.get_tenant_availability", return_value=_AVAILABILITY):
        r1 = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose",
            json={"selected_slot": _FUTURE_SLOT},
        )
        r2 = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose",
            json={"selected_slot": _FUTURE_SLOT},
        )
    assert r1.status_code == 200
    assert r2.status_code in (200, 422)
    db = tenant_db()
    try:
        count = db.query(ApprovalRequest).filter(
            ApprovalRequest.action_type == "book_meeting",
            ApprovalRequest.target_id == str(_CONTACT_A),
            ApprovalRequest.status == "pending",
        ).count()
        assert count == 1
    finally:
        db.close()


def test_ui_d2_duplicate_approve_one_booking(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    with patch("revenue_os.services.revenue_orchestration_service.get_tenant_availability", return_value=_AVAILABILITY):
        body = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose",
            json={"selected_slot": _FUTURE_SLOT},
        ).json()
    cal = {"ok": True, "provider_event_id": "evt-dup", "connector": "google_calendar"}
    with patch("revenue_os.services.calendar_executor.create_tenant_calendar_event", return_value=cal):
        client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
    db = tenant_db()
    try:
        assert db.query(Activity).filter(Activity.activity_type == ActivityType.MEETING).count() == 1
    finally:
        db.close()


# --- Tenant security ---


def test_ui_d2_cross_tenant_availability_blocked(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-b@example.com", "pass-b", str(_ORG_B))
    r = client.get(f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/availability")
    assert r.status_code == 422


def test_ui_d2_cross_tenant_proposal_blocked(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-b@example.com", "pass-b", str(_ORG_B))
    with patch("revenue_os.services.revenue_orchestration_service.get_tenant_availability", return_value=_AVAILABILITY):
        r = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose",
            json={"selected_slot": _FUTURE_SLOT, "organization_id": str(_ORG_B)},
        )
    assert r.status_code == 422


def test_ui_d2_cross_tenant_approval_blocked(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    with patch("revenue_os.services.revenue_orchestration_service.get_tenant_availability", return_value=_AVAILABILITY):
        body = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose",
            json={"selected_slot": _FUTURE_SLOT},
        ).json()
    _login(client, "owner-b@example.com", "pass-b", str(_ORG_B))
    r = client.get("/pending-approvals")
    assert "Book meeting with Alice" not in r.text
    with patch("revenue_os.services.calendar_executor.create_tenant_calendar_event") as mock_create:
        r2 = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        assert r2.status_code in (403, 404, 409, 422)
        mock_create.assert_not_called()


def test_ui_d2_client_decided_by_spoof_blocked(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    with patch("revenue_os.services.revenue_orchestration_service.get_tenant_availability", return_value=_AVAILABILITY):
        body = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose",
            json={"selected_slot": _FUTURE_SLOT},
        ).json()
    with patch(
        "revenue_os.services.calendar_executor.create_tenant_calendar_event",
        return_value={"ok": True, "provider_event_id": "evt-spoof", "connector": "google_calendar"},
    ):
        client.post(
            f"/api/v1/approvals/{body['approval_id']}/approve",
            json={"decided_by": "booking_worker"},
        )
    db = tenant_db()
    try:
        req = db.get(ApprovalRequest, body["approval_id"])
        assert req.decided_by != "booking_worker"
    finally:
        db.close()


def test_ui_d2_outlook_fails_closed(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    outlook = ("outlook_calendar", {"tenant_id": "t", "access_token": "tok"})
    with patch("revenue_os.services.founder_ui_read_model.resolve_calendar_connector", return_value=outlook):
        r = client.get(f"/contacts/{_CONTACT_A}")
    assert 'data-testid="booking-outlook-unavailable"' in r.text
    assert "not available for this calendar connection" in r.text.lower()


def test_ui_d2_no_connector_safe_state(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    with patch("revenue_os.services.founder_ui_read_model.resolve_calendar_connector", return_value=None):
        r = client.get(f"/contacts/{_CONTACT_A}")
    assert 'data-testid="booking-no-connector"' in r.text


def test_ui_d2_no_secret_exposure(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    secret_cfg = ("google_calendar", {"client_secret": "super-secret-xyz", "refresh_token": "rt-abc"})
    with patch("revenue_os.services.founder_ui_read_model.resolve_calendar_connector", return_value=secret_cfg):
        r = client.get(f"/contacts/{_CONTACT_A}")
    assert "super-secret-xyz" not in r.text
    assert "rt-abc" not in r.text


def test_ui_d2_contact_deal_unchanged(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db, with_deal=True)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    with patch("revenue_os.services.revenue_orchestration_service.get_tenant_availability", return_value=_AVAILABILITY):
        body = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose",
            json={"selected_slot": _FUTURE_SLOT},
        ).json()
    with patch(
        "revenue_os.services.calendar_executor.create_tenant_calendar_event",
        return_value={"ok": True, "provider_event_id": "evt-crm", "connector": "google_calendar"},
    ):
        client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
    db = tenant_db()
    try:
        contact = db.query(Contact).filter(Contact.email == "alice@example.com").one()
        assert contact.status == ContactStatus.LEAD
        from sqlalchemy import text

        row = db.execute(
            text("SELECT stage FROM deals WHERE name = :name"),
            {"name": "Alice deal"},
        ).fetchone()
        assert row is not None
        assert str(row[0]).lower() == "qualified"
    finally:
        db.close()
