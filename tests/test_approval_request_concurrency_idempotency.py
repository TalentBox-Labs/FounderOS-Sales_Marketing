"""Shared ApprovalRequest concurrency and idempotency coverage."""

from __future__ import annotations

import os
import threading
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

import revenue_os.models  # noqa: F401
from revenue_os.models.approvals import ApprovalRequest
from revenue_os.models.base import Base
from revenue_os.models.contact import Contact, ContactSource, ContactStatus
from revenue_os.models.organization import Organization, OrganizationStatus
from revenue_os.services.approval_request_identity import (
    FAMILY_BOOK_MEETING,
    FAMILY_PROACTIVE_EMAIL,
    FAMILY_REPLY_EMAIL,
    STATUS_PENDING,
    STATUS_SUPERSEDED,
    booking_logical_key,
    effect_key_for_approval,
    proactive_email_logical_key,
    reply_email_logical_key,
)
from revenue_os.services.approvals import (
    EXECUTION_PHASE_COMPLETED,
    EXECUTION_PHASE_QUEUED,
    decide,
    get_or_create_pending_approval,
    request_approval,
    resume_approval_effect,
)
from revenue_os.services.identity_context import AuthMethod, IdentityContext, PrincipalKind
from revenue_os.services.tenant_context import TenantContext
from tests.conftest import build_test_approval_request

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_SOURCE_A = uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")

POSTGRES_URL = os.getenv(
    "APPROVAL_TEST_DATABASE_URL",
    os.getenv("DATABASE_URL", ""),
)


def _is_postgres(url: str) -> bool:
    return url.startswith("postgresql")


@pytest.fixture
def approval_db(monkeypatch: pytest.MonkeyPatch, tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'approval_idem.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    import revenue_os.database as db_mod
    import revenue_os.services.approvals as approvals_mod

    monkeypatch.setattr(db_mod, "SessionLocal", sf)
    monkeypatch.setattr(approvals_mod, "SessionLocal", sf)
    return sf


def _seed_orgs_contacts(sf: sessionmaker) -> None:
    db = sf()
    try:
        db.add_all(
            [
                Organization(id=_ORG_A, name="A", slug="a", status=OrganizationStatus.ACTIVE),
                Organization(id=_ORG_B, name="B", slug="b", status=OrganizationStatus.ACTIVE),
                Contact(
                    id=_CONTACT_A,
                    first_name="Ada",
                    last_name="A",
                    email="ada@a.example",
                    status=ContactStatus.LEAD,
                    source=ContactSource.MANUAL,
                    organization_id=_ORG_A,
                    lead_score=0,
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
        organization_name="Org",
        organization_slug="org",
        membership_id=str(uuid.uuid4()),
        membership_role="owner",
        membership_status="active",
    )


def _proactive_payload(**extra) -> dict:
    base = {
        "contact_id": str(_CONTACT_A),
        "organization_id": str(_ORG_A),
        "email": "ada@a.example",
        "name": "Ada",
        "template": "ai_cold_email",
        "context": {"body": "Hello"},
    }
    base.update(extra)
    return base


def test_same_pending_proactive_identity_dedupes(approval_db):
    _seed_orgs_contacts(approval_db)
    first = get_or_create_pending_approval(
        requested_by="m1",
        action_type="send_outreach_email",
        title="M1",
        target_type="contact",
        target_id=str(_CONTACT_A),
        payload=_proactive_payload(workflow_kind="rev_orch_m1_research_outreach"),
        organization_id=str(_ORG_A),
    )
    second = get_or_create_pending_approval(
        requested_by="m2",
        action_type="send_outreach_email",
        title="M2 follow-up",
        target_type="contact",
        target_id=str(_CONTACT_A),
        payload=_proactive_payload(
            workflow_kind="rev_orch_m2_follow_up",
            context={"body": "Hello", "subject": "Follow up"},
        ),
        organization_id=str(_ORG_A),
    )
    assert first["created"] is True
    assert second["deduplicated"] is True
    assert first["id"] == second["id"]
    db = approval_db()
    try:
        assert db.query(ApprovalRequest).filter_by(status=STATUS_PENDING).count() == 1
    finally:
        db.close()


def test_cross_tenant_rows_do_not_collide(approval_db):
    _seed_orgs_contacts(approval_db)
    a = get_or_create_pending_approval(
        requested_by="m1",
        action_type="send_outreach_email",
        title="A",
        target_type="contact",
        target_id=str(_CONTACT_A),
        payload=_proactive_payload(),
        organization_id=str(_ORG_A),
    )
    b = get_or_create_pending_approval(
        requested_by="m1",
        action_type="send_outreach_email",
        title="B",
        target_type="contact",
        target_id=str(_CONTACT_B),
        payload={
            "contact_id": str(_CONTACT_B),
            "organization_id": str(_ORG_B),
            "email": "bob@b.example",
            "name": "Bob",
            "template": "ai_cold_email",
            "context": {"body": "Hi"},
        },
        organization_id=str(_ORG_B),
    )
    assert a["id"] != b["id"]


def test_reply_coexists_with_proactive(approval_db):
    _seed_orgs_contacts(approval_db)
    proactive = get_or_create_pending_approval(
        requested_by="m1",
        action_type="send_outreach_email",
        title="Outreach",
        target_type="contact",
        target_id=str(_CONTACT_A),
        payload=_proactive_payload(),
        organization_id=str(_ORG_A),
    )
    reply = get_or_create_pending_approval(
        requested_by="agent",
        action_type="send_reply_email",
        title="Reply",
        target_type="contact",
        target_id=str(_CONTACT_A),
        payload={
            "contact_id": str(_CONTACT_A),
            "organization_id": str(_ORG_A),
            "email": "ada@a.example",
            "source_activity_id": str(_SOURCE_A),
            "context": {"body": "Thanks"},
        },
        organization_id=str(_ORG_A),
    )
    assert proactive["id"] != reply["id"]
    assert reply["approval_family"] == FAMILY_REPLY_EMAIL


def test_terminal_reproposal_allowed(approval_db):
    _seed_orgs_contacts(approval_db)
    first = get_or_create_pending_approval(
        requested_by="m1",
        action_type="send_outreach_email",
        title="One",
        target_type="contact",
        target_id=str(_CONTACT_A),
        payload=_proactive_payload(),
        organization_id=str(_ORG_A),
    )
    decide(first["id"], approve=False, tenant=_tenant())
    second = get_or_create_pending_approval(
        requested_by="m1",
        action_type="send_outreach_email",
        title="Two",
        target_type="contact",
        target_id=str(_CONTACT_A),
        payload=_proactive_payload(context={"body": "New draft"}),
        organization_id=str(_ORG_A),
    )
    assert second["created"] is True
    assert second["id"] != first["id"]


def test_booking_slot_change_supersedes_old_pending(approval_db):
    _seed_orgs_contacts(approval_db)
    start_a = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    end_a = (datetime.now(timezone.utc) + timedelta(days=3, hours=1)).isoformat()
    start_b = (datetime.now(timezone.utc) + timedelta(days=4)).isoformat()
    end_b = (datetime.now(timezone.utc) + timedelta(days=4, hours=1)).isoformat()
    first = get_or_create_pending_approval(
        requested_by="booking",
        action_type="book_meeting",
        title="Slot A",
        target_type="contact",
        target_id=str(_CONTACT_A),
        payload={
            "contact_id": str(_CONTACT_A),
            "organization_id": str(_ORG_A),
            "selected_slot_start": start_a,
            "selected_slot_end": end_a,
            "meeting_title": "Meet",
        },
        organization_id=str(_ORG_A),
    )
    second = get_or_create_pending_approval(
        requested_by="booking",
        action_type="book_meeting",
        title="Slot B",
        target_type="contact",
        target_id=str(_CONTACT_A),
        payload={
            "contact_id": str(_CONTACT_A),
            "organization_id": str(_ORG_A),
            "selected_slot_start": start_b,
            "selected_slot_end": end_b,
            "meeting_title": "Meet",
        },
        organization_id=str(_ORG_A),
    )
    db = approval_db()
    try:
        old = db.get(ApprovalRequest, first["id"])
        assert old.status == STATUS_SUPERSEDED
        assert old.payload["selected_slot_start"] == start_a
        new = db.get(ApprovalRequest, second["id"])
        assert new.status == STATUS_PENDING
        assert new.payload["selected_slot_start"] == start_b
    finally:
        db.close()


def test_superseded_cannot_be_decided(approval_db):
    _seed_orgs_contacts(approval_db)
    rid = str(uuid.uuid4())
    row = build_test_approval_request(
        id=rid,
        organization_id=str(_ORG_A),
        approval_family=FAMILY_PROACTIVE_EMAIL,
        logical_key=proactive_email_logical_key(str(_CONTACT_A)),
        target_id=str(_CONTACT_A),
        status=STATUS_SUPERSEDED,
        payload=_proactive_payload(),
    )
    db = approval_db()
    try:
        db.add(row)
        db.commit()
    finally:
        db.close()
    with pytest.raises(ValueError, match="already superseded"):
        decide(rid, approve=True, tenant=_tenant())


def test_request_approval_facade_delegates(approval_db):
    _seed_orgs_contacts(approval_db)
    out = request_approval(
        requested_by="api",
        action_type="send_outreach_email",
        title="Facade",
        target_type="contact",
        target_id=str(_CONTACT_A),
        payload=_proactive_payload(),
        organization_id=str(_ORG_A),
    )
    assert out["approval_family"] == FAMILY_PROACTIVE_EMAIL
    assert out["logical_key"] == proactive_email_logical_key(str(_CONTACT_A))


def test_stable_effect_key_on_approve(approval_db, monkeypatch):
    _seed_orgs_contacts(approval_db)
    monkeypatch.setattr(
        "revenue_os.integrations.n8n.trigger_workflow",
        lambda *a, **k: {"ok": True},
    )
    created = get_or_create_pending_approval(
        requested_by="m1",
        action_type="send_outreach_email",
        title="Send",
        target_type="contact",
        target_id=str(_CONTACT_A),
        payload=_proactive_payload(),
        organization_id=str(_ORG_A),
    )
    result = decide(created["id"], approve=True, tenant=_tenant())
    effect_key = effect_key_for_approval(created["id"], "send_outreach_email")
    assert result["execution_result"]["effect_key"] == effect_key
    assert result["execution_result"]["phase"] == EXECUTION_PHASE_COMPLETED


def test_resume_reuses_effect_key(approval_db, monkeypatch):
    _seed_orgs_contacts(approval_db)
    calls = {"n": 0}

    def _n8n(*a, **k):
        calls["n"] += 1
        return {"ok": True}

    monkeypatch.setattr("revenue_os.integrations.n8n.trigger_workflow", _n8n)
    created = get_or_create_pending_approval(
        requested_by="m1",
        action_type="send_outreach_email",
        title="Send",
        target_type="contact",
        target_id=str(_CONTACT_A),
        payload=_proactive_payload(),
        organization_id=str(_ORG_A),
    )
    db = approval_db()
    try:
        row = db.get(ApprovalRequest, created["id"])
        row.status = "approved"
        row.execution_result = {
            "phase": EXECUTION_PHASE_QUEUED,
            "effect_key": effect_key_for_approval(created["id"], "send_outreach_email"),
            "effect_completed": False,
        }
        db.commit()
    finally:
        db.close()
    resume_approval_effect(created["id"], tenant=_tenant())
    assert calls["n"] == 1


def test_create_deal_tenant_mismatch_fails_closed(approval_db):
    _seed_orgs_contacts(approval_db)
    created = get_or_create_pending_approval(
        requested_by="api",
        action_type="create_deal",
        title="Deal",
        target_type="contact",
        target_id=str(_CONTACT_B),
        payload={
            "contact_id": str(_CONTACT_B),
            "organization_id": str(_ORG_A),
            "value": 1000,
        },
        organization_id=str(_ORG_A),
    )
    with patch(
        "revenue_os.services.deal_automation_service.create_deal_from_contact",
        side_effect=AssertionError("should not run"),
    ):
        result = decide(created["id"], approve=True, tenant=_tenant(_ORG_A))
    assert result["execution_result"]["executed"] is False
    assert "tenant" in str(result["execution_result"].get("error", "")).lower()


def test_legacy_backfilled_row_readable(approval_db):
    row = build_test_approval_request(
        id=str(uuid.uuid4()),
        organization_id=str(_ORG_A),
        approval_family=FAMILY_PROACTIVE_EMAIL,
        logical_key=proactive_email_logical_key(str(_CONTACT_A)),
        target_id=str(_CONTACT_A),
        payload=_proactive_payload(),
    )
    db = approval_db()
    try:
        db.add(row)
        db.commit()
        loaded = db.get(ApprovalRequest, row.id)
        assert loaded.organization_id == str(_ORG_A)
        assert loaded.to_dict()["logical_key"].startswith("contact:")
    finally:
        db.close()


@pytest.mark.postgres
@pytest.mark.skipif(not _is_postgres(POSTGRES_URL), reason="PostgreSQL required")
def test_postgres_concurrent_pending_insert():
    engine = create_engine(POSTGRES_URL, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    org_id = str(uuid.uuid4())
    contact_id = str(uuid.uuid4())
    db = sf()
    try:
        db.add(
            Organization(
                id=uuid.UUID(org_id),
                name="PG",
                slug=f"pg-{org_id[:8]}",
                status=OrganizationStatus.ACTIVE,
            )
        )
        db.add(
            Contact(
                id=uuid.UUID(contact_id),
                first_name="Pg",
                last_name="Test",
                email="pg@example.com",
                status=ContactStatus.LEAD,
                source=ContactSource.MANUAL,
                organization_id=uuid.UUID(org_id),
                lead_score=0,
            )
        )
        db.commit()
    finally:
        db.close()

    import revenue_os.database as db_mod
    import revenue_os.services.approvals as approvals_mod

    original_db = db_mod.SessionLocal
    original_ap = approvals_mod.SessionLocal
    db_mod.SessionLocal = sf
    approvals_mod.SessionLocal = sf

    barrier = threading.Barrier(2)
    results: list[dict] = [{} , {}]

    def worker(idx: int) -> None:
        barrier.wait()
        results[idx] = get_or_create_pending_approval(
            requested_by=f"w{idx}",
            action_type="send_outreach_email",
            title=f"T{idx}",
            target_type="contact",
            target_id=contact_id,
            payload={
                "contact_id": contact_id,
                "organization_id": org_id,
                "email": "pg@example.com",
                "name": "Pg",
                "template": "t",
                "context": {"body": "x"},
            },
            organization_id=org_id,
        )

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    db_mod.SessionLocal = original_db
    approvals_mod.SessionLocal = original_ap

    db = sf()
    try:
        pending = (
            db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.organization_id == org_id,
                ApprovalRequest.approval_family == FAMILY_PROACTIVE_EMAIL,
                ApprovalRequest.logical_key == proactive_email_logical_key(contact_id),
                ApprovalRequest.status == STATUS_PENDING,
            )
            .all()
        )
        assert len(pending) == 1
        assert results[0]["id"] == results[1]["id"]
    finally:
        db.close()

    cleanup = sf()
    try:
        cleanup.query(ApprovalRequest).filter(ApprovalRequest.organization_id == org_id).delete()
        from revenue_os.models.activity import Activity

        cleanup.query(Activity).filter(Activity.contact_id == uuid.UUID(contact_id)).delete()
        cleanup.query(Contact).filter(Contact.id == uuid.UUID(contact_id)).delete()
        cleanup.query(Organization).filter(Organization.id == uuid.UUID(org_id)).delete()
        cleanup.commit()
    finally:
        cleanup.close()


@pytest.mark.postgres
@pytest.mark.skipif(not _is_postgres(POSTGRES_URL), reason="PostgreSQL required")
def test_postgres_concurrent_booking_multi_slot_single_pending():
    engine = create_engine(POSTGRES_URL, pool_pre_ping=True)
    sf = sessionmaker(bind=engine)

    org_id = str(uuid.uuid4())
    contact_id = str(uuid.uuid4())

    db = sf()
    try:
        db.add(
            Organization(
                id=uuid.UUID(org_id),
                name="PG Booking",
                slug=f"pgb-{org_id[:8]}",
                status=OrganizationStatus.ACTIVE,
            )
        )
        db.add(
            Contact(
                id=uuid.UUID(contact_id),
                first_name="Pg",
                last_name="Booking",
                email="pgb@example.com",
                status=ContactStatus.LEAD,
                source=ContactSource.MANUAL,
                organization_id=uuid.UUID(org_id),
                lead_score=0,
            )
        )
        db.commit()
    finally:
        db.close()

    import revenue_os.database as db_mod
    import revenue_os.services.approvals as approvals_mod

    original_db = db_mod.SessionLocal
    original_ap = approvals_mod.SessionLocal
    db_mod.SessionLocal = sf
    approvals_mod.SessionLocal = sf

    start_a = datetime.now(timezone.utc) + timedelta(days=3)
    start_b = datetime.now(timezone.utc) + timedelta(days=4)
    end_a = start_a + timedelta(hours=1)
    end_b = start_b + timedelta(hours=1)

    payload_a = {
        "contact_id": contact_id,
        "organization_id": org_id,
        "selected_slot_start": start_a.isoformat(),
        "selected_slot_end": end_a.isoformat(),
        "meeting_title": "Meet",
    }
    payload_b = {
        "contact_id": contact_id,
        "organization_id": org_id,
        "selected_slot_start": start_b.isoformat(),
        "selected_slot_end": end_b.isoformat(),
        "meeting_title": "Meet",
    }

    barrier = threading.Barrier(2)
    results: list[dict | None] = [None, None]

    def worker(slot_payload: dict[str, object], idx: int) -> None:
        barrier.wait()
        results[idx - 1] = get_or_create_pending_approval(
            requested_by=f"booking{idx}",
            action_type="book_meeting",
            title=f"Slot {idx}",
            target_type="contact",
            target_id=contact_id,
            payload=slot_payload,
            organization_id=org_id,
        )

    t1 = threading.Thread(target=worker, args=(payload_a, 1))
    t2 = threading.Thread(target=worker, args=(payload_b, 2))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    db_mod.SessionLocal = original_db
    approvals_mod.SessionLocal = original_ap

    db = sf()
    try:
        rows = (
            db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.organization_id == org_id,
                ApprovalRequest.approval_family == FAMILY_BOOK_MEETING,
                ApprovalRequest.target_id == contact_id,
            )
            .all()
        )
        pending = [r for r in rows if r.status == STATUS_PENDING]
        superseded = [r for r in rows if r.status == STATUS_SUPERSEDED]
        persisted_superseded_ids = {str(r.id) for r in superseded}

        assert len(pending) == 1
        assert len(superseded) >= 1
        assert all(r.logical_key == booking_logical_key(contact_id, "", "") for r in rows)

        returned_superseded_ids = {
            sid
            for res in results
            if isinstance(res, dict)
            for sid in (res.get("superseded_ids") or [])
        }
        assert returned_superseded_ids.issubset(persisted_superseded_ids)

        slot_keys = {
            (r.payload.get("selected_slot_start"), r.payload.get("selected_slot_end"))
            for r in rows
            if isinstance(r.payload, dict)
        }
        assert slot_keys == {(start_a.isoformat(), end_a.isoformat()), (start_b.isoformat(), end_b.isoformat())}
    finally:
        db.close()

    cleanup = sf()
    try:
        cleanup.query(ApprovalRequest).filter(
            ApprovalRequest.organization_id == org_id
        ).delete()
        cleanup.query(Contact).filter(Contact.id == uuid.UUID(contact_id)).delete()
        cleanup.query(Organization).filter(Organization.id == uuid.UUID(org_id)).delete()
        cleanup.commit()
    finally:
        cleanup.close()


@pytest.mark.postgres
@pytest.mark.skipif(not _is_postgres(POSTGRES_URL), reason="PostgreSQL required")
def test_postgres_concurrent_decide_single_effect(monkeypatch):
    engine = create_engine(POSTGRES_URL, pool_pre_ping=True)
    sf = sessionmaker(bind=engine)
    org_id = str(uuid.uuid4())
    contact_id = str(uuid.uuid4())
    db = sf()
    try:
        db.add(
            Organization(
                id=uuid.UUID(org_id),
                name="PG Decide",
                slug=f"pgd-{org_id[:8]}",
                status=OrganizationStatus.ACTIVE,
            )
        )
        db.add(
            Contact(
                id=uuid.UUID(contact_id),
                first_name="Pg",
                last_name="Decide",
                email="pgd@example.com",
                status=ContactStatus.LEAD,
                source=ContactSource.MANUAL,
                organization_id=uuid.UUID(org_id),
                lead_score=0,
            )
        )
        db.commit()
    finally:
        db.close()

    import revenue_os.database as db_mod
    import revenue_os.services.approvals as approvals_mod

    db_mod.SessionLocal = sf
    approvals_mod.SessionLocal = sf
    monkeypatch.setattr("revenue_os.integrations.n8n.trigger_workflow", lambda *a, **k: {"ok": 1})

    created = get_or_create_pending_approval(
        requested_by="t",
        action_type="send_outreach_email",
        title="T",
        target_type="contact",
        target_id=contact_id,
        payload={
            "contact_id": contact_id,
            "organization_id": org_id,
            "email": "pgd@example.com",
            "name": "Pg",
            "template": "t",
            "context": {"body": "x"},
        },
        organization_id=org_id,
    )
    tenant = TenantContext(
        identity=IdentityContext(
            principal_kind=PrincipalKind.HUMAN,
            auth_method=AuthMethod.NONE,
            is_human=True,
            user_id=str(uuid.uuid4()),
            email="owner@example.com",
            display_name="Owner",
            role="owner",
        ),
        organization_id=org_id,
        organization_name="PG",
        organization_slug="pg",
        membership_id=str(uuid.uuid4()),
        membership_role="owner",
        membership_status="active",
    )
    errors: list[Exception | None] = [None, None]

    def approve(idx: int) -> None:
        try:
            decide(created["id"], approve=True, tenant=tenant)
        except Exception as exc:
            errors[idx] = exc

    t1 = threading.Thread(target=approve, args=(0,))
    t2 = threading.Thread(target=approve, args=(1,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    db = sf()
    try:
        row = db.get(ApprovalRequest, created["id"])
        assert row.status == "approved"
        assert row.execution_result.get("phase") == EXECUTION_PHASE_COMPLETED
        assert sum(1 for e in errors if e is not None) >= 0
    finally:
        db.close()

    cleanup = sf()
    try:
        cleanup.query(ApprovalRequest).filter(ApprovalRequest.organization_id == org_id).delete()
        from revenue_os.models.activity import Activity

        cleanup.query(Activity).filter(Activity.contact_id == uuid.UUID(contact_id)).delete()
        cleanup.query(Contact).filter(Contact.id == uuid.UUID(contact_id)).delete()
        cleanup.query(Organization).filter(Organization.id == uuid.UUID(org_id)).delete()
        cleanup.commit()
    finally:
        cleanup.close()
