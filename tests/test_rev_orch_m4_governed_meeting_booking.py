"""REV-ORCH M4 — governed meeting booking tests."""

from __future__ import annotations

import inspect
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
from revenue_os.agents.orchestration import REV_ORCH_M4_WORKFLOW_KEY, WorkflowOrchestrator
from revenue_os.auth import hash_password
from revenue_os.models.activity import Activity, ActivityType, MeetingActivity
from revenue_os.models.approvals import ApprovalRequest
from revenue_os.models.automation_state import AgentActionLog
from revenue_os.models.base import Base
from revenue_os.models.contact import Contact, ContactSource, ContactStatus
from revenue_os.models.organization import (
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationStatus,
)
from revenue_os.models.user import User
from revenue_os.services.revenue_workers import WORKER_BOOKING, run_booking_worker
from revenue_os.services.tenant_resolution import ORGANIZATION_COOKIE
from runner_api import app

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_OPERATOR = "Krishna Founder"

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
    engine = create_engine(f"sqlite:///{tmp_path / 'm4_rev_orch.db'}")
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
        org_a = Organization(id=_ORG_A, name="A", slug="org-a", status=OrganizationStatus.ACTIVE)
        org_b = Organization(id=_ORG_B, name="B", slug="org-b", status=OrganizationStatus.ACTIVE)
        owner_a = User(
            email="owner-a@example.com",
            hashed_password=hash_password("pass-o"),
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
        db.add_all([org_a, org_b, owner_a, owner_b])
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
                contact_id=_CONTACT_A,
                activity_type=ActivityType.EMAIL_REPLY,
                subject="Meeting interest reply",
                body="Can we schedule a call?",
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
                        "message_id": "msg-meeting-1",
                        "assessment": {"reply_type": "MEETING_INTEREST", "meeting_interest": True},
                        "routing": {
                            "reply_type": "MEETING_INTEREST",
                            "booking_eligible": True,
                            "recommended_next_action": "BOOKING_ELIGIBLE",
                            "booking_created": False,
                        },
                    },
                )
            )
        db.commit()
        return {"org_a": str(_ORG_A), "org_b": str(_ORG_B)}
    finally:
        db.close()


def _login(client: TestClient, email: str, password: str, org_id: str) -> None:
    r = client.post("/api/v1/identity/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    client.cookies.set(ORGANIZATION_COOKIE, org_id)


def _propose_booking(
    client: TestClient,
    contact_id: str = str(_CONTACT_A),
    *,
    availability: dict | None = None,
) -> dict:
    avail = availability or _AVAILABILITY
    with patch("revenue_os.services.revenue_orchestration_service.get_tenant_availability", return_value=avail):
        r = client.post(f"/api/v1/revenue/contacts/{contact_id}/booking/propose", json={})
    assert r.status_code == 200, r.text
    return r.json()


# --- Core lifecycle ---

def test_m4_canonical_dispatch_uses_orchestrator() -> None:
    WorkflowOrchestrator.seed_revenue_workflows()
    names = [w.name for w in WorkflowOrchestrator.list_workflows()]
    assert REV_ORCH_M4_WORKFLOW_KEY in names
    src = inspect.getsource(WorkflowOrchestrator._handle_m4_booking_to_meeting)
    assert "run_booking_to_meeting" in src


def test_m4_happy_path_proposal_and_approval(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", str(_ORG_A))
    body = _propose_booking(client)
    assert body["ok"] is True
    assert body["approval_id"]
    assert body["approval_status"] == "pending"
    assert body["state"] == "BOOKING_PROPOSED"

    calendar_result = {
        "ok": True,
        "provider_event_id": "evt-123",
        "connector": "google_calendar",
        "organization_id": str(_ORG_A),
        "idempotency_key": body.get("eligibility", {}).get("idempotency_key"),
    }
    with patch("revenue_os.services.calendar_executor.create_tenant_calendar_event", return_value=calendar_result):
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
    assert r.status_code == 200, r.text
    exec_result = r.json().get("request", {}).get("execution_result") or {}
    assert exec_result.get("executed") is True
    assert exec_result.get("provider_event_id") == "evt-123"

    db = tenant_db()
    try:
        contact = db.get(Contact, _CONTACT_A)
        assert contact.status == ContactStatus.LEAD
        meetings = db.query(Activity).filter(
            Activity.contact_id == _CONTACT_A, Activity.activity_type == ActivityType.MEETING
        ).all()
        assert len(meetings) == 1
        assert db.query(MeetingActivity).filter(MeetingActivity.activity_id == meetings[0].id).count() == 1
    finally:
        db.close()


# --- Tenant isolation ---

def test_m4_cross_tenant_booking_blocked(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-b@example.com", "pass-b", str(_ORG_B))
    with patch("revenue_os.services.revenue_orchestration_service.get_tenant_availability", return_value=_AVAILABILITY):
        r = client.post(f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose", json={})
    assert r.status_code == 422


def test_m4_eligibility_cross_tenant_read_blocked(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-b@example.com", "pass-b", str(_ORG_B))
    r = client.get(f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/eligibility")
    assert r.status_code == 422


# --- Eligibility ---

def test_m4_no_meeting_interest_not_eligible(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db, booking_eligible=False)
    _login(client, "owner-a@example.com", "pass-o", str(_ORG_A))
    r = client.get(f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/eligibility")
    assert r.status_code == 200
    assert r.json()["eligible"] is False
    assert r.json()["state"] == "BOOKING_NO_MEETING_INTEREST"


def test_m4_opt_out_contact_not_eligible(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    db = tenant_db()
    try:
        contact = db.get(Contact, _CONTACT_A)
        contact.tags = "unsubscribed"
        db.commit()
    finally:
        db.close()
    _login(client, "owner-a@example.com", "pass-o", str(_ORG_A))
    r = client.get(f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/eligibility")
    assert r.json()["eligible"] is False
    assert r.json()["state"] == "BOOKING_STOPPED"


# --- AI authority ---

def test_m4_booking_worker_cannot_create_calendar_event() -> None:
    src = inspect.getsource(run_booking_worker)
    assert "create_event" not in src
    assert "create_tenant_calendar_event" not in src
    assert "decide(" not in src


def test_m4_booking_worker_classification() -> None:
    src = inspect.getsource(run_booking_worker)
    assert "SPECIALIZED_AI_WORKER" in src
    assert WORKER_BOOKING == "booking_worker"


# --- Human authority ---

def test_m4_pending_booking_cannot_execute(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", str(_ORG_A))
    body = _propose_booking(client)
    db = tenant_db()
    try:
        req = db.get(ApprovalRequest, body["approval_id"])
        assert req.status == "pending"
        assert req.action_type == "book_meeting"
    finally:
        db.close()


def test_m4_rejected_booking_cannot_execute(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", str(_ORG_A))
    body = _propose_booking(client)
    r = client.post(f"/api/v1/approvals/{body['approval_id']}/reject", json={})
    assert r.status_code == 200
    with patch("revenue_os.services.calendar_executor.create_tenant_calendar_event") as mock_create:
        r2 = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        assert r2.status_code == 422 or "already rejected" in r2.text.lower()
        mock_create.assert_not_called()


def test_m4_duplicate_approval_idempotent(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", str(_ORG_A))
    body = _propose_booking(client)
    calendar_result = {
        "ok": True,
        "provider_event_id": "evt-dup",
        "connector": "google_calendar",
        "organization_id": str(_ORG_A),
    }
    with patch("revenue_os.services.calendar_executor.create_tenant_calendar_event", return_value=calendar_result):
        r1 = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        r2 = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
    assert r1.status_code == 200
    assert r2.status_code in (200, 409, 422)
    db = tenant_db()
    try:
        count = db.query(Activity).filter(
            Activity.contact_id == _CONTACT_A, Activity.activity_type == ActivityType.MEETING
        ).count()
        assert count == 1
    finally:
        db.close()


# --- CRM authority ---

def test_m4_booking_does_not_mutate_contact_status(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", str(_ORG_A))
    body = _propose_booking(client)
    calendar_result = {"ok": True, "provider_event_id": "evt-crm", "connector": "google_calendar"}
    with patch("revenue_os.services.calendar_executor.create_tenant_calendar_event", return_value=calendar_result):
        client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
    db = tenant_db()
    try:
        assert db.get(Contact, _CONTACT_A).status == ContactStatus.LEAD
    finally:
        db.close()


# --- Calendar credential isolation ---

def test_m4_availability_requires_tenant_connector(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", str(_ORG_A))
    no_connector = {"ok": False, "reason": "No tenant-scoped calendar connector configured", "slots": []}
    with patch("revenue_os.services.revenue_orchestration_service.get_tenant_availability", return_value=no_connector):
        r = client.post(f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose", json={})
    assert r.status_code == 422


def test_m4_calendar_executor_uses_tenant_scoped_credentials() -> None:
    from revenue_os.services import calendar_executor

    src = inspect.getsource(calendar_executor.resolve_calendar_connector)
    assert "allow_global_fallback=False" in src


# --- Stale slot ---

def test_m4_stale_slot_blocked_at_execution(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", str(_ORG_A))
    past_slot = {
        "start": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        "end": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
    }
    body = _propose_booking(client, availability={**_AVAILABILITY, "slots": [past_slot]})
    calendar_result = {"ok": True, "provider_event_id": "evt-stale", "connector": "google_calendar"}
    with patch("revenue_os.services.calendar_executor.create_tenant_calendar_event", return_value=calendar_result) as mock_create:
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
    assert r.status_code == 200
    exec_result = r.json().get("request", {}).get("execution_result") or {}
    assert exec_result.get("executed") is False or "past" in str(exec_result.get("error", "")).lower()
    mock_create.assert_not_called()


# --- Legacy ---

def test_m4_legacy_integrations_route_not_canonical_booking() -> None:
    import runner_api_routers.integrations as int_mod

    src = inspect.getsource(int_mod.create_google_calendar_event)
    assert "WorkflowOrchestrator" not in src
    assert "book_meeting" not in src


def test_m4_worker_cannot_self_approve() -> None:
    from revenue_os.services import revenue_workers

    src = inspect.getsource(revenue_workers.run_booking_worker)
    assert "request_approval" not in src
    assert WORKER_BOOKING == "booking_worker"
