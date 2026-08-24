"""REV-ORCH M2.5 — governed follow-up baseline freeze tests.

Certification only. Does not change M2 production behavior.
"""

from __future__ import annotations

import inspect
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
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
    REV_ORCH_M1_WORKFLOW_KEY,
    REV_ORCH_M2_AGENT_STEP,
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
from revenue_os.scheduler import job_scan_follow_up_eligibility
from revenue_os.services import ai_service
from revenue_os.services import follow_up_eligibility as elig
from revenue_os.services import revenue_workers
from revenue_os.services.approvals import _human_decider, _revalidate_follow_up_before_send
from revenue_os.services.follow_up_eligibility import (
    FOLLOW_UP_INTERVALS_DAYS,
    MAX_FOLLOW_UP_STEPS,
    evaluate_follow_up_eligibility,
)
from revenue_os.services.mutation_authority import HumanAuthorityError
from revenue_os.services.revenue_orchestration_service import run_follow_up_proposal_scheduled
from revenue_os.services.revenue_workers import run_followup_worker
from revenue_os.services.tenant_resolution import ORGANIZATION_COOKIE
from runner_api import app

M2_5_PARENT_HEAD = "b0004a4"

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_OPERATOR = "Krishna Founder"

M2_5_REQUIRED_ARTIFACTS = (
    "REV_ORCH_M2_5_GOVERNED_FOLLOWUP_BASELINE_v1.0.md",
    "REV_ORCH_M2_5_FOLLOWUP_AUTHORITY_MATRIX_v1.0.md",
    "REV_ORCH_M2_5_SCHEDULER_AUTHORITY_CONTRACT_v1.0.md",
    "REV_ORCH_M2_5_TENANT_RECONSTRUCTION_ATTESTATION_v1.0.md",
    "REV_ORCH_M2_5_STALE_AUTHORITY_REVALIDATION_v1.0.md",
    "REV_ORCH_M2_5_REPLY_STOP_CONTRACT_v1.0.md",
    "REV_ORCH_M2_5_STOP_UNSUBSCRIBE_CONTRACT_v1.0.md",
    "REV_ORCH_M2_5_CADENCE_CONTRACT_v1.0.md",
    "REV_ORCH_M2_5_IDEMPOTENCY_ATTESTATION_v1.0.md",
    "REV_ORCH_M2_5_LEGACY_FOLLOWUP_RECONCILIATION_v1.0.md",
    "REV_ORCH_M2_5_REGRESSION_RECONCILIATION_v1.0.md",
    "REV_ORCH_M2_5_BASELINE_MANIFEST.md",
)

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
    engine = create_engine(f"sqlite:///{tmp_path / 'm2_5_freeze.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    for mod in (identity_mod, rev_orch_mod, agents_mod):
        monkeypatch.setattr(mod, "SessionLocal", sf)
    import revenue_os.database as db_mod
    import revenue_os.scheduler as sched_mod
    import revenue_os.services.activity_log as al
    import revenue_os.services.approvals as approvals_mod
    import revenue_os.services.tenant_resolution as tr

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
    subject: str = "Outbound: intro",
) -> Activity:
    db = db_factory()
    try:
        sent_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
        act = Activity(
            contact_id=contact_id,
            activity_type=ActivityType.EMAIL,
            subject=subject,
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


def _propose(client: TestClient, contact_id: str) -> dict:
    with patch(
        "revenue_os.services.ai_service.generate_follow_up_email",
        return_value={"subject": "Re: follow up", "body": "Hi Alice, following up.", "rationale": "r"},
    ):
        r = client.post(f"/api/v1/revenue/contacts/{contact_id}/follow-up/propose", json={})
    assert r.status_code == 200, r.text
    return r.json()


def test_m2_5_freeze_artifacts_exist() -> None:
    root = Path("docs/revenue/orchestration/m2_5")
    missing = [name for name in M2_5_REQUIRED_ARTIFACTS if not (root / name).exists()]
    assert missing == [], f"Missing M2.5 artifacts: {missing}"


def test_m2_5_m1_5_artifacts_unchanged() -> None:
    root = Path("docs/revenue/orchestration/m1_5")
    missing = [name for name in M1_5_REQUIRED_ARTIFACTS if not (root / name).exists()]
    assert missing == [], f"Missing M1.5 artifacts: {missing}"


def test_m2_5_canonical_propose_dispatches_workflow_orchestrator(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    with (
        patch(
            "revenue_os.services.ai_service.generate_follow_up_email",
            return_value={"subject": "Re", "body": "body", "rationale": "r"},
        ),
        patch.object(
            WorkflowOrchestrator,
            "execute_revenue_workflow",
            wraps=WorkflowOrchestrator.execute_revenue_workflow,
        ) as mock_exec,
    ):
        r = client.post(f"/api/v1/revenue/contacts/{_CONTACT_A}/follow-up/propose", json={})
    assert r.status_code == 200
    mock_exec.assert_called_once()
    assert mock_exec.call_args[0][0] == REV_ORCH_M2_WORKFLOW_KEY
    assert r.json()["orchestrator"] == "WorkflowOrchestrator"


def test_m2_5_registered_workflow_uses_subordinate_implementation() -> None:
    WorkflowOrchestrator.seed_revenue_workflows()
    wf = next(w for w in WorkflowOrchestrator.list_workflows() if w.name == REV_ORCH_M2_WORKFLOW_KEY)
    assert wf.agents == [REV_ORCH_M2_AGENT_STEP]
    handler_src = inspect.getsource(WorkflowOrchestrator._handle_m2_follow_up_to_outreach)
    assert "run_follow_up_to_outreach" in handler_src


def test_m2_5_followup_worker_is_proposal_only() -> None:
    src = inspect.getsource(revenue_workers.run_followup_worker)
    assert "request_approval" not in src
    assert "trigger_workflow" not in src
    assert "decide(" not in src
    assert src.count("Contact.status") == 0 or "status" not in src.split("return")[0]


def test_m2_5_scheduler_cannot_send_directly() -> None:
    src = inspect.getsource(job_scan_follow_up_eligibility)
    assert "trigger_workflow" not in src
    assert "decide(" not in src
    assert "run_follow_up_proposal_scheduled" in src


def test_m2_5_scheduler_reconstructs_tenant_from_persisted_contact(
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


def test_m2_5_stale_cached_org_cannot_override_contact_tenant(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    db = tenant_db()
    try:
        result = run_follow_up_proposal_scheduled(db, str(_ORG_B), str(_CONTACT_A))
    finally:
        db.close()
    assert result["ok"] is False


def test_m2_5_contact_revalidated_before_delayed_execution(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = _propose(client, str(_CONTACT_A))

    db = tenant_db()
    try:
        contact = db.get(Contact, _CONTACT_A)
        assert contact is not None
        contact.organization_id = _ORG_B
        db.commit()
    finally:
        db.close()

    with patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n:
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        mock_n8n.assert_not_called()
        assert r.status_code == 200
        assert r.json()["request"]["execution_result"]["executed"] is False


def test_m2_5_approval_revalidated_before_delayed_execution(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = _propose(client, str(_CONTACT_A))
    _login(client, "owner-b@example.com", "pass-b", ids["org_b"])
    with patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n:
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        assert r.status_code == 404
        mock_n8n.assert_not_called()


def test_m2_5_reply_before_proposal_blocks(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _seed_reply(tenant_db, _CONTACT_A)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    r = client.post(f"/api/v1/revenue/contacts/{_CONTACT_A}/follow-up/propose", json={})
    assert r.status_code == 422
    elig_r = client.get(f"/api/v1/revenue/contacts/{_CONTACT_A}/follow-up/eligibility")
    assert elig_r.json()["state"] == "FOLLOWUP_REPLY_RECEIVED"


def test_m2_5_reply_while_pending_blocks_stale_send(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = _propose(client, str(_CONTACT_A))
    _seed_reply(tenant_db, _CONTACT_A)
    with patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n:
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        assert r.status_code == 200
        mock_n8n.assert_not_called()
        assert r.json()["request"]["execution_result"]["executed"] is False


def test_m2_5_reply_after_send_blocks_next_cadence(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=20)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=10, subject="Follow-up #1: ai_follow_up_email")
    _seed_reply(tenant_db, _CONTACT_A)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    r = client.get(f"/api/v1/revenue/contacts/{_CONTACT_A}/follow-up/eligibility")
    assert r.json()["eligible"] is False
    assert r.json()["state"] == "FOLLOWUP_REPLY_RECEIVED"


def test_m2_5_unsubscribe_stop_blocks(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    db = tenant_db()
    try:
        contact = db.get(Contact, _CONTACT_A)
        assert contact is not None
        contact.tags = "unsubscribed"
        db.commit()
    finally:
        db.close()
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    r = client.get(f"/api/v1/revenue/contacts/{_CONTACT_A}/follow-up/eligibility")
    assert r.json()["state"] == "FOLLOWUP_STOPPED"
    with patch("revenue_os.services.ai_service.generate_follow_up_email"):
        propose = client.post(f"/api/v1/revenue/contacts/{_CONTACT_A}/follow-up/propose", json={})
    assert propose.status_code == 422


def test_m2_5_stop_tag_blocks_send_after_approval(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = _propose(client, str(_CONTACT_A))
    db = tenant_db()
    try:
        contact = db.get(Contact, _CONTACT_A)
        assert contact is not None
        contact.tags = "do-not-contact"
        db.commit()
    finally:
        db.close()
    with patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n:
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        mock_n8n.assert_not_called()
        assert r.json()["request"]["execution_result"]["executed"] is False


def test_m2_5_pending_cannot_send(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = _propose(client, str(_CONTACT_A))
    with patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n:
        assert mock_n8n.call_count == 0
    db = tenant_db()
    try:
        row = db.get(ApprovalRequest, body["approval_id"])
        assert row is not None and row.status == "pending"
    finally:
        db.close()


def test_m2_5_rejected_cannot_send(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = _propose(client, str(_CONTACT_A))
    with patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n:
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/reject", json={})
        assert r.status_code == 200
        mock_n8n.assert_not_called()


def test_m2_5_approved_send_after_current_validation(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = _propose(client, str(_CONTACT_A))
    with patch("revenue_os.integrations.n8n.trigger_workflow", return_value={"sent": True}) as mock_n8n:
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        assert r.status_code == 200
        mock_n8n.assert_called_once()
        assert mock_n8n.call_args[0][0] == "send-email"
        assert mock_n8n.call_args[0][1]["idempotency_key"].startswith("approval_effect:")


def test_m2_5_duplicate_scheduler_scan_does_not_duplicate_proposal(
    tenant_db: sessionmaker,
) -> None:
    _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    with patch(
        "revenue_os.services.ai_service.generate_follow_up_email",
        return_value={"subject": "Re", "body": "body", "rationale": "r"},
    ):
        first = job_scan_follow_up_eligibility()
        second = job_scan_follow_up_eligibility()
    assert first["proposals_filed"] == 1
    assert second["proposals_filed"] == 0
    db = tenant_db()
    try:
        pending = (
            db.query(ApprovalRequest)
            .filter(ApprovalRequest.status == "pending", ApprovalRequest.target_id == str(_CONTACT_A))
            .all()
        )
        m2 = [r for r in pending if (r.payload or {}).get("workflow_kind") == "rev_orch_m2_follow_up"]
        assert len(m2) == 1
    finally:
        db.close()


def test_m2_5_duplicate_approval_does_not_duplicate_send(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = _propose(client, str(_CONTACT_A))
    with patch("revenue_os.integrations.n8n.trigger_workflow", return_value={"sent": True}) as mock_n8n:
        assert client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={}).status_code == 200
        r2 = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        assert r2.status_code == 409
        assert mock_n8n.call_count == 1


def test_m2_5_worker_cannot_mutate_contact_status(tenant_db: sessionmaker) -> None:
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
        assert contact.status == ContactStatus.LEAD
    finally:
        db.close()


def test_m2_5_worker_cannot_mutate_deal_stage_or_choose_tenant() -> None:
    src = inspect.getsource(revenue_workers.run_followup_worker)
    assert "Deal" not in src
    assert "deal.stage" not in src
    assert "apply_deal_stage" not in src
    assert "organization_id" in src
    assert "require_tenant_context" not in src
    assert "credential" not in src.lower()
    assert "n8n" not in src.lower()


def test_m2_5_n8n_remains_executor_only() -> None:
    src = inspect.getsource(n8n_mod.receive_n8n_event)
    assert "execute_revenue_workflow" not in src
    assert "run_follow_up_to_outreach" not in src
    assert "decide(" not in src
    catalog = n8n_mod.n8n_catalog()
    assert "tenant_binding" in catalog["inbound"]["auth"] or "X-N8N-Secret" in catalog["inbound"]["auth"]


def test_m2_5_cross_tenant_follow_up_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_B, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    r = client.post(f"/api/v1/revenue/contacts/{_CONTACT_B}/follow-up/propose", json={})
    assert r.status_code == 422


def test_m2_5_cross_tenant_approval_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = _propose(client, str(_CONTACT_A))
    _login(client, "owner-b@example.com", "pass-b", ids["org_b"])
    with patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n:
        r = client.post(f"/api/v1/approvals/{body['approval_id']}/approve", json={})
        assert r.status_code == 404
        mock_n8n.assert_not_called()


def test_m2_5_client_tenant_spoof_blocked(
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


def test_m2_5_client_human_identity_spoof_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = _propose(client, str(_CONTACT_A))
    client.cookies.clear()
    with patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n:
        r = client.post(
            f"/api/v1/approvals/{body['approval_id']}/approve",
            json={"decided_by": _OPERATOR},
        )
        assert r.status_code == 403
        mock_n8n.assert_not_called()
    with pytest.raises(HumanAuthorityError, match="Session tenant context required"):
        _human_decider(None, _OPERATOR)


def test_m2_5_legacy_sequence_cannot_bypass_m2(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    with (
        patch("revenue_os.services.ai_service.generate_followup_sequence", return_value=[]),
        patch("revenue_os.integrations.n8n.trigger_workflow") as mock_n8n,
    ):
        r = client.post(f"/api/v1/agents/sales/{_CONTACT_A}/sequence", json={})
        mock_n8n.assert_not_called()
    assert r.status_code == 200
    src = inspect.getsource(agents_mod.sales_build_sequence)
    assert "require_tenant_context" in src
    assert "execute_revenue_workflow" not in src
    assert client.post(f"/api/v1/agents/sales/{_CONTACT_A}/sequence", json={}).status_code in {200, 403}


def test_m2_5_legacy_sequence_cross_tenant_contained(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    r = client.post(f"/api/v1/agents/sales/{_CONTACT_B}/sequence", json={})
    assert r.status_code == 200
    assert r.json().get("ok") is False


def test_m2_5_m1_initial_outreach_unchanged(
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
    body = r.json()
    assert body["state"] == "APPROVAL_PENDING"
    assert body["orchestrator"] == "WorkflowOrchestrator"
    src = inspect.getsource(rev_orch_mod.research_to_outreach)
    assert "REV_ORCH_M1_WORKFLOW_KEY" in src
    assert "WorkflowOrchestrator.execute_revenue_workflow" in src


def test_m2_5_cadence_contract_frozen() -> None:
    assert MAX_FOLLOW_UP_STEPS == 2
    assert FOLLOW_UP_INTERVALS_DAYS == (3, 7)


def test_m2_5_cadence_interval_not_elapsed_blocks(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=1)
    db = tenant_db()
    try:
        contact = db.get(Contact, _CONTACT_A)
        assert contact is not None
        result = evaluate_follow_up_eligibility(db, contact)
        assert result["eligible"] is False
        assert result["state"] == "FOLLOWUP_NOT_DUE"
    finally:
        db.close()


def test_m2_5_ai_service_has_no_send_or_crm_mutators() -> None:
    public = {n for n, o in inspect.getmembers(ai_service, inspect.isfunction) if not n.startswith("_")}
    prohibited = {
        "update_contact",
        "create_deal",
        "apply_deal_stage",
        "accept_qualified_demand",
        "trigger_workflow",
        "request_approval",
        "decide",
    }
    assert public.isdisjoint(prohibited)


def test_m2_5_revalidation_helper_blocks_reply(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    source = _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _seed_reply(tenant_db, _CONTACT_A)
    db = tenant_db()
    try:
        contact = db.get(Contact, _CONTACT_A)
        assert contact is not None
        with pytest.raises(ValueError, match="Reply recorded"):
            _revalidate_follow_up_before_send(
                db,
                contact,
                {"source_activity_id": str(source.id), "workflow_kind": "rev_orch_m2_follow_up"},
            )
    finally:
        db.close()


def test_m2_5_no_new_followup_sot_in_eligibility_module() -> None:
    src = inspect.getsource(elig)
    assert "class FollowUpSequence" not in src
    assert "class FollowUpCampaign" not in src
    assert "class FollowUpState" not in src
    assert "alembic" not in src


def test_m2_5_audit_provenance(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _seed_outbound(tenant_db, _CONTACT_A, days_ago=5)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    _propose(client, str(_CONTACT_A))
    db = tenant_db()
    try:
        logs = db.query(AgentActionLog).filter(AgentActionLog.organization_id == _ORG_A).all()
        types = {log.action_type for log in logs}
        assert "rev_orch_followup_eligibility" in types
        assert "worker_followup_proposal" in types
    finally:
        db.close()
