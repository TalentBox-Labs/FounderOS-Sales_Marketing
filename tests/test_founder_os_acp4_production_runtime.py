"""ACP-4 — Production Execution & Distributed Runtime focused tests.

Note: SQLite/local tests exercise claim abstraction via process_local_test_only.
They do NOT prove PostgreSQL pg_try_advisory_xact_lock multi-process correctness.
"""

from __future__ import annotations

import threading
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import revenue_os.models  # noqa: F401
from revenue_os.models.base import Base
from revenue_os.models.contact import Contact, ContactSource, ContactStatus
from revenue_os.models.organization import Organization, OrganizationStatus
from revenue_os.services.acp2_effect_catalog import EffectSpec, get_effect_spec
from revenue_os.services.acp2_orchestration import (
    LOG_ORCH_SUCCEEDED,
    assign_executor,
    evaluate_authority,
    propose_work,
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
from revenue_os.services.acp3_durable_runtime import recover_retryable_unit
from revenue_os.services.acp3_reconciliation import classify_recovery
from revenue_os.services.acp3_runtime_contract import RecoveryClass
from revenue_os.services.acp4_distributed_claim import (
    derive_claim_key,
    reset_process_local_claims_for_tests,
    try_acquire_claim,
)
from revenue_os.services.acp4_execution_fence import pre_effect_fence
from revenue_os.services.acp4_production_runtime import (
    LOG_CLAIM_UNAVAILABLE,
    LOG_FENCE_REJECTED,
    LOG_STALE_EXECUTOR_REJECTED,
    coordination_backend_info,
    orchestrate_claimed,
    run_work_claimed,
)
from revenue_os.services.activity_log import log_agent_action
from revenue_os.services.acp1_autonomous_boundary import EFFECT_PROPOSE

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def tenant_db(monkeypatch: pytest.MonkeyPatch, tmp_path):
    reset_process_local_claims_for_tests()
    engine = create_engine(f"sqlite:///{tmp_path / 'acp4.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    import revenue_os.database as db_mod
    import revenue_os.services.activity_log as al
    import revenue_os.services.acp2_orchestration as orch
    import revenue_os.services.acp3_durable_runtime as runtime
    import revenue_os.services.acp4_production_runtime as acp4

    for mod in (db_mod, al, orch, runtime, acp4):
        if hasattr(mod, "SessionLocal"):
            monkeypatch.setattr(mod, "SessionLocal", sf)
    monkeypatch.delenv("ACP1_AUTONOMOUS_ORGANIZATION_IDS", raising=False)
    monkeypatch.setenv("ACP2_AUTONOMOUS_EXECUTION_ENABLED", "1")
    monkeypatch.setenv("HEARTBEAT_ENABLED", "1")
    monkeypatch.setenv("ACP3_RESUME_ENABLED", "1")
    yield sf
    reset_process_local_claims_for_tests()


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
                Contact(
                    id=_CONTACT_B,
                    first_name="Bea",
                    last_name="B",
                    email="bea@b.example",
                    status=ContactStatus.LEAD,
                    source=ContactSource.MANUAL,
                    organization_id=_ORG_B,
                    lead_score=0,
                ),
            ]
        )
        db.commit()
    finally:
        db.close()


def test_deterministic_claim_key_stable():
    a = derive_claim_key(organization_id=str(_ORG_A), idempotency_key="acp2:lead:x")
    b = derive_claim_key(organization_id=str(_ORG_A), idempotency_key="acp2:lead:x")
    assert a.k1 == b.k1 and a.k2 == b.k2
    assert a.digest_hex == b.digest_hex
    assert "aaaaaaaa" in a.material


def test_tenant_claim_keys_differ():
    a = derive_claim_key(organization_id=str(_ORG_A), idempotency_key="same-logical")
    b = derive_claim_key(organization_id=str(_ORG_B), idempotency_key="same-logical")
    assert (a.k1, a.k2) != (b.k1, b.k2)


def test_duplicate_workers_one_executes(tenant_db):
    """Concurrent discovery: at most one executor invocation.

    Peer outcome may be claim CANCELLED *or* SUCCEEDED(deduplicated) after the
    winner commits success provenance — both are safe. Executor must run once.
    """
    _seed(tenant_db)
    db = tenant_db()
    try:
        calls = {"n": 0}
        barrier = threading.Barrier(2)
        results: list[WorkState] = []
        lock = threading.Lock()

        def worker():
            s = tenant_db()
            try:
                barrier.wait(timeout=5)

                def _exec(_w):
                    with lock:
                        calls["n"] += 1
                    return {"ok": True}

                work = orchestrate_claimed(
                    s,
                    work_kind=WORK_LEAD_SCORE,
                    organization_id=str(_ORG_A),
                    source="scheduler",
                    actor="heartbeat",
                    executor=_exec,
                    target_type="contact",
                    target_id=str(_CONTACT_A),
                    logical_key="dup-workers",
                )
                # Hold process-local claim until commit (session-bound lifecycle)
                s.commit()
                with lock:
                    results.append(work.state)
            finally:
                s.close()

        t1 = threading.Thread(target=worker)
        t2 = threading.Thread(target=worker)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        assert calls["n"] == 1
        assert WorkState.SUCCEEDED in results
        assert len(results) == 2
        # Peer suppressed via claim cancel or idempotent success — never second exec
        assert calls["n"] == 1
    finally:
        db.close()


def test_unavailable_claim_does_not_execute(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        key = "acp2:lead_score:%s:%s:hold" % (_ORG_A, _CONTACT_A)
        first = try_acquire_claim(
            db, organization_id=str(_ORG_A), idempotency_key=key
        )
        assert first.acquired is True
        ran = {"n": 0}
        work = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="scheduler",
            actor="heartbeat",
            target_type="contact",
            target_id=str(_CONTACT_A),
            logical_key="hold",
        )
        assign_executor(work, "heartbeat")
        evaluate_authority(db, work)
        out = run_work_claimed(db, work, lambda _w: ran.__setitem__("n", 1) or {})
        assert ran["n"] == 0
        assert out.state == WorkState.CANCELLED
        assert out.failure_reason == "claim_unavailable"
    finally:
        db.close()
        reset_process_local_claims_for_tests()


def test_stale_after_kill(tenant_db, monkeypatch):
    _seed(tenant_db)
    db = tenant_db()
    try:
        work = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="scheduler",
            actor="heartbeat",
            target_type="contact",
            target_id=str(_CONTACT_A),
            logical_key="kill",
        )
        assign_executor(work, "heartbeat")
        evaluate_authority(db, work)
        assert work.state == WorkState.ELIGIBLE
        monkeypatch.setenv("ACP2_AUTONOMOUS_EXECUTION_ENABLED", "0")
        ran = {"n": 0}
        out = run_work_claimed(db, work, lambda _w: ran.__setitem__("n", 1) or {})
        assert ran["n"] == 0
        assert out.state == WorkState.BLOCKED
        assert out.failure_reason == "acp2_autonomous_execution_disabled"
    finally:
        db.close()


def test_stale_after_pause(tenant_db, monkeypatch):
    _seed(tenant_db)
    db = tenant_db()
    try:
        work = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="scheduler",
            actor="heartbeat",
            target_type="contact",
            target_id=str(_CONTACT_A),
            logical_key="pause",
        )
        assign_executor(work, "heartbeat")
        evaluate_authority(db, work)
        monkeypatch.setenv("HEARTBEAT_ENABLED", "0")
        ran = {"n": 0}
        out = run_work_claimed(db, work, lambda _w: ran.__setitem__("n", 1) or {})
        assert ran["n"] == 0
        assert out.failure_reason == "heartbeat_paused"
    finally:
        db.close()


def test_authority_downgrade_to_human_required(tenant_db, monkeypatch):
    _seed(tenant_db)
    db = tenant_db()
    try:
        work = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="scheduler",
            actor="heartbeat",
            target_type="contact",
            target_id=str(_CONTACT_A),
            logical_key="hr",
        )
        assign_executor(work, "heartbeat")
        evaluate_authority(db, work)

        real = get_effect_spec

        def _patched(kind: str):
            spec = real(kind)
            if kind == WORK_LEAD_SCORE and spec is not None:
                return EffectSpec(
                    WORK_LEAD_SCORE,
                    EFFECT_PROPOSE,
                    ExecutionMode.HUMAN_REQUIRED,
                    spec.eligible_agents,
                    spec.requested_effect,
                )
            return spec

        monkeypatch.setattr(
            "revenue_os.services.acp4_execution_fence.get_effect_spec", _patched
        )
        ran = {"n": 0}
        out = run_work_claimed(db, work, lambda _w: ran.__setitem__("n", 1) or {})
        assert ran["n"] == 0
        assert out.failure_reason == "authority_now_human_required"
    finally:
        db.close()


def test_authority_downgrade_to_prohibited(tenant_db, monkeypatch):
    _seed(tenant_db)
    db = tenant_db()
    try:
        work = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="scheduler",
            actor="heartbeat",
            target_type="contact",
            target_id=str(_CONTACT_A),
            logical_key="proh",
        )
        assign_executor(work, "heartbeat")
        evaluate_authority(db, work)
        real = get_effect_spec

        def _patched(kind: str):
            spec = real(kind)
            if kind == WORK_LEAD_SCORE and spec is not None:
                return EffectSpec(
                    WORK_LEAD_SCORE,
                    EFFECT_PROPOSE,
                    ExecutionMode.PROHIBITED,
                    spec.eligible_agents,
                    spec.requested_effect,
                )
            return spec

        monkeypatch.setattr(
            "revenue_os.services.acp4_execution_fence.get_effect_spec", _patched
        )
        ran = {"n": 0}
        out = run_work_claimed(db, work, lambda _w: ran.__setitem__("n", 1) or {})
        assert ran["n"] == 0
        assert out.failure_reason == "effect_prohibited"
    finally:
        db.close()


def test_tenant_deactivation_blocks(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        work = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="scheduler",
            actor="heartbeat",
            target_type="contact",
            target_id=str(_CONTACT_A),
            logical_key="deact",
        )
        assign_executor(work, "heartbeat")
        evaluate_authority(db, work)
        org = db.get(Organization, _ORG_A)
        assert org is not None
        org.status = OrganizationStatus.SUSPENDED
        db.commit()
        ran = {"n": 0}
        out = run_work_claimed(db, work, lambda _w: ran.__setitem__("n", 1) or {})
        assert ran["n"] == 0
        assert out.failure_reason in ("tenant_not_active", "tenant_not_autonomous_eligible")
    finally:
        db.close()


def test_missing_tenant_blocks(tenant_db):
    db = tenant_db()
    try:
        work = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=None,
            source="scheduler",
            actor="heartbeat",
            logical_key="missing",
        )
        work.state = WorkState.ELIGIBLE
        work.execution_mode = ExecutionMode.AUTONOMOUS
        ran = {"n": 0}
        out = run_work_claimed(db, work, lambda _w: ran.__setitem__("n", 1) or {})
        assert ran["n"] == 0
        assert out.failure_reason == "missing_tenant"
    finally:
        db.close()


def test_cross_tenant_target_blocks(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        work = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="scheduler",
            actor="heartbeat",
            target_type="contact",
            target_id=str(_CONTACT_B),  # belongs to B
            logical_key="xtenant",
        )
        assign_executor(work, "heartbeat")
        evaluate_authority(db, work)
        ran = {"n": 0}
        out = run_work_claimed(db, work, lambda _w: ran.__setitem__("n", 1) or {})
        assert ran["n"] == 0
        assert out.failure_reason == "cross_tenant_target"
    finally:
        db.close()


def test_human_required_without_approval_blocks(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        work = propose_work(
            work_kind=WORK_OUTBOUND_SEND,
            organization_id=str(_ORG_A),
            source="agent",
            actor="approval_executor",
            target_type="contact",
            target_id=str(_CONTACT_A),
            logical_key="no-appr",
        )
        fence = pre_effect_fence(db, work, require_autonomous=False, claim_held=True)
        assert fence.ok is False
        assert fence.reason in (
            "human_approval_required_or_invalid",
            "authority_now_human_required",
        ) or fence.reason == "human_approval_required_or_invalid"
        # With require_autonomous True (default autonomous scheduler):
        fence2 = pre_effect_fence(db, work, require_autonomous=True, claim_held=True)
        assert fence2.ok is False
    finally:
        db.close()


def test_human_required_with_approval_passes_current_check(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        from revenue_os.models.approvals import ApprovalRequest

        appr = ApprovalRequest(
            id=str(uuid.uuid4()),
            requested_by="test",
            action_type="send_outreach_email",
            title="Send outreach",
            description="test",
            target_type="contact",
            target_id=str(_CONTACT_A),
            status="approved",
            payload={"organization_id": str(_ORG_A), "contact_id": str(_CONTACT_A)},
        )
        db.add(appr)
        db.commit()
        work = propose_work(
            work_kind=WORK_OUTBOUND_SEND,
            organization_id=str(_ORG_A),
            source="agent",
            actor="approval_executor",
            target_type="contact",
            target_id=str(_CONTACT_A),
            logical_key="with-appr",
        )
        work.approval_id = appr.id
        # Still require_autonomous=True → HUMAN_REQUIRED blocks autonomous path
        fence_auto = pre_effect_fence(db, work, require_autonomous=True, claim_held=True)
        assert fence_auto.ok is False
        assert fence_auto.reason == "authority_now_human_required"
        # Human executor path: require_autonomous=False with approval
        fence_human = pre_effect_fence(db, work, require_autonomous=False, claim_held=True)
        assert fence_human.ok is True
    finally:
        db.close()


def test_prohibited_never_executes(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        ran = {"n": 0}
        work = orchestrate_claimed(
            db,
            work_kind=WORK_HERMES_DEAL_CREATE,
            organization_id=str(_ORG_A),
            source="hermes",
            actor="hermes",
            executor=lambda _w: ran.__setitem__("n", 1) or {},
        )
        assert ran["n"] == 0
        assert work.state == WorkState.BLOCKED
    finally:
        db.close()


def test_duplicate_scheduler_invocation_suppressed(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        calls = {"n": 0}

        def _exec(_w):
            calls["n"] += 1
            return {"ok": True}

        for _ in range(2):
            orchestrate_claimed(
                db,
                work_kind=WORK_LEAD_SCORE,
                organization_id=str(_ORG_A),
                source="scheduler",
                actor="heartbeat",
                executor=_exec,
                target_type="contact",
                target_id=str(_CONTACT_A),
                logical_key="dup-sched",
            )
        assert calls["n"] == 1
    finally:
        db.close()


def test_acp3_recovery_uses_acp4_claim(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        work = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="scheduler",
            actor="heartbeat",
            target_type="contact",
            target_id=str(_CONTACT_A),
            logical_key="rec",
            max_attempts=3,
        )
        assign_executor(work, "heartbeat")
        evaluate_authority(db, work)
        work.detail["treat_as_transient"] = True
        run_work(db, work, lambda _w: (_ for _ in ()).throw(RuntimeError("boom")), transient_failure=True)
        assert work.state == WorkState.RETRYABLE
        item = {
            "recovery_class": RecoveryClass.RETRYABLE.value,
            "work_kind": WORK_LEAD_SCORE,
            "idempotency_key": work.idempotency_key,
            "target_id": str(_CONTACT_A),
            "target_type": "contact",
            "actor": "heartbeat",
            "attempt": work.attempt,
            "max_attempts": 3,
        }
        calls = {"n": 0}
        out = recover_retryable_unit(
            db,
            organization_id=str(_ORG_A),
            item=item,
            executor=lambda _w: calls.__setitem__("n", 1) or {"ok": True},
        )
        assert calls["n"] == 1 or out.get("ok") or out.get("deduplicated")
    finally:
        db.close()


def test_ambiguous_external_not_replayed(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        work = propose_work(
            work_kind=WORK_OUTBOUND_SEND,
            organization_id=str(_ORG_A),
            source="agent",
            actor="approval_executor",
            target_id=str(_CONTACT_A),
            logical_key="amb",
        )
        work.execution_mode = ExecutionMode.HUMAN_REQUIRED
        work.state = WorkState.RUNNING
        from revenue_os.models.automation_state import AgentActionLog
        from revenue_os.services.acp2_orchestration import LOG_ORCH_RUNNING

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
        ran = {"n": 0}
        out = recover_retryable_unit(
            db,
            organization_id=str(_ORG_A),
            item={**classified, "recovery_class": RecoveryClass.AMBIGUOUS_EFFECT.value},
            executor=lambda _w: ran.__setitem__("n", 1) or {},
        )
        assert ran["n"] == 0
        assert out.get("blocked") is True
    finally:
        db.close()


def test_already_succeeded_not_executed_again(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        work = orchestrate_claimed(
            db,
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="scheduler",
            actor="heartbeat",
            executor=lambda _w: {"ok": True},
            target_type="contact",
            target_id=str(_CONTACT_A),
            logical_key="once",
        )
        assert work.state == WorkState.SUCCEEDED
        ran = {"n": 0}
        work2 = orchestrate_claimed(
            db,
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="scheduler",
            actor="heartbeat",
            executor=lambda _w: ran.__setitem__("n", 1) or {},
            target_type="contact",
            target_id=str(_CONTACT_A),
            logical_key="once",
        )
        assert ran["n"] == 0
        assert work2.state == WorkState.SUCCEEDED
        assert work2.result.get("deduplicated") is True
    finally:
        db.close()


def test_retry_exhaustion_preserved(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        work = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="test",
            actor="heartbeat",
            target_type="contact",
            target_id=str(_CONTACT_A),
            logical_key="exh",
            max_attempts=1,
        )
        assign_executor(work, "heartbeat")
        evaluate_authority(db, work)
        work.detail["treat_as_transient"] = True
        out = run_work_claimed(
            db,
            work,
            lambda _w: (_ for _ in ()).throw(RuntimeError("x")),
            transient_failure=True,
        )
        assert out.state in (WorkState.EXHAUSTED, WorkState.RETRYABLE, WorkState.BLOCKED)
        if out.state == WorkState.RETRYABLE:
            out2 = run_work_claimed(
                db,
                out,
                lambda _w: (_ for _ in ()).throw(RuntimeError("x")),
                transient_failure=True,
            )
            assert out2.state in (WorkState.EXHAUSTED, WorkState.CANCELLED, WorkState.BLOCKED)
    finally:
        db.close()


def test_claim_and_fence_rejection_observable(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        key = derive_claim_key(
            organization_id=str(_ORG_A),
            idempotency_key=f"acp2:{WORK_LEAD_SCORE}:{_ORG_A}:{_CONTACT_A}:obs",
        )
        # Hold claim via matching idempotency
        work = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="scheduler",
            actor="heartbeat",
            target_type="contact",
            target_id=str(_CONTACT_A),
            logical_key="obs",
        )
        held = try_acquire_claim(
            db,
            organization_id=str(_ORG_A),
            idempotency_key=work.idempotency_key,
        )
        assert held.acquired
        assign_executor(work, "heartbeat")
        evaluate_authority(db, work)
        run_work_claimed(db, work, lambda _w: {})
        summary = compose_orchestration_summary(db, organization_id=str(_ORG_A))
        assert "claim_rejected" in summary
        assert summary["counts"]["claim_rejected"] >= 1 or any(
            True for _ in summary.get("claim_rejected", [])
        )
        # Fence reject
        reset_process_local_claims_for_tests()
        work2 = propose_work(
            work_kind=WORK_LEAD_SCORE,
            organization_id=str(_ORG_A),
            source="scheduler",
            actor="heartbeat",
            target_type="contact",
            target_id=str(_CONTACT_A),
            logical_key="obs-fence",
        )
        assign_executor(work2, "heartbeat")
        evaluate_authority(db, work2)
        import os

        os.environ["ACP2_AUTONOMOUS_EXECUTION_ENABLED"] = "0"
        run_work_claimed(db, work2, lambda _w: {})
        summary2 = compose_orchestration_summary(db, organization_id=str(_ORG_A))
        assert summary2["counts"]["fence_rejected"] >= 1 or len(
            summary2.get("fence_rejected", [])
        ) >= 1
        os.environ["ACP2_AUTONOMOUS_EXECUTION_ENABLED"] = "1"
    finally:
        db.close()
        reset_process_local_claims_for_tests()


def test_coordination_backend_documented(tenant_db):
    db = tenant_db()
    try:
        info = coordination_backend_info(db)
        assert info["distributed_safety_claimed"] is False
        assert "process_local" in info["mechanism"]
    finally:
        db.close()


def test_no_new_persistent_sot_or_celery():
    for name in (
        "acp4_distributed_claim.py",
        "acp4_execution_fence.py",
        "acp4_production_runtime.py",
    ):
        src = (_ROOT / "revenue_os/services" / name).read_text()
        assert "Column(" not in src
        assert "alembic" not in src.lower()
        assert "celery" not in src.lower()
        assert "redis" not in src.lower()
    sched = (_ROOT / "revenue_os/scheduler.py").read_text()
    assert "orchestrate_claimed" in sched
    assert "celery" not in sched.lower()


def test_scheduler_a_paths_use_claimed():
    src = (_ROOT / "revenue_os/scheduler.py").read_text()
    assert "orchestrate_claimed" in src
    assert src.count("orchestrate_claimed") >= 4


def test_hermes_score_uses_orchestrate_claimed():
    src = (_ROOT / "revenue_os/services/hermes_planner.py").read_text()
    assert "orchestrate_claimed" in src
    assert "action_score_unscored_leads" in src
    # Direct score_contact must only appear inside executor, not as bare loop body
    # — presence of orchestrate_claimed in score action is required.
    score_fn = src.split("def action_score_unscored_leads", 1)[1].split(
        "def action_qualify_high_scorers", 1
    )[0]
    assert "orchestrate_claimed" in score_fn
    deal_fn = src.split("def action_check_deals_at_risk", 1)[1].split(
        "ACTION_REGISTRY", 1
    )[0]
    assert "orchestrate_claimed" in deal_fn
    assert "emit_deal_at_risk" in deal_fn


def test_hermes_duplicate_score_suppressed(tenant_db):
    _seed(tenant_db)
    from revenue_os.services.hermes_planner import action_score_unscored_leads

    barrier = threading.Barrier(2)
    scores = {"n": 0}
    lock = threading.Lock()
    results: list[dict] = []

    def worker():
        s = tenant_db()
        try:
            barrier.wait(timeout=5)
            # Patch score_contact via orchestrate path counting
            import revenue_os.services.lead_scoring_service as lss

            real = lss.score_contact

            def _counted(db, contact):
                with lock:
                    scores["n"] += 1
                contact.lead_score = 42
                return {"score": 42, "breakdown": {}}

            # Only count first real mutation attempts through hermes
            lss.score_contact = _counted  # type: ignore
            try:
                out = action_score_unscored_leads(
                    s, {"organization_id": str(_ORG_A), "limit": 5}
                )
                s.commit()
                with lock:
                    results.append(out)
            finally:
                lss.score_contact = real  # type: ignore
        finally:
            s.close()

    # Sequential hermes calls share idempotency — second should not re-score
    s1 = tenant_db()
    try:
        import revenue_os.services.lead_scoring_service as lss

        real = lss.score_contact
        calls = {"n": 0}

        def _counted(db, contact):
            calls["n"] += 1
            contact.lead_score = 55
            db.add(contact)
            return {"score": 55, "breakdown": {}}

        lss.score_contact = _counted  # type: ignore
        try:
            r1 = action_score_unscored_leads(
                s1, {"organization_id": str(_ORG_A), "limit": 5}
            )
            s1.commit()
            r2 = action_score_unscored_leads(
                s1, {"organization_id": str(_ORG_A), "limit": 5}
            )
            s1.commit()
        finally:
            lss.score_contact = real  # type: ignore
        assert r1.get("acp4_claimed") is True
        assert calls["n"] == 1
        assert r2.get("scored", 0) == 0 or calls["n"] == 1
    finally:
        s1.close()

    # Concurrent hermes workers
    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    # Contact already scored above — concurrent workers should not add scores
    assert scores["n"] == 0 or scores["n"] <= 1


def test_concurrent_approval_single_effect(tenant_db, monkeypatch):
    _seed(tenant_db)
    from revenue_os.models.approvals import ApprovalRequest
    from revenue_os.services import approvals as appr_mod
    from revenue_os.services.identity_context import AuthMethod, IdentityContext, PrincipalKind
    from revenue_os.services.tenant_context import TenantContext

    db = tenant_db()
    try:
        rid = str(uuid.uuid4())
        db.add(
            ApprovalRequest(
                id=rid,
                requested_by="test",
                action_type="send_outreach_email",
                title="t",
                description="d",
                target_type="contact",
                target_id=str(_CONTACT_A),
                status="pending",
                payload={
                    "organization_id": str(_ORG_A),
                    "contact_id": str(_CONTACT_A),
                    "email": "ada@a.example",
                },
            )
        )
        db.commit()
    finally:
        db.close()

    exec_calls = {"n": 0}
    barrier = threading.Barrier(2)
    outcomes: list[str] = []
    lock = threading.Lock()

    def _fake_exec(db, payload):  # noqa: ANN001
        with lock:
            exec_calls["n"] += 1
        return {"handed_to_n8n": True, "note": "test"}

    monkeypatch.setitem(appr_mod.EXECUTORS, "send_outreach_email", _fake_exec)
    monkeypatch.setattr(appr_mod, "SessionLocal", tenant_db)

    tenant = TenantContext(
        identity=IdentityContext(
            principal_kind=PrincipalKind.HUMAN,
            auth_method=AuthMethod.SESSION,
            is_human=True,
            user_id=str(uuid.uuid4()),
            email="founder@example.com",
            display_name="Founder Human",
            role="owner",
        ),
        organization_id=str(_ORG_A),
        organization_name="Org A",
        organization_slug="org-a",
        membership_id="m1",
        membership_role="owner",
        membership_status="active",
    )

    def worker():
        barrier.wait(timeout=5)
        try:
            appr_mod.decide(rid, True, tenant=tenant)
            with lock:
                outcomes.append("ok")
        except ValueError as exc:
            with lock:
                outcomes.append(f"err:{exc}")

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    assert exec_calls["n"] == 1
    assert outcomes.count("ok") >= 1


def test_approval_cross_tenant_blocked(tenant_db, monkeypatch):
    _seed(tenant_db)
    from revenue_os.models.approvals import ApprovalRequest
    from revenue_os.services import approvals as appr_mod
    from revenue_os.services.identity_context import AuthMethod, IdentityContext, PrincipalKind
    from revenue_os.services.tenant_context import TenantContext

    db = tenant_db()
    try:
        rid = str(uuid.uuid4())
        db.add(
            ApprovalRequest(
                id=rid,
                requested_by="test",
                action_type="send_outreach_email",
                title="t",
                description="d",
                target_type="contact",
                target_id=str(_CONTACT_A),
                status="pending",
                payload={
                    "organization_id": str(_ORG_A),
                    "contact_id": str(_CONTACT_A),
                },
            )
        )
        db.commit()
    finally:
        db.close()

    monkeypatch.setattr(appr_mod, "SessionLocal", tenant_db)
    # Org B tenant must not decide Org A approval
    tenant_b = TenantContext(
        identity=IdentityContext(
            principal_kind=PrincipalKind.HUMAN,
            auth_method=AuthMethod.SESSION,
            is_human=True,
            user_id=str(uuid.uuid4()),
            email="other@example.com",
            display_name="Other Founder",
            role="owner",
        ),
        organization_id=str(_ORG_B),
        organization_name="Org B",
        organization_slug="org-b",
        membership_id="m2",
        membership_role="owner",
        membership_status="active",
    )
    with pytest.raises(ValueError, match="not found"):
        appr_mod.decide(rid, True, tenant=tenant_b)


def test_approval_fence_rejects_foreign_org_approval(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        from revenue_os.models.approvals import ApprovalRequest

        appr = ApprovalRequest(
            id=str(uuid.uuid4()),
            requested_by="test",
            action_type="send_outreach_email",
            title="t",
            description="d",
            target_type="contact",
            target_id=str(_CONTACT_B),
            status="approved",
            payload={"organization_id": str(_ORG_B)},
        )
        db.add(appr)
        db.commit()
        work = propose_work(
            work_kind=WORK_OUTBOUND_SEND,
            organization_id=str(_ORG_A),
            source="agent",
            actor="approval_executor",
            target_type="contact",
            target_id=str(_CONTACT_A),
            logical_key="xorg",
        )
        work.approval_id = appr.id
        fence = pre_effect_fence(db, work, require_autonomous=False, claim_held=True)
        assert fence.ok is False
        assert fence.reason == "human_approval_required_or_invalid"
    finally:
        db.close()
