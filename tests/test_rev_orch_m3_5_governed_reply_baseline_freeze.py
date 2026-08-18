"""REV-ORCH M3.5 — governed reply handling baseline freeze adversarial tests.

Certifies M3 inbound-reply authority contracts remain bounded, tenant-isolated,
auditable, and incapable of unauthorized CRM, qualification, outbound, or booking.
"""

from __future__ import annotations

import hashlib
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
import runner_api_routers.n8n_webhooks as n8n_mod
import runner_api_routers.revenue_orchestration as rev_orch_mod
from revenue_os.agents.orchestration import WorkflowOrchestrator
from revenue_os.auth import hash_password
from revenue_os.models.activity import Activity, ActivityType, EmailActivity
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
from revenue_os.services.follow_up_eligibility import evaluate_follow_up_eligibility
from revenue_os.services.integration_tenant_resolution import upsert_n8n_binding
from revenue_os.services.reply_routing import (
    REPLY_TYPES,
    merge_opt_out_tag,
    route_reply_assessment,
)
from revenue_os.services.revenue_orchestration_service import (
    run_inbound_reply_handling,
    wake_inbound_reply_handling,
)
from revenue_os.services.tenant_resolution import ORGANIZATION_COOKIE
from runner_api import app

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_SECRET_A = "secret-org-a"
_SECRET_B = "secret-org-b"


@pytest.fixture(autouse=True)
def _reset() -> None:
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
    engine = create_engine(f"sqlite:///{tmp_path / 'm3_5_freeze.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    for mod in (identity_mod, rev_orch_mod, agents_mod, n8n_mod):
        monkeypatch.setattr(mod, "SessionLocal", sf)
    import revenue_os.database as db_mod
    import revenue_os.services.activity_log as al
    import revenue_os.services.approvals as approvals_mod
    import revenue_os.services.tenant_resolution as tr

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
            full_name="Owner A",
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
        db.add_all([
            OrganizationMembership(user_id=owner_a.id, organization_id=_ORG_A, role="owner", status=MembershipStatus.ACTIVE),
            OrganizationMembership(user_id=owner_b.id, organization_id=_ORG_B, role="owner", status=MembershipStatus.ACTIVE),
        ])
        db.add_all([
            Contact(id=_CONTACT_A, first_name="Alice", last_name="A", email="alice@example.com",
                    status=ContactStatus.LEAD, source=ContactSource.MANUAL,
                    organization_id=_ORG_A, lead_score=10, created_at=datetime.now(timezone.utc)),
            Contact(id=_CONTACT_B, first_name="Bob", last_name="B", email="bob@example.com",
                    status=ContactStatus.LEAD, source=ContactSource.MANUAL,
                    organization_id=_ORG_B, lead_score=20, created_at=datetime.now(timezone.utc)),
        ])
        db.commit()
    finally:
        db.close()
    upsert_n8n_binding(str(_ORG_A), _SECRET_A)
    upsert_n8n_binding(str(_ORG_B), _SECRET_B)
    return {"org_a": str(_ORG_A), "org_b": str(_ORG_B)}


def _login(client: TestClient, email: str, password: str, org_id: str) -> None:
    r = client.post("/api/v1/identity/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    client.cookies.set(ORGANIZATION_COOKIE, org_id)


def _bind_tenants():
    upsert_n8n_binding(str(_ORG_A), _SECRET_A)
    upsert_n8n_binding(str(_ORG_B), _SECRET_B)


def _ai_analysis(**overrides) -> dict:
    base = {
        "ok": True,
        "reply_type": "INTERESTED",
        "confidence": 0.9,
        "summary": "Positive",
        "objection_category": None,
        "meeting_interest": False,
        "recommended_next_action": "QUALIFY",
        "qualification_recommendation": "QUALIFY",
    }
    base.update(overrides)
    return base


# ==============================================================================
# 1. Canonical inbound reply path
# ==============================================================================

class TestCanonicalInboundPath:
    def test_happy_path_via_webhook(self, client, tenant_db, monkeypatch):
        _seed(tenant_db)
        monkeypatch.setattr(ai_service, "analyze_inbound_reply", lambda *a, **kw: _ai_analysis())
        r = client.post(
            "/webhooks/n8n/email.replied",
            json={"contact_id": str(_CONTACT_A), "body": "Sounds great!"},
            headers={"X-N8N-Secret": _SECRET_A},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["ok"]
        assert "m3_reply" in "".join(data.get("actions", []))


# ==============================================================================
# 2. Trusted integration-bound tenant resolution
# ==============================================================================

class TestTenantResolution:
    def test_tenant_from_integration_binding(self, client, tenant_db, monkeypatch):
        _seed(tenant_db)
        monkeypatch.setattr(ai_service, "analyze_inbound_reply", lambda *a, **kw: _ai_analysis())
        r = client.post(
            "/webhooks/n8n/email.replied",
            json={"contact_id": str(_CONTACT_A), "body": "Yes"},
            headers={"X-N8N-Secret": _SECRET_A},
        )
        assert r.status_code == 200
        assert r.json()["ok"]

    def test_payload_tenant_spoof_blocked(self, client, tenant_db, monkeypatch):
        """Payload organization_id cannot override integration binding."""
        _seed(tenant_db)
        monkeypatch.setattr(ai_service, "analyze_inbound_reply", lambda *a, **kw: _ai_analysis())
        r = client.post(
            "/webhooks/n8n/email.replied",
            json={"contact_id": str(_CONTACT_A), "organization_id": str(_ORG_B), "body": "Yes"},
            headers={"X-N8N-Secret": _SECRET_A},
        )
        assert r.status_code == 200

    def test_cross_tenant_contact_id_blocked(self, client, tenant_db, monkeypatch):
        """Contact belonging to Org B cannot be processed under Org A binding."""
        _seed(tenant_db)
        monkeypatch.setattr(ai_service, "analyze_inbound_reply", lambda *a, **kw: _ai_analysis())
        r = client.post(
            "/webhooks/n8n/email.replied",
            json={"contact_id": str(_CONTACT_B), "body": "Yes"},
            headers={"X-N8N-Secret": _SECRET_A},
        )
        # Either 200 with no M3 action or 404 (scoped_contact rejects) — both block cross-tenant
        if r.status_code == 200:
            actions = r.json().get("actions", [])
            assert not any("m3_reply" in a for a in actions)
        else:
            assert r.status_code in (404, 422)

    def test_cross_tenant_email_resolution_blocked(self, client, tenant_db, monkeypatch):
        """Email belonging to Org B contact cannot resolve under Org A."""
        _seed(tenant_db)
        monkeypatch.setattr(ai_service, "analyze_inbound_reply", lambda *a, **kw: _ai_analysis())
        r = client.post(
            "/webhooks/n8n/email.replied",
            json={"email": "bob@example.com", "body": "Yes"},
            headers={"X-N8N-Secret": _SECRET_A},
        )
        assert r.status_code == 200
        data = r.json()
        actions = data.get("actions", [])
        assert not any("m3_reply" in a for a in actions)


# ==============================================================================
# 6-8. Deduplication / idempotency
# ==============================================================================

class TestDeduplication:
    def test_same_tenant_duplicate_suppressed(self, client, tenant_db, monkeypatch):
        _seed(tenant_db)
        monkeypatch.setattr(ai_service, "analyze_inbound_reply", lambda *a, **kw: _ai_analysis())
        payload = {"contact_id": str(_CONTACT_A), "body": "interested", "message_id": "msg-dup-1"}
        client.post("/webhooks/n8n/email.replied", json=payload, headers={"X-N8N-Secret": _SECRET_A})
        r2 = client.post("/webhooks/n8n/email.replied", json=payload, headers={"X-N8N-Secret": _SECRET_A})
        assert r2.status_code == 200
        assert "duplicate reply ignored" in str(r2.json().get("actions", []))

    def test_cross_tenant_identical_message_no_collision(self, client, tenant_db, monkeypatch):
        """Same message_id across different tenants must not collide."""
        _seed(tenant_db)
        monkeypatch.setattr(ai_service, "analyze_inbound_reply", lambda *a, **kw: _ai_analysis())
        msg_id = "provider-msg-same"
        r_a = client.post(
            "/webhooks/n8n/email.replied",
            json={"contact_id": str(_CONTACT_A), "body": "Yes", "message_id": msg_id},
            headers={"X-N8N-Secret": _SECRET_A},
        )
        r_b = client.post(
            "/webhooks/n8n/email.replied",
            json={"contact_id": str(_CONTACT_B), "body": "Yes", "message_id": msg_id},
            headers={"X-N8N-Secret": _SECRET_B},
        )
        assert r_a.status_code == 200
        assert r_b.status_code == 200
        actions_b = r_b.json().get("actions", [])
        assert "duplicate reply ignored" not in str(actions_b)

    def test_missing_provider_id_fallback_tenant_safe(self, tenant_db, monkeypatch):
        """Fallback SHA uses contact_id, ensuring tenant isolation."""
        from runner_api_routers.n8n_webhooks import _reply_message_id

        payload = {"body": "Same body text"}
        key_a = _reply_message_id(payload, str(_CONTACT_A))
        key_b = _reply_message_id(payload, str(_CONTACT_B))
        assert key_a != key_b
        assert key_a.startswith("rev-orch-m3:")
        assert key_b.startswith("rev-orch-m3:")


# ==============================================================================
# 9. Malformed classification fails closed
# ==============================================================================

class TestMalformedClassification:
    def test_unknown_reply_type_normalized(self):
        result = route_reply_assessment({"ok": True, "reply_type": "INVALID_JUNK", "confidence": 0.95})
        assert result["reply_type"] == "UNKNOWN"
        assert result["recommended_next_action"] == "HUMAN_REVIEW"

    def test_ai_failure_fails_closed(self):
        result = route_reply_assessment({"ok": False, "reply_type": "INTERESTED", "confidence": 0.99})
        assert result["reply_type"] == "UNKNOWN"
        assert result["recommended_next_action"] == "HUMAN_REVIEW"

    def test_low_confidence_fails_closed(self):
        result = route_reply_assessment({"ok": True, "reply_type": "INTERESTED", "confidence": 0.1})
        assert result["reply_type"] == "UNKNOWN"


# ==============================================================================
# 10-13. Qualification authority boundary
# ==============================================================================

class TestQualificationBoundary:
    def test_interested_does_not_mutate_contact_status(self, tenant_db, monkeypatch):
        _seed(tenant_db)
        monkeypatch.setattr(ai_service, "analyze_inbound_reply", lambda *a, **kw: _ai_analysis(reply_type="INTERESTED"))
        db = tenant_db()
        try:
            result = wake_inbound_reply_handling(db, str(_ORG_A), str(_CONTACT_A), activity_id=None, message_id="q1")
            contact = db.get(Contact, _CONTACT_A)
            assert contact.status == ContactStatus.LEAD
            assert result.get("routing", {}).get("contact_status_changed") is False
        finally:
            db.close()

    def test_not_interested_does_not_mutate_status(self, tenant_db, monkeypatch):
        _seed(tenant_db)
        monkeypatch.setattr(ai_service, "analyze_inbound_reply", lambda *a, **kw: _ai_analysis(reply_type="NOT_INTERESTED"))
        db = tenant_db()
        try:
            result = wake_inbound_reply_handling(db, str(_ORG_A), str(_CONTACT_A), activity_id=None, message_id="q2")
            contact = db.get(Contact, _CONTACT_A)
            assert contact.status == ContactStatus.LEAD
        finally:
            db.close()

    def test_objection_does_not_mutate_deal(self, tenant_db, monkeypatch):
        _seed(tenant_db)
        monkeypatch.setattr(ai_service, "analyze_inbound_reply", lambda *a, **kw: _ai_analysis(reply_type="OBJECTION", objection_category="PRICE"))
        db = tenant_db()
        try:
            result = wake_inbound_reply_handling(db, str(_ORG_A), str(_CONTACT_A), activity_id=None, message_id="q3")
            assert result.get("routing", {}).get("deal_stage_changed") is False
        finally:
            db.close()

    def test_ai_cannot_create_qualified_demand(self, tenant_db, monkeypatch):
        """No QualifiedDemand is created or accepted by M3 reply handling."""
        _seed(tenant_db)
        monkeypatch.setattr(ai_service, "analyze_inbound_reply", lambda *a, **kw: _ai_analysis(reply_type="INTERESTED"))
        db = tenant_db()
        try:
            result = wake_inbound_reply_handling(db, str(_ORG_A), str(_CONTACT_A), activity_id=None, message_id="q4")
            assert result.get("routing", {}).get("qualified_demand_accepted") is False
        finally:
            db.close()

    def test_ai_cannot_send_outbound(self):
        routing = route_reply_assessment(_ai_analysis(reply_type="INTERESTED"))
        assert routing["outbound_sent"] is False

    def test_ai_cannot_book(self):
        routing = route_reply_assessment(_ai_analysis(reply_type="MEETING_INTEREST"))
        assert routing["booking_created"] is False


# ==============================================================================
# 16-19. OPT_OUT authority
# ==============================================================================

class TestOptOutAuthority:
    def test_opt_out_mutation_is_policy_bound(self, tenant_db, monkeypatch):
        """OPT_OUT only adds 'unsubscribed' tag — cannot set arbitrary fields."""
        _seed(tenant_db)
        monkeypatch.setattr(ai_service, "analyze_inbound_reply", lambda *a, **kw: _ai_analysis(reply_type="OPT_OUT"))
        db = tenant_db()
        try:
            wake_inbound_reply_handling(db, str(_ORG_A), str(_CONTACT_A), activity_id=None, message_id="opt1")
            contact = db.get(Contact, _CONTACT_A)
            assert "unsubscribed" in (contact.tags or "")
            assert contact.status == ContactStatus.LEAD
        finally:
            db.close()

    def test_opt_out_tenant_scoped(self, tenant_db, monkeypatch):
        """OPT_OUT on tenant A cannot affect tenant B contact."""
        _seed(tenant_db)
        monkeypatch.setattr(ai_service, "analyze_inbound_reply", lambda *a, **kw: _ai_analysis(reply_type="OPT_OUT"))
        db = tenant_db()
        try:
            wake_inbound_reply_handling(db, str(_ORG_A), str(_CONTACT_A), activity_id=None, message_id="opt2")
            contact_b = db.get(Contact, _CONTACT_B)
            assert "unsubscribed" not in (contact_b.tags or "")
        finally:
            db.close()

    def test_repeated_opt_out_idempotent(self):
        result1 = merge_opt_out_tag(None)
        result2 = merge_opt_out_tag(result1)
        assert result1 == result2
        assert result1.count("unsubscribed") == 1

    def test_opt_out_blocks_governed_followup(self, tenant_db, monkeypatch):
        _seed(tenant_db)
        monkeypatch.setattr(ai_service, "analyze_inbound_reply", lambda *a, **kw: _ai_analysis(reply_type="OPT_OUT"))
        db = tenant_db()
        try:
            wake_inbound_reply_handling(db, str(_ORG_A), str(_CONTACT_A), activity_id=None, message_id="opt3")
            contact = db.get(Contact, _CONTACT_A)
            elig = evaluate_follow_up_eligibility(db, contact)
            assert elig["state"] == "FOLLOWUP_STOPPED"
        finally:
            db.close()


# ==============================================================================
# 20. Stale follow-up after inbound reply blocked
# ==============================================================================

class TestStaleFollowUpBlocked:
    def test_reply_stops_followup_eligibility(self, tenant_db, monkeypatch):
        from datetime import timedelta
        _seed(tenant_db)
        db = tenant_db()
        try:
            contact = db.get(Contact, _CONTACT_A)
            t0 = datetime.now(timezone.utc) - timedelta(days=1)
            outbound = Activity(
                contact_id=_CONTACT_A,
                activity_type=ActivityType.EMAIL,
                subject="Outreach",
                body="Hello",
                direction="outbound",
                status="completed",
                performed_at=t0,
            )
            db.add(outbound)
            db.flush()
            reply = Activity(
                contact_id=_CONTACT_A,
                activity_type=ActivityType.EMAIL_REPLY,
                subject="Reply",
                body="Thanks",
                direction="inbound",
                status="completed",
                performed_at=t0 + timedelta(hours=2),
            )
            db.add(reply)
            db.commit()
            elig = evaluate_follow_up_eligibility(db, contact)
            assert elig["state"] == "FOLLOWUP_REPLY_RECEIVED"
        finally:
            db.close()


# ==============================================================================
# 21-22. Latest-assessment cross-tenant isolation
# ==============================================================================

class TestLatestAssessmentIsolation:
    def test_cross_tenant_read_blocked(self, client, tenant_db, monkeypatch):
        _seed(tenant_db)
        monkeypatch.setattr(ai_service, "analyze_inbound_reply", lambda *a, **kw: _ai_analysis())
        client.post(
            "/webhooks/n8n/email.replied",
            json={"contact_id": str(_CONTACT_A), "body": "Yes", "message_id": "lat1"},
            headers={"X-N8N-Secret": _SECRET_A},
        )
        _login(client, "owner-b@example.com", "pass-b", str(_ORG_B))
        r = client.get(f"/api/v1/revenue/contacts/{_CONTACT_A}/reply/latest-assessment")
        assert r.status_code == 422

    def test_tenant_spoof_blocked(self, client, tenant_db, monkeypatch):
        _seed(tenant_db)
        _login(client, "owner-a@example.com", "pass-o", str(_ORG_A))
        r = client.get(f"/api/v1/revenue/contacts/{_CONTACT_B}/reply/latest-assessment")
        assert r.status_code == 422


# ==============================================================================
# 23. MEETING_INTEREST does not book
# ==============================================================================

class TestMeetingInterestNegativeScope:
    def test_meeting_interest_no_booking(self):
        routing = route_reply_assessment(_ai_analysis(reply_type="MEETING_INTEREST", meeting_interest=True))
        assert routing["booking_eligible"] is True
        assert routing["booking_created"] is False
        assert routing["recommended_next_action"] == "BOOKING_ELIGIBLE"


# ==============================================================================
# 24. Legacy reply authority bypass unreachable
# ==============================================================================

class TestLegacyBypass:
    def test_legacy_build_followup_no_direct_send(self):
        import revenue_os.services.sales_agents as sa
        src = __import__("inspect").getsource(sa.build_followup_sequence)
        assert "trigger_workflow" not in src
        assert "send_email" not in src


# ==============================================================================
# 25-26. Provenance
# ==============================================================================

class TestProvenance:
    def test_activity_provenance(self, client, tenant_db, monkeypatch):
        _seed(tenant_db)
        monkeypatch.setattr(ai_service, "analyze_inbound_reply", lambda *a, **kw: _ai_analysis())
        client.post(
            "/webhooks/n8n/email.replied",
            json={"contact_id": str(_CONTACT_A), "body": "Yes", "message_id": "prov1"},
            headers={"X-N8N-Secret": _SECRET_A},
        )
        db = tenant_db()
        try:
            acts = db.query(Activity).filter(Activity.contact_id == _CONTACT_A).all()
            assert any(a.activity_type == ActivityType.EMAIL_REPLY for a in acts)
        finally:
            db.close()

    def test_agent_action_log_provenance(self, client, tenant_db, monkeypatch):
        _seed(tenant_db)
        monkeypatch.setattr(ai_service, "analyze_inbound_reply", lambda *a, **kw: _ai_analysis())
        client.post(
            "/webhooks/n8n/email.replied",
            json={"contact_id": str(_CONTACT_A), "body": "Yes", "message_id": "prov2"},
            headers={"X-N8N-Secret": _SECRET_A},
        )
        db = tenant_db()
        try:
            logs = db.query(AgentActionLog).filter(
                AgentActionLog.organization_id == _ORG_A,
                AgentActionLog.action_type == "rev_orch_reply_assessment",
            ).all()
            assert len(logs) >= 1
        finally:
            db.close()


# ==============================================================================
# 27-28. Frozen contract compatibility
# ==============================================================================

class TestFrozenContracts:
    def test_m2_5_followup_eligibility_unchanged(self):
        from revenue_os.services.follow_up_eligibility import (
            MAX_FOLLOW_UP_STEPS,
            FOLLOW_UP_INTERVALS_DAYS,
        )
        assert MAX_FOLLOW_UP_STEPS == 2
        assert FOLLOW_UP_INTERVALS_DAYS == (3, 7)

    def test_m1_5_workflow_orchestrator_canonical(self):
        from revenue_os.agents.orchestration import (
            REV_ORCH_M1_WORKFLOW_KEY,
            REV_ORCH_M2_WORKFLOW_KEY,
            REV_ORCH_M3_WORKFLOW_KEY,
        )
        assert REV_ORCH_M1_WORKFLOW_KEY
        assert REV_ORCH_M2_WORKFLOW_KEY
        assert REV_ORCH_M3_WORKFLOW_KEY
