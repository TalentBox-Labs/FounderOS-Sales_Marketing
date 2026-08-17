"""MC06 — CommercialOutcome Sales→Revenue handoff tests."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

import runner_api_routers.commercial_outcome as co_router
from revenue_os.models.deal import DealStage
from revenue_os.services.commercial_outcome_service import (
    ACTION_ACCEPTED,
    ACTION_HANDOFF,
    ACTION_REJECTED,
    CommercialOutcomePayload,
    accept_commercial_outcome,
    register_commercial_outcome_handoff,
    reject_commercial_outcome,
)
from revenue_os.services.deal_automation_service import apply_deal_stage_update
from revenue_os.services.lead_scoring_service import apply_contact_status_update
from revenue_os.services.mutation_authority import HumanAuthorityError
from revenue_os.services.qualified_demand_service import (
    QualifiedDemandPayload,
    accept_qualified_demand,
    register_marketing_handoff,
)
from runner_api import app

_DEAL_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_OUTCOME_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


class _FakeDeal:
    def __init__(self, stage: DealStage = DealStage.CLOSED_WON) -> None:
        self.id = UUID(_DEAL_ID)
        self.name = "Closed Deal"
        self.stage = stage
        self.probability = 100
        self.value = 25000.0
        self.currency = "USD"
        self.contact_id = None
        self.closed_at = datetime.now(timezone.utc)
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


class _FakeContact:
    def __init__(self) -> None:
        self.id = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
        self.status = "lead"
        self.lead_score = 0
        self.notes = None
        self.email = "mc06@example.com"


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
        self.target_type = "commercial_outcome"
        self.detail = detail or {}
        self.actor = actor
        self.status = "completed"


class _FakeDB:
    def __init__(self, deal: _FakeDeal | None) -> None:
        self.deal = deal
        self.logs: list = []
        self.contacts: list = []
        self.added: list = []
        self.committed = False

    def get(self, _model, _id):  # noqa: ANN001
        if self.deal is None:
            return None
        if str(self.deal.id) == str(_id):
            return self.deal
        return None

    def add(self, obj) -> None:  # noqa: ANN001
        self.added.append(obj)
        if hasattr(obj, "action_type"):
            self.logs.append(obj)
        elif hasattr(obj, "email"):
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

    def _action_target(self) -> tuple[str | None, str | None]:
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
        return action_type, target_id

    def first(self):  # noqa: ANN001
        name = getattr(self._model, "__name__", str(self._model))
        if name == "AgentActionLog":
            rows = self.all()
            return rows[0] if rows else None
        if name == "Deal":
            deal_id = None
            for f in self._filters:
                left = getattr(f, "left", None)
                right = getattr(f, "right", None)
                if left is not None and hasattr(left, "key") and left.key == "id":
                    deal_id = getattr(right, "value", right)
            if self._db.deal is None:
                return None
            if deal_id is None or str(self._db.deal.id) == str(deal_id):
                return self._db.deal
            return None
        if name == "Contact":
            return None
        if name == "Company":
            return None
        return None

    def all(self):  # noqa: ANN001
        name = getattr(self._model, "__name__", str(self._model))
        if name != "AgentActionLog":
            return []
        action_type, target_id = self._action_target()
        rows = []
        for row in self._db.logs:
            if action_type and row.action_type != action_type:
                continue
            if target_id and row.target_id != target_id:
                continue
            rows.append(row)
        return rows


def _payload(
    outcome_id: str = _OUTCOME_ID,
    deal_id: str = _DEAL_ID,
    outcome: str = "closed_won",
) -> CommercialOutcomePayload:
    return CommercialOutcomePayload(
        outcome_id=outcome_id,
        deal_id=deal_id,
        outcome=outcome,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        handoff_hints="delivery kickoff",
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_valid_closed_won_handoff_and_accept() -> None:
    deal = _FakeDeal(DealStage.CLOSED_WON)
    db = _FakeDB(deal)
    register_commercial_outcome_handoff(db, _payload(), "Krishna Sales")
    result = accept_commercial_outcome(db, _OUTCOME_ID, "Krishna Revenue")
    assert result["accepted"] is True
    assert result["commercial_outcome_emitted"] is True
    assert result["deal_id"] == _DEAL_ID
    assert result["provenance"]["deal_id"] == _DEAL_ID
    assert result["recognized_revenue"] is False
    assert any(log.action_type == ACTION_ACCEPTED for log in db.logs)


def test_invalid_deal_rejected() -> None:
    db = _FakeDB(None)
    with pytest.raises(ValueError, match="Deal not found"):
        register_commercial_outcome_handoff(db, _payload(), "Krishna Sales")
    assert db.logs == []


def test_non_closed_won_rejected() -> None:
    db = _FakeDB(_FakeDeal(DealStage.NEGOTIATION))
    with pytest.raises(ValueError, match="closed_won"):
        register_commercial_outcome_handoff(db, _payload(), "Krishna Sales")
    assert db.logs == []


def test_closed_lost_cannot_create_accepted_outcome() -> None:
    db = _FakeDB(_FakeDeal(DealStage.CLOSED_LOST))
    with pytest.raises(ValueError, match="closed_won"):
        register_commercial_outcome_handoff(db, _payload(), "Krishna Sales")


def test_duplicate_handoff_same_outcome_is_idempotent() -> None:
    db = _FakeDB(_FakeDeal())
    first = register_commercial_outcome_handoff(db, _payload(), "Krishna Sales")
    second = register_commercial_outcome_handoff(db, _payload(), "Krishna Sales")
    assert first["idempotent"] is False
    assert second["idempotent"] is True
    assert len([log for log in db.logs if log.action_type == ACTION_HANDOFF]) == 1


def test_duplicate_deal_different_outcome_id_rejected() -> None:
    db = _FakeDB(_FakeDeal())
    register_commercial_outcome_handoff(db, _payload(), "Krishna Sales")
    other = _payload(outcome_id=str(uuid4()))
    with pytest.raises(ValueError, match="already registered"):
        register_commercial_outcome_handoff(db, other, "Krishna Sales")


def test_accept_idempotent_retry() -> None:
    db = _FakeDB(_FakeDeal())
    register_commercial_outcome_handoff(db, _payload(), "Krishna Sales")
    first = accept_commercial_outcome(db, _OUTCOME_ID, "Krishna Revenue")
    second = accept_commercial_outcome(db, _OUTCOME_ID, "Krishna Revenue")
    assert first["accepted"] is True
    assert second["idempotent"] is True
    assert len([log for log in db.logs if log.action_type == ACTION_ACCEPTED]) == 1


def test_provenance_preserved() -> None:
    deal = _FakeDeal()
    db = _FakeDB(deal)
    register_commercial_outcome_handoff(db, _payload(), "Krishna Sales")
    result = accept_commercial_outcome(db, _OUTCOME_ID, "Krishna Revenue")
    provenance = result["provenance"]
    assert provenance["deal_id"] == _DEAL_ID
    assert provenance["source_stage"] == "closed_won"
    assert provenance["value_snapshot"] == 25000.0
    assert provenance["currency_snapshot"] == "USD"
    assert provenance["value_authoritative"] is False


def test_authorized_human_path() -> None:
    db = _FakeDB(_FakeDeal())
    result = register_commercial_outcome_handoff(db, _payload(), "Krishna Founder")
    assert result["handoff_registered"] is True
    assert result["requested_by"] == "Krishna Founder"


def test_agent_direct_mutation_blocked() -> None:
    db = _FakeDB(_FakeDeal())
    with pytest.raises(HumanAuthorityError):
        register_commercial_outcome_handoff(db, _payload(), "agent")
    assert db.logs == []


def test_ai_direct_mutation_blocked() -> None:
    db = _FakeDB(_FakeDeal())
    with pytest.raises(HumanAuthorityError):
        register_commercial_outcome_handoff(db, _payload(), "ai:copilot")
    with pytest.raises(HumanAuthorityError):
        accept_commercial_outcome(db, _OUTCOME_ID, "ai")
    assert db.logs == []


def test_spoofed_requested_by_blocked() -> None:
    db = _FakeDB(_FakeDeal())
    with pytest.raises(HumanAuthorityError):
        register_commercial_outcome_handoff(db, _payload(), "automation")
    with pytest.raises(HumanAuthorityError):
        register_commercial_outcome_handoff(db, _payload(), "bot")


def test_acceptance_audit() -> None:
    db = _FakeDB(_FakeDeal())
    register_commercial_outcome_handoff(db, _payload(), "Krishna Sales")
    accept_commercial_outcome(db, _OUTCOME_ID, "Krishna Revenue", notes="booked")
    accepted = [log for log in db.logs if log.action_type == ACTION_ACCEPTED]
    assert len(accepted) == 1
    assert accepted[0].actor == "Krishna Revenue"
    assert accepted[0].detail["deal_id"] == _DEAL_ID


def test_rejection_audit() -> None:
    db = _FakeDB(_FakeDeal())
    register_commercial_outcome_handoff(db, _payload(), "Krishna Sales")
    result = reject_commercial_outcome(db, _OUTCOME_ID, "Krishna Revenue", "value mismatch")
    assert result["rejected"] is True
    rejected = [log for log in db.logs if log.action_type == ACTION_REJECTED]
    assert len(rejected) == 1
    assert rejected[0].detail["reason"] == "value mismatch"


def test_sales_state_protection() -> None:
    deal = _FakeDeal(DealStage.CLOSED_WON)
    original_stage = deal.stage
    original_value = deal.value
    original_closed_at = deal.closed_at
    db = _FakeDB(deal)
    register_commercial_outcome_handoff(db, _payload(), "Krishna Sales")
    accept_commercial_outcome(db, _OUTCOME_ID, "Krishna Revenue")
    reject_db = _FakeDB(_FakeDeal())
    register_commercial_outcome_handoff(
        reject_db, _payload(outcome_id=str(uuid4())), "Krishna Sales"
    )
    assert deal.stage is original_stage
    assert deal.value == original_value
    assert deal.closed_at is original_closed_at


def test_revenue_boundary_no_financial_entities() -> None:
    db = _FakeDB(_FakeDeal())
    register_commercial_outcome_handoff(db, _payload(), "Krishna Sales")
    result = accept_commercial_outcome(db, _OUTCOME_ID, "Krishna Revenue")
    assert result["billing_created"] is False
    assert result["invoice_created"] is False
    assert result["client_created"] is False
    assert result["project_created"] is False
    assert result["recognized_revenue"] is False
    assert all(hasattr(obj, "action_type") for obj in db.added)


def test_no_shared_sot_handoff_is_audit_only() -> None:
    db = _FakeDB(_FakeDeal())
    register_commercial_outcome_handoff(db, _payload(), "Krishna Sales")
    assert db.contacts == []
    assert all(log.action_type == ACTION_HANDOFF for log in db.logs)


def test_a3_5_stage_update_still_does_not_emit_outcome() -> None:
    deal = _FakeDeal(DealStage.NEGOTIATION)
    db = _FakeDB(deal)
    result = apply_deal_stage_update(
        db, deal, DealStage.CLOSED_WON, requested_by="Krishna Sales"
    )
    assert result["commercial_outcome_emitted"] is False
    assert deal.stage == DealStage.CLOSED_WON
    assert not any(getattr(obj, "action_type", None) == ACTION_HANDOFF for obj in db.added)


def test_a4_5_contact_status_contract_untouched() -> None:
    contact = _FakeContact()

    class _StatusDB:
        def add(self, _obj) -> None:
            return None

        def commit(self) -> None:
            return None

        def refresh(self, _obj) -> None:
            return None

    from revenue_os.models.contact import ContactStatus

    contact.status = ContactStatus.LEAD
    result = apply_contact_status_update(
        _StatusDB(), contact, ContactStatus.QUALIFIED, requested_by="Krishna Sales"
    )
    assert result["new_status"] == "qualified"
    assert "commercial_outcome_emitted" not in result or result.get(
        "commercial_outcome_emitted"
    ) in (False, None)


def test_mc04_5_accept_still_does_not_emit_outcome() -> None:
    demand_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"
    db = _FakeDB(_FakeDeal())
    payload = QualifiedDemandPayload(
        demand_id=demand_id,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        source="manual",
        person={"email": "mc06-qd@example.com", "name": "QD Lead"},
    )
    register_marketing_handoff(db, payload, "Krishna Founder")
    result = accept_qualified_demand(db, demand_id, "Krishna Sales")
    assert result["commercial_outcome_emitted"] is False
    assert result["deal_created"] is False


def test_runner_valid_human_flow(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = _FakeDB(_FakeDeal())
    monkeypatch.setattr(co_router, "SessionLocal", lambda: db)
    events: list = []
    monkeypatch.setattr(co_router.EventBus, "publish", lambda e: events.append(e))

    handoff = client.post(
        "/api/v1/sales/commercial-outcome/handoff",
        json={
            "outcome_id": _OUTCOME_ID,
            "deal_id": _DEAL_ID,
            "outcome": "closed_won",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "requested_by": "Krishna Sales",
        },
    )
    assert handoff.status_code == 200
    assert handoff.json()["handoff_registered"] is True

    accept = client.post(
        "/api/v1/revenue/intake/commercial-outcome/accept",
        json={"outcome_id": _OUTCOME_ID, "requested_by": "Krishna Revenue"},
    )
    assert accept.status_code == 200
    body = accept.json()
    assert body["accepted"] is True
    assert body["commercial_outcome_emitted"] is True
    assert any(
        getattr(e.event_type, "value", e.event_type) == "commercial_outcome_accepted"
        for e in events
    )


def test_runner_rejects_agent_handoff(client: TestClient) -> None:
    r = client.post(
        "/api/v1/sales/commercial-outcome/handoff",
        json={
            "outcome_id": str(uuid4()),
            "deal_id": _DEAL_ID,
            "outcome": "closed_won",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "requested_by": "agent",
        },
    )
    assert r.status_code == 403


def test_runner_rejects_ai_accept(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = _FakeDB(_FakeDeal())
    register_commercial_outcome_handoff(db, _payload(), "Krishna Sales")
    monkeypatch.setattr(co_router, "SessionLocal", lambda: db)
    r = client.post(
        "/api/v1/revenue/intake/commercial-outcome/accept",
        json={"outcome_id": _OUTCOME_ID, "requested_by": "ai:copilot"},
    )
    assert r.status_code == 403
    assert not any(log.action_type == ACTION_ACCEPTED for log in db.logs)


def test_runner_rejects_spoofed_human(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(co_router, "SessionLocal", lambda: _FakeDB(_FakeDeal()))
    r = client.post(
        "/api/v1/sales/commercial-outcome/handoff",
        json={
            "outcome_id": _OUTCOME_ID,
            "deal_id": _DEAL_ID,
            "outcome": "closed_won",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "requested_by": "system",
        },
    )
    assert r.status_code == 403


def test_runner_rejects_missing_deal(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(co_router, "SessionLocal", lambda: _FakeDB(None))
    r = client.post(
        "/api/v1/sales/commercial-outcome/handoff",
        json={
            "outcome_id": _OUTCOME_ID,
            "deal_id": _DEAL_ID,
            "outcome": "closed_won",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "requested_by": "Krishna Sales",
        },
    )
    assert r.status_code == 422


def test_runner_reject_creates_audit(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = _FakeDB(_FakeDeal())
    register_commercial_outcome_handoff(db, _payload(), "Krishna Sales")
    monkeypatch.setattr(co_router, "SessionLocal", lambda: db)
    r = client.post(
        "/api/v1/revenue/intake/commercial-outcome/reject",
        json={
            "outcome_id": _OUTCOME_ID,
            "requested_by": "Krishna Revenue",
            "reason": "Not commercially final",
        },
    )
    assert r.status_code == 200
    assert r.json()["rejected"] is True
    assert any(log.action_type == ACTION_REJECTED for log in db.logs)


def test_cannot_accept_after_reject() -> None:
    db = _FakeDB(_FakeDeal())
    register_commercial_outcome_handoff(db, _payload(), "Krishna Sales")
    reject_commercial_outcome(db, _OUTCOME_ID, "Krishna Revenue", "no")
    with pytest.raises(ValueError, match="already rejected"):
        accept_commercial_outcome(db, _OUTCOME_ID, "Krishna Revenue")


def test_cannot_reject_after_accept() -> None:
    db = _FakeDB(_FakeDeal())
    register_commercial_outcome_handoff(db, _payload(), "Krishna Sales")
    accept_commercial_outcome(db, _OUTCOME_ID, "Krishna Revenue")
    with pytest.raises(ValueError, match="already accepted"):
        reject_commercial_outcome(db, _OUTCOME_ID, "Krishna Revenue", "too late")
