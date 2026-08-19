"""COS-1 — Founder OS commercial spine (governed person journey)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

import revenue_os.models  # noqa: F401
import runner_api_routers.identity as identity_mod
import runner_api_routers.revenue_orchestration as rev_orch_mod
import runner_api_routers.ui as ui_mod
from revenue_os.agents.orchestration import WorkflowOrchestrator
from revenue_os.auth import hash_password
from revenue_os.models.activity import Activity, ActivityType
from revenue_os.models.approvals import ApprovalRequest
from revenue_os.models.automation_state import AgentActionLog
from revenue_os.models.base import Base
from revenue_os.models.contact import Company, Contact, ContactSource, ContactStatus
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
_COMPANY_A = uuid.UUID("ca11e001-0000-4000-8000-00000000000a")
_COMPANY_B = uuid.UUID("ca11e001-0000-4000-8000-00000000000b")
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
    engine = create_engine(f"sqlite:///{tmp_path / 'cos1.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    import revenue_os.database as db_mod
    import revenue_os.services.activity_log as al
    import revenue_os.services.approvals as approvals_mod
    import revenue_os.services.founder_ui_read_model as founder_rm
    import revenue_os.services.operator_flow_read_model as of_rm
    import revenue_os.services.revenue_orchestration_service as rev_svc
    import revenue_os.services.tenant_resolution as tr

    for mod in (
        db_mod,
        tr,
        approvals_mod,
        al,
        ui_mod,
        founder_rm,
        of_rm,
        rev_svc,
        identity_mod,
        rev_orch_mod,
    ):
        if hasattr(mod, "SessionLocal"):
            monkeypatch.setattr(mod, "SessionLocal", sf)
    monkeypatch.setenv("FOUNDER_OS_REQUIRE_LOGIN", "0")
    return sf


def _login(client: TestClient, email: str, password: str, org_id: str) -> None:
    client.post("/login", data={"email": email, "password": password})
    client.cookies.set(ORGANIZATION_COOKIE, org_id)


def _google_connector():
    return ("google_calendar", {"client_id": "x", "client_secret": "y", "refresh_token": "z"})


def _seed(db_factory: sessionmaker) -> None:
    db = db_factory()
    try:
        db.add_all(
            [
                Organization(id=_ORG_A, name="A", slug="org-a", status=OrganizationStatus.ACTIVE),
                Organization(id=_ORG_B, name="B", slug="org-b", status=OrganizationStatus.ACTIVE),
            ]
        )
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
        company = Company(id=_COMPANY_A, name="Acme Labs", domain="acme-cos1.demo.local")
        company_b = Company(
            id=_COMPANY_B, name="OtherCo Secret", domain="otherco-cos1.demo.local"
        )
        db.add_all([company, company_b])
        db.flush()
        db.add_all(
            [
                OrganizationMembership(
                    user_id=owner_a.id,
                    organization_id=_ORG_A,
                    role="owner",
                    status=MembershipStatus.ACTIVE,
                ),
                OrganizationMembership(
                    user_id=owner_b.id,
                    organization_id=_ORG_B,
                    role="owner",
                    status=MembershipStatus.ACTIVE,
                ),
                Contact(
                    id=_CONTACT_A,
                    first_name="Alice",
                    last_name="A",
                    email="alice@example.com",
                    status=ContactStatus.LEAD,
                    source=ContactSource.MANUAL,
                    organization_id=_ORG_A,
                    company_id=company.id,
                    lead_score=70,
                ),
                Contact(
                    id=_CONTACT_B,
                    first_name="Bob",
                    last_name="B",
                    email="bob@example.com",
                    status=ContactStatus.LEAD,
                    source=ContactSource.MANUAL,
                    organization_id=_ORG_B,
                    company_id=company_b.id,
                ),
            ]
        )
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
        db.add_all(
            [
                AgentActionLog(
                    organization_id=_ORG_A,
                    actor="revenue_workflow_orchestrator",
                    action_type="rev_orch_research_to_outreach",
                    target_type="contact",
                    target_id=str(_CONTACT_A),
                    status="completed",
                ),
                AgentActionLog(
                    organization_id=_ORG_A,
                    actor="revenue_workflow_orchestrator",
                    action_type="send_outreach_email",
                    target_type="contact",
                    target_id=str(_CONTACT_A),
                    status="completed",
                ),
                AgentActionLog(
                    organization_id=_ORG_A,
                    actor="revenue_workflow_orchestrator",
                    action_type="rev_orch_followup_eligibility",
                    target_type="contact",
                    target_id=str(_CONTACT_A),
                    status="completed",
                ),
                AgentActionLog(
                    organization_id=_ORG_A,
                    actor="revenue_workflow_orchestrator",
                    action_type="rev_orch_reply_assessment",
                    target_type="contact",
                    target_id=str(_CONTACT_A),
                    status="completed",
                    detail={
                        "activity_id": str(reply_act.id),
                        "assessment": {
                            "reply_type": "MEETING_INTEREST",
                            "meeting_interest": True,
                            "summary": "Wants a call",
                        },
                        "routing": {
                            "reply_type": "MEETING_INTEREST",
                            "booking_eligible": True,
                            "recommended_next_action": "BOOKING_ELIGIBLE",
                        },
                    },
                ),
            ]
        )
        db.commit()
    finally:
        db.close()


def test_home_renders_org_scoped(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    r = client.get("/command")
    assert r.status_code == 200
    assert 'data-testid="founder-org-name"' in r.text
    assert "Command Center" in r.text
    assert 'data-testid="command-approvals"' in r.text
    assert "bob@example.com" not in r.text


def test_people_surface_org_scoped(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    r = client.get("/demand")
    assert r.status_code == 200
    assert 'data-testid="contacts-list"' in r.text
    assert "alice@example.com" in r.text
    assert "Acme Labs" in r.text
    assert "bob@example.com" not in r.text
    assert "Open workspace" in r.text


def test_person_workspace_tenant_safe_and_spine(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    with patch(
        "revenue_os.services.founder_ui_read_model.resolve_calendar_connector",
        return_value=_google_connector(),
    ):
        r = client.get(f"/contacts/{_CONTACT_A}")
    assert r.status_code == 200
    body = r.text
    assert "alice@example.com" in body
    assert "Acme Labs" in body
    assert 'data-testid="contact-workflow"' in body
    assert "Research" in body
    assert "Outreach" in body
    assert 'data-testid="contact-followup"' in body
    assert 'data-testid="contact-reply"' in body
    assert "Meeting interest" in body
    assert "Wants a call" in body
    assert "advisory only" in body.lower()
    assert 'data-testid="contact-booking-panel"' in body
    assert 'data-testid="booking-eligible-panel"' in body
    assert 'data-testid="contact-timeline"' in body
    assert "Researched" in body or "rev_orch_research_to_outreach" in body


def test_cross_tenant_person_blocked(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-b@example.com", "pass-b", str(_ORG_B))
    r = client.get(f"/contacts/{_CONTACT_A}")
    assert r.status_code == 200
    assert "alice@example.com" not in r.text
    assert 'data-testid="contact-not-found"' in r.text


def test_approval_inbox_booking_and_spoof(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    with patch(
        "revenue_os.services.revenue_orchestration_service.get_tenant_availability",
        return_value=_AVAILABILITY,
    ):
        body = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose",
            json={"selected_slot": _FUTURE_SLOT},
        ).json()
    inbox = client.get("/pending-approvals")
    assert inbox.status_code == 200
    assert "Meeting" in inbox.text
    assert 'data-testid="approve-btn"' in inbox.text
    approvals_src = (
        Path(__file__).resolve().parents[1] / "templates" / "founder_approvals.html"
    ).read_text()
    assert "JSON.stringify({})" in approvals_src
    spoof = client.post(
        f"/api/v1/approvals/{body['approval_id']}/approve",
        json={"decided_by": "booking_worker", "requested_by": "booking_worker"},
    )
    assert spoof.status_code in (200, 409, 422, 403)
    db = tenant_db()
    try:
        req = db.get(ApprovalRequest, body["approval_id"])
        assert req is not None
        assert req.decided_by != "booking_worker"
    finally:
        db.close()


def test_pending_and_rejected_booking_cannot_execute(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    with patch(
        "revenue_os.services.revenue_orchestration_service.get_tenant_availability",
        return_value=_AVAILABILITY,
    ):
        proposed = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose",
            json={"selected_slot": _FUTURE_SLOT},
        ).json()
    approval_id = proposed["approval_id"]
    with patch("revenue_os.services.calendar_executor.create_tenant_calendar_event") as mock_create:
        mock_create.side_effect = AssertionError("must not execute pending")
        # pending: executor is only on approve path; proposing must not create
        mock_create.assert_not_called()
        client.post(f"/api/v1/approvals/{approval_id}/reject", json={})
        client.post(f"/api/v1/approvals/{approval_id}/approve", json={})
        mock_create.assert_not_called()


def test_approved_booking_uses_governed_executor(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    with patch(
        "revenue_os.services.revenue_orchestration_service.get_tenant_availability",
        return_value=_AVAILABILITY,
    ):
        proposed = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose",
            json={"selected_slot": _FUTURE_SLOT},
        ).json()
    with patch(
        "revenue_os.services.calendar_executor.create_tenant_calendar_event",
        return_value={
            "ok": True,
            "provider_event_id": "evt-cos1",
            "connector": "google_calendar",
        },
    ) as mock_create:
        r = client.post(f"/api/v1/approvals/{proposed['approval_id']}/approve", json={})
    assert r.status_code == 200
    mock_create.assert_called()


def test_activity_provenance(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    r = client.get("/activity")
    assert r.status_code == 200
    assert 'data-testid="activity-timeline"' in r.text
    assert "Reply assessed" in r.text or "rev_orch_reply_assessment" in r.text
    assert "agent_log" in r.text or "revenue_workflow_orchestrator" in r.text


def test_no_unscoped_company_deal_tables_added() -> None:
    from revenue_os.models.contact import Company as CompanyModel
    from revenue_os.models.deal import Deal as DealModel

    assert CompanyModel.__tablename__ == "companies"
    assert DealModel.__tablename__ == "deals"
    assert not hasattr(CompanyModel, "accounts")


def test_no_contact_status_auto_mutation_from_booking(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    before = ContactStatus.LEAD
    with patch(
        "revenue_os.services.revenue_orchestration_service.get_tenant_availability",
        return_value=_AVAILABILITY,
    ):
        body = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/booking/propose",
            json={"selected_slot": _FUTURE_SLOT},
        ).json()
    with patch(
        "revenue_os.services.calendar_executor.create_tenant_calendar_event",
        return_value={"ok": True, "provider_event_id": "evt", "connector": "google_calendar"},
    ):
        client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
    db = tenant_db()
    try:
        contact = db.query(Contact).filter(Contact.email == "alice@example.com").one()
        assert contact.status == before
    finally:
        db.close()


def test_no_client_org_spoof_person_workspace(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _login(client, "owner-b@example.com", "pass-b", str(_ORG_B))
    client.cookies.set(ORGANIZATION_COOKIE, str(_ORG_A))
    r = client.get(f"/contacts/{_CONTACT_A}")
    assert r.status_code == 200
    assert "alice@example.com" not in r.text


def test_unresolved_org_context_never_queries_contacts(
    tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed(tenant_db)
    import revenue_os.services.founder_ui_read_model as founder_rm

    def _must_not_open_session() -> None:
        raise AssertionError("unscoped Contact read: SessionLocal must not open")

    monkeypatch.setattr(founder_rm, "SessionLocal", _must_not_open_session)
    for org_id in (None, "not-a-uuid", "bogus"):
        snap = founder_rm.build_demand_contacts_snapshot(organization_id=org_id)
        assert snap["contacts"] == []
        assert snap["pending_demands"] == []
        assert snap["state"] == "unavailable"


def test_other_org_company_cannot_enrich_people(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    from revenue_os.services.founder_ui_read_model import build_demand_contacts_snapshot

    leaked = {
        "id": str(_CONTACT_B),
        "email": "bob@example.com",
        "name": "Bob B",
        "demand_link": None,
        "deal_link": None,
        "recommendation": None,
    }
    with patch(
        "revenue_os.services.founder_ui_read_model.build_operator_flow_snapshot",
        return_value={"contacts": [leaked], "pending_demands": []},
    ):
        snap = build_demand_contacts_snapshot(organization_id=str(_ORG_A))
    assert snap["state"] == "ok"
    people = snap["contacts"]
    assert people
    assert people[0].get("company_name") is None
    blob = str(people)
    assert "OtherCo Secret" not in blob
    assert "Acme Labs" not in blob


def test_valid_org_people_render_company_name(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    from revenue_os.services.founder_ui_read_model import build_demand_contacts_snapshot

    snap = build_demand_contacts_snapshot(organization_id=str(_ORG_A))
    names = {str(p.get("company_name")) for p in snap["contacts"]}
    emails = {str(p.get("email")) for p in snap["contacts"]}
    assert "Acme Labs" in names
    assert "alice@example.com" in emails
    assert "OtherCo Secret" not in names
    assert "bob@example.com" not in emails

    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    r = client.get("/demand")
    assert r.status_code == 200
    assert "Acme Labs" in r.text
    assert "OtherCo Secret" not in r.text


def test_ai_work_excludes_human_timeline_events(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    db = tenant_db()
    try:
        db.add(
            AgentActionLog(
                organization_id=_ORG_A,
                actor="owner-a@example.com",
                action_type="contact_status_updated",
                target_type="contact",
                target_id=str(_CONTACT_A),
                status="completed",
            )
        )
        db.commit()
    finally:
        db.close()
    from revenue_os.services.founder_ui_read_model import build_contact_workspace_snapshot

    with patch(
        "revenue_os.services.founder_ui_read_model.resolve_calendar_connector",
        return_value=_google_connector(),
    ):
        snap = build_contact_workspace_snapshot(
            organization_id=str(_ORG_A),
            contact_id=str(_CONTACT_A),
        )
    labels = [t.get("label") for t in snap.get("timeline") or []]
    assert "Contact status updated" in labels
    completed = (snap.get("presentation") or {}).get("ai_work", {}).get("completed") or []
    assert "Contact status updated" not in completed
    assert any(
        label in completed
        for label in ("Researched", "Reply assessed", "Follow-up checked")
    )


def test_schema_has_no_lead_or_opportunity_tables(tenant_db: sessionmaker) -> None:
    db = tenant_db()
    try:
        names = set(inspect(db.get_bind()).get_table_names())
    finally:
        db.close()
    assert "leads" not in names
    assert "opportunities" not in names
    assert "audiences" not in names
