"""I2 — Command Home V2 focused presentation tests (projection over I1 only)."""

from __future__ import annotations

import re
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import runner_api_routers.identity as identity_mod
from revenue_os.services.command_v2_projection import (
    BUCKET_BLOCKED_OR_DEGRADED,
    BUCKET_NEEDS_YOUR_JUDGMENT,
    BUCKET_RECENTLY_CHANGED,
    BUCKET_RUNNING_WITHOUT_YOU,
    compose_command_v2_projection,
)
from revenue_os.services.founder_ui_read_model import ensure_command_center_snapshot_shape

_ORG_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_ORG_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


@pytest.fixture(autouse=True)
def _reset_identity() -> None:
    identity_mod._revoked_jtis.clear()
    identity_mod._login_failures.clear()


@pytest.fixture
def client(cms_client: TestClient) -> TestClient:
    return cms_client


def _v2_snap(**overrides):
    base = {
        "generated_at": "now",
        "state": "ok",
        "organization_id": _ORG_A,
        "message": "",
        "pending_approvals": [],
        "pending_approval_count": 0,
        "pending_demands": [],
        "pending_demand_count": 0,
        "pipeline": {"contacts": 0, "deals": 0, "deals_by_stage": {}},
        "recent_replies": [],
        "meeting_interest": [],
        "follow_up_signals": [],
        "recent_activity": [],
        "decision_items": [],
        "decision_loop": {
            "total": 0,
            "requires_founder": 0,
            "ready": 0,
            "completed": 0,
            "informational": 0,
        },
        "commercial_funnel": {},
        "agent_orchestration": {"counts": {}},
        "errors": [],
    }
    base.update(overrides)
    return ensure_command_center_snapshot_shape(base)


def _get_command(client: TestClient, snap: dict) -> str:
    with patch("runner_api_routers.ui.founder_login_redirect", return_value=None):
        with patch(
            "runner_api_routers.ui.build_command_center_snapshot",
            return_value=snap,
        ):
            r = client.get("/command")
    assert r.status_code == 200
    return r.text


def test_four_command_sections_render_from_i1(client: TestClient) -> None:
    snap = _v2_snap(
        pending_approvals=[
            {
                "id": "ar-1",
                "title": "Send outreach to Ada",
                "action_type": "send_outreach_email",
                "action_label": "Send outreach",
            }
        ],
        pending_approval_count=1,
        agent_orchestration={
            "blocked": [{"work_id": "b1", "action_type": "worker_research"}],
            "retryable": [
                {
                    "work_id": "r1",
                    "action_type": "worker_research",
                    "execution_mode": "AUTONOMOUS",
                    "recovery_class": "RETRYABLE",
                }
            ],
            "running": [
                {
                    "work_id": "run-1",
                    "action_type": "worker_research",
                    "execution_mode": "AUTONOMOUS",
                    "state": "running",
                }
            ],
            "succeeded_recently": [
                {"work_id": "s1", "action_type": "worker_research"}
            ],
            "pause": {"recovery_execution_allowed": True},
        },
        decision_loop={
            "total": 1,
            "requires_founder": 1,
            "ready": 0,
            "completed": 0,
            "informational": 0,
        },
    )
    body = _get_command(client, snap)
    assert 'data-testid="command-v2-home"' in body
    assert 'data-testid="command-v2-needs-judgment"' in body
    assert 'data-testid="command-v2-blocked"' in body
    assert 'data-testid="command-v2-running"' in body
    assert 'data-testid="command-v2-recent"' in body
    # Dominant section markup
    assert "command-v2-section dominant" in body
    assert body.index('data-testid="command-v2-needs-judgment"') < body.index(
        'data-testid="command-v2-blocked"'
    )


def test_needs_your_judgment_is_dominant() -> None:
    tpl = (
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "templates"
        / "founder_command.html"
    ).read_text(encoding="utf-8")
    assert "command-v2-section dominant" in tpl
    assert 'data-testid="command-v2-needs-judgment"' in tpl
    # No separate recommendations rail
    assert "Next Best Moves" not in tpl
    assert re.search(r"next best moves", tpl, re.I) is None


def test_no_duplicate_same_situation_in_v2_buckets() -> None:
    snap = {
        "organization_id": _ORG_A,
        "pending_approvals": [
            {"id": "ar-1", "action_type": "send_outreach_email", "title": "A"}
        ],
        "decision_items": [
            {
                "item_id": "di-1",
                "kind": "approval",
                "title": "A",
                "authority_state": "requires_founder",
                "provenance": {"subject_id": "ar-1"},
            }
        ],
        "agent_orchestration": {},
    }
    proj = compose_command_v2_projection(snap, organization_id=_ORG_A)
    keys = [c["card_key"] for c in proj["cards"]]
    assert len(keys) == len(set(keys))
    needs = proj["buckets"][BUCKET_NEEDS_YOUR_JUDGMENT]
    assert len(needs) == 1


def test_booking_eligible_not_pending(client: TestClient) -> None:
    snap = _v2_snap(
        meeting_interest=[
            {
                "contact_id": str(uuid.uuid4()),
                "booking_status": "eligible",
                "booking_eligible": True,
            }
        ]
    )
    body = _get_command(client, snap)
    assert "Ready to propose a meeting" in body
    needs_section = body.split('data-testid="command-v2-needs-judgment"')[1].split(
        'data-testid="command-v2-blocked"'
    )[0]
    assert "Approval required" not in needs_section or "Meeting approvals" not in needs_section
    # Eligibility must not invent Needs Your Judgment cards
    v2 = snap["command_v2"]
    assert v2["buckets"][BUCKET_NEEDS_YOUR_JUDGMENT] == []


def test_pending_approval_renders_decision(client: TestClient) -> None:
    snap = _v2_snap(
        pending_approvals=[
            {
                "id": "ar-pending",
                "title": "Outreach to Sam",
                "action_type": "send_outreach_email",
                "action_label": "Send outreach",
            }
        ],
        pending_approval_count=1,
    )
    body = _get_command(client, snap)
    assert "Outreach to Sam" in body
    assert "Needs your judgment" in body
    assert snap["command_v2"]["buckets"][BUCKET_NEEDS_YOUR_JUDGMENT]


def test_blocked_and_provider_waiting(client: TestClient) -> None:
    snap = _v2_snap(
        agent_orchestration={
            "blocked": [
                {
                    "work_id": "b1",
                    "action_type": "worker_research",
                    "failure_reason": "policy_blocked",
                }
            ],
            "waiting_on_provider": [
                {
                    "work_id": "p1",
                    "title": "Calendar provider unavailable",
                    "reason": "connector_down",
                }
            ],
        }
    )
    body = _get_command(client, snap)
    blocked = body.split('data-testid="command-v2-blocked"')[1].split(
        'data-testid="command-v2-running"'
    )[0]
    assert "Blocked" in blocked or "policy_blocked" in blocked
    assert "Waiting on provider" in blocked
    assert "booked" not in blocked.lower()
    assert "confirmed" not in blocked.lower()
    assert "successful" not in blocked.lower()


def test_recovering_not_blocked_and_labelled_recovering(client: TestClient) -> None:
    snap = _v2_snap(
        agent_orchestration={
            "failed": [
                {
                    "work_id": "same",
                    "action_type": "worker_research",
                    "execution_mode": "AUTONOMOUS",
                }
            ],
            "retryable": [
                {
                    "work_id": "same",
                    "action_type": "worker_research",
                    "execution_mode": "AUTONOMOUS",
                    "recovery_class": "RETRYABLE",
                }
            ],
            "pause": {"recovery_execution_allowed": True},
        }
    )
    body = _get_command(client, snap)
    running = body.split('data-testid="command-v2-running"')[1].split(
        'data-testid="command-v2-recent"'
    )[0]
    blocked = body.split('data-testid="command-v2-blocked"')[1].split(
        'data-testid="command-v2-running"'
    )[0]
    assert "Recovering" in running
    assert 'data-visible-state="RECOVERING"' in running
    assert 'data-visible-state="RECOVERING"' not in blocked
    assert 'data-testid="command-v2-blocked-card"' not in blocked or "No blocked" in blocked
    assert snap["command_v2"]["buckets"][BUCKET_RUNNING_WITHOUT_YOU][0]["visible_state"] == (
        "RECOVERING"
    )


def test_active_autonomous_renders_running(client: TestClient) -> None:
    snap = _v2_snap(
        agent_orchestration={
            "running": [
                {
                    "work_id": "run-1",
                    "action_type": "worker_research",
                    "execution_mode": "AUTONOMOUS",
                    "state": "running",
                }
            ],
            "active": [
                {
                    "work_id": "failed-alias",
                    "action_type": "worker_research",
                    "execution_mode": "AUTONOMOUS",
                    "state": "failed",
                }
            ],
        }
    )
    body = _get_command(client, snap)
    running = body.split('data-testid="command-v2-running"')[1].split(
        'data-testid="command-v2-recent"'
    )[0]
    assert "Running" in running
    assert "failed-alias" not in running
    assert snap["command_v2"]["buckets"][BUCKET_RUNNING_WITHOUT_YOU][0]["visible_state"] == (
        "RUNNING"
    )


def test_decision_required_not_duplicated_as_running(client: TestClient) -> None:
    snap = _v2_snap(
        pending_approvals=[
            {"id": "ar-1", "title": "Approve send", "action_type": "send_outreach_email"}
        ],
        agent_orchestration={
            "awaiting_human": [
                {
                    "work_id": "wait-1",
                    "action_type": "send_outreach_email",
                    "execution_mode": "HUMAN_REQUIRED",
                    "approval_request_id": "ar-1",
                }
            ],
            "running": [
                {
                    "work_id": "wait-1",
                    "action_type": "send_outreach_email",
                    "execution_mode": "AUTONOMOUS",
                    "state": "running",
                    "approval_request_id": "ar-1",
                }
            ],
        },
    )
    v2 = snap["command_v2"]
    assert v2["buckets"][BUCKET_NEEDS_YOUR_JUDGMENT]
    # Pending AR subject excluded from running
    running_ids = {c.get("source_identity") for c in v2["buckets"][BUCKET_RUNNING_WITHOUT_YOU]}
    assert "work:wait-1" not in running_ids


def test_recently_changed_proven_only(client: TestClient) -> None:
    snap = _v2_snap(
        recent_activity=[
            {"id": "act-1", "label": "Outreach prepared", "created_at": "2026-01-01"}
        ],
        agent_orchestration={
            "succeeded_recently": [{"work_id": "s1", "action_type": "worker_research"}]
        },
    )
    body = _get_command(client, snap)
    recent = body.split('data-testid="command-v2-recent"')[1].split(
        'data-testid="command-v1-compatibility"'
    )[0]
    assert "Outreach prepared" in recent
    assert len(snap["command_v2"]["buckets"][BUCKET_RECENTLY_CHANGED]) >= 1


def test_next_move_omission_when_unsupported(client: TestClient) -> None:
    snap = _v2_snap(
        agent_orchestration={
            "blocked": [{"work_id": "b-unknown", "action_type": "worker_research"}]
        }
    )
    card = snap["command_v2"]["buckets"][BUCKET_BLOCKED_OR_DEGRADED][0]
    assert card.get("next_move") is None
    body = _get_command(client, snap)
    blocked = body.split('data-testid="command-v2-blocked"')[1].split(
        'data-testid="command-v2-running"'
    )[0]
    # Card renders without inventing a next-move line for unsupported
    assert "HUMAN_DECISION_REQUIRED" not in blocked


def test_recommendation_never_appears_as_authority(client: TestClient) -> None:
    snap = _v2_snap(
        decision_items=[
            {
                "item_id": "di-ready",
                "kind": "meeting_interest",
                "title": "Propose a meeting",
                "authority_state": "ready",
                "authority_state_label": "Ready",
                "proposed_action": "Review times",
                "provenance": {"subject_id": "c-1"},
            }
        ],
        decision_loop={
            "total": 1,
            "requires_founder": 0,
            "ready": 1,
            "completed": 0,
            "informational": 0,
        },
    )
    body = _get_command(client, snap)
    assert "Recommendation — not authority" in body
    assert "Propose a meeting" in body
    # Ready item must not land in Needs Your Judgment bucket
    assert snap["command_v2"]["buckets"][BUCKET_NEEDS_YOUR_JUDGMENT] == []


def test_missing_projection_fields_and_empty_state(client: TestClient) -> None:
    snap = _v2_snap(command_v2=None)  # ensure will recompose
    # Force empty projection path via missing org
    empty = ensure_command_center_snapshot_shape(
        {
            "state": "ok",
            "pipeline": {"contacts": 0, "deals": 0, "deals_by_stage": {}},
            "pending_approvals": [],
            "pending_demands": [],
            "recent_replies": [],
            "meeting_interest": [],
            "follow_up_signals": [],
            "recent_activity": [],
            "errors": [],
        }
    )
    body = _get_command(client, empty)
    assert 'data-testid="command-v2-home"' in body
    assert "Nothing needs your judgment" in body or "0 decisions need you" in body
    assert "No blocked or degraded" in body
    assert "randint" not in body
    assert "confidence" not in body.lower()
    assert "priority score" not in body.lower()


def test_partial_snapshot_shows_degraded(client: TestClient) -> None:
    snap = _v2_snap(state="partial", errors=["database", "agent_orchestration"], message="Partial")
    body = _get_command(client, snap)
    assert 'data-testid="command-v2-degraded"' in body
    assert "Incomplete or degraded" in body


def test_no_fabricated_metrics_or_raw_situation_ids(client: TestClient) -> None:
    snap = _v2_snap(
        pending_approvals=[
            {
                "id": "ar-1",
                "title": "Send outreach",
                "action_type": "send_outreach_email",
            }
        ]
    )
    body = _get_command(client, snap)
    v2_home = body.split('data-testid="command-v2-home"')[1].split(
        'data-testid="command-v1-compatibility"'
    )[0]
    assert "situation_id" not in v2_home.lower()
    assert "presentation_subject_key" not in v2_home
    assert "Business is healthy" not in body
    assert "Revenue risk is high" not in body
    assert not re.search(r"\bSLA\b", v2_home)
    assert "impact score" not in v2_home.lower()


def test_tenant_isolation_in_rendered_composition(client: TestClient) -> None:
    secret = "secret-org-b-only@example.com"
    snap = _v2_snap(
        organization_id=_ORG_A,
        pending_approvals=[
            {"id": "ar-a", "title": "Org A approval", "action_type": "send_outreach_email"}
        ],
    )
    # Ensure projection cannot join foreign org stamp
    foreign = dict(snap)
    foreign["organization_id"] = _ORG_B
    foreign["pending_approvals"] = [
        {"id": "ar-b", "title": secret, "action_type": "send_outreach_email"}
    ]
    shaped = ensure_command_center_snapshot_shape(foreign)
    # Call projection as org A against mismatched stamp
    from revenue_os.services.command_v2_projection import compose_command_v2_projection

    proj = compose_command_v2_projection(shaped, organization_id=_ORG_A)
    assert proj["cards"] == []
    body = _get_command(client, snap)
    assert secret not in body
    assert "Org A approval" in body
