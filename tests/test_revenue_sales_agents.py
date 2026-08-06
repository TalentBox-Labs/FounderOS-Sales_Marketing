"""Sales Agent crew regression coverage — all 5 agents, real DB writes,
mocked LLM/LinkedIn calls so tests don't depend on external network access
or API keys.
"""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest


@pytest.fixture
def contact(revenue_db):
    from revenue_os.models.contact import Contact

    c = Contact(
        first_name="Jamie", last_name="Prospect", email=f"jamie-{uuid.uuid4().hex[:8]}@example.com",
        linkedin_url="https://linkedin.com/in/jamie-prospect",
    )
    revenue_db.add(c)
    revenue_db.commit()
    revenue_db.refresh(c)
    yield c


FAKE_PERSON = {
    "ok": True, "configured": True,
    "profile": {
        "occupation": "VP of Sales", "headline": "VP Sales at Acme Robotics",
        "experiences": [{"ends_at": None, "company": "Acme Robotics",
                          "company_linkedin_profile_url": "https://linkedin.com/company/acme-robotics"}],
    },
}
FAKE_COMPANY = {
    "ok": True, "configured": True,
    "profile": {"name": "Acme Robotics", "industry": "Computer Software",
                "company_size": [51, 200], "description": "Robots.", "website": "https://acme.example"},
}


class TestICPResearchAgent:
    def test_research_contact_requires_linkedin_url(self, revenue_db) -> None:
        from revenue_os.models.contact import Contact
        from revenue_os.services.sales_agents import research_contact

        bare = Contact(first_name="No", last_name="LinkedIn", email=f"nolink-{uuid.uuid4().hex[:8]}@example.com")
        revenue_db.add(bare)
        revenue_db.commit()

        result = research_contact(str(bare.id))
        assert result["ok"] is False
        assert "LinkedIn" in result["reason"]

    def test_research_contact_populates_company_and_icp_fit(self, contact, revenue_db) -> None:
        from revenue_os.services.sales_agents import research_contact

        with patch("revenue_os.services.linkedin_enrichment.enrich_person", return_value=FAKE_PERSON), \
             patch("revenue_os.services.linkedin_enrichment.enrich_company", return_value=FAKE_COMPANY):
            result = research_contact(str(contact.id))

        assert result["ok"] is True
        assert result["icp_fit"]["score"] == 100
        assert result["signals"]["tech_stack"]["available"] is False  # honest — no provider configured


class TestColdEmailAgent:
    def test_draft_cold_email_files_approval(self, contact) -> None:
        from revenue_os.services.sales_agents import draft_cold_email

        result = draft_cold_email(str(contact.id))
        assert result["ok"] is True
        assert result["approval_id"]
        assert "Jamie" in result["body"]  # real context, not a merge-tag placeholder

        from revenue_os.services.approvals import list_requests

        pending = list_requests(status="pending")
        assert any(r["id"] == result["approval_id"] and r["action_type"] == "send_outreach_email" for r in pending)

    def test_draft_cold_email_requires_email(self, revenue_db) -> None:
        from revenue_os.models.contact import Contact
        from revenue_os.services.sales_agents import draft_cold_email

        no_email = Contact(first_name="No", last_name="Email", email=None)
        revenue_db.add(no_email)
        revenue_db.commit()

        result = draft_cold_email(str(no_email.id))
        assert result["ok"] is False


class TestLinkedInOpenerAgent:
    def test_draft_linkedin_opener_files_approval(self, contact) -> None:
        from revenue_os.services.sales_agents import draft_linkedin_opener

        result = draft_linkedin_opener(str(contact.id))
        assert result["ok"] is True
        assert len(result["connection_note"]) <= 300
        assert result["approval_id"]


class TestFollowUpSequenceAgent:
    def test_build_followup_sequence_creates_real_sequence(self, contact, revenue_db) -> None:
        from revenue_os.models.activity import OutreachSequence, SequenceStep
        from revenue_os.services.sales_agents import build_followup_sequence

        result = build_followup_sequence(str(contact.id))
        assert result["ok"] is True
        assert 5 <= len(result["steps"]) <= 7

        seq = revenue_db.get(OutreachSequence, uuid.UUID(result["sequence_id"]))
        assert seq is not None
        assert seq.steps_count == len(result["steps"])
        steps = revenue_db.query(SequenceStep).filter(SequenceStep.sequence_id == seq.id).all()
        assert len(steps) == len(result["steps"])
        # A real mixed-channel sequence — not every step is email.
        action_types = {s.action_type for s in steps}
        assert action_types & {"linkedin_connect", "linkedin_message"}


class TestObjectionHandlerAgent:
    def test_handle_latest_reply_with_no_inbound_email(self, contact) -> None:
        from revenue_os.services.sales_agents import handle_latest_reply

        result = handle_latest_reply(str(contact.id))
        assert result["ok"] is False
        assert "reply" in result["reason"].lower()

    def test_handle_latest_reply_classifies_and_files_distinct_approval(self, contact, revenue_db) -> None:
        from revenue_os.models.activity import Activity, ActivityType
        from revenue_os.services.approvals import request_approval
        from revenue_os.services.sales_agents import handle_latest_reply

        reply = Activity(
            contact_id=contact.id, activity_type=ActivityType.EMAIL, direction="inbound",
            subject="Re: intro", body="Not interested right now, thanks", status="completed",
        )
        revenue_db.add(reply)
        revenue_db.commit()

        # Simulate a still-pending cold-outreach draft for the same contact first,
        # to prove the dedup-collision bug (fixed via send_reply_email) stays fixed.
        pre_existing = request_approval(
            requested_by="cold_email_agent", action_type="send_outreach_email",
            title="Earlier cold email", target_type="contact", target_id=str(contact.id), payload={},
        )

        result = handle_latest_reply(str(contact.id))
        assert result["ok"] is True
        assert result["category"] == "not_interested"
        assert result["approval_id"] != pre_existing["id"]
