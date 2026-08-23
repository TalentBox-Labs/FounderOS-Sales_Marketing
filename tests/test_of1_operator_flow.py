"""OF1 — Operator Flow Completion focused tests."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

import runner_api_routers.operator_flow as of_router
from revenue_os.models.contact import ContactSource, ContactStatus
from revenue_os.models.deal import DealStage
from revenue_os.services.commercial_outcome_service import (
    ACTION_ACCEPTED as CO_ACCEPTED,
)
from revenue_os.services.commercial_outcome_service import CommercialOutcomePayload
from revenue_os.services.commercial_outcome_service import (
    register_commercial_outcome_handoff,
)
from revenue_os.services.qualified_demand_service import (
    ACTION_HANDOFF as QD_HANDOFF,
)
from revenue_os.services.qualified_demand_service import (
    QualifiedDemandPayload,
    register_marketing_handoff,
)
from runner_api import app

_OPERATOR = "Krishna Founder"
_DEMAND_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_CONTACT_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
_DEAL_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
_OUTCOME_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd"


class _FakeContact:
    def __init__(self) -> None:
        self.id = UUID(_CONTACT_ID)
        self.first_name = "Op"
        self.last_name = "Lead"
        self.email = "op@example.com"
        self.status = ContactStatus.LEAD
        self.lead_score = 80
        self.source = ContactSource.MANUAL
        self.phone = None
        self.notes = None


class _FakeDeal:
    def __init__(self, stage: DealStage = DealStage.NEGOTIATION) -> None:
        self.id = UUID(_DEAL_ID)
        self.name = "Operator Deal"
        self.stage = stage
        self.probability = 80
        self.value = 10000.0
        self.currency = "USD"
        self.contact_id = UUID(_CONTACT_ID)
        self.closed_at = None
        self.updated_at = datetime.now(timezone.utc)


class _FakePipeline:
    def __init__(self) -> None:
        self.id = UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
        self.is_default = 1


class _FakeDB:
    def __init__(self) -> None:
        self.contacts = [_FakeContact()]
        self.deals = [_FakeDeal()]
        self.logs: list = []
        self.added: list = []
        self.pipeline = _FakePipeline()

    def get(self, model, ident):  # noqa: ANN001
        name = getattr(model, "__name__", "")
        if name == "Contact" and str(ident) == _CONTACT_ID:
            return self.contacts[0]
        if name == "Deal" and str(ident) == _DEAL_ID:
            return self.deals[0]
        return None

    def add(self, obj) -> None:  # noqa: ANN001
        self.added.append(obj)
        if hasattr(obj, "action_type"):
            self.logs.append(obj)
        if getattr(obj, "email", None) and obj not in self.contacts:
            if not getattr(obj, "id", None):
                obj.id = UUID(_CONTACT_ID)
            self.contacts.append(obj)
        if getattr(obj, "pipeline_id", None) is not None and hasattr(obj, "stage"):
            if not getattr(obj, "id", None):
                obj.id = uuid4()
            if obj not in self.deals:
                self.deals.append(obj)

    def commit(self) -> None:
        return None

    def flush(self) -> None:
        return None

    def refresh(self, obj) -> None:  # noqa: ANN001
        if getattr(obj, "id", None) is None:
            obj.id = uuid4()

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

    def order_by(self, *_a) -> _FakeQuery:  # noqa: ANN001
        return self

    def first(self):  # noqa: ANN001
        rows = self.all()
        return rows[0] if rows else None

    def all(self):  # noqa: ANN001
        name = getattr(self._model, "__name__", str(self._model))
        if name == "Contact":
            return self._db.contacts
        if name == "Deal":
            return self._db.deals
        if name == "Pipeline":
            return [self._db.pipeline]
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
            rows = []
            for row in self._db.logs:
                if action_type and row.action_type != action_type:
                    continue
                if target_id and row.target_id != target_id:
                    continue
                rows.append(row)
            return rows
        return []


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def operator_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)


def _seed_handoff(db: _FakeDB) -> None:
    register_marketing_handoff(
        db,
        QualifiedDemandPayload(
            demand_id=_DEMAND_ID,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            source="manual",
            person={"email": "op@example.com", "name": "Op Lead"},
        ),
        _OPERATOR,
    )


def test_unauthenticated_mutation_rejected(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    monkeypatch.setenv("RUNNER_API_KEY", "of1-secret-key")
    r = client.post(
        "/api/v1/operator/actions/qualified-demand/accept",
        json={"demand_id": _DEMAND_ID},
    )
    assert r.status_code == 401


def test_agent_mutation_rejected(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", "agent")
    r = client.post(
        "/api/v1/operator/actions/deal/stage",
        json={"deal_id": _DEAL_ID, "stage": "closed_won"},
    )
    assert r.status_code == 503


def test_ai_mutation_rejected(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", "ai:copilot")
    r = client.post(
        "/api/v1/operator/actions/contact-status",
        json={"contact_id": _CONTACT_ID, "status": "qualified"},
    )
    assert r.status_code == 503


def test_spoofed_human_identity_ignored(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    db = _FakeDB()
    _seed_handoff(db)
    monkeypatch.setattr(of_router, "SessionLocal", lambda: db)
    r = client.post(
        "/api/v1/operator/actions/qualified-demand/accept",
        json={"demand_id": _DEMAND_ID, "requested_by": "agent:spoof"},
    )
    assert r.status_code == 200
    assert r.json()["operator"] == _OPERATOR
    assert r.json()["requested_by"] == _OPERATOR


def test_path_a_qualified_demand_accept(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    db = _FakeDB()
    _seed_handoff(db)
    monkeypatch.setattr(of_router, "SessionLocal", lambda: db)
    r = client.post(
        "/api/v1/operator/actions/qualified-demand/accept",
        json={"demand_id": _DEMAND_ID},
    )
    assert r.status_code == 200
    assert r.json()["action"] == "qualified_demand_accept"
    assert r.json()["contact_id"]


def test_path_a_qualified_demand_reject(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    db = _FakeDB()
    _seed_handoff(db)
    monkeypatch.setattr(of_router, "SessionLocal", lambda: db)
    r = client.post(
        "/api/v1/operator/actions/qualified-demand/reject",
        json={"demand_id": _DEMAND_ID, "reason": "ICP mismatch"},
    )
    assert r.status_code == 200
    assert r.json()["rejected"] is True


def test_path_b_contact_status(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    db = _FakeDB()
    monkeypatch.setattr(of_router, "SessionLocal", lambda: db)
    r = client.post(
        "/api/v1/operator/actions/contact-status",
        json={"contact_id": _CONTACT_ID, "status": "qualified"},
    )
    assert r.status_code == 200
    assert r.json()["new_status"] == "qualified"
    assert db.contacts[0].status == ContactStatus.QUALIFIED


def test_path_c_valid_deal_stage(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    db = _FakeDB()
    monkeypatch.setattr(of_router, "SessionLocal", lambda: db)
    r = client.post(
        "/api/v1/operator/actions/deal/stage",
        json={"deal_id": _DEAL_ID, "stage": "closed_won"},
    )
    assert r.status_code == 200
    assert r.json()["new_stage"] == "closed_won"
    assert r.json()["commercial_outcome_emitted"] is False


def test_invalid_deal_transition_rejected(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    db = _FakeDB()
    db.deals[0].stage = DealStage.CLOSED_WON
    monkeypatch.setattr(of_router, "SessionLocal", lambda: db)
    r = client.post(
        "/api/v1/operator/actions/deal/stage",
        json={"deal_id": _DEAL_ID, "stage": "discovery"},
    )
    assert r.status_code == 422


def test_commercial_outcome_requires_closed_won(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    db = _FakeDB()
    db.deals[0].stage = DealStage.NEGOTIATION
    monkeypatch.setattr(of_router, "SessionLocal", lambda: db)
    r = client.post(
        "/api/v1/operator/actions/commercial-outcome/handoff",
        json={"deal_id": _DEAL_ID},
    )
    assert r.status_code == 422


def test_path_d_eligible_handoff(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    db = _FakeDB()
    db.deals[0].stage = DealStage.CLOSED_WON
    monkeypatch.setattr(of_router, "SessionLocal", lambda: db)
    r = client.post(
        "/api/v1/operator/actions/commercial-outcome/handoff",
        json={"deal_id": _DEAL_ID},
    )
    assert r.status_code == 200
    assert r.json()["handoff_registered"] is True
    assert r.json()["deal_mutated"] is False


def test_path_e_revenue_accept_and_idempotent(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    db = _FakeDB()
    db.deals[0].stage = DealStage.CLOSED_WON
    register_commercial_outcome_handoff(
        db,
        CommercialOutcomePayload(
            outcome_id=_OUTCOME_ID,
            deal_id=_DEAL_ID,
            outcome="closed_won",
            occurred_at=datetime.now(timezone.utc).isoformat(),
        ),
        _OPERATOR,
    )
    monkeypatch.setattr(of_router, "SessionLocal", lambda: db)
    first = client.post(
        "/api/v1/operator/actions/commercial-outcome/accept",
        json={"outcome_id": _OUTCOME_ID},
    )
    second = client.post(
        "/api/v1/operator/actions/commercial-outcome/accept",
        json={"outcome_id": _OUTCOME_ID},
    )
    assert first.status_code == 200
    assert first.json()["accepted"] is True
    assert second.json()["idempotent"] is True
    assert len([log for log in db.logs if log.action_type == CO_ACCEPTED]) == 1


def test_revenue_reject_human_only(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    db = _FakeDB()
    db.deals[0].stage = DealStage.CLOSED_WON
    register_commercial_outcome_handoff(
        db,
        CommercialOutcomePayload(
            outcome_id=_OUTCOME_ID,
            deal_id=_DEAL_ID,
            outcome="closed_won",
            occurred_at=datetime.now(timezone.utc).isoformat(),
        ),
        _OPERATOR,
    )
    monkeypatch.setattr(of_router, "SessionLocal", lambda: db)
    r = client.post(
        "/api/v1/operator/actions/commercial-outcome/reject",
        json={"outcome_id": _OUTCOME_ID, "reason": "value mismatch"},
    )
    assert r.status_code == 200
    assert r.json()["rejected"] is True


def test_deal_create_links_contact(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    db = _FakeDB()
    db.deals = []
    monkeypatch.setattr(of_router, "SessionLocal", lambda: db)
    r = client.post(
        "/api/v1/operator/actions/deal/create",
        json={"name": "New Deal", "contact_id": _CONTACT_ID, "stage": "discovery"},
    )
    assert r.status_code == 200
    assert r.json()["contact_id"] == _CONTACT_ID
    assert r.json()["stage"] == "discovery"


def test_deal_create_rejects_closed_won(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    monkeypatch.setattr(of_router, "SessionLocal", lambda: _FakeDB())
    r = client.post(
        "/api/v1/operator/actions/deal/create",
        json={"name": "Skip", "contact_id": _CONTACT_ID, "stage": "closed_won"},
    )
    assert r.status_code == 422


def test_path_f_page_degrades_without_fabricated_links(
    client: TestClient, operator_env: None
) -> None:
    r = client.get("/operator")
    assert r.status_code == 200
    assert "Operator Flow" in r.text
    assert "no_linked_record" in r.text or "No pending QualifiedDemand" in r.text
    assert "fabricated" not in r.text.lower()


def test_operator_page_in_canonical_shell(client: TestClient) -> None:
    r = client.get("/operator")
    assert r.status_code == 200
    assert "Founder OS" in r.text
    assert 'data-testid="stage-demand"' in r.text
    assert 'data-testid="stage-deals"' in r.text


def test_cockpit_still_has_only_two_mutations() -> None:
    import runner_api_routers.cockpit as cockpit_mod

    mutation_routes = [
        route.path
        for route in cockpit_mod.router.routes
        if hasattr(route, "methods") and "POST" in route.methods
    ]
    assert sorted(mutation_routes) == [
        "/api/v1/cockpit/actions/contact-status",
        "/api/v1/cockpit/actions/qualified-demand/accept",
    ]


def test_audit_trail_on_accept(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    db = _FakeDB()
    _seed_handoff(db)
    monkeypatch.setattr(of_router, "SessionLocal", lambda: db)
    client.post(
        "/api/v1/operator/actions/qualified-demand/accept",
        json={"demand_id": _DEMAND_ID},
    )
    assert any(log.action_type == "qualified_demand_accepted" for log in db.logs)
    assert any(log.action_type == QD_HANDOFF for log in db.logs)


def test_ui1_1_service_bypass_still_blocked() -> None:
    from revenue_os.services.mutation_authority import HumanAuthorityError
    from revenue_os.services.deal_automation_service import apply_deal_stage_update

    deal = _FakeDeal()
    with pytest.raises(HumanAuthorityError):
        apply_deal_stage_update(_FakeDB(), deal, DealStage.CLOSED_WON, requested_by="agent")
