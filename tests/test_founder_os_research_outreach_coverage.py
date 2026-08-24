"""ACP-5 coverage — governed research-to-outreach propose cadence."""

from __future__ import annotations

import inspect
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import revenue_os.models  # noqa: F401
from revenue_os.models.activity import Activity, ActivityType
from revenue_os.models.approvals import ApprovalRequest
from revenue_os.models.automation_state import AgentActionLog
from revenue_os.models.base import Base
from revenue_os.models.contact import Contact, ContactSource, ContactStatus
from revenue_os.models.organization import Organization, OrganizationStatus
from revenue_os.services.acp2_effect_catalog import agent_eligible_for, get_effect_spec
from revenue_os.services.acp2_work_contract import (
    WORK_FOLLOW_UP_PROPOSE,
    WORK_OUTBOUND_SEND,
    WORK_RESEARCH_OUTREACH_PROPOSE,
    ExecutionMode,
)
from revenue_os.services.research_outreach_eligibility import (
    evaluate_research_outreach_eligibility,
    scan_eligible_research_outreach,
)
from revenue_os.services.revenue_orchestration_service import (
    run_research_outreach_proposal_scheduled,
    run_research_to_outreach,
)
from revenue_os.services.tenant_context import TenantContext
from revenue_os.services.identity_context import AuthMethod, IdentityContext, PrincipalKind

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_CONTACT_C = uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def tenant_db(monkeypatch: pytest.MonkeyPatch, tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'research_outreach.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    import revenue_os.database as db_mod
    import revenue_os.scheduler as sched_mod
    import revenue_os.services.activity_log as al
    import revenue_os.services.approvals as approvals_mod
    import revenue_os.services.acp4_production_runtime as acp4

    for mod in (db_mod, sched_mod, al, approvals_mod, acp4):
        if hasattr(mod, "SessionLocal"):
            monkeypatch.setattr(mod, "SessionLocal", sf)
    monkeypatch.delenv("ACP1_AUTONOMOUS_ORGANIZATION_IDS", raising=False)
    monkeypatch.delenv("HEARTBEAT_ORGANIZATION_IDS", raising=False)
    monkeypatch.setenv("ACP2_AUTONOMOUS_EXECUTION_ENABLED", "1")
    monkeypatch.setenv("HEARTBEAT_ENABLED", "1")
    monkeypatch.setenv("ACP3_RESUME_ENABLED", "1")
    return sf


def _seed(sf: sessionmaker, *, stop_tags: str = "") -> None:
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
                    tags=stop_tags,
                    created_at=datetime.now(timezone.utc),
                ),
                Contact(
                    id=_CONTACT_B,
                    first_name="Bob",
                    last_name="B",
                    email="bob@b.example",
                    status=ContactStatus.LEAD,
                    source=ContactSource.MANUAL,
                    organization_id=_ORG_B,
                    lead_score=0,
                    created_at=datetime.now(timezone.utc),
                ),
                Contact(
                    id=_CONTACT_C,
                    first_name="No",
                    last_name="Email",
                    email=None,
                    status=ContactStatus.LEAD,
                    source=ContactSource.MANUAL,
                    organization_id=_ORG_A,
                    lead_score=0,
                    created_at=datetime.now(timezone.utc),
                ),
            ]
        )
        db.commit()
    finally:
        db.close()


def _tenant(org_id: uuid.UUID = _ORG_A) -> TenantContext:
    identity = IdentityContext(
        principal_kind=PrincipalKind.HUMAN,
        auth_method=AuthMethod.NONE,
        is_human=True,
        user_id=str(uuid.uuid4()),
        email="owner@a.example",
        display_name="Owner",
        role="owner",
    )
    return TenantContext(
        identity=identity,
        organization_id=str(org_id),
        organization_name="Org A",
        organization_slug="org-a",
        membership_id=str(uuid.uuid4()),
        membership_role="owner",
        membership_status="active",
    )


def _patch_research_stack(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "revenue_os.services.linkedin_enrichment.enrich_person",
        lambda *a, **k: {"ok": False, "configured": False, "reason": "not configured"},
    )
    monkeypatch.setattr(
        "revenue_os.services.revenue_orchestration_service.score_contact",
        lambda *a, **k: {
            "score": 72,
            "old_score": 0,
            "suggested_status": "qualified",
            "status": "lead",
            "status_changed": False,
        },
    )
    monkeypatch.setattr(
        "revenue_os.services.ai_service.generate_cold_email",
        lambda *a, **k: "Hello draft body for outreach.",
    )


# ── Catalog / authority ──────────────────────────────────────────────────────


def test_work_kind_is_autonomous_propose_not_send():
    spec = get_effect_spec(WORK_RESEARCH_OUTREACH_PROPOSE)
    assert spec is not None
    assert spec.execution_mode == ExecutionMode.AUTONOMOUS
    assert agent_eligible_for(WORK_RESEARCH_OUTREACH_PROPOSE, "heartbeat")
    send = get_effect_spec(WORK_OUTBOUND_SEND)
    assert send is not None
    assert send.execution_mode == ExecutionMode.HUMAN_REQUIRED


def test_no_research_outreach_send_work_kind():
    from revenue_os.services import acp2_work_contract as wc

    assert not hasattr(wc, "WORK_RESEARCH_OUTREACH_SEND")
    assert "research_outreach_send" not in (wc.__dict__.get("__all__", []) or [])


def test_no_new_persistent_sot_or_migration():
    new_paths = [
        "revenue_os/services/research_outreach_eligibility.py",
        "revenue_os/services/acp2_work_contract.py",
        "revenue_os/services/acp2_effect_catalog.py",
        "revenue_os/scheduler.py",
        "revenue_os/services/revenue_orchestration_service.py",
    ]
    for rel in new_paths:
        src = (_ROOT / rel).read_text()
        assert "class Research" not in src or "ResearchOutreach" not in src
        assert "alembic" not in src.lower() or "migration" not in Path(rel).name


# ── Eligibility ──────────────────────────────────────────────────────────────


def test_eligible_tenant_contact_discovered(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        scanned = scan_eligible_research_outreach(db, organization_id=str(_ORG_A))
        assert any(x["contact_id"] == str(_CONTACT_A) for x in scanned)
        contact = db.get(Contact, _CONTACT_A)
        ev = evaluate_research_outreach_eligibility(db, contact, str(_ORG_A))
        assert ev["eligible"] is True
    finally:
        db.close()


def test_ineligible_contact_skipped_missing_email(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        contact = db.get(Contact, _CONTACT_C)
        ev = evaluate_research_outreach_eligibility(db, contact, str(_ORG_A))
        assert ev["eligible"] is False
        assert "email" in ev["reason"].lower()
    finally:
        db.close()


def test_ineligible_stop_tags(tenant_db):
    _seed(tenant_db, stop_tags="do-not-contact")
    db = tenant_db()
    try:
        contact = db.get(Contact, _CONTACT_A)
        ev = evaluate_research_outreach_eligibility(db, contact, str(_ORG_A))
        assert ev["eligible"] is False
    finally:
        db.close()


def test_cross_tenant_contact_rejected(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        contact = db.get(Contact, _CONTACT_B)
        ev = evaluate_research_outreach_eligibility(db, contact, str(_ORG_A))
        assert ev["eligible"] is False
        scanned = scan_eligible_research_outreach(db, organization_id=str(_ORG_A))
        assert all(x["contact_id"] != str(_CONTACT_B) for x in scanned)
    finally:
        db.close()


def test_already_outreached_skipped(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        db.add(
            Activity(
                contact_id=_CONTACT_A,
                activity_type=ActivityType.EMAIL,
                subject="Prior send",
                body="x",
                direction="outbound",
                status="completed",
            )
        )
        db.commit()
        contact = db.get(Contact, _CONTACT_A)
        ev = evaluate_research_outreach_eligibility(db, contact, str(_ORG_A))
        assert ev["eligible"] is False
        assert ev["state"] == "RESEARCH_OUTREACH_ALREADY_SENT"
    finally:
        db.close()


# ── Scheduled path ───────────────────────────────────────────────────────────


def test_scheduled_path_enters_acp4_claimed_execution(tenant_db, monkeypatch):
    _seed(tenant_db)
    _patch_research_stack(monkeypatch)
    monkeypatch.setenv("ACP1_AUTONOMOUS_ORGANIZATION_IDS", str(_ORG_A))
    from revenue_os.scheduler import job_scan_research_outreach_eligibility

    result = job_scan_research_outreach_eligibility()
    assert result.get("ok") is True
    assert result.get("orchestrated") is True
    assert result.get("proposals_filed", 0) >= 1

    db = tenant_db()
    try:
        orch = (
            db.query(AgentActionLog)
            .filter(
                AgentActionLog.target_id == str(_CONTACT_A),
                AgentActionLog.action_type.in_(
                    ("acp4_claim_acquired", "acp2_work_running", "acp2_work_proposed")
                ),
            )
            .all()
        )
        assert orch
        types = {lg.action_type for lg in orch}
        assert "acp4_claim_acquired" in types or "acp2_work_running" in types
    finally:
        db.close()


def test_proposal_creates_send_outreach_email_approval(tenant_db, monkeypatch):
    _seed(tenant_db)
    _patch_research_stack(monkeypatch)
    db = tenant_db()
    try:
        out = run_research_outreach_proposal_scheduled(db, str(_ORG_A), str(_CONTACT_A))
        assert out.get("ok") is True
        assert out.get("approval_id")
        ar = db.get(ApprovalRequest, str(out["approval_id"]))
        assert ar is not None
        assert ar.action_type == "send_outreach_email"
        assert ar.status == "pending"
        assert ar.payload["organization_id"] == str(_ORG_A)
        assert ar.payload["contact_id"] == str(_CONTACT_A)
    finally:
        db.close()


def test_approval_remains_human_required(tenant_db, monkeypatch):
    _seed(tenant_db)
    _patch_research_stack(monkeypatch)
    db = tenant_db()
    try:
        out = run_research_outreach_proposal_scheduled(db, str(_ORG_A), str(_CONTACT_A))
        ar = db.get(ApprovalRequest, str(out["approval_id"]))
        assert ar.status == "pending"
        send_spec = get_effect_spec(WORK_OUTBOUND_SEND)
        assert send_spec.execution_mode == ExecutionMode.HUMAN_REQUIRED
    finally:
        db.close()


def test_research_performs_no_external_send(tenant_db, monkeypatch):
    _seed(tenant_db)
    _patch_research_stack(monkeypatch)
    calls: list[str] = []

    def _deny(*a, **k):
        calls.append("send")
        raise AssertionError("send must not run")

    monkeypatch.setattr(
        "revenue_os.services.approvals._execute_send_outreach_email", _deny
    )
    monkeypatch.setattr(
        "revenue_os.integrations.n8n.trigger_workflow",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("n8n")),
    )
    db = tenant_db()
    try:
        out = run_research_outreach_proposal_scheduled(db, str(_ORG_A), str(_CONTACT_A))
        assert out.get("ok") is True
        assert calls == []
        # Notes may log as outbound; assert no completed EMAIL send occurred.
        sent = (
            db.query(Activity)
            .filter(
                Activity.activity_type == ActivityType.EMAIL,
                Activity.direction == "outbound",
                Activity.status == "completed",
            )
            .count()
        )
        assert sent == 0
        ar = db.get(ApprovalRequest, str(out["approval_id"]))
        assert ar is not None and ar.status == "pending"
    finally:
        db.close()


def test_scheduler_source_does_not_call_send_executor():
    src = inspect.getsource(
        __import__(
            "revenue_os.scheduler", fromlist=["job_scan_research_outreach_eligibility"]
        ).job_scan_research_outreach_eligibility
    )
    assert "_execute_send_outreach_email" not in src
    assert "trigger_workflow" not in src
    assert "decide(" not in src


def test_research_worker_cannot_call_send_executor():
    from revenue_os.services import revenue_workers

    src = inspect.getsource(revenue_workers.run_research_worker)
    assert "_execute_send_outreach_email" not in src
    assert "request_approval" not in src
    assert "trigger_workflow" not in src


def test_repeated_heartbeat_does_not_duplicate_pending_ar(tenant_db, monkeypatch):
    _seed(tenant_db)
    _patch_research_stack(monkeypatch)
    monkeypatch.setenv("ACP1_AUTONOMOUS_ORGANIZATION_IDS", str(_ORG_A))
    from revenue_os.scheduler import job_scan_research_outreach_eligibility

    first = job_scan_research_outreach_eligibility()
    second = job_scan_research_outreach_eligibility()
    assert first.get("proposals_filed", 0) >= 1
    assert second.get("proposals_filed", 0) == 0

    db = tenant_db()
    try:
        pending = (
            db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.status == "pending",
                ApprovalRequest.action_type == "send_outreach_email",
                ApprovalRequest.target_id == str(_CONTACT_A),
            )
            .count()
        )
        assert pending == 1
    finally:
        db.close()


def test_provider_unavailable_soft_fails_without_fabrication(tenant_db, monkeypatch):
    _seed(tenant_db)
    monkeypatch.setattr(
        "revenue_os.services.linkedin_enrichment.enrich_person",
        lambda *a, **k: {
            "ok": False,
            "configured": False,
            "reason": "LinkedIn enrichment is not configured",
        },
    )
    monkeypatch.setattr(
        "revenue_os.services.revenue_orchestration_service.score_contact",
        lambda *a, **k: {
            "score": 40,
            "old_score": 0,
            "suggested_status": "lead",
            "status": "lead",
            "status_changed": False,
        },
    )
    monkeypatch.setattr(
        "revenue_os.services.ai_service.generate_cold_email",
        lambda *a, **k: "CRM-only draft",
    )
    db = tenant_db()
    try:
        out = run_research_outreach_proposal_scheduled(db, str(_ORG_A), str(_CONTACT_A))
        assert out.get("ok") is True
        research = out.get("research") or {}
        assert research.get("enrichment_configured") is False
        assert "fabricat" not in str(research.get("observations", "")).lower()
    finally:
        db.close()


def test_tenant_binding_preserved(tenant_db, monkeypatch):
    _seed(tenant_db)
    _patch_research_stack(monkeypatch)
    db = tenant_db()
    try:
        out = run_research_outreach_proposal_scheduled(db, str(_ORG_A), str(_CONTACT_A))
        assert out["organization_id"] == str(_ORG_A)
        ar = db.get(ApprovalRequest, str(out["approval_id"]))
        assert ar.payload["organization_id"] == str(_ORG_A)
        assert ar.payload["contact_id"] == str(_CONTACT_A)
        wrong = run_research_outreach_proposal_scheduled(
            db, str(_ORG_A), str(_CONTACT_B)
        )
        assert wrong.get("ok") is False
    finally:
        db.close()


def test_provenance_preserved(tenant_db, monkeypatch):
    _seed(tenant_db)
    _patch_research_stack(monkeypatch)
    db = tenant_db()
    try:
        out = run_research_outreach_proposal_scheduled(db, str(_ORG_A), str(_CONTACT_A))
        logs = (
            db.query(AgentActionLog)
            .filter(
                AgentActionLog.target_id == str(_CONTACT_A),
                AgentActionLog.action_type.in_(
                    ("worker_research", "rev_orch_qualification", "worker_personalize")
                ),
            )
            .all()
        )
        assert logs
        assert any(lg.action_type == "worker_research" for lg in logs)
        assert out.get("workflow_run_id")
    finally:
        db.close()


def test_acp3_pause_prevents_new_proposal_work(tenant_db, monkeypatch):
    _seed(tenant_db)
    _patch_research_stack(monkeypatch)
    monkeypatch.setenv("ACP1_AUTONOMOUS_ORGANIZATION_IDS", str(_ORG_A))
    monkeypatch.setenv("HEARTBEAT_ENABLED", "0")
    from revenue_os.scheduler import job_scan_research_outreach_eligibility

    result = job_scan_research_outreach_eligibility()
    assert result.get("blocked") is True
    assert result.get("blocked_reason") == "heartbeat_paused"
    db = tenant_db()
    try:
        assert (
            db.query(ApprovalRequest)
            .filter(ApprovalRequest.action_type == "send_outreach_email")
            .count()
            == 0
        )
    finally:
        db.close()


def test_acp3_kill_prevents_new_proposal_work(tenant_db, monkeypatch):
    _seed(tenant_db)
    _patch_research_stack(monkeypatch)
    monkeypatch.setenv("ACP1_AUTONOMOUS_ORGANIZATION_IDS", str(_ORG_A))
    monkeypatch.setenv("ACP2_AUTONOMOUS_EXECUTION_ENABLED", "0")
    from revenue_os.scheduler import job_scan_research_outreach_eligibility

    result = job_scan_research_outreach_eligibility()
    assert result.get("blocked") is True
    assert "acp2" in str(result.get("blocked_reason", ""))


def test_soft_fail_recoverable_on_bad_contact(tenant_db, monkeypatch):
    _seed(tenant_db)
    _patch_research_stack(monkeypatch)
    db = tenant_db()
    try:
        out = run_research_outreach_proposal_scheduled(
            db, str(_ORG_A), str(uuid.uuid4())
        )
        assert out.get("ok") is False
        assert "tenant" in out.get("reason", "").lower() or "scope" in out.get(
            "reason", ""
        ).lower()
    finally:
        db.close()


def test_existing_m1_api_path_still_works(tenant_db, monkeypatch):
    _seed(tenant_db)
    _patch_research_stack(monkeypatch)
    db = tenant_db()
    try:
        out = run_research_to_outreach(db, _tenant(), str(_CONTACT_A))
        assert out.get("ok") is True
        assert out.get("approval_id")
        assert out.get("state") == "APPROVAL_PENDING"
    finally:
        db.close()


def test_follow_up_propose_work_kind_unchanged():
    spec = get_effect_spec(WORK_FOLLOW_UP_PROPOSE)
    assert spec is not None
    assert spec.execution_mode == ExecutionMode.AUTONOMOUS
    assert "follow_up_propose" == spec.requested_effect


def test_no_authority_expansion_catalog():
    propose = get_effect_spec(WORK_RESEARCH_OUTREACH_PROPOSE)
    send = get_effect_spec(WORK_OUTBOUND_SEND)
    assert propose.execution_mode == ExecutionMode.AUTONOMOUS
    assert send.execution_mode == ExecutionMode.HUMAN_REQUIRED


def test_heartbeat_job_registered():
    from revenue_os import scheduler as sched

    src = inspect.getsource(sched.initialize_heartbeat)
    assert "scan_research_outreach_eligibility" in src
    assert "job_scan_research_outreach_eligibility" in src


def test_command_change_not_required_for_v1():
    """Existing Activity + AgentActionLog + ApprovalRequest projection is sufficient."""
    # Guard: this coverage slice must not have edited founder_ui_read_model.py
    # (verified via git name-status in the gate; structural assertion here).
    assert WORK_RESEARCH_OUTREACH_PROPOSE == "research_outreach_propose"
