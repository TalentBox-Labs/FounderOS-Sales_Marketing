"""ACP-3 — Durable Autonomous Operations Runtime focused tests."""

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
from revenue_os.models.organization import Organization, OrganizationStatus
from revenue_os.services.acp2_orchestration import (
    LOG_ORCH_RUNNING,
    LOG_ORCH_SUCCEEDED,
    orchestrate,
    propose_work,
    assign_executor,
    evaluate_authority,
    run_work,
)
from revenue_os.services.acp2_oversight import compose_orchestration_summary
from revenue_os.services.acp2_work_contract import (
    WORK_HERMES_DEAL_CREATE,
    WORK_LEAD_SCORE,
    WORK_OUTBOUND_SEND,
    ExecutionMode,
    WorkState,
)
from revenue_os.services.acp3_durable_runtime import (
    bounded_resume_pass,
    gate_new_mutating_work,
    recover_retryable_unit,
    runtime_gates,
)
from revenue_os.services.acp3_reconciliation import (
    classify_recovery,
    reconcile_organization,
)
from revenue_os.services.acp3_runtime_contract import RecoveryClass
from revenue_os.services.activity_log import log_agent_action

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def tenant_db(monkeypatch: pytest.MonkeyPatch, tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'acp3.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    import revenue_os.database as db_mod
    import revenue_os.scheduler as sched
    import revenue_os.services.activity_log as al
    import revenue_os.services.acp2_orchestration as orch
    import revenue_os.services.acp3_durable_runtime as runtime

    for mod in (db_mod, al, orch, sched, runtime):
        if hasattr(mod, "SessionLocal"):
            monkeypatch.setattr(mod, "SessionLocal", sf)
    monkeypatch.delenv("ACP1_AUTONOMOUS_ORGANIZATION_IDS", raising=False)
    monkeypatch.setenv("ACP2_AUTONOMOUS_EXECUTION_ENABLED", "1")
    monkeypatch.setenv("HEARTBEAT_ENABLED", "1")
    monkeypatch.setenv("ACP3_RESUME_ENABLED", "1")
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


def test_duplicate_scheduler_invocation_idempotent(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        calls = {"n": 0}

        def _exec(_w):
            calls["n"] += 1
            return {"ok": True}

        for _ in range(2):
            orchestrate(
                db,
                work_kind=WORK_LEAD_SCORE,
                organization_id=str(_ORG_A),
                source="scheduler",
                actor="heartbeat",
                executor=_exec,
                target_id=str(_CONTACT_A),
                logical_key="unscored",
            )
        assert calls["n"] == 1
    finally:
        db.close()


def test_restart_before_execution_is_retryable(tenant_db):
    """PROPOSED (eligible logged) without RUNNING → recovery class RETRYABLE."""
    _seed(tenant_db)
    db = tenant_db()
    try:
        work = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="scheduler",
            actor="heartbeat",
            target_id=str(_CONTACT_A),
            logical_key="pre-exec",
        )
        assign_executor(work, "heartbeat")
        evaluate_authority(db, work)
        assert work.state == WorkState.ELIGIBLE
        report = reconcile_organization(db, organization_id=str(_ORG_A))
        keys = [i["idempotency_key"] for i in report["buckets"]["retryable"]]
        assert work.idempotency_key in keys
    finally:
        db.close()


def test_running_without_success_lead_score_replay_safe_when_incomplete(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        work = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="scheduler",
            actor="heartbeat",
            target_id=str(_CONTACT_A),
            logical_key="crash-mid",
        )
        work.attempt = 1
        work.state = WorkState.RUNNING
        log_agent_action(
            actor="heartbeat",
            action_type=LOG_ORCH_RUNNING,
            status="completed",
            organization_id=str(_ORG_A),
            target_type="contact",
            target_id=str(_CONTACT_A),
            detail=work.to_dict(),
        )
        row = (
            db.query(AgentActionLog)
            .filter(AgentActionLog.action_type == LOG_ORCH_RUNNING)
            .first()
        )
        assert row is not None
        classified = classify_recovery(db, organization_id=str(_ORG_A), row=row)
        assert classified["recovery_class"] == RecoveryClass.RETRYABLE.value
    finally:
        db.close()


def test_running_with_domain_proof_is_succeeded(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        contact = db.get(Contact, _CONTACT_A)
        assert contact is not None
        contact.lead_score = 77
        db.commit()
        work = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="scheduler",
            actor="heartbeat",
            target_id=str(_CONTACT_A),
            logical_key="proved",
        )
        work.attempt = 1
        log_agent_action(
            actor="heartbeat",
            action_type=LOG_ORCH_RUNNING,
            status="completed",
            organization_id=str(_ORG_A),
            target_id=str(_CONTACT_A),
            detail=work.to_dict(),
        )
        row = (
            db.query(AgentActionLog)
            .filter(AgentActionLog.action_type == LOG_ORCH_RUNNING)
            .first()
        )
        classified = classify_recovery(db, organization_id=str(_ORG_A), row=row)
        assert classified["recovery_class"] == RecoveryClass.SUCCEEDED.value
    finally:
        db.close()


def test_outbound_running_is_ambiguous_no_blind_replay(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        work = propose_work(
            work_kind=WORK_OUTBOUND_SEND,
            organization_id=str(_ORG_A),
            source="agent",
            actor="approval_executor",
            target_id=str(_CONTACT_A),
            logical_key="send",
        )
        # Force a RUNNING log as if crash after external send attempt
        work.execution_mode = ExecutionMode.HUMAN_REQUIRED
        work.state = WorkState.RUNNING
        log_agent_action(
            actor="approval_executor",
            action_type=LOG_ORCH_RUNNING,
            status="completed",
            organization_id=str(_ORG_A),
            detail=work.to_dict(),
        )
        row = (
            db.query(AgentActionLog)
            .filter(AgentActionLog.action_type == LOG_ORCH_RUNNING)
            .first()
        )
        classified = classify_recovery(db, organization_id=str(_ORG_A), row=row)
        assert classified["recovery_class"] == RecoveryClass.AMBIGUOUS_EFFECT.value
    finally:
        db.close()


def test_human_required_recovery_does_not_execute(tenant_db):
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
            executor=lambda _w: ran.__setitem__("n", 1) or {"sent": True},
        )
        assert work.state == WorkState.WAITING_HUMAN
        report = reconcile_organization(db, organization_id=str(_ORG_A))
        assert any(
            i["idempotency_key"] == work.idempotency_key
            for i in report["buckets"]["waiting_human"]
        )
        # resume pass must not execute outbound
        out = bounded_resume_pass(
            db,
            organization_id=str(_ORG_A),
            executors={WORK_OUTBOUND_SEND: lambda _w: ran.__setitem__("n", 99) or {}},
        )
        assert ran["n"] == 0
        assert out["executed"] == 0
    finally:
        db.close()


def test_prohibited_recovery_does_not_execute(tenant_db):
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
            executor=lambda _w: ran.__setitem__("n", 1) or {},
        )
        assert work.state == WorkState.BLOCKED
        bounded_resume_pass(
            db,
            organization_id=str(_ORG_A),
            executors={WORK_HERMES_DEAL_CREATE: lambda _w: ran.__setitem__("n", 99) or {}},
        )
        assert ran["n"] == 0
    finally:
        db.close()


def test_missing_tenant_fails_closed(tenant_db):
    report = reconcile_organization(tenant_db(), organization_id="")
    assert report.get("blocked") is True


def test_cross_tenant_recovery_isolation(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        orchestrate(
            db,
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="scheduler",
            actor="heartbeat",
            executor=lambda _w: {"ok": True},
            target_id=str(_CONTACT_A),
            logical_key="iso",
        )
        report_b = reconcile_organization(db, organization_id=str(_ORG_B))
        assert report_b["counts"]["succeeded"] == 0
        assert report_b["scanned"] == 0 or all(
            i.get("organization_id") == str(_ORG_B)
            for bucket in report_b["buckets"].values()
            for i in bucket
        )
    finally:
        db.close()


def test_pause_blocks_new_mutating_work(tenant_db, monkeypatch):
    monkeypatch.setenv("HEARTBEAT_ENABLED", "0")
    gate = gate_new_mutating_work(organization_id=str(_ORG_A))
    assert gate is not None
    assert gate["blocked_reason"] == "heartbeat_paused"


def test_kill_blocks_execution(tenant_db, monkeypatch):
    monkeypatch.setenv("ACP2_AUTONOMOUS_EXECUTION_ENABLED", "0")
    gate = gate_new_mutating_work(organization_id=str(_ORG_A))
    assert gate is not None
    assert gate["blocked_reason"] == "acp2_autonomous_execution_disabled"


def test_resume_bounded_and_re_evaluates_authority(tenant_db, monkeypatch):
    _seed(tenant_db)
    db = tenant_db()
    try:
        # Create retryable unit via failed transient run
        work = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="scheduler",
            actor="heartbeat",
            target_id=str(_CONTACT_A),
            logical_key="resume-me",
            max_attempts=3,
        )
        assign_executor(work, "heartbeat")
        evaluate_authority(db, work)
        work.detail["treat_as_transient"] = True
        run_work(db, work, lambda _w: (_ for _ in ()).throw(RuntimeError("boom")), transient_failure=True)
        assert work.state == WorkState.RETRYABLE

        calls = {"n": 0}

        def _exec(_w):
            calls["n"] += 1
            return {"ok": True}

        # Authority narrowed: kill before resume → observational only
        monkeypatch.setenv("ACP2_AUTONOMOUS_EXECUTION_ENABLED", "0")
        out = bounded_resume_pass(
            db, organization_id=str(_ORG_A), executors={WORK_LEAD_SCORE: _exec}
        )
        assert calls["n"] == 0
        assert out.get("note") == "observational_only_under_pause_or_kill"

        monkeypatch.setenv("ACP2_AUTONOMOUS_EXECUTION_ENABLED", "1")
        out2 = bounded_resume_pass(
            db, organization_id=str(_ORG_A), executors={WORK_LEAD_SCORE: _exec}
        )
        assert out2["executed"] >= 1 or any(
            r.get("deduplicated") or (r.get("work") or {}).get("state") == "SUCCEEDED"
            for r in out2.get("recovered", [])
        )
    finally:
        db.close()


def test_retry_exhaustion_observable(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        work = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="test",
            actor="heartbeat",
            target_id="exh",
            logical_key="exh",
            max_attempts=1,
        )
        assign_executor(work, "heartbeat")
        evaluate_authority(db, work)
        work.detail["treat_as_transient"] = True
        run_work(db, work, lambda _w: (_ for _ in ()).throw(RuntimeError("x")), transient_failure=True)
        # attempt 1 fails → with max 1 should exhaust (attempt increments then fail)
        # If RETRYABLE, force second failure
        if work.state == WorkState.RETRYABLE:
            from revenue_os.services.acp2_orchestration import retry_work

            retry_work(db, work, lambda _w: (_ for _ in ()).throw(RuntimeError("x")))
        report = reconcile_organization(db, organization_id=str(_ORG_A))
        assert (
            report["counts"]["exhausted"] >= 1
            or work.state == WorkState.EXHAUSTED
        )
    finally:
        db.close()


def test_authority_narrower_on_recovery_wins(tenant_db, monkeypatch):
    _seed(tenant_db)
    db = tenant_db()
    try:
        work = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="test",
            actor="heartbeat",
            target_id=str(_CONTACT_A),
            logical_key="narrow",
        )
        assign_executor(work, "heartbeat")
        evaluate_authority(db, work)
        work.detail["treat_as_transient"] = True
        run_work(db, work, lambda _w: (_ for _ in ()).throw(RuntimeError("t")), transient_failure=True)
        item = {
            "recovery_class": RecoveryClass.RETRYABLE.value,
            "work_kind": WORK_LEAD_SCORE,
            "idempotency_key": work.idempotency_key,
            "target_id": str(_CONTACT_A),
            "actor": "heartbeat",
            "attempt": work.attempt,
            "max_attempts": 3,
        }
        monkeypatch.setenv("ACP1_AUTONOMOUS_ORGANIZATION_IDS", str(_ORG_B))
        result = recover_retryable_unit(
            db,
            organization_id=str(_ORG_A),
            item=item,
            executor=lambda _w: {"ok": True},
        )
        assert result.get("blocked") is True or (
            result.get("work") or {}
        ).get("state") in ("BLOCKED", "CANCELLED")
    finally:
        db.close()


def test_oversight_exposes_gates_and_recovery(tenant_db):
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
        assert "runtime_gates" in summary
        assert "retryable" in summary
        assert "ambiguous_effect" in summary
        assert "requires_founder_action" in summary["counts"]
        gates = runtime_gates()
        assert "new_mutating_work_allowed" in gates
    finally:
        db.close()


def test_scheduler_registers_acp3_reconcile():
    src = (_ROOT / "revenue_os/scheduler.py").read_text()
    assert "acp3_reconcile" in src
    assert "job_acp3_reconcile" in src
    assert "gate_new_mutating_work" in src
    assert "WORK_DEAL_AT_RISK" in src
    assert "WORK_GMAIL_INBOUND" in src
    assert "WORK_METRICS_SNAPSHOT" in src


def test_no_new_persistent_sot():
    for name in (
        "acp3_durable_runtime.py",
        "acp3_reconciliation.py",
        "acp3_runtime_contract.py",
    ):
        src = (_ROOT / "revenue_os/services" / name).read_text()
        assert "Column(" not in src
        assert "alembic" not in src.lower()
        assert "class AgentRun" not in src


def test_celery_not_activated():
    src = (_ROOT / "revenue_os/services/acp3_durable_runtime.py").read_text()
    assert "celery" not in src.lower()
    sched = (_ROOT / "revenue_os/scheduler.py").read_text()
    assert "celery" not in sched.lower()
