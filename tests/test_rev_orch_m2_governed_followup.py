"""REV-ORCH M2 — governed follow-up lifecycle tests."""

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
from revenue_os.agents.orchestration import (
    REV_ORCH_M2_WORKFLOW_KEY,
    WorkflowOrchestrator,
)
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
from revenue_os.services.revenue_orchestration_service import run_follow_up_proposal_scheduled
from revenue_os.services.revenue_workers import WORKER_FOLLOWUP, run_followup_worker
from revenue_os.services.tenant_resolution import ORGANIZATION_COOKIE
from runner_api import app

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_OPERATOR = "Krishna Founder"


@pytest.fixture(autouse=True)
def _reset_state() -> None:
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
    engine = create_engine(f"sqlite:///{tmp_path / 'm2_rev_orch.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    for mod in (identity_mod, rev_orch_mod):
        monkeypatch.setattr(mod, "SessionLocal", sf)
    import revenue_os.database as db_mod
    import revenue_os.services.tenant_resolution as tr
    import revenue_os.services.approvals as approvals_mod
    import revenue_os.services.activity_log as al
    import revenue_os.scheduler as sched_mod

    monkeypatch.setattr(db_mod, "SessionLocal", sf)
    monkeypatch.setattr(tr, "SessionLocal", sf)
    monkeypatch.setattr(approvals_mod, "SessionLocal", sf)
    monkeypatch.setattr(al, "SessionLocal", sf)
    monkeypatch.setattr(sched_mod, "SessionLocal", sf)
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


def _seed_outbound(
    db_factory: sessionmaker,
    contact_id: uuid.UUID,
    *,
    days_ago: int = 5,
) -> Activity:
    db = db_factory()
    try:
        sent_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
        act = Activity(
            contact_id=contact_id,
            activity_type=ActivityType.EMAIL,
            subject="Outbound: intro",
            body="Initial outreach body",
            direction="outbound",
            status="completed",
            performed_at=sent_at,
            created_at=sent_at,
        )
        db.add(act)
        db.commit()
        db.refresh(act)
        return act
    finally:
        db.close()


def _seed_reply(db_factory: sessionmaker, contact_id: uuid.UUID) -> None:
    db = db_factory()
    try:
        now = datetime.now(timezone.utc)
        db.add(
            Activity(
                contact_id=contact_id,
                activity_type=ActivityType.EMAIL_REPLY,
                subject="Reply",
                body="Thanks for reaching out",
                direction="inbound",
                status="completed",
                performed_at=now,
                created_at=now,
            )
        )
        db.commit()
    finally:
        db.close()


def _propose_follow_up(client: TestClient, contact_id: str) -> dict:
    with patch(
        "revenue_os.services.ai_service.generate_follow_up_email",
        return_value={
            "subject": "Re: follow up",
            "body": "Hi Alice, following up.",
            "rationale": "Bounded follow-up",
        },
    ):
        r = client.post(f"/api/v1/revenue/contacts/{contact_id}/follow-up/propose", json={})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["state"] == "FOLLOWUP_PROPOSED"
    return body


def test_m2_eligibility_requires_initial_outbound(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])

    r = client.get(f"/api/v1/revenue/contacts/{_CONTACT_A}/follow-up/eligibility")
    assert r.status_code == 200
    assert r.json()["eligible"] is False
    assert r.json()["state"] == "FOLLOWUP_NOT_DUE"


def test_m2_happy_path_proposal(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])

    body = _propose_follow_up(client, str(_CONTACT_A))
    assert body["proposal"]["cadence_step"] == 1
    assert body["approval_id"]

    db = tenant_db()
    try:
        approval = db.get(ApprovalRequest, body["approval_id"])
        assert approval is not None
        assert approval.status == "pending"
        assert approval.payload["workflow_kind"] == "rev_orch_m2_follow_up"
        assert approval.requested_by == WORKER_FOLLOWUP
    finally:
        db.close()


def test_m2_reply_before_proposal_blocks(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _seed_reply(tenant_db, _CONTACT_A)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])

    r = client.post(f"/api/v1/revenue/contacts/{_CONTACT_A}/follow-up/propose", json={})
    assert r.status_code == 422

    r2 = client.get(f"/api/v1/revenue/contacts/{_CONTACT_A}/follow-up/eligibility")
    assert r2.json()["state"] == "FOLLOWUP_REPLY_RECEIVED"


def test_m2_reply_after_approval_blocks_send(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    outbound = _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = _propose_follow_up(client, str(_CONTACT_A))
    _seed_reply(tenant_db, _CONTACT_A)

    with patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n:
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        assert r.status_code == 200
        mock_n8n.assert_not_called()
        assert r.json()["request"]["execution_result"]["executed"] is False


def test_m2_pending_cannot_send(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = _propose_follow_up(client, str(_CONTACT_A))

    with patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n:
        # No approve call — pending must not trigger n8n
        assert mock_n8n.call_count == 0

    db = tenant_db()
    try:
        approval = db.get(ApprovalRequest, body["approval_id"])
        assert approval.status == "pending"
    finally:
        db.close()


def test_m2_rejected_cannot_send(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = _propose_follow_up(client, str(_CONTACT_A))

    with patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n:
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/reject", json={})
        assert r.status_code == 200
        mock_n8n.assert_not_called()


def test_m2_approved_send_pass(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = _propose_follow_up(client, str(_CONTACT_A))

    with patch("revenue_os.integrations.n8n.trigger_workflow", return_value={"sent": True}) as mock_n8n:
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        assert r.status_code == 200
        mock_n8n.assert_called_once()
        assert "rev-orch-m2:" in mock_n8n.call_args[0][1]["idempotency_key"]


def test_m2_cross_tenant_propose_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_B, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])

    r = client.post(f"/api/v1/revenue/contacts/{_CONTACT_B}/follow-up/propose", json={})
    assert r.status_code == 422


def test_m2_cross_tenant_eligibility_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_B, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])

    r = client.get(f"/api/v1/revenue/contacts/{_CONTACT_B}/follow-up/eligibility")
    assert r.status_code == 422


def test_m2_cross_tenant_approval_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = _propose_follow_up(client, str(_CONTACT_A))

    _login(client, "owner-b@example.com", "pass-b", ids["org_b"])
    with patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n:
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        assert r.status_code == 404
        mock_n8n.assert_not_called()


def test_m2_client_org_spoof_ignored(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])

    with patch(
        "revenue_os.services.ai_service.generate_follow_up_email",
        return_value={"subject": "Re", "body": "body", "rationale": "r"},
    ):
        r = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/follow-up/propose",
            json={"organization_id": str(_ORG_B)},
        )
    assert r.status_code == 200
    assert r.json()["organization_id"] == ids["org_a"]


def test_m2_agent_cannot_approve(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", str(_ORG_A))
    body = _propose_follow_up(client, str(_CONTACT_A))

    client.cookies.clear()
    with patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n:
        r = client.post(
            f"/api/v1/approvals/{body['approval_id']}/approve",
            json={"decided_by": "agent:hermes"},
        )
        assert r.status_code == 403
        mock_n8n.assert_not_called()


def test_m2_worker_cannot_mutate_contact_status(
    tenant_db: sessionmaker,
) -> None:
    _seed(tenant_db)
    db = tenant_db()
    try:
        contact = db.get(Contact, _CONTACT_A)
        assert contact is not None
        before = contact.status
        run_followup_worker(
            db,
            contact,
            str(_ORG_A),
            cadence_step=1,
            source_activity_id=str(uuid.uuid4()),
            eligibility={"state": "FOLLOWUP_ELIGIBLE", "recommended_send_after": "now"},
        )
        db.refresh(contact)
        assert contact.status == before
    finally:
        db.close()


def test_m2_duplicate_proposal_collapsed(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])

    with patch(
        "revenue_os.services.ai_service.generate_follow_up_email",
        return_value={"subject": "Re", "body": "body", "rationale": "r"},
    ):
        r1 = client.post(f"/api/v1/revenue/contacts/{_CONTACT_A}/follow-up/propose", json={})
        r2 = client.post(f"/api/v1/revenue/contacts/{_CONTACT_A}/follow-up/propose", json={})
    assert r1.status_code == 200
    assert r2.status_code == 422


def test_m2_double_approve_idempotent(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = _propose_follow_up(client, str(_CONTACT_A))

    with patch("revenue_os.integrations.n8n.trigger_workflow", return_value={"sent": True}) as mock_n8n:
        r1 = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        assert r1.status_code == 200
        r2 = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        assert r2.status_code == 409
        assert mock_n8n.call_count == 1


def test_m2_scheduler_reconstructs_tenant_from_contact(
    tenant_db: sessionmaker,
) -> None:
    _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)

    with patch(
        "revenue_os.services.ai_service.generate_follow_up_email",
        return_value={"subject": "Re", "body": "body", "rationale": "r"},
    ):
        db = tenant_db()
        try:
            result = run_follow_up_proposal_scheduled(db, str(_ORG_A), str(_CONTACT_A))
        finally:
            db.close()
    assert result["ok"] is True
    assert result["organization_id"] == str(_ORG_A)


def test_m2_scheduler_rejects_org_mismatch(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    db = tenant_db()
    try:
        result = run_follow_up_proposal_scheduled(db, str(_ORG_B), str(_CONTACT_A))
    finally:
        db.close()
    assert result["ok"] is False


def test_m2_stop_tag_blocks(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    db = tenant_db()
    try:
        contact = db.get(Contact, _CONTACT_A)
        assert contact is not None
        contact.tags = "do-not-contact"
        db.commit()
    finally:
        db.close()
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])

    r = client.get(f"/api/v1/revenue/contacts/{_CONTACT_A}/follow-up/eligibility")
    assert r.json()["state"] == "FOLLOWUP_STOPPED"


def test_m2_orchestrator_workflow_registered() -> None:
    WorkflowOrchestrator.seed_revenue_workflows()
    names = [w.name for w in WorkflowOrchestrator.list_workflows()]
    assert REV_ORCH_M2_WORKFLOW_KEY in names


def test_m2_audit_provenance(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    _propose_follow_up(client, str(_CONTACT_A))

    db = tenant_db()
    try:
        logs = (
            db.query(AgentActionLog)
            .filter(AgentActionLog.organization_id == _ORG_A)
            .all()
        )
        types = {log.action_type for log in logs}
        assert "rev_orch_followup_eligibility" in types
        assert "worker_followup_proposal" in types
    finally:
        db.close()


def test_m2_m1_route_unchanged(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    with (
        patch("revenue_os.services.ai_service.generate_cold_email", return_value="draft"),
        patch(
            "revenue_os.services.revenue_orchestration_service.score_contact",
            return_value={
                "score": 70,
                "old_score": 0,
                "suggested_status": "qualified",
                "status": "lead",
                "status_changed": False,
            },
        ),
    ):
        r = client.post(f"/api/v1/revenue/contacts/{_CONTACT_A}/research-to-outreach", json={})
    assert r.status_code == 200
    assert r.json()["state"] == "APPROVAL_PENDING"
