"""REV-ORCH M1.5 — research-to-approved-outreach baseline freeze tests."""

from __future__ import annotations

import inspect
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

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
from revenue_os.services import ai_service
from revenue_os.services import revenue_workers
from revenue_os.services.approvals import _human_decider, decide
from revenue_os.services.mutation_authority import HumanAuthorityError
from revenue_os.services.tenant_resolution import ORGANIZATION_COOKIE
from runner_api import app

M1_5_PARENT_HEAD = "d36d7a2"

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_OPERATOR = "Krishna Founder"

M1_5_REQUIRED_ARTIFACTS = (
    "REV_ORCH_M1_5_RESEARCH_TO_APPROVED_OUTREACH_BASELINE_v1.0.md",
    "REV_ORCH_M1_5_AUTHORITY_MATRIX_v1.0.md",
    "REV_ORCH_M1_5_TENANT_IDENTITY_APPROVAL_ATTESTATION_v1.0.md",
    "REV_ORCH_M1_5_OUTBOUND_IDEMPOTENCY_ATTESTATION_v1.0.md",
    "REV_ORCH_M1_5_LEGACY_PATH_RECONCILIATION_v1.0.md",
    "REV_ORCH_M1_5_REGRESSION_RECONCILIATION_v1.0.md",
    "REV_ORCH_M1_5_BASELINE_MANIFEST.md",
)


@pytest.fixture(autouse=True)
def _reset_orchestrator() -> None:
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
    engine = create_engine(f"sqlite:///{tmp_path / 'm1_5_freeze.db'}")
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


def _login(client: TestClient, org_id: str) -> None:
    r = client.post("/api/v1/identity/login", json={"email": "owner-a@example.com", "password": "pass-o"})
    assert r.status_code == 200
    client.cookies.set(ORGANIZATION_COOKIE, org_id)


def _qual_patch():
    return {
        "score": 72,
        "old_score": 0,
        "suggested_status": "qualified",
        "status": "lead",
        "status_changed": False,
    }


def _run_m1(client: TestClient, contact_id: str | uuid.UUID = _CONTACT_A) -> dict:
    with (
        patch("revenue_os.services.ai_service.generate_cold_email", return_value="Hi Alice, draft."),
        patch("revenue_os.services.revenue_orchestration_service.score_contact", return_value=_qual_patch()),
    ):
        r = client.post(f"/api/v1/revenue/contacts/{contact_id}/research-to-outreach", json={})
    assert r.status_code == 200, r.text
    return r.json()


# ── Artifact presence ─────────────────────────────────────────────────────────


def test_m1_5_freeze_artifacts_present() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "docs" / "revenue" / "orchestration" / "m1_5"
    missing = [name for name in M1_5_REQUIRED_ARTIFACTS if not (root / name).exists()]
    assert missing == [], f"Missing M1.5 artifacts: {missing}"


# ── A–D: orchestration + tenant/identity through dispatch ─────────────────────


def test_m1_5_canonical_route_dispatches_workflow_orchestrator(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    ids = _seed(tenant_db)
    _login(client, ids["org_a"])
    with (
        patch("revenue_os.services.ai_service.generate_cold_email", return_value="draft"),
        patch("revenue_os.services.revenue_orchestration_service.score_contact", return_value=_qual_patch()),
        patch.object(WorkflowOrchestrator, "execute_revenue_workflow", wraps=WorkflowOrchestrator.execute_revenue_workflow) as mock_exec,
    ):
        r = client.post(f"/api/v1/revenue/contacts/{_CONTACT_A}/research-to-outreach", json={})
    assert r.status_code == 200
    mock_exec.assert_called_once()
    body = r.json()
    assert body["orchestrator"] == "WorkflowOrchestrator"
    assert REV_ORCH_M1_WORKFLOW_KEY in [w.name for w in WorkflowOrchestrator.list_workflows()] or mock_exec.call_args[0][0] == REV_ORCH_M1_WORKFLOW_KEY


def test_m1_5_registered_workflow_uses_subordinate_implementation() -> None:
    WorkflowOrchestrator.seed_revenue_workflows()
    wf = next(w for w in WorkflowOrchestrator.list_workflows() if w.name == REV_ORCH_M1_WORKFLOW_KEY)
    assert wf.agents == [REV_ORCH_M1_AGENT_STEP]
    handler_src = inspect.getsource(WorkflowOrchestrator._handle_m1_research_to_outreach)
    assert "run_research_to_outreach" in handler_src


def test_m1_5_tenant_context_preserved_through_dispatch(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    ids = _seed(tenant_db)
    _login(client, ids["org_a"])
    body = _run_m1(client)
    assert body["organization_id"] == ids["org_a"]


# ── E–G: tenant isolation + spoof ───────────────────────────────────────────


def test_m1_5_cross_tenant_contact_blocked(client: TestClient, tenant_db: sessionmaker) -> None:
    ids = _seed(tenant_db)
    _login(client, ids["org_a"])
    with patch("revenue_os.services.ai_service.generate_cold_email", return_value="x"):
        r = client.post(f"/api/v1/revenue/contacts/{_CONTACT_B}/research-to-outreach", json={})
    assert r.status_code == 422


def test_m1_5_cross_tenant_approval_blocked(client: TestClient, tenant_db: sessionmaker) -> None:
    ids = _seed(tenant_db)
    _login(client, ids["org_a"])
    body = _run_m1(client)
    client.cookies.set(ORGANIZATION_COOKIE, ids["org_b"])
    with patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n:
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        assert r.status_code in {403, 404}
        mock_n8n.assert_not_called()


def test_m1_5_client_org_spoof_ignored(client: TestClient, tenant_db: sessionmaker) -> None:
    ids = _seed(tenant_db)
    _login(client, ids["org_a"])
    with (
        patch("revenue_os.services.ai_service.generate_cold_email", return_value="draft"),
        patch("revenue_os.services.revenue_orchestration_service.score_contact", return_value=_qual_patch()),
    ):
        r = client.post(
            f"/api/v1/revenue/contacts/{_CONTACT_A}/research-to-outreach",
            json={"organization_id": ids["org_b"]},
        )
    assert r.status_code == 200
    assert r.json()["organization_id"] == ids["org_a"]


# ── H: human identity spoof ───────────────────────────────────────────────────


def test_m1_5_client_decided_by_spoof_blocked(client: TestClient, tenant_db: sessionmaker) -> None:
    ids = _seed(tenant_db)
    _login(client, ids["org_a"])
    body = _run_m1(client)
    client.cookies.clear()
    with patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n:
        r = client.post(
            f"/api/v1/approvals/{body['approval_id']}/approve",
            json={"decided_by": _OPERATOR},
        )
        assert r.status_code == 403
        mock_n8n.assert_not_called()


def test_m1_5_decide_service_rejects_no_tenant() -> None:
    with pytest.raises(HumanAuthorityError, match="Session tenant context required"):
        _human_decider(None, "Krishna Founder")


# ── I–K: AI authority ─────────────────────────────────────────────────────────


def test_m1_5_ai_service_has_no_outbound_or_crm_mutators() -> None:
    public = {n for n, o in inspect.getmembers(ai_service, inspect.isfunction) if not n.startswith("_")}
    prohibited = {
        "update_contact",
        "create_deal",
        "apply_deal_stage",
        "accept_qualified_demand",
        "trigger_workflow",
        "request_approval",
    }
    assert public.isdisjoint(prohibited)


def test_m1_5_personalization_worker_does_not_send_or_approve() -> None:
    src = inspect.getsource(revenue_workers.run_personalization_worker)
    assert "request_approval" not in src
    assert "trigger_workflow" not in src
    assert "decide(" not in src


def test_m1_5_research_worker_does_not_send_or_approve() -> None:
    src = inspect.getsource(revenue_workers.run_research_worker)
    assert "trigger_workflow" not in src
    assert "request_approval" not in src


# ── L–P: approval + outbound ─────────────────────────────────────────────────


def test_m1_5_pending_cannot_send(client: TestClient, tenant_db: sessionmaker) -> None:
    ids = _seed(tenant_db)
    _login(client, ids["org_a"])
    body = _run_m1(client)
    with patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n:
        mock_n8n.assert_not_called()
    db = tenant_db()
    try:
        row = db.get(ApprovalRequest, body["approval_id"])
        assert row is not None and row.status == "pending"
    finally:
        db.close()


def test_m1_5_rejected_cannot_send(client: TestClient, tenant_db: sessionmaker) -> None:
    ids = _seed(tenant_db)
    _login(client, ids["org_a"])
    body = _run_m1(client)
    with patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n:
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/reject", json={})
        assert r.status_code == 200
        mock_n8n.assert_not_called()


def test_m1_5_approved_reaches_n8n_executor(client: TestClient, tenant_db: sessionmaker) -> None:
    ids = _seed(tenant_db)
    _login(client, ids["org_a"])
    body = _run_m1(client)
    with patch("revenue_os.integrations.n8n.trigger_workflow", return_value={"sent": True}) as mock_n8n:
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        assert r.status_code == 200
        mock_n8n.assert_called_once()
        assert mock_n8n.call_args[0][0] == "send-email"


def test_m1_5_outbound_idempotency_on_replay(client: TestClient, tenant_db: sessionmaker) -> None:
    ids = _seed(tenant_db)
    _login(client, ids["org_a"])
    body = _run_m1(client)
    with patch("revenue_os.integrations.n8n.trigger_workflow", return_value={"sent": True}) as mock_n8n:
        assert client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={}).status_code == 200
        r2 = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        assert r2.status_code == 409
        assert mock_n8n.call_count == 1


# ── Q–R: audit provenance ─────────────────────────────────────────────────────


def test_m1_5_agent_action_log_has_organization_id(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    ids = _seed(tenant_db)
    _login(client, ids["org_a"])
    _run_m1(client)
    db = tenant_db()
    try:
        logs = db.query(AgentActionLog).filter(AgentActionLog.organization_id == _ORG_A).all()
        assert len(logs) >= 2
        assert any("rev_orch" in (log.action_type or "") for log in logs)
    finally:
        db.close()


# ── S–T: legacy containment ───────────────────────────────────────────────────


def test_m1_5_legacy_sales_route_tenant_scoped(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    ids = _seed(tenant_db)
    _login(client, ids["org_a"])
    with patch("revenue_os.services.ai_service.generate_cold_email", return_value="x"):
        r = client.post(f"/api/v1/agents/sales/{_CONTACT_B}/cold-email", json={})
    assert r.status_code == 200
    assert r.json().get("ok") is False


def test_m1_5_legacy_sales_requires_tenant(client: TestClient) -> None:
    assert client.post(f"/api/v1/agents/sales/{_CONTACT_A}/cold-email", json={}).status_code == 403


# ── U: no parallel orchestrator on M1 path ────────────────────────────────────


def test_m1_5_no_parallel_orchestrator_on_canonical_route() -> None:
    src = inspect.getsource(rev_orch_mod.research_to_outreach)
    assert "WorkflowOrchestrator.execute_revenue_workflow" in src
    assert "run_research_to_outreach(" not in src.replace("RevenueOrchestrationError", "")


# ── V–W: qualification recommend-only ───────────────────────────────────────


def test_m1_5_qualification_recommend_only_in_response(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    ids = _seed(tenant_db)
    _login(client, ids["org_a"])
    body = _run_m1(client)
    assert body["qualification"]["status_changed"] is False
    db = tenant_db()
    try:
        contact = db.get(Contact, _CONTACT_A)
        assert contact is not None
        assert contact.status == ContactStatus.LEAD
    finally:
        db.close()


def test_m1_5_no_deal_mutation_in_orchestration_service() -> None:
    from revenue_os.services import revenue_orchestration_service as ros

    src = inspect.getsource(ros.run_research_to_outreach)
    assert "create_deal" not in src
    assert "apply_deal_stage" not in src
    assert "Deal(" not in src
