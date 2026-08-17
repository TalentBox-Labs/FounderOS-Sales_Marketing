"""UI1.1 — mutation boundary authority remediation adversarial tests."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

import runner_api_routers.crm as crm
import runner_api_routers.n8n_webhooks as n8n_mod
from revenue_os.models.contact import ContactSource, ContactStatus
from revenue_os.services.deal_automation_service import apply_deal_stage_update
from revenue_os.services.lead_scoring_service import apply_contact_status_update
from revenue_os.services.mutation_authority import HumanAuthorityError
from revenue_os.services.qualified_demand_service import (
    QualifiedDemandPayload,
    accept_qualified_demand,
    register_marketing_handoff,
    reject_qualified_demand,
)
from runner_api import app

_CONTACT_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
_DEMAND_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd"
_HUMAN = "Krishna Sales"
_AGENT = "agent:hermes"


class _FakeContact:
    def __init__(self, status: ContactStatus = ContactStatus.LEAD) -> None:
        self.id = UUID(_CONTACT_ID)
        self.first_name = "Test"
        self.last_name = "Lead"
        self.email = "ui11@example.com"
        self.status = status
        self.lead_score = 50
        self.phone = None
        self.designation = None
        self.linkedin_url = None
        self.source = ContactSource.WEB_FORM
        self.created_at = datetime.now(timezone.utc)
        self.last_contacted_at = None
        self.company = None


class _FakeDeal:
    def __init__(self, stage) -> None:  # noqa: ANN001
        from revenue_os.models.deal import DealStage

        self.id = UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
        self.stage = stage
        self.probability = 50
        self.closed_at = None
        if stage in (DealStage.CLOSED_WON, DealStage.CLOSED_LOST):
            self.closed_at = datetime.now(timezone.utc)


class _FakeAgentLog:
    def __init__(
        self,
        action_type: str,
        target_id: str,
        detail: dict | None = None,
        actor: str = _HUMAN,
    ) -> None:
        self.action_type = action_type
        self.target_id = target_id
        self.target_type = "qualified_demand"
        self.detail = detail or {}
        self.actor = actor
        self.status = "completed"


class _FakeDB:
    def __init__(self, contact: _FakeContact | None = None) -> None:
        self._contact = contact
        self.committed = False
        self.logs: list[_FakeAgentLog] = []
        self.contacts: list = []

    def get(self, _model, _id):  # noqa: ANN001
        return self._contact

    def query(self, model):  # noqa: ANN001
        return _FakeQuery(self, model)

    def add(self, obj) -> None:  # noqa: ANN001
        if hasattr(obj, "action_type"):
            self.logs.append(obj)
        elif hasattr(obj, "email"):
            self.contacts.append(obj)

    def commit(self) -> None:
        self.committed = True

    def refresh(self, _obj) -> None:  # noqa: ANN001
        return None

    def close(self) -> None:
        return None


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
            contact_id = None
            email = None
            for f in self._filters:
                left = getattr(f, "left", None)
                right = getattr(f, "right", None)
                if left is not None and hasattr(left, "key"):
                    if left.key == "email" and right is not None:
                        email = getattr(right, "value", right)
                    if left.key == "id" and right is not None:
                        contact_id = str(getattr(right, "value", right))
            if email:
                for c in self._db.contacts:
                    if c.email == email:
                        return c
            if contact_id and self._db._contact is not None:
                if str(self._db._contact.id) == contact_id:
                    return self._db._contact
            return self._db._contact
        return None


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _demand_payload() -> QualifiedDemandPayload:
    return QualifiedDemandPayload(
        demand_id=_DEMAND_ID,
        occurred_at="2026-08-13T10:00:00Z",
        source="web_form",
        person={"email": "demand@example.com", "name": "Demand Lead"},
    )


# --- Bypass UI1-B1: JWT PUT status field ---


def test_jwt_put_contact_status_change_blocked() -> None:
    contact = _FakeContact(status=ContactStatus.LEAD)
    db = _FakeDB(contact)
    from fastapi import HTTPException
    from revenue_os.api.v1.contacts import ContactUpdate, update_contact

    with pytest.raises(HTTPException) as exc:
        update_contact(
            _CONTACT_ID,
            ContactUpdate(status=ContactStatus.QUALIFIED),
            db=db,  # type: ignore[arg-type]
        )
    assert exc.value.status_code == 403
    assert contact.status == ContactStatus.LEAD


# --- Bypass UI1-B2: n8n meeting.booked auto-qualify ---


def test_n8n_meeting_booked_does_not_mutate_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contact = _FakeContact(status=ContactStatus.PROSPECT)
    db = _FakeDB(contact)
    monkeypatch.setattr(n8n_mod, "SessionLocal", lambda: db)
    monkeypatch.setattr(n8n_mod, "_verify_n8n_auth", lambda: "ok")
    events: list = []
    monkeypatch.setattr(n8n_mod.EventBus, "publish", lambda e: events.append(e))

    client = TestClient(app)
    r = client.post(
        f"/webhooks/n8n/meeting.booked",
        json={"contact_id": _CONTACT_ID},
        headers={"Authorization": "Bearer test"},
    )
    assert r.status_code == 200
    assert contact.status == ContactStatus.PROSPECT
    assert db.committed is False
    assert any(e.data.get("human_gate_required") for e in events)


# --- Bypass UI1-B3: service-layer direct call ---


def test_service_contact_status_blocks_agent_direct_call() -> None:
    contact = _FakeContact(status=ContactStatus.LEAD)
    with pytest.raises(HumanAuthorityError, match="Human requester required"):
        apply_contact_status_update(
            _FakeDB(contact), contact, ContactStatus.QUALIFIED, requested_by=_AGENT
        )  # type: ignore[arg-type]
    assert contact.status == ContactStatus.LEAD


def test_service_deal_stage_blocks_agent_direct_call() -> None:
    from revenue_os.models.deal import DealStage

    deal = _FakeDeal(DealStage.DISCOVERY)
    with pytest.raises(HumanAuthorityError, match="Human requester required"):
        apply_deal_stage_update(
            _FakeDB(), deal, DealStage.PROPOSAL, requested_by="AI"
        )  # type: ignore[arg-type]


def test_service_accept_demand_blocks_spoofed_automation() -> None:
    db = _FakeDB()
    register_marketing_handoff(db, _demand_payload(), _HUMAN)
    with pytest.raises(HumanAuthorityError):
        accept_qualified_demand(db, _DEMAND_ID, _AGENT)


def test_service_reject_demand_blocks_automation_identity() -> None:
    db = _FakeDB()
    register_marketing_handoff(db, _demand_payload(), _HUMAN)
    with pytest.raises(HumanAuthorityError):
        reject_qualified_demand(db, _DEMAND_ID, _AGENT, "bad fit")


def test_service_human_mutation_succeeds() -> None:
    contact = _FakeContact(status=ContactStatus.LEAD)
    result = apply_contact_status_update(
        _FakeDB(contact), contact, ContactStatus.QUALIFIED, requested_by=_HUMAN
    )  # type: ignore[arg-type]
    assert result["changed"] is True
    assert contact.status == ContactStatus.QUALIFIED


def test_runner_contact_status_blocks_spoofed_human(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    contact = _FakeContact(status=ContactStatus.LEAD)
    monkeypatch.setattr(crm, "SessionLocal", lambda: _FakeDB(contact))
    r = client.patch(
        f"/api/v1/crm/contacts/{_CONTACT_ID}/status",
        json={"status": "qualified", "requested_by": _AGENT},
    )
    assert r.status_code == 403
    assert contact.status == ContactStatus.LEAD


def test_runner_contact_status_valid_human_passes(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    contact = _FakeContact(status=ContactStatus.LEAD)
    monkeypatch.setattr(crm, "SessionLocal", lambda: _FakeDB(contact))
    r = client.patch(
        f"/api/v1/crm/contacts/{_CONTACT_ID}/status",
        json={"status": "qualified", "requested_by": _HUMAN},
    )
    assert r.status_code == 200
    assert contact.status == ContactStatus.QUALIFIED
