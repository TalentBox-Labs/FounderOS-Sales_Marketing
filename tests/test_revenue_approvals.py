"""Approval queue regression coverage.

Includes a dedicated regression test for a real bug found while building
the Sales Agent crew: request_approval() collapses pending duplicates by
(action_type, target_id) alone, so two semantically different drafts for
the same contact (e.g. a cold-outreach email and an objection-handler
reply) would silently collapse into one if they shared an action_type.
Fixed by giving the reply path its own action_type (send_reply_email)
that reuses the same executor. This test guards that fix.
"""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest

_TEST_ORG_ID = "00000000-0000-0000-0000-0000000000a1"


def _human_tenant(name: str = "tester", org_id: str = _TEST_ORG_ID):
    from revenue_os.services.identity_context import AuthMethod, IdentityContext, PrincipalKind
    from revenue_os.services.tenant_context import TenantContext

    return TenantContext(
        identity=IdentityContext(
            principal_kind=PrincipalKind.HUMAN,
            auth_method=AuthMethod.SESSION,
            is_human=True,
            display_name=name,
            role="member",
        ),
        organization_id=org_id,
        organization_name="Test Org",
        organization_slug="test-org",
        membership_id="m-test",
        membership_role="member",
        membership_status="active",
    )


def test_request_approval_dedupes_same_action_and_target() -> None:
    from revenue_os.services.approvals import request_approval

    first = request_approval(
        requested_by="test_agent", action_type="send_outreach_email",
        title="First draft", target_type="contact", target_id="contact-dedup-1",
        payload={"body": "first"},
    )
    second = request_approval(
        requested_by="test_agent", action_type="send_outreach_email",
        title="Second draft", target_type="contact", target_id="contact-dedup-1",
        payload={"body": "second"},
    )
    assert second["id"] == first["id"]
    assert second.get("deduplicated") is True
    # The payload from the second call never made it in — this IS the bug
    # shape: a second draft can be silently dropped if it shares an
    # action_type + target_id with a still-pending one.
    assert second["payload"]["body"] == "first"


def test_distinct_action_types_do_not_dedupe_for_same_target() -> None:
    """Regression test for the fix: send_reply_email is a distinct
    action_type from send_outreach_email specifically so an objection
    reply never gets swallowed by a pending cold-outreach draft."""
    from revenue_os.services.approvals import request_approval

    cold_email = request_approval(
        requested_by="cold_email_agent", action_type="send_outreach_email",
        title="Cold email", target_type="contact", target_id="contact-dedup-2",
        payload={"body": "cold outreach"},
    )
    reply = request_approval(
        requested_by="objection_handler_agent", action_type="send_reply_email",
        title="Reply to objection", target_type="contact", target_id="contact-dedup-2",
        payload={"body": "reply to their objection"},
    )
    assert reply["id"] != cold_email["id"]
    assert reply.get("deduplicated") is not True
    assert reply["payload"]["body"] == "reply to their objection"


def test_decide_reject_does_not_execute() -> None:
    from revenue_os.services.approvals import decide, request_approval

    req = request_approval(
        requested_by="test_agent", action_type="send_outreach_email",
        title="Reject me", target_type="contact", target_id="contact-reject-1",
        payload={"body": "x"}, organization_id=_TEST_ORG_ID,
    )
    result = decide(req["id"], approve=False, tenant=_human_tenant())
    assert result["status"] == "rejected"
    assert result["execution_result"] is None


def test_decide_approve_executes_and_persists_result(revenue_db) -> None:
    from revenue_os.models.contact import Contact
    from revenue_os.services.approvals import decide, request_approval

    contact = Contact(
        first_name="X", last_name="Approve", email="x@example.com",
        organization_id=uuid.UUID(_TEST_ORG_ID),
    )
    revenue_db.add(contact)
    revenue_db.commit()
    revenue_db.refresh(contact)

    with patch("revenue_os.integrations.n8n.trigger_workflow", return_value=None) as mock_trigger:
        req = request_approval(
            requested_by="test_agent", action_type="send_outreach_email",
            title="Approve me", target_type="contact", target_id=str(contact.id),
            payload={"contact_id": str(contact.id), "email": "x@example.com", "name": "X"},
            organization_id=_TEST_ORG_ID,
        )
        result = decide(req["id"], approve=True, tenant=_human_tenant())

    assert result["status"] == "approved"
    assert result["execution_result"]["executed"] is True
    assert result["execution_result"]["handed_to_n8n"] is False  # mocked trigger_workflow returned None
    mock_trigger.assert_called_once()


def test_decide_unknown_action_type_records_no_executor() -> None:
    from revenue_os.services.approvals import decide, request_approval

    req = request_approval(
        requested_by="test_agent", action_type="totally_made_up_action",
        title="No executor for this", payload={}, organization_id=_TEST_ORG_ID,
    )
    result = decide(req["id"], approve=True, tenant=_human_tenant())
    assert result["status"] == "approved"
    assert result["execution_result"]["executed"] is False


def test_decide_twice_raises() -> None:
    from revenue_os.services.approvals import decide, request_approval

    req = request_approval(
        requested_by="test_agent", action_type="create_deal", title="Once only",
        payload={}, organization_id=_TEST_ORG_ID,
    )
    decide(req["id"], approve=False, tenant=_human_tenant())
    with pytest.raises(ValueError):
        decide(req["id"], approve=False, tenant=_human_tenant())


class TestExecutors:
    """Each executor should run without raising, whether or not the
    external system it talks to (n8n, Meta's WhatsApp API) is reachable —
    every executor in this codebase degrades to executed=True with a
    'not delivered' note rather than throwing."""

    def test_send_linkedin_message_is_always_manual(self) -> None:
        from revenue_os.services.approvals import _execute_send_linkedin_message

        result = _execute_send_linkedin_message(None, {"connection_note": "hi", "follow_up_dm": "thanks"})
        assert result["delivery"] == "manual"
        assert result["connection_note"] == "hi"

