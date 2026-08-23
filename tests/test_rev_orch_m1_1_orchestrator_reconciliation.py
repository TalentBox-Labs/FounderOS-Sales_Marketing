"""REV-ORCH M1.1 — orchestrator wiring, legacy containment, authority reconciliation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import revenue_os.models  # noqa: F401
import runner_api_routers.agents as agents_mod
import runner_api_routers.identity as identity_mod
import runner_api_routers.revenue_orchestration as rev_orch_mod
from revenue_os.agents.orchestration import (
    REV_ORCH_M1_AGENT_STEP,
    REV_ORCH_M1_WORKFLOW_KEY,
    WorkflowOrchestrator,
)
from revenue_os.auth import hash_password
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
    WorkflowOrchestrator._workflows.clear()
    WorkflowOrchestrator._executions.clear()
    WorkflowOrchestrator._revenue_workflows_seeded = False


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def tenant_db(monkeypatch: pytest.MonkeyPatch, tmp_path) -> sessionmaker:
    engine = create_engine(f"sqlite:///{tmp_path / 'm1_1.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    for mod in (identity_mod, rev_orch_mod, agents_mod):
        monkeypatch.setattr(mod, "SessionLocal", sf)
    import revenue_os.database as db_mod
    import revenue_os.services.tenant_resolution as tr
    import revenue_os.services.approvals as approvals_mod
    import revenue_os.services.activity_log as al

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
        db.add_all([org_a, org_b, owner_a])
        db.flush()
        db.add(
            OrganizationMembership(
                user_id=owner_a.id,
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
                created_at=datetime.now(timezone.utc),
            )
        )
        db.add(
            Contact(
                id=_CONTACT_B,
                first_name="Bob",
                last_name="B",
                email="bob@example.com",
                status=ContactStatus.LEAD,
                source=ContactSource.MANUAL,
                organization_id=_ORG_B,
                created_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
        return {"org_a": str(_ORG_A)}
    finally:
        db.close()


def _login(client: TestClient, org_id: str) -> None:
    r = client.post("/api/v1/identity/login", json={"email": "owner-a@example.com", "password": "pass-o"})
    assert r.status_code == 200
    client.cookies.set(ORGANIZATION_COOKIE, org_id)


def test_m1_1_m1_route_uses_workflow_orchestrator(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    ids = _seed(tenant_db)
    _login(client, ids["org_a"])
    qual = {
        "score": 70,
        "old_score": 0,
        "suggested_status": "qualified",
        "status": "lead",
        "status_changed": False,
    }
    with (
        patch("revenue_os.services.ai_service.generate_cold_email", return_value="draft"),
        patch("revenue_os.services.revenue_orchestration_service.score_contact", return_value=qual),
        patch.object(WorkflowOrchestrator, "execute_revenue_workflow", wraps=WorkflowOrchestrator.execute_revenue_workflow) as mock_exec,
    ):
        r = client.post(f"/api/v1/revenue/contacts/{_CONTACT_A}/research-to-outreach", json={})
    assert r.status_code == 200, r.text
    mock_exec.assert_called_once()
    assert r.json()["orchestrator"] == "WorkflowOrchestrator"
    assert "workflow_execution_id" in r.json()


def test_m1_1_workflow_orchestrator_registers_m1_workflow() -> None:
    WorkflowOrchestrator.seed_revenue_workflows()
    names = [w.name for w in WorkflowOrchestrator.list_workflows()]
    assert REV_ORCH_M1_WORKFLOW_KEY in names
    wf = next(w for w in WorkflowOrchestrator.list_workflows() if w.name == REV_ORCH_M1_WORKFLOW_KEY)
    assert wf.agents == [REV_ORCH_M1_AGENT_STEP]


def test_m1_1_legacy_sales_route_blocks_cross_tenant(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    ids = _seed(tenant_db)
    _login(client, ids["org_a"])
    with patch("revenue_os.services.ai_service.generate_cold_email", return_value="x"):
        r = client.post(f"/api/v1/agents/sales/{_CONTACT_B}/cold-email", json={})
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is False or body.get("reason") == "Contact not found"


def test_m1_1_legacy_sales_route_requires_tenant(client: TestClient) -> None:
    r = client.post(f"/api/v1/agents/sales/{_CONTACT_A}/cold-email", json={})
    assert r.status_code == 403


def test_m1_1_approve_without_session_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    ids = _seed(tenant_db)
    _login(client, ids["org_a"])
    qual = {
        "score": 70,
        "old_score": 0,
        "suggested_status": "qualified",
        "status": "lead",
        "status_changed": False,
    }
    with (
        patch("revenue_os.services.ai_service.generate_cold_email", return_value="draft"),
        patch("revenue_os.services.revenue_orchestration_service.score_contact", return_value=qual),
    ):
        body = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/research-to-outreach", json={}
        ).json()
    client.cookies.clear()
    with patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n:
        r = client.post(
            f"/api/v1/approvals/{body['approval_id']}/approve",
            json={"decided_by": "Krishna Founder"},
        )
        assert r.status_code == 403
        mock_n8n.assert_not_called()
