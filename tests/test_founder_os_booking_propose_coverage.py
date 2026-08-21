"""Booking-propose coverage I1 — Option B cadence + eligibility scan."""

from __future__ import annotations

import inspect
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import revenue_os.models  # noqa: F401
import runner_api_routers.identity as identity_mod
import runner_api_routers.operator_flow as of_router
import runner_api_routers.ui as ui_mod
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
from revenue_os.scheduler import job_scan_booking_eligibility
from revenue_os.services.acp2_effect_catalog import get_effect_spec
from revenue_os.services.acp2_work_contract import (
    WORK_BOOKING_EXECUTE,
    WORK_BOOKING_PROPOSE,
    ExecutionMode,
    WorkState,
)
from revenue_os.services.acp4_production_runtime import orchestrate_claimed
from revenue_os.services.approvals import decide, request_approval
from revenue_os.services.booking_eligibility import (
    STATE_ALREADY_BOOKED,
    STATE_PENDING,
    evaluate_booking_eligibility,
    scan_eligible_bookings,
)
from revenue_os.services.founder_ui_read_model import build_command_center_snapshot
from revenue_os.services.identity_context import AuthMethod, IdentityContext, PrincipalKind
from revenue_os.services.revenue_orchestration_service import (
    run_booking_proposal_scheduled,
)
from revenue_os.services.tenant_context import TenantContext
from revenue_os.services.tenant_resolution import ORGANIZATION_COOKIE

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_CONTACT_INELIGIBLE = uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
_OPERATOR = "Krishna Founder"
_ROOT = Path(__file__).resolve().parents[1]

_FUTURE_SLOT = {
    "start": (datetime.now(timezone.utc) + timedelta(days=2)).replace(microsecond=0).isoformat(),
    "end": (datetime.now(timezone.utc) + timedelta(days=2, minutes=30)).replace(microsecond=0).isoformat(),
}
_AVAILABILITY = {
    "ok": True,
    "connector": "google_calendar",
    "organization_id": str(_ORG_A),
    "duration_minutes": 30,
    "slots": [_FUTURE_SLOT],
}


@pytest.fixture(autouse=True)
def _reset() -> None:
    identity_mod._revoked_jtis.clear()
    identity_mod._login_failures.clear()


@pytest.fixture
def tenant_db(monkeypatch: pytest.MonkeyPatch, tmp_path) -> sessionmaker:
    engine = create_engine(f"sqlite:///{tmp_path / 'booking_propose_coverage.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    import revenue_os.database as db_mod
    import revenue_os.scheduler as sched_mod
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
        sched_mod,
    ):
        if hasattr(mod, "SessionLocal"):
            monkeypatch.setattr(mod, "SessionLocal", sf)
    monkeypatch.setenv("FOUNDER_OS_REQUIRE_LOGIN", "0")
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    monkeypatch.setenv("SECRET_KEY", "ui-d2-1-local-test-secret-key-32b")
    monkeypatch.setenv("ACP2_AUTONOMOUS_EXECUTION_ENABLED", "1")
    monkeypatch.setenv("HEARTBEAT_ENABLED", "1")
    monkeypatch.setenv("ACP3_RESUME_ENABLED", "1")
    monkeypatch.delenv("ACP1_AUTONOMOUS_ORGANIZATION_IDS", raising=False)
    monkeypatch.delenv("HEARTBEAT_ORGANIZATION_IDS", raising=False)
    return sf


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


def _seed_meeting_interest(
    db,
    *,
    contact_id: uuid.UUID,
    org_id: uuid.UUID,
    activity_id: uuid.UUID | None = None,
) -> uuid.UUID:
    act_id = activity_id or uuid.uuid4()
    reply_act = Activity(
        id=act_id,
        contact_id=contact_id,
        activity_type=ActivityType.EMAIL,
        subject="Meeting interest reply",
        body="Can we schedule a call?",
        direction="inbound",
        status="completed",
    )
    db.add(reply_act)
    db.flush()
    db.add(
        AgentActionLog(
            organization_id=org_id,
            actor="revenue_workflow_orchestrator",
            action_type="rev_orch_reply_assessment",
            target_type="contact",
            target_id=str(contact_id),
            status="completed",
            detail={
                "activity_id": str(act_id),
                "message_id": f"msg-{contact_id}",
                "assessment": {"reply_type": "MEETING_INTEREST", "meeting_interest": True},
                "routing": {
                    "reply_type": "MEETING_INTEREST",
                    "booking_eligible": True,
                    "recommended_next_action": "BOOKING_ELIGIBLE",
                    "booking_created": False,
                },
            },
        )
    )
    return act_id


def _seed(db_factory: sessionmaker, *, with_interest: bool = True) -> None:
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
                    lead_score=10,
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
                    lead_score=10,
                    created_at=datetime.now(timezone.utc),
                ),
                Contact(
                    id=_CONTACT_INELIGIBLE,
                    first_name="Ivy",
                    last_name="Ineligible",
                    email="ivy@example.com",
                    status=ContactStatus.LEAD,
                    source=ContactSource.MANUAL,
                    organization_id=_ORG_A,
                    lead_score=1,
                    created_at=datetime.now(timezone.utc),
                ),
            ]
        )
        db.flush()
        if with_interest:
            _seed_meeting_interest(db, contact_id=_CONTACT_A, org_id=_ORG_A)
        db.commit()
    finally:
        db.close()


# ── Eligibility scan ──────────────────────────────────────────────────────────


def test_scan_eligible_bookings_org_scoped(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        hits = scan_eligible_bookings(db, organization_id=str(_ORG_A))
        assert any(h["contact_id"] == str(_CONTACT_A) for h in hits)
        assert all(h["organization_id"] == str(_ORG_A) for h in hits)
        assert not any(h["contact_id"] == str(_CONTACT_B) for h in hits)
        assert not any(h["contact_id"] == str(_CONTACT_INELIGIBLE) for h in hits)
    finally:
        db.close()


def test_scan_tenant_isolation(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        hits_b = scan_eligible_bookings(db, organization_id=str(_ORG_B))
        assert hits_b == []
        contact_a = db.get(Contact, _CONTACT_A)
        assert contact_a is not None
        cross = evaluate_booking_eligibility(db, contact_a, str(_ORG_B))
        assert cross.get("eligible") is False
    finally:
        db.close()


def test_ineligible_contacts_excluded(tenant_db):
    _seed(tenant_db, with_interest=False)
    db = tenant_db()
    try:
        hits = scan_eligible_bookings(db, organization_id=str(_ORG_A))
        assert hits == []
    finally:
        db.close()


def test_pending_book_meeting_suppresses_eligibility(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        request_approval(
            requested_by="test",
            action_type="book_meeting",
            title="Pending booking",
            target_type="contact",
            target_id=str(_CONTACT_A),
            payload={"organization_id": str(_ORG_A), "contact_id": str(_CONTACT_A)},
            organization_id=str(_ORG_A),
        )
        contact = db.get(Contact, _CONTACT_A)
        result = evaluate_booking_eligibility(db, contact, str(_ORG_A))
        assert result.get("eligible") is False
        assert result.get("state") == STATE_PENDING
        hits = scan_eligible_bookings(db, organization_id=str(_ORG_A))
        assert not any(h["contact_id"] == str(_CONTACT_A) for h in hits)
    finally:
        db.close()


def test_completed_meeting_suppresses_eligibility(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        db.add(
            Activity(
                contact_id=_CONTACT_A,
                activity_type=ActivityType.MEETING,
                subject="Already booked",
                body="prior",
                direction="outbound",
                status="completed",
                performed_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
        contact = db.get(Contact, _CONTACT_A)
        result = evaluate_booking_eligibility(db, contact, str(_ORG_A))
        assert result.get("eligible") is False
        assert result.get("state") == STATE_ALREADY_BOOKED
        hits = scan_eligible_bookings(db, organization_id=str(_ORG_A))
        assert not any(h["contact_id"] == str(_CONTACT_A) for h in hits)
    finally:
        db.close()


# ── Scheduler cadence / claim ─────────────────────────────────────────────────


def test_scheduler_cadence_invokes_booking_propose(tenant_db, monkeypatch):
    _seed(tenant_db)
    monkeypatch.setenv("ACP1_AUTONOMOUS_ORGANIZATION_IDS", str(_ORG_A))
    with patch(
        "revenue_os.services.revenue_orchestration_service.get_tenant_availability",
        return_value=_AVAILABILITY,
    ), patch(
        "revenue_os.services.calendar_executor.create_tenant_calendar_event"
    ) as write_mock:
        out = job_scan_booking_eligibility()
        assert out.get("ok") is True
        assert out.get("orchestrated") is True
        assert out.get("candidates", 0) >= 1
        assert out.get("proposals_filed", 0) >= 1
        write_mock.assert_not_called()

    db = tenant_db()
    try:
        pending = (
            db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.action_type == "book_meeting",
                ApprovalRequest.target_id == str(_CONTACT_A),
                ApprovalRequest.status == "pending",
            )
            .all()
        )
        assert len(pending) == 1
        payload = pending[0].payload or {}
        assert payload.get("selected_slot_start") == _FUTURE_SLOT["start"]
        assert payload.get("selected_slot_end") == _FUTURE_SLOT["end"]
        logs = (
            db.query(AgentActionLog)
            .filter(AgentActionLog.action_type == "booking_proposal_scheduled")
            .all()
        )
        assert len(logs) >= 1
    finally:
        db.close()


def test_scheduler_uses_orchestrate_claimed():
    src = inspect.getsource(job_scan_booking_eligibility)
    assert "orchestrate_claimed" in src
    assert "WORK_BOOKING_PROPOSE" in src
    assert "run_booking_proposal_scheduled" in src
    assert "scan_eligible_bookings" in src
    sched = (_ROOT / "revenue_os/scheduler.py").read_text(encoding="utf-8")
    assert "scan_booking_eligibility" in sched
    assert "job_scan_booking_eligibility" in sched


def test_two_worker_duplicate_claim_behavior(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        ran = {"n": 0}

        def _exec(_work):
            ran["n"] += 1
            return {
                "ok": True,
                "waiting_human": True,
                "escalation_reason": "booking_execute_requires_approval",
            }

        w1 = orchestrate_claimed(
            db,
            work_kind=WORK_BOOKING_PROPOSE,
            organization_id=str(_ORG_A),
            source="scheduler",
            actor="heartbeat",
            executor=_exec,
            target_type="contact",
            target_id=str(_CONTACT_A),
            logical_key="book-once",
        )
        w2 = orchestrate_claimed(
            db,
            work_kind=WORK_BOOKING_PROPOSE,
            organization_id=str(_ORG_A),
            source="scheduler",
            actor="heartbeat",
            executor=_exec,
            target_type="contact",
            target_id=str(_CONTACT_A),
            logical_key="book-once",
        )
        assert w1.state in (WorkState.SUCCEEDED, WorkState.WAITING_HUMAN)
        assert ran["n"] == 1
        assert w2.result.get("deduplicated") is True or ran["n"] == 1
    finally:
        db.close()


def test_repeated_scheduler_does_not_storm_approvals(tenant_db, monkeypatch):
    _seed(tenant_db)
    monkeypatch.setenv("ACP1_AUTONOMOUS_ORGANIZATION_IDS", str(_ORG_A))
    with patch(
        "revenue_os.services.revenue_orchestration_service.get_tenant_availability",
        return_value=_AVAILABILITY,
    ):
        first = job_scan_booking_eligibility()
        second = job_scan_booking_eligibility()
    assert first.get("proposals_filed", 0) >= 1
    db = tenant_db()
    try:
        pending = (
            db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.action_type == "book_meeting",
                ApprovalRequest.target_id == str(_CONTACT_A),
                ApprovalRequest.status == "pending",
            )
            .count()
        )
        assert pending == 1
        assert second.get("candidates", 0) == 0 or second.get("proposals_filed", 0) == 0
    finally:
        db.close()


# ── Proposal-only / calendar / approval ───────────────────────────────────────


def test_proposal_only_no_calendar_write(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        with patch(
            "revenue_os.services.revenue_orchestration_service.get_tenant_availability",
            return_value=_AVAILABILITY,
        ), patch(
            "revenue_os.services.calendar_executor.create_tenant_calendar_event"
        ) as write_mock:
            result = run_booking_proposal_scheduled(db, str(_ORG_A), str(_CONTACT_A))
            assert result.get("ok") is True
            assert result.get("approval_id")
            write_mock.assert_not_called()
        assert "create_tenant_calendar_event" not in inspect.getsource(
            run_booking_proposal_scheduled
        )
        propose_src = inspect.getsource(
            __import__(
                "revenue_os.services.revenue_orchestration_service",
                fromlist=["_run_booking_proposal"],
            )._run_booking_proposal
        )
        assert "create_tenant_calendar_event" not in propose_src
        assert "get_tenant_availability" in propose_src
    finally:
        db.close()


def test_unavailable_calendar_soft_fails(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        with patch(
            "revenue_os.services.revenue_orchestration_service.get_tenant_availability",
            return_value={"ok": False, "reason": "No calendar connector"},
        ):
            result = run_booking_proposal_scheduled(db, str(_ORG_A), str(_CONTACT_A))
        assert result.get("ok") is False
        assert "calendar" in (result.get("reason") or "").lower() or "unavailable" in (
            result.get("reason") or ""
        ).lower() or "connector" in (result.get("reason") or "").lower()
        pending = (
            db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.action_type == "book_meeting",
                ApprovalRequest.target_id == str(_CONTACT_A),
            )
            .count()
        )
        assert pending == 0
    finally:
        db.close()


def test_empty_availability_soft_fails(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        empty = {**_AVAILABILITY, "slots": []}
        with patch(
            "revenue_os.services.revenue_orchestration_service.get_tenant_availability",
            return_value=empty,
        ):
            result = run_booking_proposal_scheduled(db, str(_ORG_A), str(_CONTACT_A))
        assert result.get("ok") is False
        pending = (
            db.query(ApprovalRequest)
            .filter(ApprovalRequest.target_id == str(_CONTACT_A))
            .count()
        )
        assert pending == 0
    finally:
        db.close()


def test_tenant_mismatch_fails_closed(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        result = run_booking_proposal_scheduled(db, str(_ORG_B), str(_CONTACT_A))
        assert result.get("ok") is False
    finally:
        db.close()


def test_approval_required_before_booking_execution_and_single_effect(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        with patch(
            "revenue_os.services.revenue_orchestration_service.get_tenant_availability",
            return_value=_AVAILABILITY,
        ):
            proposed = run_booking_proposal_scheduled(db, str(_ORG_A), str(_CONTACT_A))
        assert proposed.get("ok") is True
        approval_id = proposed["approval_id"]
        payload = proposed.get("proposal", {}).get("selected_slot") or {}

        calendar_calls: list[dict] = []

        def _fake_create(org_id, **kwargs):
            calendar_calls.append({"org_id": org_id, **kwargs})
            return {
                "ok": True,
                "provider_event_id": "evt-1",
                "connector": "google_calendar",
                "organization_id": org_id,
            }

        with patch(
            "revenue_os.services.calendar_executor.create_tenant_calendar_event",
            side_effect=_fake_create,
        ):
            decided = decide(
                approval_id,
                True,
                tenant=_human_tenant(),
            )
        assert decided.get("status") == "approved"
        assert len(calendar_calls) == 1
        assert calendar_calls[0]["start_time"].isoformat().replace("+00:00", "+00:00")
        # Executor must use approved payload slots, not re-select.
        ar = db.get(ApprovalRequest, approval_id)
        assert ar is not None
        ar_payload = ar.payload or {}
        assert ar_payload.get("selected_slot_start") == _FUTURE_SLOT["start"]
        assert ar_payload.get("selected_slot_end") == _FUTURE_SLOT["end"]
        assert str(calendar_calls[0]["start_time"].replace(microsecond=0).isoformat()).replace(
            "+00:00", ""
        ) in _FUTURE_SLOT["start"].replace("+00:00", "").replace("Z", "")
    finally:
        db.close()


def test_executor_cannot_substitute_slot_source():
    from revenue_os.services import approvals as approvals_mod

    src = inspect.getsource(approvals_mod._execute_book_meeting)
    assert "selected_slot_start" in src
    assert "selected_slot_end" in src
    assert "recommended_slot" not in src
    assert "get_tenant_availability" not in src
    assert "run_booking_worker" not in src


def test_provenance_present(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        with patch(
            "revenue_os.services.revenue_orchestration_service.get_tenant_availability",
            return_value=_AVAILABILITY,
        ):
            result = run_booking_proposal_scheduled(db, str(_ORG_A), str(_CONTACT_A))
        assert result.get("ok") is True
        contact_types = {
            row.action_type
            for row in db.query(AgentActionLog)
            .filter(AgentActionLog.target_id == str(_CONTACT_A))
            .all()
        }
        assert "rev_orch_booking_eligibility" in contact_types
        assert "worker_booking_proposal" in contact_types
        all_types = {row.action_type for row in db.query(AgentActionLog).all()}
        assert "approval_requested" in all_types
        pending = (
            db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.action_type == "book_meeting",
                ApprovalRequest.target_id == str(_CONTACT_A),
                ApprovalRequest.status == "pending",
            )
            .count()
        )
        assert pending == 1
    finally:
        db.close()


# ── Authority / Command ───────────────────────────────────────────────────────


def test_heartbeat_eligibility_does_not_change_authority_classification():
    propose = get_effect_spec(WORK_BOOKING_PROPOSE)
    execute = get_effect_spec(WORK_BOOKING_EXECUTE)
    assert propose is not None and execute is not None
    assert propose.execution_mode == ExecutionMode.AUTONOMOUS
    assert execute.execution_mode == ExecutionMode.HUMAN_REQUIRED
    assert "heartbeat" in propose.eligible_agents
    assert "heartbeat" not in execute.eligible_agents


def test_command_visibility_for_pending_book_meeting(tenant_db):
    _seed(tenant_db)
    db = tenant_db()
    try:
        with patch(
            "revenue_os.services.revenue_orchestration_service.get_tenant_availability",
            return_value=_AVAILABILITY,
        ):
            proposed = run_booking_proposal_scheduled(db, str(_ORG_A), str(_CONTACT_A))
        assert proposed.get("ok") is True
        snap = build_command_center_snapshot(organization_id=str(_ORG_A))
        pending = snap.get("pending_approvals") or []
        book = [a for a in pending if a.get("action_type") == "book_meeting"]
        assert len(book) >= 1
        meeting_pending = snap.get("meeting_booking_pending") or []
        assert len(meeting_pending) >= 1 or any(
            i.get("kind") == "approval" for i in (snap.get("decision_items") or [])
        )
    finally:
        db.close()


def test_scan_reuses_canonical_evaluator():
    src = inspect.getsource(scan_eligible_bookings)
    assert "evaluate_booking_eligibility" in src
    assert "get_tenant_availability" not in src
    assert "request_approval" not in src
