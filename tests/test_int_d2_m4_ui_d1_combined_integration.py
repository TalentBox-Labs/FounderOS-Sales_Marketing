"""INT-D2 — combined M4 + UI-D1 integration certification (no booking UI)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import revenue_os.models  # noqa: F401
from tests.conftest import build_test_approval_request
import runner_api_routers.identity as identity_mod
import runner_api_routers.revenue_orchestration as rev_orch_mod
import runner_api_routers.ui as ui_mod
from revenue_os.auth import hash_password
from revenue_os.models.activity import Activity, ActivityType
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
from revenue_os.services.tenant_resolution import ORGANIZATION_COOKIE
from runner_api import app

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")


@pytest.fixture(autouse=True)
def _reset() -> None:
    identity_mod._revoked_jtis.clear()
    identity_mod._login_failures.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def tenant_db(monkeypatch: pytest.MonkeyPatch, tmp_path) -> sessionmaker:
    engine = create_engine(f"sqlite:///{tmp_path / 'int_d2.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    import revenue_os.database as db_mod
    import revenue_os.services.activity_log as al
    import revenue_os.services.approvals as approvals_mod
    import revenue_os.services.founder_ui_read_model as founder_rm
    import revenue_os.services.tenant_resolution as tr

    for mod in (
        db_mod,
        tr,
        approvals_mod,
        al,
        ui_mod,
        founder_rm,
        identity_mod,
        rev_orch_mod,
    ):
        if hasattr(mod, "SessionLocal"):
            monkeypatch.setattr(mod, "SessionLocal", sf)
    monkeypatch.setenv("FOUNDER_OS_REQUIRE_LOGIN", "0")
    return sf


def _seed(db_factory: sessionmaker) -> None:
    db = db_factory()
    try:
        owner_a = User(
            email="owner-a@example.com", hashed_password=hash_password("pass-a"),
            full_name="Owner A", role="owner", is_active=1,
        )
        owner_b = User(
            email="owner-b@example.com", hashed_password=hash_password("pass-b"),
            full_name="Owner B", role="owner", is_active=1,
        )
        db.add_all([
            Organization(id=_ORG_A, name="A", slug="org-a", status=OrganizationStatus.ACTIVE),
            Organization(id=_ORG_B, name="B", slug="org-b", status=OrganizationStatus.ACTIVE),
            owner_a, owner_b,
        ])
        db.flush()
        db.add_all([
            OrganizationMembership(user_id=owner_a.id, organization_id=_ORG_A, role="owner", status=MembershipStatus.ACTIVE),
            OrganizationMembership(user_id=owner_b.id, organization_id=_ORG_B, role="owner", status=MembershipStatus.ACTIVE),
            Contact(
                id=_CONTACT_A, first_name="Alice", last_name="A", email="alice@example.com",
                status=ContactStatus.LEAD, source=ContactSource.MANUAL, organization_id=_ORG_A,
            ),
            Contact(
                id=_CONTACT_B, first_name="Bob", last_name="B", email="bob@example.com",
                status=ContactStatus.LEAD, source=ContactSource.MANUAL, organization_id=_ORG_B,
            ),
        ])
        db.add(AgentActionLog(
            organization_id=_ORG_A,
            actor="revenue_workflow_orchestrator",
            action_type="rev_orch_reply_assessment",
            target_type="contact",
            target_id=str(_CONTACT_A),
            status="completed",
            detail={
                "assessment": {"reply_type": "MEETING_INTEREST", "meeting_interest": True, "summary": "Wants a call"},
                "routing": {
                    "reply_type": "MEETING_INTEREST",
                    "booking_eligible": True,
                    "recommended_next_action": "BOOKING_ELIGIBLE",
                    "meeting_interest": True,
                },
            },
        ))
        db.add(AgentActionLog(
            organization_id=_ORG_A,
            actor="booking_worker",
            action_type="worker_booking_proposal",
            target_type="contact",
            target_id=str(_CONTACT_A),
            status="completed",
            detail={"meeting_title": "Discovery call"},
        ))
        db.add(Activity(
            contact_id=_CONTACT_A,
            activity_type=ActivityType.MEETING,
            subject="Booked meeting",
            body='{"idempotency_key":"rev-orch-m4:book:demo","provider_event_id":"evt-int-d2"}',
            direction="outbound",
            status="completed",
        ))
        db.add(build_test_approval_request(
            requested_by="booking_worker",
            action_type="book_meeting",
            title="Book meeting with Alice A",
            description="M4 booking proposal",
            target_id=str(_CONTACT_A),
            payload={
                "organization_id": str(_ORG_A),
                "contact_id": str(_CONTACT_A),
                "selected_slot_start": "2026-01-15T10:00:00+00:00",
                "selected_slot_end": "2026-01-15T10:30:00+00:00",
            },
        ))
        db.commit()
    finally:
        db.close()


def _login(client: TestClient, email: str, password: str, org_id: str) -> None:
    r = client.post("/api/v1/identity/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    client.cookies.set(ORGANIZATION_COOKIE, org_id)


def test_int_d2_route_coexistence() -> None:
    paths = set(app.openapi()["paths"].keys())
    assert "/api/v1/revenue/contacts/{contact_id}/booking/eligibility" in paths
    assert "/api/v1/revenue/contacts/{contact_id}/booking/availability" in paths
    assert "/api/v1/revenue/contacts/{contact_id}/booking/propose" in paths
    assert "/api/v1/approvals/{request_id}/approve" in paths
    ui_paths = {getattr(r, "path", None) for r in ui_mod.router.routes}
    assert "/command" in ui_paths
    assert "/demand" in ui_paths
    assert "/contacts/{contact_id}" in ui_paths
    assert "/pending-approvals" in ui_paths
    assert "/activity" in ui_paths


def test_int_d2_book_meeting_approval_renders_generically(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    r = client.get("/pending-approvals")
    assert r.status_code == 200
    assert "Book meeting with Alice A" in r.text
    assert "Meeting booking" in r.text or "Approve booking" in r.text
    assert 'data-testid="approve-btn"' in r.text
    assert "send-email" not in r.text.lower() or "approve booking" in r.text.lower()


def test_int_d2_booking_eligible_visible_without_booking_ui(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    r = client.get(f"/contacts/{_CONTACT_A}")
    assert r.status_code == 200
    assert "Meeting interest" in r.text
    assert "Booking eligible" in r.text
    assert (
        "approval required" in r.text.lower()
        or 'data-testid="booking-approval-pending"' in r.text
    )
    assert "Propose booking" not in r.text
    assert 'data-testid="booking-eligible-panel"' not in r.text
    assert 'data-testid="booking-submit-proposal"' not in r.text
    assert "contactAction('booking')" not in r.text


def test_int_d2_m4_activity_shape_renders(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    r = client.get("/activity")
    assert r.status_code == 200
    assert r.status_code != 500
    assert "Worker Booking Proposal" in r.text or "worker_booking_proposal" in r.text
    assert "Reply assessed" in r.text or "rev_orch_reply_assessment" in r.text


def test_int_d2_cross_tenant_ui_and_booking_blocked(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-b@example.com", "pass-b", str(_ORG_B))
    contact = client.get(f"/contacts/{_CONTACT_A}")
    assert contact.status_code in (200, 404, 422)
    if contact.status_code == 200:
        assert "alice@example.com" not in contact.text
        assert 'data-testid="contact-not-found"' in contact.text or "unavailable" in contact.text.lower() or "not found" in contact.text.lower()
    approvals = client.get("/pending-approvals")
    assert approvals.status_code == 200
    assert "Book meeting with Alice A" not in approvals.text
    elig = client.get(f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/eligibility")
    assert elig.status_code == 422
    propose = client.post(f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose", json={})
    assert propose.status_code == 422
