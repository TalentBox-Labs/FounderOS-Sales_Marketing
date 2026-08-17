"""REV-ORCH M3 — governed inbound reply handling tests."""

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
import runner_api_routers.agents as agents_mod
import runner_api_routers.identity as identity_mod
import runner_api_routers.n8n_webhooks as n8n_mod
import runner_api_routers.revenue_orchestration as rev_orch_mod
from revenue_os.agents.orchestration import (
    REV_ORCH_M3_WORKFLOW_KEY,
    WorkflowOrchestrator,
)
from revenue_os.auth import hash_password
from revenue_os.models.activity import Activity, ActivityType, EmailActivity
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
from revenue_os.services import ai_service
from revenue_os.services import revenue_workers
from revenue_os.services.integration_tenant_resolution import upsert_n8n_binding
from revenue_os.services.reply_routing import route_reply_assessment
from revenue_os.services.revenue_workers import run_reply_analysis_worker
from revenue_os.services.tenant_resolution import ORGANIZATION_COOKIE
from runner_api import app

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_OPERATOR = "Krishna Founder"
_SECRET_A = "secret-org-a"


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
    engine = create_engine(f"sqlite:///{tmp_path / 'm3_rev_orch.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    for mod in (identity_mod, rev_orch_mod, agents_mod, n8n_mod):
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


def _seed(db_factory: sessionmaker) -> dict[str, str]:
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
            ]
        )
        db.add_all(
            [
                Contact(
                    id=_CONTACT_A,
                    first_name="Alice",
                    last_name="A",
                    email="alice@example.com",
                    status=ContactStatus.LEAD,
                    source=ContactSource.MANUAL,
                    organization_id=_ORG_A,
                    lead_score=10,
                    created_at=datetime.now(timezone.utc),
                ),
                Contact(
                    id=_CONTACT_B,
                    first_name="Bob",
                    last_name="B",
                    email="bob@example.com",
                    status=ContactStatus.LEAD,
                    source=ContactSource.MANUAL,
                    organization_id=_ORG_B,
                    lead_score=20,
                    created_at=datetime.now(timezone.utc),
                ),
            ]
        )
        db.commit()
        return {"org_a": str(_ORG_A), "org_b": str(_ORG_B)}
    finally:
        db.close()


def _login(client: TestClient, email: str, password: str, org_id: str) -> None:
    r = client.post("/api/v1/identity/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    client.cookies.set(ORGANIZATION_COOKIE, org_id)


def _analysis(**overrides: object) -> dict:
    base = {
        "ok": True,
        "reply_type": "INTERESTED",
        "confidence": 0.9,
        "summary": "Positive interest",
        "objection_category": None,
        "meeting_interest": False,
        "recommended_next_action": "QUALIFY",
        "qualification_recommendation": "QUALIFY",
    }
    base.update(overrides)
    return base


def _post_reply(client: TestClient, contact_id: str, *, body: str, message_id: str, analysis: dict) -> dict:
    with patch("revenue_os.services.ai_service.analyze_inbound_reply", return_value=analysis):
        r = client.post(
            "/webhooks/n8n/email.replied",
            json={
                "contact_id": contact_id,
                "body": body,
                "message_id": message_id,
                "organization_id": str(_ORG_B),
            },
            headers={"X-N8N-Secret": _SECRET_A},
        )
    assert r.status_code == 200, r.text
    return r.json()


def test_m3_happy_path_interested_recommendation_only(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    ids = _seed(tenant_db)
    upsert_n8n_binding(ids["org_a"], _SECRET_A)
    body = _post_reply(
        client,
        str(_CONTACT_A),
        body="I'm interested",
        message_id="msg-interested-1",
        analysis=_analysis(),
    )
    assert body["ok"] is True
    db = tenant_db()
    try:
        contact = db.get(Contact, _CONTACT_A)
        assert contact is not None
        assert contact.status == ContactStatus.LEAD
        assert contact.lead_score == 20
        replies = (
            db.query(Activity)
            .filter(Activity.contact_id == _CONTACT_A, Activity.activity_type == ActivityType.EMAIL_REPLY)
            .all()
        )
        assert len(replies) == 1
        logs = db.query(AgentActionLog).filter(AgentActionLog.action_type == "rev_orch_reply_assessment").all()
        assert logs
        routing = (logs[0].detail or {}).get("routing") or {}
        assert routing.get("qualification_recommendation") == "QUALIFY"
        assert routing.get("contact_status_changed") is False
        assert routing.get("booking_created") is False
    finally:
        db.close()


def test_m3_canonical_dispatch_uses_orchestrator() -> None:
    WorkflowOrchestrator.seed_revenue_workflows()
    names = [w.name for w in WorkflowOrchestrator.list_workflows()]
    assert REV_ORCH_M3_WORKFLOW_KEY in names
    src = inspect.getsource(WorkflowOrchestrator._handle_m3_inbound_reply)
    assert "run_inbound_reply_handling" in src


def test_m3_cross_tenant_reply_injection_blocked(client: TestClient, tenant_db: sessionmaker) -> None:
    ids = _seed(tenant_db)
    upsert_n8n_binding(ids["org_a"], _SECRET_A)
    r = client.post(
        "/webhooks/n8n/email.replied",
        json={"contact_id": str(_CONTACT_B), "body": "hi", "organization_id": str(_ORG_B)},
        headers={"X-N8N-Secret": _SECRET_A},
    )
    assert r.status_code == 404
    db = tenant_db()
    try:
        assert db.get(Contact, _CONTACT_B).lead_score == 20
        assert db.query(Activity).filter(Activity.contact_id == _CONTACT_B).count() == 0
    finally:
        db.close()


def test_m3_contact_id_alone_does_not_establish_tenant(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    ids = _seed(tenant_db)
    upsert_n8n_binding(ids["org_a"], _SECRET_A)
    r = client.post(
        "/webhooks/n8n/email.replied",
        json={"contact_id": str(_CONTACT_B)},
        headers={"X-N8N-Secret": _SECRET_A},
    )
    assert r.status_code == 404


def test_m3_duplicate_reply_idempotent(client: TestClient, tenant_db: sessionmaker) -> None:
    ids = _seed(tenant_db)
    upsert_n8n_binding(ids["org_a"], _SECRET_A)
    analysis = _analysis()
    _post_reply(client, str(_CONTACT_A), body="interested", message_id="dup-1", analysis=analysis)
    _post_reply(client, str(_CONTACT_A), body="interested", message_id="dup-1", analysis=analysis)
    db = tenant_db()
    try:
        assert db.query(Activity).filter(Activity.contact_id == _CONTACT_A).count() == 1
        assert db.query(EmailActivity).filter(EmailActivity.message_id == "dup-1").count() == 1
        assert db.get(Contact, _CONTACT_A).lead_score == 20
        assessments = (
            db.query(AgentActionLog)
            .filter(AgentActionLog.action_type == "rev_orch_reply_assessment")
            .all()
        )
        assert len(assessments) == 1
    finally:
        db.close()


def test_m3_unmatched_reply_no_crm_mutation(client: TestClient, tenant_db: sessionmaker) -> None:
    ids = _seed(tenant_db)
    upsert_n8n_binding(ids["org_a"], _SECRET_A)
    r = client.post(
        "/webhooks/n8n/email.replied",
        json={"email": "nobody@example.com", "body": "hello"},
        headers={"X-N8N-Secret": _SECRET_A},
    )
    assert r.status_code == 200
    db = tenant_db()
    try:
        assert db.get(Contact, _CONTACT_A).status == ContactStatus.LEAD
        assert db.get(Contact, _CONTACT_A).lead_score == 10
    finally:
        db.close()


def test_m3_worker_cannot_mutate_contact_or_deal() -> None:
    src = inspect.getsource(revenue_workers.run_reply_analysis_worker)
    assert "request_approval" not in src
    assert "trigger_workflow" not in src
    assert "apply_contact_status_update" not in src
    assert "accept_qualified_demand" not in src
    assert "Deal" not in src
    public = {n for n, o in inspect.getmembers(ai_service, inspect.isfunction) if not n.startswith("_")}
    assert public.isdisjoint({"trigger_workflow", "accept_qualified_demand", "apply_contact_status_update"})


def test_m3_opt_out_stops_follow_up(client: TestClient, tenant_db: sessionmaker) -> None:
    ids = _seed(tenant_db)
    upsert_n8n_binding(ids["org_a"], _SECRET_A)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    sent_at = datetime.now(timezone.utc) - timedelta(days=5)
    db = tenant_db()
    try:
        db.add(
            Activity(
                contact_id=_CONTACT_A,
                activity_type=ActivityType.EMAIL,
                direction="outbound",
                status="completed",
                subject="intro",
                performed_at=sent_at,
                created_at=sent_at,
            )
        )
        db.commit()
    finally:
        db.close()
    _post_reply(
        client,
        str(_CONTACT_A),
        body="please unsubscribe",
        message_id="opt-1",
        analysis=_analysis(reply_type="OPT_OUT", confidence=0.99, summary="opt out"),
    )
    elig = client.get(f"/api/v1/revenue/contacts/{_CONTACT_A}/follow-up/eligibility")
    assert elig.status_code == 200
    assert elig.json()["eligible"] is False
    db = tenant_db()
    try:
        contact = db.get(Contact, _CONTACT_A)
        assert "unsubscribed" in (contact.tags or "")
        assert contact.status == ContactStatus.LEAD
    finally:
        db.close()


def test_m3_reply_stops_m2_cadence(client: TestClient, tenant_db: sessionmaker) -> None:
    ids = _seed(tenant_db)
    upsert_n8n_binding(ids["org_a"], _SECRET_A)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    sent_at = datetime.now(timezone.utc) - timedelta(days=5)
    db = tenant_db()
    try:
        db.add(
            Activity(
                contact_id=_CONTACT_A,
                activity_type=ActivityType.EMAIL,
                direction="outbound",
                status="completed",
                subject="intro",
                performed_at=sent_at,
                created_at=sent_at,
            )
        )
        db.commit()
    finally:
        db.close()
    _post_reply(
        client,
        str(_CONTACT_A),
        body="thanks",
        message_id="reply-stop-1",
        analysis=_analysis(reply_type="NEEDS_INFO"),
    )
    elig = client.get(f"/api/v1/revenue/contacts/{_CONTACT_A}/follow-up/eligibility")
    assert elig.json()["state"] == "FOLLOWUP_REPLY_RECEIVED"


def test_m3_meeting_interest_is_booking_eligibility_only(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    ids = _seed(tenant_db)
    upsert_n8n_binding(ids["org_a"], _SECRET_A)
    _post_reply(
        client,
        str(_CONTACT_A),
        body="can we book a meeting?",
        message_id="meet-1",
        analysis=_analysis(
            reply_type="MEETING_INTEREST",
            meeting_interest=True,
            recommended_next_action="BOOKING_ELIGIBLE",
        ),
    )
    db = tenant_db()
    try:
        log = (
            db.query(AgentActionLog)
            .filter(AgentActionLog.action_type == "rev_orch_reply_assessment")
            .first()
        )
        routing = (log.detail or {}).get("routing") or {}
        assert routing.get("booking_eligible") is True
        assert routing.get("booking_created") is False
        assert routing.get("recommended_next_action") == "BOOKING_ELIGIBLE"
        assert db.get(Contact, _CONTACT_A).status == ContactStatus.LEAD
    finally:
        db.close()


def test_m3_unknown_low_confidence_fails_closed() -> None:
    routed = route_reply_assessment(
        {"ok": True, "reply_type": "INTERESTED", "confidence": 0.1}
    )
    assert routed["reply_type"] == "UNKNOWN"
    assert routed["requires_human_review"] is True
    assert routed["contact_status_changed"] is False


def test_m3_ai_failure_unknown(client: TestClient, tenant_db: sessionmaker) -> None:
    ids = _seed(tenant_db)
    upsert_n8n_binding(ids["org_a"], _SECRET_A)
    _post_reply(
        client,
        str(_CONTACT_A),
        body="???",
        message_id="fail-1",
        analysis={"ok": False, "reason": "timeout", "reply_type": "UNKNOWN", "confidence": 0.0},
    )
    db = tenant_db()
    try:
        assert db.get(Contact, _CONTACT_A).status == ContactStatus.LEAD
        log = (
            db.query(AgentActionLog)
            .filter(AgentActionLog.action_type == "rev_orch_reply_assessment")
            .first()
        )
        assert (log.detail or {}).get("routing", {}).get("reply_type") == "UNKNOWN"
    finally:
        db.close()


def test_m3_worker_does_not_change_status(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    db = tenant_db()
    try:
        contact = db.get(Contact, _CONTACT_A)
        before = contact.status
        with patch(
            "revenue_os.services.ai_service.analyze_inbound_reply",
            return_value=_analysis(),
        ):
            run_reply_analysis_worker(db, contact, str(_ORG_A), reply_body="interested")
        db.refresh(contact)
        assert contact.status == before
    finally:
        db.close()


def test_m3_legacy_handle_reply_does_not_bypass(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    src = inspect.getsource(agents_mod.sales_handle_reply)
    assert "require_tenant_context" in src
    assert "execute_revenue_workflow" not in src
    r = client.post(f"/api/v1/agents/sales/{_CONTACT_B}/handle-reply", json={})
    assert r.status_code == 200
    assert r.json().get("ok") is False


def test_m3_cross_tenant_assessment_blocked(client: TestClient, tenant_db: sessionmaker) -> None:
    ids = _seed(tenant_db)
    upsert_n8n_binding(ids["org_a"], _SECRET_A)
    _post_reply(
        client, str(_CONTACT_A), body="hi", message_id="vis-1", analysis=_analysis()
    )
    _login(client, "owner-b@example.com", "pass-b", ids["org_b"])
    r = client.get(f"/api/v1/revenue/contacts/{_CONTACT_A}/reply/latest-assessment")
    assert r.status_code == 422


def test_m3_webhook_does_not_call_orchestrator_directly() -> None:
    src = inspect.getsource(n8n_mod.receive_n8n_event)
    assert "execute_revenue_workflow" not in src
    assert "decide(" not in src
    assert "wake_inbound_reply_handling" in src


def test_m3_n8n_not_approver() -> None:
    src = inspect.getsource(n8n_mod.receive_n8n_event)
    assert "apply_contact_status_update" not in src
    assert "accept_qualified_demand" not in src


def test_m3_routing_not_interested_and_objection() -> None:
    declined = route_reply_assessment(
        {"ok": True, "reply_type": "NOT_INTERESTED", "confidence": 0.9}
    )
    assert declined["recommended_next_action"] == "DISQUALIFY"
    assert declined["suggested_contact_status"] == "churned"
    assert declined["contact_status_changed"] is False
    paused = route_reply_assessment({"ok": True, "reply_type": "NOT_NOW", "confidence": 0.8})
    assert paused["recommended_next_action"] == "PAUSE"
    obj = route_reply_assessment(
        {"ok": True, "reply_type": "OBJECTION", "confidence": 0.8, "objection_category": "PRICE"}
    )
    assert obj["recommended_next_action"] == "HANDLE_OBJECTION"
    assert obj["objection_category"] == "PRICE"
    assert obj["deal_stage_changed"] is False
