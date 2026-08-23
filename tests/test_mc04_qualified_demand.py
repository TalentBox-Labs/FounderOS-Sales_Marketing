"""MC04 — QualifiedDemand Marketing→Sales handoff tests."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import revenue_os.models  # noqa: F401 — register tables
import revenue_os.services.tenant_resolution as tenant_resolution_mod
import runner_api_routers.identity as identity_mod
import runner_api_routers.qualified_demand as qd_router
from revenue_os.auth import hash_password
from revenue_os.models.base import Base
from revenue_os.models.contact import ContactSource, ContactStatus
from revenue_os.models.organization import (
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationStatus,
)
from revenue_os.models.user import User
from revenue_os.services.qualified_demand_service import (
    ACTION_ACCEPTED,
    ACTION_HANDOFF,
    ACTION_REJECTED,
    QualifiedDemandPayload,
    accept_qualified_demand,
    register_marketing_handoff,
    reject_qualified_demand,
)
from runner_api import app

_DEMAND_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
_EMAIL = "demand@example.com"
_OPERATOR_EMAIL = "mc04-operator@example.com"
_OPERATOR_PASSWORD = "correct-horse-battery"


class _FakeAgentLog:
    def __init__(
        self,
        action_type: str,
        target_id: str,
        detail: dict | None = None,
        actor: str = "Krishna",
    ) -> None:
        self.action_type = action_type
        self.target_id = target_id
        self.target_type = "qualified_demand"
        self.detail = detail or {}
        self.actor = actor
        self.status = "completed"


class _FakeContact:
    def __init__(self, email: str = _EMAIL) -> None:
        self.id = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
        self.first_name = "Demand"
        self.last_name = "Lead"
        self.email = email
        self.phone = None
        self.linkedin_url = None
        self.designation = None
        self.source = ContactSource.WEB_FORM
        self.status = ContactStatus.LEAD
        self.lead_score = 0
        self.notes = None
        self.company_id = None
        self.company = None


class _FakeDB:
    def __init__(self) -> None:
        self.logs: list[_FakeAgentLog] = []
        self.contacts: list[_FakeContact] = []
        self.committed = False

    def add(self, obj) -> None:  # noqa: ANN001
        if hasattr(obj, "action_type"):
            self.logs.append(obj)
        elif hasattr(obj, "email"):
            if obj not in self.contacts:
                self.contacts.append(obj)

    def commit(self) -> None:
        self.committed = True

    def flush(self) -> None:
        return None

    def refresh(self, _obj) -> None:  # noqa: ANN001
        return None

    def close(self) -> None:
        return None

    def query(self, model):  # noqa: ANN001
        return _FakeQuery(self, model)


class _FakeQuery:
    def __init__(self, db: _FakeDB, model) -> None:  # noqa: ANN001
        self._db = db
        self._model = model
        self._filters: list = []

    def filter(self, *args) -> _FakeQuery:  # noqa: ANN001
        self._filters.extend(args)
        return self

    def first(self):  # noqa: ANN001
        name = getattr(self._model, "__name__", str(self._model))
        if name == "AgentActionLog":
            action_type = None
            target_id = None
            for f in self._filters:
                left = getattr(f, "left", None)
                right = getattr(f, "right", None)
                if left is not None and hasattr(left, "key"):
                    if left.key == "action_type" and right is not None:
                        action_type = getattr(right, "value", right)
                    if left.key == "target_id" and right is not None:
                        target_id = getattr(right, "value", right)
            for row in self._db.logs:
                if action_type and row.action_type != action_type:
                    continue
                if target_id and row.target_id != target_id:
                    continue
                return row
            return None
        if name == "Contact":
            email = None
            for f in self._filters:
                left = getattr(f, "left", None)
                right = getattr(f, "right", None)
                if left is not None and hasattr(left, "key") and left.key == "email":
                    email = getattr(right, "value", right)
            if email:
                for c in self._db.contacts:
                    if c.email == email:
                        return c
            return None
        if name == "Company":
            return None
        return None


def _payload() -> QualifiedDemandPayload:
    return QualifiedDemandPayload(
        demand_id=_DEMAND_ID,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        source="web_form",
        channel="landing-page",
        person={"email": _EMAIL, "name": "Demand Lead"},
        marketing_qualification={"tier": "mql", "score": 72},
        content_attribution={"utm_source": "website"},
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def human_session(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path
) -> str:
    """SaaS S2+: mutations resolve tenant from a real logged-in session with an
    active OrganizationMembership — a human-looking requested_by string alone
    no longer satisfies require_tenant_mutation()."""
    engine = create_engine(f"sqlite:///{tmp_path / 'mc04_identity.db'}")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    monkeypatch.setattr(identity_mod, "SessionLocal", session_factory)
    monkeypatch.setattr(tenant_resolution_mod, "SessionLocal", session_factory)

    db = session_factory()
    try:
        user = User(
            email=_OPERATOR_EMAIL,
            hashed_password=hash_password(_OPERATOR_PASSWORD),
            full_name="Krishna Founder",
            role="owner",
            is_active=1,
        )
        db.add(user)
        db.flush()
        org = Organization(name="MC04 Org", slug="mc04-org", status=OrganizationStatus.ACTIVE)
        db.add(org)
        db.flush()
        db.add(
            OrganizationMembership(
                user_id=user.id,
                organization_id=org.id,
                role="owner",
                status=MembershipStatus.ACTIVE,
            )
        )
        db.commit()
        org_id = str(org.id)
    finally:
        db.close()

    r = client.post(
        "/login",
        data={"email": _OPERATOR_EMAIL, "password": _OPERATOR_PASSWORD, "next": "/cockpit"},
        follow_redirects=False,
    )
    assert r.status_code == 303, r.text
    return org_id


def test_register_handoff_does_not_create_contact() -> None:
    db = _FakeDB()
    payload = _payload()
    result = register_marketing_handoff(db, payload, "Krishna Founder")
    assert result["handoff_registered"] is True
    assert db.contacts == []
    assert any(log.action_type == ACTION_HANDOFF for log in db.logs)


def test_accept_creates_canonical_contact() -> None:
    db = _FakeDB()
    payload = _payload()
    register_marketing_handoff(db, payload, "Krishna Founder")
    result = accept_qualified_demand(db, _DEMAND_ID, "Krishna Sales")
    assert result["created"] is True
    assert result["contact_id"]
    assert result["deal_created"] is False
    assert db.contacts[0].status == ContactStatus.LEAD
    assert db.contacts[0].source == ContactSource.WEB_FORM


def test_accept_idempotent() -> None:
    db = _FakeDB()
    payload = _payload()
    register_marketing_handoff(db, payload, "Krishna Founder")
    first = accept_qualified_demand(db, _DEMAND_ID, "Krishna Sales")
    second = accept_qualified_demand(db, _DEMAND_ID, "Krishna Sales")
    assert first["contact_id"] == second["contact_id"]
    assert second["idempotent"] is True
    assert len(db.contacts) == 1


def test_duplicate_email_merges_not_duplicates() -> None:
    db = _FakeDB()
    db.contacts.append(_FakeContact(_EMAIL))
    payload = _payload()
    register_marketing_handoff(db, payload, "Krishna Founder")
    result = accept_qualified_demand(db, _DEMAND_ID, "Krishna Sales")
    assert result["merged"] is True
    assert result["created"] is False
    assert len(db.contacts) == 1


def test_reject_audit_without_contact() -> None:
    db = _FakeDB()
    register_marketing_handoff(db, _payload(), "Krishna Founder")
    result = reject_qualified_demand(db, _DEMAND_ID, "Krishna Sales", "ICP mismatch")
    assert result["rejected"] is True
    assert db.contacts == []
    assert any(log.action_type == ACTION_REJECTED for log in db.logs)


def test_runner_handoff_and_accept_flow(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, human_session: str
) -> None:
    db = _FakeDB()
    monkeypatch.setattr(qd_router, "SessionLocal", lambda: db)
    events: list = []
    monkeypatch.setattr(qd_router.EventBus, "publish", lambda e: events.append(e))

    handoff = client.post(
        "/api/v1/marketing/qualified-demand/handoff",
        json={
            "demand_id": _DEMAND_ID,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "source": "web_form",
            "person": {"email": _EMAIL, "name": "Demand Lead"},
            "marketing_qualification": {"tier": "mql"},
            "requested_by": "Krishna Founder",
        },
    )
    assert handoff.status_code == 200
    assert handoff.json()["handoff_registered"] is True
    assert db.contacts == []

    accept = client.post(
        "/api/v1/sales/intake/demand/accept",
        json={"demand_id": _DEMAND_ID, "requested_by": "Krishna Sales"},
    )
    assert accept.status_code == 200
    body = accept.json()
    assert body["created"] is True
    assert body["status"] == "lead"
    assert len(db.contacts) == 1


def test_runner_rejects_agent_handoff(client: TestClient) -> None:
    r = client.post(
        "/api/v1/marketing/qualified-demand/handoff",
        json={
            "demand_id": str(uuid4()),
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "source": "web_form",
            "person": {"email": "x@example.com", "name": "X"},
            "requested_by": "agent",
        },
    )
    assert r.status_code == 403


def test_runner_rejects_agent_intake(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = _FakeDB()
    register_marketing_handoff(db, _payload(), "Krishna Founder")
    monkeypatch.setattr(qd_router, "SessionLocal", lambda: db)
    r = client.post(
        "/api/v1/sales/intake/demand/accept",
        json={"demand_id": _DEMAND_ID, "requested_by": "ai:copilot"},
    )
    assert r.status_code == 403
    assert db.contacts == []


def test_runner_rejects_invalid_payload(client: TestClient) -> None:
    r = client.post(
        "/api/v1/marketing/qualified-demand/handoff",
        json={
            "demand_id": "not-a-uuid",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "source": "web_form",
            "person": {"email": "bad", "name": "X"},
            "requested_by": "Krishna",
        },
    )
    assert r.status_code == 422


def test_accept_without_handoff_rejected(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(qd_router, "SessionLocal", lambda: _FakeDB())
    r = client.post(
        "/api/v1/sales/intake/demand/accept",
        json={"demand_id": _DEMAND_ID, "requested_by": "Krishna"},
    )
    assert r.status_code == 422


def test_reject_creates_audit(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, human_session: str
) -> None:
    db = _FakeDB()
    register_marketing_handoff(db, _payload(), "Krishna Founder", organization_id=human_session)
    monkeypatch.setattr(qd_router, "SessionLocal", lambda: db)
    r = client.post(
        "/api/v1/sales/intake/demand/reject",
        json={
            "demand_id": _DEMAND_ID,
            "requested_by": "Krishna Sales",
            "reason": "Spam",
        },
    )
    assert r.status_code == 200
    assert r.json()["rejected"] is True
    assert db.contacts == []


def test_handoff_idempotent(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, human_session: str
) -> None:
    db = _FakeDB()
    monkeypatch.setattr(qd_router, "SessionLocal", lambda: db)
    body = {
        "demand_id": _DEMAND_ID,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "source": "web_form",
        "person": {"email": _EMAIL, "name": "Demand Lead"},
        "requested_by": "Krishna Founder",
    }
    r1 = client.post("/api/v1/marketing/qualified-demand/handoff", json=body)
    r2 = client.post("/api/v1/marketing/qualified-demand/handoff", json=body)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json()["idempotent"] is True
