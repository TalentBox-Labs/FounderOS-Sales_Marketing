"""REV-ORCH M1 — research-to-approved-outreach vertical slice tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import revenue_os.models  # noqa: F401
import runner_api_routers.identity as identity_mod
import runner_api_routers.revenue_orchestration as rev_orch_mod
from revenue_os.auth import hash_password
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
_OPERATOR = "Krishna Founder"


@pytest.fixture(autouse=True)
def _reset_identity() -> None:
    identity_mod._revoked_jtis.clear()
    identity_mod._login_failures.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def tenant_db(monkeypatch: pytest.MonkeyPatch, tmp_path) -> sessionmaker:
    engine = create_engine(f"sqlite:///{tmp_path / 'm1_rev_orch.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    for mod in (identity_mod, rev_orch_mod):
        monkeypatch.setattr(mod, "SessionLocal", sf)
    import revenue_os.services.tenant_resolution as tr
    import revenue_os.services.approvals as approvals_mod
    import revenue_os.services.activity_log as al

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


def _run_workflow(client: TestClient, contact_id: str) -> dict:
    qual = {
        "score": 72,
        "old_score": 0,
        "suggested_status": "qualified",
        "status": "lead",
        "status_changed": False,
    }
    with (
        patch("revenue_os.services.ai_service.generate_cold_email", return_value="Hi Alice, draft body."),
        patch(
            "revenue_os.services.revenue_orchestration_service.score_contact",
            return_value=qual,
        ),
    ):
        r = client.post(f"/api/v1/revenue/contacts/{contact_id}/research-to-outreach", json={})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["state"] == "APPROVAL_PENDING"
    assert body["approval_id"]
    return body


def test_m1_happy_path_to_approval_pending(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])

    body = _run_workflow(client, str(_CONTACT_A))
    assert body["qualification"]["status_changed"] is False
    assert "approval_id" in body

    db = tenant_db()
    try:
        approval = db.get(ApprovalRequest, body["approval_id"])
        assert approval is not None
        assert approval.status == "pending"
        assert approval.payload["organization_id"] == ids["org_a"]
        logs = db.query(AgentActionLog).filter(AgentActionLog.organization_id == _ORG_A).all()
        assert len(logs) >= 2
    finally:
        db.close()


def test_m1_approval_required_before_outbound(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = _run_workflow(client, str(_CONTACT_A))

    with patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n:
        mock_n8n.assert_not_called()

    db = tenant_db()
    try:
        approval = db.get(ApprovalRequest, body["approval_id"])
        assert approval.status == "pending"
    finally:
        db.close()


def test_m1_approve_triggers_outbound_handoff(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = _run_workflow(client, str(_CONTACT_A))

    with patch("revenue_os.integrations.n8n.trigger_workflow", return_value={"sent": True}) as mock_n8n:
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        assert r.status_code == 200, r.text
        mock_n8n.assert_called_once()
        call_payload = mock_n8n.call_args[0][1]
        assert call_payload["email"] == "alice@example.com"
        assert "idempotency_key" in call_payload
        assert call_payload["context"]["body"] == "Hi Alice, draft body."


def test_m1_rejected_proposal_cannot_send(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = _run_workflow(client, str(_CONTACT_A))

    with patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n:
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/reject", json={})
        assert r.status_code == 200
        mock_n8n.assert_not_called()

    db = tenant_db()
    try:
        approval = db.get(ApprovalRequest, body["approval_id"])
        assert approval.status == "rejected"
    finally:
        db.close()


def test_m1_cross_tenant_contact_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])

    with patch("revenue_os.services.ai_service.generate_cold_email", return_value="x"):
        r = client.post(f"/api/v1/revenue/contacts/{_CONTACT_B}/research-to-outreach", json={})
    assert r.status_code == 422


def test_m1_cross_tenant_approval_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = _run_workflow(client, str(_CONTACT_A))

    _login(client, "owner-b@example.com", "pass-b", ids["org_b"])
    with patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n:
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        assert r.status_code == 404
        mock_n8n.assert_not_called()


def test_m1_client_org_spoof_does_not_override_tenant(
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
        r = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/research-to-outreach",
            json={"organization_id": str(_ORG_B)},
        )
    assert r.status_code == 200
    assert r.json()["organization_id"] == ids["org_a"]


def test_m1_agent_cannot_approve(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = _run_workflow(client, str(_CONTACT_A))

    # Without session tenant, client-supplied agent identity must not approve.
    client.cookies.clear()
    with patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n:
        r = client.post(
            f"/api/v1/approvals/{body['approval_id']}/approve",
            json={"decided_by": "agent:hermes"},
        )
        assert r.status_code == 403
        mock_n8n.assert_not_called()


def test_m1_double_approve_idempotent_on_n8n(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = _run_workflow(client, str(_CONTACT_A))

    with patch("revenue_os.integrations.n8n.trigger_workflow", return_value={"sent": True}) as mock_n8n:
        r1 = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        assert r1.status_code == 200
        r2 = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        assert r2.status_code == 409
        assert mock_n8n.call_count == 1


def test_m1_legacy_crewai_route_not_mounted(client: TestClient) -> None:
    r = client.post("/api/v1/agents/score-lead", json={"company_name": "Acme"})
    assert r.status_code in {404, 405, 422}
