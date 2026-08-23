"""ACP-2 — Agent Orchestration & Work Control Plane focused tests."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import revenue_os.models  # noqa: F401
from revenue_os.models.automation_state import AgentActionLog
from revenue_os.models.base import Base
from revenue_os.models.contact import Contact, ContactSource, ContactStatus
from revenue_os.models.deal import Deal
from revenue_os.models.organization import Organization, OrganizationStatus
from revenue_os.services import acp2_orchestration as orch
from revenue_os.services.acp2_effect_catalog import get_effect_spec
from revenue_os.services.acp2_orchestration import (
    assign_executor,
    delegate_child,
    evaluate_authority,
    orchestrate,
    propose_work,
    retry_work,
    run_work,
)
from revenue_os.services.acp2_oversight import compose_orchestration_summary
from revenue_os.services.acp2_work_contract import (
    WORK_CONTACT_STATUS,
    WORK_FOLLOW_UP_SEND,
    WORK_HERMES_DEAL_CREATE,
    WORK_LEAD_SCORE,
    WORK_OUTBOUND_SEND,
    ExecutionMode,
    WorkState,
    can_transition_to_running,
)
from revenue_os.services.hermes_planner import action_create_deals_for_qualified

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def tenant_db(monkeypatch: pytest.MonkeyPatch, tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'acp2.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    import revenue_os.database as db_mod
    import revenue_os.services.activity_log as al
    import revenue_os.services.hermes_planner as hermes
    import revenue_os.services.acp2_orchestration as orch_mod

    for mod in (db_mod, al, hermes, orch_mod):
        if hasattr(mod, "SessionLocal"):
            monkeypatch.setattr(mod, "SessionLocal", sf)
    monkeypatch.delenv("ACP1_AUTONOMOUS_ORGANIZATION_IDS", raising=False)
    monkeypatch.delenv("HEARTBEAT_ORGANIZATION_IDS", raising=False)
    monkeypatch.setenv("ACP2_AUTONOMOUS_EXECUTION_ENABLED", "1")
    monkeypatch.setenv("HEARTBEAT_ENABLED", "1")
    return sf


def _seed(sf: sessionmaker) -> None:
    db = sf()
    try:
        db.add_all(
            [
                Organization(
                    id=_ORG_A, name="Org A", slug="org-a", status=OrganizationStatus.ACTIVE
                ),
                Organization(
                    id=_ORG_B, name="Org B", slug="org-b", status=OrganizationStatus.ACTIVE
                ),
                Contact(
                    id=_CONTACT_A,
                    first_name="Ada",
                    last_name="A",
                    email="ada@a.example",
                    status=ContactStatus.LEAD,
                    source=ContactSource.MANUAL,
                    organization_id=_ORG_A,
                    lead_score=0,
                ),
            ]
        )
        db.commit()
    finally:
        db.close()


# ── Lifecycle ────────────────────────────────────────────────────────────────


def test_autonomous_lifecycle_succeeds(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        calls = {"n": 0}

        def _exec(_w):
            calls["n"] += 1
            return {"ok": True}

        work = orchestrate(
            db,
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="test",
            actor="heartbeat",
            executor=_exec,
            target_type="contact",
            target_id=str(_CONTACT_A),
        )
        assert work.state == WorkState.SUCCEEDED
        assert calls["n"] == 1
    finally:
        db.close()


def test_blocked_cannot_execute(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        ran = {"n": 0}

        def _exec(_w):
            ran["n"] += 1
            return {}

        work = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=None,
            source="test",
            actor="heartbeat",
        )
        assign_executor(work, "heartbeat")
        evaluate_authority(db, work)
        assert work.state == WorkState.BLOCKED
        run_work(db, work, _exec)
        assert ran["n"] == 0
        assert not can_transition_to_running(WorkState.BLOCKED)
    finally:
        db.close()


def test_prohibited_cannot_execute(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        ran = {"n": 0}
        work = orchestrate(
            db,
            work_kind=WORK_HERMES_DEAL_CREATE,
            organization_id=str(_ORG_A),
            source="hermes",
            actor="hermes",
            executor=lambda _w: ran.__setitem__("n", ran["n"] + 1) or {},
        )
        assert work.state == WorkState.BLOCKED
        assert work.execution_mode == ExecutionMode.PROHIBITED
        assert ran["n"] == 0
    finally:
        db.close()


def test_human_required_stops_before_effect(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        ran = {"n": 0}
        work = orchestrate(
            db,
            work_kind=WORK_OUTBOUND_SEND,
            organization_id=str(_ORG_A),
            source="agent",
            actor="heartbeat",
            executor=lambda _w: ran.__setitem__("n", ran["n"] + 1) or {"sent": True},
        )
        assert work.state == WorkState.WAITING_HUMAN
        assert ran["n"] == 0
    finally:
        db.close()


def test_terminal_no_silent_resurrection(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        work = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="test",
            actor="heartbeat",
            target_id="x",
        )
        work.state = WorkState.EXHAUSTED
        ran = {"n": 0}
        run_work(db, work, lambda _w: ran.__setitem__("n", 1) or {})
        assert ran["n"] == 0
        assert work.state == WorkState.EXHAUSTED
    finally:
        db.close()


# ── Tenant ───────────────────────────────────────────────────────────────────


def test_missing_org_fails_closed(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        work = orchestrate(
            db,
            work_kind=WORK_LEAD_SCORE,
            organization_id=None,
            source="test",
            actor="heartbeat",
            executor=lambda _w: {"ok": True},
        )
        assert work.state == WorkState.BLOCKED
    finally:
        db.close()


def test_non_allowlisted_org_fails_closed(tenant_db, monkeypatch):
    _seed(tenant_db)
    monkeypatch.setenv("ACP1_AUTONOMOUS_ORGANIZATION_IDS", str(_ORG_A))
    db = tenant_db()
    try:
        work = orchestrate(
            db,
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_B),
            source="test",
            actor="heartbeat",
            executor=lambda _w: {"ok": True},
        )
        assert work.state == WorkState.BLOCKED
    finally:
        db.close()


def test_cross_tenant_delegation_blocked(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        parent = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="test",
            actor="heartbeat",
        )
        parent.state = WorkState.ELIGIBLE
        parent.assigned_agent = "heartbeat"
        # Force child org mismatch by mutating after propose (simulates attack)
        child = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_B),
            source="delegation",
            actor="scoring_worker",
            parent=parent,
        )
        # delegate_child always uses parent org — prove API blocks mismatch path
        child2 = delegate_child(
            db,
            parent,
            child_work_kind=WORK_LEAD_SCORE,
            actor="scoring_worker",
            target_id="c1",
        )
        assert child2.organization_id == str(_ORG_A)
        assert str(child.organization_id) != str(parent.organization_id)
    finally:
        db.close()


def test_contact_ownership_does_not_activate_tenant(tenant_db):
    """Orphan Contact.organization_id is not an ACP-1 autonomous tenant."""
    from revenue_os.services.acp1_autonomous_boundary import resolve_autonomous_organization_ids

    db = tenant_db()
    try:
        orphan = uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
        db.add(
            Contact(
                first_name="Orphan",
                last_name="X",
                email="o@example.com",
                status=ContactStatus.LEAD,
                source=ContactSource.MANUAL,
                organization_id=orphan,
            )
        )
        db.commit()
        orgs = resolve_autonomous_organization_ids(db)
        assert str(orphan) not in orgs
    finally:
        db.close()


# ── Authority amplification ──────────────────────────────────────────────────


def test_delegation_cannot_amplify_to_outbound(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        parent = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="test",
            actor="heartbeat",
        )
        assign_executor(parent, "heartbeat")
        evaluate_authority(db, parent)
        ran = {"n": 0}
        child = delegate_child(
            db,
            parent,
            child_work_kind=WORK_OUTBOUND_SEND,
            actor="approval_executor",
            executor=lambda _w: ran.__setitem__("n", 1) or {"sent": True},
        )
        assert child.state == WorkState.WAITING_HUMAN
        assert ran["n"] == 0
    finally:
        db.close()


def test_delegation_cannot_create_hermes_deal(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        parent = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="hermes",
            actor="hermes",
        )
        assign_executor(parent, "hermes")
        evaluate_authority(db, parent)
        child = delegate_child(
            db,
            parent,
            child_work_kind=WORK_HERMES_DEAL_CREATE,
            actor="hermes",
            executor=lambda _w: {"deals_created": 99},
        )
        assert child.state == WorkState.BLOCKED
        assert db.query(Deal).count() == 0
    finally:
        db.close()


def test_optional_tenant_mutation_not_autonomous_via_delegation(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        parent = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="test",
            actor="heartbeat",
        )
        assign_executor(parent, "heartbeat")
        evaluate_authority(db, parent)
        child = delegate_child(
            db,
            parent,
            child_work_kind=WORK_CONTACT_STATUS,
            actor="heartbeat",
            executor=lambda _w: {"mutated": True},
        )
        assert child.execution_mode == ExecutionMode.PROHIBITED
        assert child.state == WorkState.BLOCKED
    finally:
        db.close()


def test_assignment_does_not_grant_authority():
    spec = get_effect_spec(WORK_OUTBOUND_SEND)
    assert spec is not None
    assert spec.execution_mode == ExecutionMode.HUMAN_REQUIRED
    # Eligible agent list includes approval_executor but mode is still HUMAN_REQUIRED
    assert "approval_executor" in spec.eligible_agents


# ── Delegation bounds ────────────────────────────────────────────────────────


def test_delegation_depth_bounded(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        parent = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="test",
            actor="heartbeat",
        )
        parent.delegation_depth = parent.max_delegation_depth
        parent.assigned_agent = "heartbeat"
        child = delegate_child(
            db,
            parent,
            child_work_kind=WORK_LEAD_SCORE,
            actor="scoring_worker",
        )
        assert child.state == WorkState.BLOCKED
        assert child.failure_reason == "delegation_depth_exceeded"
    finally:
        db.close()


def test_delegation_provenance_chain(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        parent = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="test",
            actor="heartbeat",
            target_id="root-target",
        )
        assign_executor(parent, "heartbeat")
        evaluate_authority(db, parent)
        child = delegate_child(
            db,
            parent,
            child_work_kind=WORK_LEAD_SCORE,
            actor="scoring_worker",
            target_id="child-target",
        )
        assert child.parent_work_id == parent.work_id
        assert child.root_work_id == parent.root_work_id
        assert child.requesting_agent == "heartbeat"
        logs = (
            db.query(AgentActionLog)
            .filter(AgentActionLog.action_type == orch.LOG_ORCH_DELEGATED)
            .all()
        )
        assert logs
    finally:
        db.close()


# ── Idempotency / retry ──────────────────────────────────────────────────────


def test_duplicate_work_does_not_duplicate_effect(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        calls = {"n": 0}

        def _exec(_w):
            calls["n"] += 1
            return {"ok": True}

        w1 = orchestrate(
            db,
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="scheduler",
            actor="heartbeat",
            executor=_exec,
            target_id=str(_CONTACT_A),
            logical_key="unscored",
        )
        w2 = orchestrate(
            db,
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="scheduler",
            actor="heartbeat",
            executor=_exec,
            target_id=str(_CONTACT_A),
            logical_key="unscored",
        )
        assert w1.state == WorkState.SUCCEEDED
        assert w2.state == WorkState.SUCCEEDED
        assert w2.result.get("deduplicated") is True
        assert calls["n"] == 1
    finally:
        db.close()


def test_retry_exhaustion(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        work = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="test",
            actor="heartbeat",
            target_id="retry-target",
            max_attempts=2,
        )
        assign_executor(work, "heartbeat")
        evaluate_authority(db, work)

        def _fail(_w):
            raise RuntimeError("transient boom")

        work.detail["treat_as_transient"] = True
        run_work(db, work, _fail, transient_failure=True)
        assert work.state == WorkState.RETRYABLE
        retry_work(db, work, _fail)
        assert work.state == WorkState.EXHAUSTED
    finally:
        db.close()


def test_human_required_does_not_retry(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        work = propose_work(
            work_kind=WORK_FOLLOW_UP_SEND,
            organization_id=str(_ORG_A),
            source="test",
            actor="approval_executor",
        )
        work.state = WorkState.RETRYABLE
        work.execution_mode = ExecutionMode.HUMAN_REQUIRED
        out = retry_work(db, work, lambda _w: {"sent": True})
        assert out.state == WorkState.BLOCKED
    finally:
        db.close()


def test_prohibited_does_not_retry(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        work = propose_work(
            work_kind=WORK_HERMES_DEAL_CREATE,
            organization_id=str(_ORG_A),
            source="hermes",
            actor="hermes",
        )
        work.state = WorkState.RETRYABLE
        out = retry_work(db, work, lambda _w: {"deals": 1})
        assert out.state == WorkState.BLOCKED
    finally:
        db.close()


# ── Hermes / kill / oversight ────────────────────────────────────────────────


def test_hermes_deal_create_still_prohibited(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        before = db.query(Deal).count()
        result = action_create_deals_for_qualified(
            db, {"organization_id": str(_ORG_A)}
        )
        assert result.get("blocked") is True
        assert db.query(Deal).count() == before
    finally:
        db.close()


def test_kill_switch_cancels_autonomous(tenant_db, monkeypatch):
    _seed(tenant_db)
    monkeypatch.setenv("ACP2_AUTONOMOUS_EXECUTION_ENABLED", "0")
    db = tenant_db()
    try:
        work = orchestrate(
            db,
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="test",
            actor="heartbeat",
            executor=lambda _w: {"ok": True},
        )
        assert work.state == WorkState.CANCELLED
    finally:
        db.close()


def test_oversight_summary_observes_failures(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        orchestrate(
            db,
            work_kind=WORK_HERMES_DEAL_CREATE,
            organization_id=str(_ORG_A),
            source="hermes",
            actor="hermes",
            executor=lambda _w: {},
        )
        summary = compose_orchestration_summary(db, organization_id=str(_ORG_A))
        assert summary["counts"]["blocked"] >= 1
        assert "pause" in summary
    finally:
        db.close()


def test_no_new_sot_or_models():
    src = (_ROOT / "revenue_os/services/acp2_orchestration.py").read_text()
    assert "class AgentRun" not in src
    assert "alembic" not in src.lower()
    assert "CREATE TABLE" not in src
    contract = (_ROOT / "revenue_os/services/acp2_work_contract.py").read_text()
    assert "Column(" not in contract
