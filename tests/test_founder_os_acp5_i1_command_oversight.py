"""ACP-5-I1 — Command oversight + follow-up loop proof + Hermes plan sanitize."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import revenue_os.models  # noqa: F401
from tests.conftest import build_test_approval_request
import runner_api_routers.identity as identity_mod
import runner_api_routers.operator_flow as of_router
import runner_api_routers.ui as ui_mod
from revenue_os.auth import hash_password
from revenue_os.models.approvals import ApprovalRequest
from revenue_os.models.automation_state import AgentActionLog
from revenue_os.models.base import Base
from revenue_os.models.organization import (
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationStatus,
)
from revenue_os.models.user import User
from revenue_os.services.acp2_orchestration import LOG_ORCH_SUCCEEDED, LOG_ORCH_WAITING
from revenue_os.services.acp2_work_contract import WORK_FOLLOW_UP_PROPOSE, WorkState
from revenue_os.services.approvals import EXECUTORS, decide, request_approval
from revenue_os.services.founder_ui_read_model import build_command_center_snapshot
from revenue_os.services.hermes_planner import ACTION_REGISTRY, generate_plan
from revenue_os.services.identity_context import AuthMethod, IdentityContext, PrincipalKind
from revenue_os.services.tenant_context import TenantContext
from revenue_os.services.tenant_resolution import ORGANIZATION_COOKIE
from runner_api import app

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_OPERATOR = "Krishna Founder"
_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _reset() -> None:
    identity_mod._revoked_jtis.clear()
    identity_mod._login_failures.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def tenant_db(monkeypatch: pytest.MonkeyPatch, tmp_path) -> sessionmaker:
    engine = create_engine(f"sqlite:///{tmp_path / 'acp5_i1.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    import revenue_os.database as db_mod
    import revenue_os.services.activity_log as al
    import revenue_os.services.approvals as approvals_mod
    import revenue_os.services.commercial_funnel_intelligence as cfi_mod
    import revenue_os.services.founder_ui_read_model as founder_rm
    import revenue_os.services.operator_flow_read_model as of_rm
    import revenue_os.services.tenant_resolution as tr

    for mod in (
        db_mod,
        tr,
        approvals_mod,
        al,
        ui_mod,
        founder_rm,
        of_rm,
        of_router,
        identity_mod,
        cfi_mod,
    ):
        if hasattr(mod, "SessionLocal"):
            monkeypatch.setattr(mod, "SessionLocal", sf)
    monkeypatch.setenv("FOUNDER_OS_REQUIRE_LOGIN", "0")
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    monkeypatch.setenv("SECRET_KEY", "ui-d2-1-local-test-secret-key-32b")
    return sf


def _seed(db_factory: sessionmaker) -> None:
    db = db_factory()
    try:
        db.add_all(
            [
                Organization(id=_ORG_A, name="Org A", slug="org-a", status=OrganizationStatus.ACTIVE),
                Organization(id=_ORG_B, name="Org B", slug="org-b", status=OrganizationStatus.ACTIVE),
            ]
        )
        owner = User(
            email="owner-a@example.com",
            hashed_password=hash_password("pass-a"),
            full_name=_OPERATOR,
            role="owner",
            is_active=1,
        )
        db.add(owner)
        db.flush()
        db.add(
            OrganizationMembership(
                user_id=owner.id,
                organization_id=_ORG_A,
                role="owner",
                status=MembershipStatus.ACTIVE,
            )
        )
        db.commit()
    finally:
        db.close()


def _human_tenant(org_id: uuid.UUID = _ORG_A) -> TenantContext:
    return TenantContext(
        identity=IdentityContext(
            principal_kind=PrincipalKind.HUMAN,
            auth_method=AuthMethod.SESSION,
            is_human=True,
            user_id=str(uuid.uuid4()),
            email="founder@example.com",
            display_name=_OPERATOR,
            role="owner",
        ),
        organization_id=str(org_id),
        organization_name="Org A",
        organization_slug="org-a",
        membership_id="m1",
        membership_role="owner",
        membership_status="active",
    )


def _login(client: TestClient, org_id: str) -> None:
    client.post("/login", data={"email": "owner-a@example.com", "password": "pass-a"})
    client.cookies.set(ORGANIZATION_COOKIE, org_id)


# ── Command oversight projection ─────────────────────────────────────────────


def test_command_template_projects_agent_orchestration_fields():
    src = (_ROOT / "templates/founder_command.html").read_text(encoding="utf-8")
    assert "command-agent-orchestration" in src
    assert "agent_orchestration" in src
    assert "awaiting_human" in src
    assert "does not grant authority" in src.lower() or "does not grant authority" in src


def test_command_snapshot_includes_agent_orchestration(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        db.add(
            AgentActionLog(
                actor="heartbeat",
                action_type=LOG_ORCH_WAITING,
                status="completed",
                organization_id=_ORG_A,
                detail={
                    "work_id": "w-wait-1",
                    "work_kind": WORK_FOLLOW_UP_PROPOSE,
                    "state": WorkState.WAITING_HUMAN.value,
                    "execution_mode": "AUTONOMOUS",
                    "escalation_reason": "follow_up_send_requires_approval",
                },
            )
        )
        db.add(
            AgentActionLog(
                actor="heartbeat",
                action_type=LOG_ORCH_SUCCEEDED,
                status="completed",
                organization_id=_ORG_A,
                detail={
                    "work_id": "w-ok-1",
                    "work_kind": "lead_score",
                    "state": WorkState.SUCCEEDED.value,
                    "execution_mode": "AUTONOMOUS",
                },
            )
        )
        db.commit()
    finally:
        db.close()

    snap = build_command_center_snapshot(organization_id=str(_ORG_A))
    orch = snap.get("agent_orchestration") or {}
    assert orch.get("counts", {}).get("awaiting_human", 0) >= 1
    assert orch.get("counts", {}).get("succeeded", 0) >= 1
    assert "pause" in orch


def test_command_page_renders_agent_orchestration(client, tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        db.add(
            AgentActionLog(
                actor="heartbeat",
                action_type=LOG_ORCH_WAITING,
                status="completed",
                organization_id=_ORG_A,
                detail={
                    "work_id": "w-wait-cmd",
                    "work_kind": WORK_FOLLOW_UP_PROPOSE,
                    "state": WorkState.WAITING_HUMAN.value,
                    "execution_mode": "AUTONOMOUS",
                    "escalation_reason": "follow_up_send_requires_approval",
                },
            )
        )
        db.commit()
    finally:
        db.close()

    _login(client, str(_ORG_A))
    r = client.get("/command")
    assert r.status_code == 200
    body = r.text
    assert 'data-testid="command-agent-orchestration"' in body
    assert 'data-testid="agent-orch-awaiting"' in body
    assert "Waiting on founder" in body or "waiting" in body.lower()


def test_founder_required_attention_visible_with_pending_approval(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        cid = str(uuid.uuid4())
        db.add(
            build_test_approval_request(
                requested_by="followup_worker",
                action_type="send_outreach_email",
                title="Follow-up #1 to Ada",
                target_id=cid,
                payload={"organization_id": str(_ORG_A), "contact_id": cid},
            )
        )
        db.commit()
    finally:
        db.close()
    snap = build_command_center_snapshot(organization_id=str(_ORG_A))
    assert snap["pending_approval_count"] >= 1
    assert snap["decision_loop"]["requires_founder"] >= 1
    kinds = {i.get("kind") for i in snap.get("decision_items") or []}
    assert "approval" in kinds


# ── Follow-up loop: proposal ≠ send ───────────────────────────────────────────


def test_follow_up_proposal_is_proposal_only_no_send_executor(monkeypatch, tenant_db):
    _seed(tenant_db)
    calls = {"n": 0}

    def _boom(db, payload):  # noqa: ANN001
        calls["n"] += 1
        raise AssertionError("send executor must not run on proposal")

    monkeypatch.setitem(EXECUTORS, "send_outreach_email", _boom)
    approval = request_approval(
        requested_by="followup_worker",
        action_type="send_outreach_email",
        title="Follow-up propose only",
        description="proposal",
        target_type="contact",
        target_id=str(uuid.uuid4()),
        payload={
            "organization_id": str(_ORG_A),
            "contact_id": str(uuid.uuid4()),
            "email": "ada@a.example",
            "workflow_kind": "rev_orch_m2_follow_up",
        },
        organization_id=str(_ORG_A),
    )
    assert approval["status"] == "pending"
    assert calls["n"] == 0


def test_approved_follow_up_uses_existing_executor_once(monkeypatch, tenant_db):
    _seed(tenant_db)
    import revenue_os.services.approvals as appr_mod

    monkeypatch.setattr(appr_mod, "SessionLocal", tenant_db)
    exec_calls = {"n": 0}

    def _fake(db, payload):  # noqa: ANN001
        exec_calls["n"] += 1
        return {"handed_to_n8n": True, "note": "test"}

    monkeypatch.setitem(appr_mod.EXECUTORS, "send_outreach_email", _fake)
    rid = str(uuid.uuid4())
    cid = str(uuid.uuid4())
    db = tenant_db()
    try:
        db.add(
            build_test_approval_request(
                id=rid,
                requested_by="followup_worker",
                action_type="send_outreach_email",
                title="Follow-up #1",
                target_id=cid,
                payload={
                    "organization_id": str(_ORG_A),
                    "contact_id": cid,
                    "email": "ada@a.example",
                },
            )
        )
        db.commit()
    finally:
        db.close()

    decide(rid, True, tenant=_human_tenant())
    assert exec_calls["n"] == 1


def test_rejected_follow_up_produces_no_outbound_effect(monkeypatch, tenant_db):
    _seed(tenant_db)
    import revenue_os.services.approvals as appr_mod

    monkeypatch.setattr(appr_mod, "SessionLocal", tenant_db)
    exec_calls = {"n": 0}

    def _fake(db, payload):  # noqa: ANN001
        exec_calls["n"] += 1
        return {"handed_to_n8n": True}

    monkeypatch.setitem(appr_mod.EXECUTORS, "send_outreach_email", _fake)
    rid = str(uuid.uuid4())
    cid = str(uuid.uuid4())
    db = tenant_db()
    try:
        db.add(
            build_test_approval_request(
                id=rid,
                requested_by="followup_worker",
                action_type="send_outreach_email",
                title="Follow-up #1",
                target_id=cid,
                payload={"organization_id": str(_ORG_A), "contact_id": cid},
            )
        )
        db.commit()
    finally:
        db.close()

    decide(rid, False, tenant=_human_tenant())
    assert exec_calls["n"] == 0


def test_cross_tenant_approval_decide_fails_closed(monkeypatch, tenant_db):
    _seed(tenant_db)
    import revenue_os.services.approvals as appr_mod

    monkeypatch.setattr(appr_mod, "SessionLocal", tenant_db)
    rid = str(uuid.uuid4())
    cid = str(uuid.uuid4())
    db = tenant_db()
    try:
        db.add(
            build_test_approval_request(
                id=rid,
                requested_by="followup_worker",
                action_type="send_outreach_email",
                title="t",
                target_id=cid,
                payload={"organization_id": str(_ORG_A), "contact_id": cid},
            )
        )
        db.commit()
    finally:
        db.close()
    with pytest.raises(ValueError, match="not found"):
        decide(rid, True, tenant=_human_tenant(_ORG_B))


def test_command_refresh_after_approval_decision(monkeypatch, tenant_db):
    _seed(tenant_db)
    import revenue_os.services.approvals as appr_mod

    monkeypatch.setattr(appr_mod, "SessionLocal", tenant_db)
    monkeypatch.setitem(
        appr_mod.EXECUTORS,
        "send_outreach_email",
        lambda db, payload: {"handed_to_n8n": True},
    )
    rid = str(uuid.uuid4())
    cid = str(uuid.uuid4())
    db = tenant_db()
    try:
        db.add(
            build_test_approval_request(
                id=rid,
                requested_by="followup_worker",
                action_type="send_outreach_email",
                title="Follow-up #1",
                target_id=cid,
                payload={"organization_id": str(_ORG_A), "contact_id": cid},
            )
        )
        db.commit()
    finally:
        db.close()

    before = build_command_center_snapshot(organization_id=str(_ORG_A))
    assert before["pending_approval_count"] >= 1
    decide(rid, True, tenant=_human_tenant())
    after = build_command_center_snapshot(organization_id=str(_ORG_A))
    assert after["pending_approval_count"] == before["pending_approval_count"] - 1


# ── Hermes sanitization ───────────────────────────────────────────────────────


def test_hermes_generate_plan_has_no_executable_deal_create():
    for metric in ("qualified_leads", "pipeline_value", "deals_closed"):
        plan = generate_plan(metric)
        actions = [s["action_type"] for s in plan]
        assert "create_deals_for_qualified" not in actions
        for step in plan:
            assert step["action_type"] in ACTION_REGISTRY
            assert step["action_type"] != "create_deals_for_qualified"


def test_hermes_sanitization_replaces_with_permitted_handoffs():
    pipeline = generate_plan("pipeline_value")
    closed = generate_plan("deals_closed")
    assert any(s["action_type"] == "qualify_high_scorers" for s in pipeline)
    assert any(s["action_type"] == "check_deals_at_risk" for s in pipeline)
    assert any(s["action_type"] == "qualify_high_scorers" for s in closed)
    assert any(s["action_type"] == "check_deals_at_risk" for s in closed)


def test_hermes_deal_create_still_prohibited_in_registry_path():
    """Defense in depth: ACTION_REGISTRY still has blocked path; catalog PROHIBITED."""
    assert "create_deals_for_qualified" in ACTION_REGISTRY
    from revenue_os.services.acp1_autonomous_boundary import hermes_action_allowed

    assert hermes_action_allowed("create_deals_for_qualified") is False


# ── Architecture invariants ───────────────────────────────────────────────────


def test_no_new_persistent_sot_or_models_in_i1_surface():
    for rel in (
        "templates/founder_command.html",
        "revenue_os/services/hermes_planner.py",
    ):
        src = (_ROOT / rel).read_text(encoding="utf-8")
        assert "alembic" not in src.lower()
        assert "Column(" not in src or rel.endswith(".html")
    # No new model modules introduced by I1
    assert not (_ROOT / "revenue_os/models/acp5_agent_work.py").exists()


def test_proposal_attention_plan_do_not_imply_send_authority():
    tpl = (_ROOT / "templates/founder_command.html").read_text(encoding="utf-8")
    assert "does not grant authority" in tpl
    hermes = (_ROOT / "revenue_os/services/hermes_planner.py").read_text(encoding="utf-8")
    assert "create_deals_for_qualified" not in hermes.split("def generate_plan", 1)[1].split(
        "def create_goal", 1
    )[0]


def test_acp4_modules_untouched_by_i1():
    """I1 must not rewrite ACP-4 claim/fence (protected). Presence check only."""
    assert (_ROOT / "revenue_os/services/acp4_distributed_claim.py").exists()
    assert (_ROOT / "revenue_os/services/acp4_execution_fence.py").exists()
    assert "orchestrate_claimed" in (_ROOT / "revenue_os/scheduler.py").read_text()


def test_missing_org_command_fail_closed():
    snap = build_command_center_snapshot(organization_id=None)
    assert snap.get("state") == "unavailable" or snap.get("decision_items") == []
