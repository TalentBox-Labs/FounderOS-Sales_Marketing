"""REV-ORCH M4.5 — governed meeting booking baseline freeze adversarial tests."""

from __future__ import annotations

import inspect
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
from revenue_os.agents.orchestration import REV_ORCH_M4_WORKFLOW_KEY, WorkflowOrchestrator
from revenue_os.auth import hash_password
from revenue_os.models.activity import Activity, ActivityType
from revenue_os.models.approvals import ApprovalRequest
from revenue_os.models.automation_state import AgentActionLog
from revenue_os.models.base import Base
from revenue_os.models.contact import Contact, ContactSource, ContactStatus
from revenue_os.models.deal import Deal
from revenue_os.models.organization import (
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationStatus,
)
from revenue_os.models.user import User
from revenue_os.services.calendar_executor import (
    create_tenant_calendar_event,
    revalidate_provider_slot,
    resolve_calendar_connector,
)
from revenue_os.services.revenue_workers import WORKER_BOOKING, run_booking_worker
from revenue_os.services.tenant_resolution import ORGANIZATION_COOKIE
from runner_api import app

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_OPERATOR = "Krishna Founder"

_FUTURE_START = (datetime.now(timezone.utc) + timedelta(days=2)).replace(microsecond=0)
_FUTURE_END = _FUTURE_START + timedelta(minutes=30)
_FUTURE_SLOT = {"start": _FUTURE_START.isoformat(), "end": _FUTURE_END.isoformat()}
_AVAILABILITY = {
    "ok": True,
    "connector": "google_calendar",
    "organization_id": str(_ORG_A),
    "duration_minutes": 30,
    "slots": [_FUTURE_SLOT],
}
_CALENDAR_OK = {
    "ok": True,
    "provider_event_id": "evt-freeze",
    "connector": "google_calendar",
    "organization_id": str(_ORG_A),
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
    engine = create_engine(f"sqlite:///{tmp_path / 'm4_5_freeze.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    for mod in (identity_mod, rev_orch_mod):
        monkeypatch.setattr(mod, "SessionLocal", sf)
    import revenue_os.database as db_mod
    import revenue_os.services.activity_log as al
    import revenue_os.services.approvals as approvals_mod
    import revenue_os.services.tenant_resolution as tr

    monkeypatch.setattr(db_mod, "SessionLocal", sf)
    monkeypatch.setattr(tr, "SessionLocal", sf)
    monkeypatch.setattr(approvals_mod, "SessionLocal", sf)
    monkeypatch.setattr(al, "SessionLocal", sf)
    return sf


def _seed(db_factory: sessionmaker, *, booking_eligible: bool = True) -> dict[str, str]:
    db = db_factory()
    try:
        db.add_all([
            Organization(id=_ORG_A, name="A", slug="org-a", status=OrganizationStatus.ACTIVE),
            Organization(id=_ORG_B, name="B", slug="org-b", status=OrganizationStatus.ACTIVE),
        ])
        owner_a = User(
            email="owner-a@example.com", hashed_password=hash_password("pass-o"),
            full_name=_OPERATOR, role="owner", is_active=1,
        )
        owner_b = User(
            email="owner-b@example.com", hashed_password=hash_password("pass-b"),
            full_name="Owner B", role="owner", is_active=1,
        )
        db.add_all([owner_a, owner_b])
        db.flush()
        db.add_all([
            OrganizationMembership(user_id=owner_a.id, organization_id=_ORG_A, role="owner", status=MembershipStatus.ACTIVE),
            OrganizationMembership(user_id=owner_b.id, organization_id=_ORG_B, role="owner", status=MembershipStatus.ACTIVE),
        ])
        db.add_all([
            Contact(
                id=_CONTACT_A, first_name="Alice", last_name="A", email="alice@example.com",
                status=ContactStatus.LEAD, source=ContactSource.MANUAL,
                organization_id=_ORG_A, lead_score=10, created_at=datetime.now(timezone.utc),
            ),
            Contact(
                id=_CONTACT_B, first_name="Bob", last_name="B", email="bob@example.com",
                status=ContactStatus.LEAD, source=ContactSource.MANUAL,
                organization_id=_ORG_B, lead_score=20, created_at=datetime.now(timezone.utc),
            ),
        ])
        if booking_eligible:
            reply_act = Activity(
                contact_id=_CONTACT_A, activity_type=ActivityType.EMAIL_REPLY,
                subject="Meeting interest", body="Let's meet",
                direction="inbound", status="completed",
            )
            db.add(reply_act)
            db.flush()
            db.add(AgentActionLog(
                organization_id=_ORG_A,
                actor="revenue_workflow_orchestrator",
                action_type="rev_orch_reply_assessment",
                target_type="contact",
                target_id=str(_CONTACT_A),
                status="completed",
                detail={
                    "activity_id": str(reply_act.id),
                    "message_id": "msg-m4-5",
                    "assessment": {"reply_type": "MEETING_INTEREST", "meeting_interest": True},
                    "routing": {
                        "reply_type": "MEETING_INTEREST",
                        "booking_eligible": True,
                        "recommended_next_action": "BOOKING_ELIGIBLE",
                        "booking_created": False,
                    },
                },
            ))
        db.commit()
        return {"org_a": str(_ORG_A), "org_b": str(_ORG_B)}
    finally:
        db.close()


def _login(client: TestClient, email: str, password: str, org_id: str) -> None:
    r = client.post("/api/v1/identity/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    client.cookies.set(ORGANIZATION_COOKIE, org_id)


def _propose(client: TestClient) -> dict:
    with patch("revenue_os.services.revenue_orchestration_service.get_tenant_availability", return_value=_AVAILABILITY):
        r = client.post(f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose", json={})
    assert r.status_code == 200, r.text
    return r.json()


def test_m4_5_canonical_booking_workflow() -> None:
    WorkflowOrchestrator.seed_revenue_workflows()
    names = [w.name for w in WorkflowOrchestrator.list_workflows()]
    assert REV_ORCH_M4_WORKFLOW_KEY in names
    assert names.count(REV_ORCH_M4_WORKFLOW_KEY) == 1
    src = inspect.getsource(WorkflowOrchestrator._handle_m4_booking_to_meeting)
    assert "run_booking_to_meeting" in src


def test_m4_5_eligibility_cannot_be_payload_forged(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db, booking_eligible=False)
    _login(client, "owner-a@example.com", "pass-o", str(_ORG_A))
    r = client.post(
        f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose",
        json={
            "organization_id": str(_ORG_A),
            "booking_eligible": True,
            "meeting_interest": True,
            "selected_slot": _FUTURE_SLOT,
        },
    )
    assert r.status_code == 422


def test_m4_5_cross_tenant_contact_booking_blocked(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-b@example.com", "pass-b", str(_ORG_B))
    r = client.post(f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose", json={})
    assert r.status_code == 422


def test_m4_5_cross_tenant_availability_blocked(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-b@example.com", "pass-b", str(_ORG_B))
    r = client.get(f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/availability")
    assert r.status_code == 422


def test_m4_5_cross_tenant_credential_resolution_blocked() -> None:
    src = inspect.getsource(resolve_calendar_connector)
    assert "allow_global_fallback=False" in src


def test_m4_5_ai_cannot_select_credential() -> None:
    src = inspect.getsource(run_booking_worker)
    assert "load_credentials" not in src
    assert "resolve_calendar_connector" not in src


def test_m4_5_ai_cannot_execute_calendar_mutation() -> None:
    src = inspect.getsource(run_booking_worker)
    assert "create_event" not in src
    assert "create_tenant_calendar_event" not in src


def test_m4_5_ai_cannot_self_approve() -> None:
    src = inspect.getsource(run_booking_worker)
    assert "request_approval" not in src
    assert "decide(" not in src
    assert WORKER_BOOKING == "booking_worker"


def test_m4_5_pending_booking_blocked(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", str(_ORG_A))
    body = _propose(client)
    db = tenant_db()
    try:
        req = db.get(ApprovalRequest, body["approval_id"])
        assert req is not None
        assert req.status == "pending"
        assert req.action_type == "book_meeting"
        assert db.query(Activity).filter(Activity.activity_type == ActivityType.MEETING).count() == 0
    finally:
        db.close()


def test_m4_5_rejected_booking_blocked(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", str(_ORG_A))
    body = _propose(client)
    assert client.post(f"/api/v1/approvals/{body['approval_id']}/reject", json={}).status_code == 200
    with patch("revenue_os.services.calendar_executor.create_tenant_calendar_event") as mock_create:
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
    assert r.status_code in (409, 422)
    mock_create.assert_not_called()


def test_m4_5_approved_booking_executes(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", str(_ORG_A))
    body = _propose(client)
    with patch("revenue_os.services.calendar_executor.create_tenant_calendar_event", return_value=_CALENDAR_OK):
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
    assert r.status_code == 200
    exec_result = r.json()["request"]["execution_result"]
    assert exec_result.get("executed") is True
    assert exec_result.get("provider_event_id") == "evt-freeze"


def test_m4_5_duplicate_execution_blocked(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", str(_ORG_A))
    body = _propose(client)
    with patch("revenue_os.services.calendar_executor.create_tenant_calendar_event", return_value=_CALENDAR_OK):
        r1 = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        r2 = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
    assert r1.status_code == 200
    assert r2.status_code in (200, 409, 422)
    db = tenant_db()
    try:
        assert db.query(Activity).filter(
            Activity.contact_id == _CONTACT_A, Activity.activity_type == ActivityType.MEETING
        ).count() == 1
    finally:
        db.close()


def test_m4_5_provider_level_stale_slot_race_blocked() -> None:
    with patch("revenue_os.services.calendar_executor.resolve_calendar_connector", return_value=("google_calendar", {"k": "v"})):
        with patch("revenue_os.integrations.calendar.GoogleCalendarClient.configure"):
            with patch("revenue_os.integrations.calendar.GoogleCalendarClient.has_busy_overlap", return_value=True):
                with patch("revenue_os.integrations.calendar.GoogleCalendarClient.create_event") as mock_create:
                    result = create_tenant_calendar_event(
                        str(_ORG_A),
                        title="Meeting",
                        description="",
                        start_time=_FUTURE_START,
                        end_time=_FUTURE_END,
                        attendees=["alice@example.com"],
                    )
    assert result["ok"] is False
    assert "no longer available" in result["reason"].lower()
    mock_create.assert_not_called()


def test_m4_5_past_slot_blocked() -> None:
    past_start = datetime.now(timezone.utc) - timedelta(hours=1)
    past_end = past_start + timedelta(minutes=30)
    result = revalidate_provider_slot(str(_ORG_A), past_start, past_end)
    assert result["ok"] is False
    assert "past" in result["reason"].lower()


def test_m4_5_suppression_before_execution_blocks(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", str(_ORG_A))
    body = _propose(client)
    db = tenant_db()
    try:
        contact = db.get(Contact, _CONTACT_A)
        contact.tags = "unsubscribed"
        db.commit()
    finally:
        db.close()
    with patch("revenue_os.services.calendar_executor.create_tenant_calendar_event") as mock_create:
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
    assert r.status_code == 200
    exec_result = r.json()["request"]["execution_result"]
    assert exec_result.get("executed") is False
    mock_create.assert_not_called()


def test_m4_5_tenant_binding_changed_fails_closed() -> None:
    with patch("revenue_os.services.calendar_executor.resolve_calendar_connector", return_value=None):
        result = create_tenant_calendar_event(
            str(_ORG_A),
            title="Meeting",
            description="",
            start_time=_FUTURE_START,
            end_time=_FUTURE_END,
            attendees=["alice@example.com"],
        )
    assert result["ok"] is False
    assert result.get("provider_event_id") is None


def test_m4_5_client_decided_by_cannot_spoof_human(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", str(_ORG_A))
    body = _propose(client)
    r = client.post(
        f"/api/v1/approvals/{body['approval_id']}/approve",
        json={"decided_by": "booking_worker"},
    )
    db = tenant_db()
    try:
        req = db.get(ApprovalRequest, body["approval_id"])
        assert req.decided_by != "booking_worker"
    finally:
        db.close()
    assert r.status_code in (200, 403, 409, 422)


def test_m4_5_contact_status_unchanged(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", str(_ORG_A))
    body = _propose(client)
    with patch("revenue_os.services.calendar_executor.create_tenant_calendar_event", return_value=_CALENDAR_OK):
        client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
    db = tenant_db()
    try:
        assert db.get(Contact, _CONTACT_A).status == ContactStatus.LEAD
    finally:
        db.close()


def test_m4_5_deal_stage_unchanged(client: TestClient, tenant_db: sessionmaker) -> None:
    from revenue_os.services.approvals import _execute_book_meeting

    src = inspect.getsource(_execute_book_meeting)
    assert "Deal.stage" not in src
    assert "deal.stage" not in src
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", str(_ORG_A))
    body = _propose(client)
    with patch("revenue_os.services.calendar_executor.create_tenant_calendar_event", return_value=_CALENDAR_OK):
        client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
    db = tenant_db()
    try:
        assert db.query(Deal).count() == 0
    finally:
        db.close()


def test_m4_5_m3_5_baseline_unchanged() -> None:
    from revenue_os.services.reply_routing import REPLY_TYPES
    from revenue_os.agents.orchestration import REV_ORCH_M3_WORKFLOW_KEY

    assert "MEETING_INTEREST" in REPLY_TYPES
    assert REV_ORCH_M3_WORKFLOW_KEY == "rev_orch_inbound_reply_handling"


def test_m4_5_legacy_booking_authority_bypass_unreachable() -> None:
    import runner_api_routers.integrations as int_mod

    src = inspect.getsource(int_mod.create_google_calendar_event)
    assert "WorkflowOrchestrator" not in src
    assert "book_meeting" not in src
    assert "evaluate_booking_eligibility" not in src


def test_m4_5_outlook_availability_fails_closed_at_execution() -> None:
    with patch(
        "revenue_os.services.calendar_executor.resolve_calendar_connector",
        return_value=("outlook_calendar", {"tenant_id": "t", "access_token": "x"}),
    ):
        result = revalidate_provider_slot(str(_ORG_A), _FUTURE_START, _FUTURE_END)
    assert result["ok"] is False
    assert "outlook" in result["reason"].lower()


def test_m4_5_timezone_naive_normalized_utc() -> None:
    naive_start = datetime.utcnow() + timedelta(days=3)
    naive_end = naive_start + timedelta(minutes=30)
    with patch("revenue_os.services.calendar_executor.resolve_calendar_connector", return_value=None):
        result = revalidate_provider_slot(str(_ORG_A), naive_start, naive_end)
    assert result["ok"] is False
    assert "connector" in result["reason"].lower() or "configured" in result["reason"].lower()


def test_m4_5_booking_worker_classification() -> None:
    src = inspect.getsource(run_booking_worker)
    assert "SPECIALIZED_AI_WORKER" in src
