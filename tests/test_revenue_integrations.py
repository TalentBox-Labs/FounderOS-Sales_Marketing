"""Integration-layer regression coverage: the encrypted credentials vault,
LinkedIn enrichment (Proxycurl), and Gmail inbox sync. External HTTP calls
are mocked; the vault's encryption round-trip is real (uses the real
Fernet key derived from SECRET_KEY).
"""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest


class TestCredentialsVault:
    def test_save_and_load_round_trip(self) -> None:
        from revenue_os.services.credentials_vault import load_credentials, save_credentials

        name = f"test_connector_{uuid.uuid4().hex[:8]}"
        save_credentials(name, "test", {"api_key": "super-secret-value"})
        loaded = load_credentials(name)
        assert loaded == {"api_key": "super-secret-value"}

    def test_list_configured_connectors_never_exposes_secret_values(self) -> None:
        from revenue_os.services.credentials_vault import list_configured_connectors, save_credentials

        name = f"test_connector_{uuid.uuid4().hex[:8]}"
        save_credentials(name, "test", {"api_key": "super-secret-value"})
        listing = list_configured_connectors()
        assert name in listing
        assert "super-secret-value" not in str(listing[name])

    def test_delete_credentials(self) -> None:
        from revenue_os.services.credentials_vault import delete_credentials, load_credentials, save_credentials

        name = f"test_connector_{uuid.uuid4().hex[:8]}"
        save_credentials(name, "test", {"api_key": "x"})
        assert delete_credentials(name) is True
        assert load_credentials(name) is None

    def test_load_unconfigured_connector_returns_none(self) -> None:
        from revenue_os.services.credentials_vault import load_credentials

        assert load_credentials(f"never-configured-{uuid.uuid4().hex}") is None


class TestLinkedInEnrichment:
    def test_enrich_person_not_configured(self) -> None:
        from revenue_os.services.credentials_vault import delete_credentials
        from revenue_os.services.linkedin_enrichment import enrich_person

        delete_credentials("linkedin_enrichment")
        result = enrich_person("https://linkedin.com/in/someone")
        assert result["ok"] is False
        assert result["configured"] is False

    def test_score_icp_fit_is_transparent_and_explainable(self) -> None:
        from revenue_os.services.linkedin_enrichment import score_icp_fit

        high = score_icp_fit("technology", 250)
        assert high["fit"] == "high"
        assert high["reasons"]  # explainable, not a black box

        low = score_icp_fit("retail", 5)
        assert low["fit"] == "low"

    def test_map_industry_handles_known_and_unknown(self) -> None:
        from revenue_os.services.linkedin_enrichment import map_industry

        assert map_industry("Computer Software") == "technology"
        assert map_industry("Something Made Up") == "other"
        assert map_industry(None) == "other"

    def test_enrich_contact_endpoint_full_pipeline(self, cms_client) -> None:
        """Mocked Proxycurl responses through the real /enrich endpoint —
        Company row created, designation set, ICP score computed, and a
        timeline note logged, all from one call."""
        from revenue_os.services import linkedin_enrichment as le

        create = cms_client.post("/api/v1/crm/contacts", json={
            "first_name": "Enrich", "last_name": "Target", "email": f"enrich-{uuid.uuid4().hex[:8]}@example.com",
        })
        contact_id = create.json()["contact"]["id"]

        fake_person = {
            "ok": True, "configured": True,
            "profile": {
                "occupation": "VP of Sales",
                "experiences": [{"ends_at": None, "company": "Acme Robotics",
                                  "company_linkedin_profile_url": "https://linkedin.com/company/acme"}],
            },
        }
        fake_company = {
            "ok": True, "configured": True,
            "profile": {"name": "Acme Robotics", "industry": "Computer Software",
                        "company_size": [51, 200], "website": "https://acme.example"},
        }
        with patch.object(le, "enrich_person", return_value=fake_person), \
             patch.object(le, "enrich_company", return_value=fake_company):
            res = cms_client.post(f"/api/v1/crm/contacts/{contact_id}/enrich",
                                   json={"linkedin_url": "https://linkedin.com/in/target"})

        assert res.status_code == 200
        body = res.json()
        assert body["ok"] is True
        assert body["contact"]["designation"] == "VP of Sales"
        assert body["icp_fit"]["fit"] == "high"

        detail = cms_client.get(f"/api/v1/crm/contacts/{contact_id}").json()["contact"]
        assert any(a["subject"] == "LinkedIn enrichment" for a in detail["activities"])


class TestGmailSync:
    def _fake_message(self, message_id: str, sender_email: str, subject: str = "Re: intro"):
        return {
            "id": message_id, "snippet": "Hey, following up on our chat...",
            "payload": {"headers": [
                {"name": "From", "value": f"Prospect <{sender_email}>"},
                {"name": "Subject", "value": subject},
            ]},
        }

    def test_sync_matches_known_contact_and_skips_unknown(self, cms_client) -> None:
        import revenue_os.integrations.gmail_sync as gs

        create = cms_client.post("/api/v1/crm/contacts", json={
            "first_name": "Gmail", "last_name": "Match", "email": f"gmailmatch-{uuid.uuid4().hex[:8]}@example.com",
        })
        contact_email = create.json()["contact"]["email"]

        matched_id = f"msg-{uuid.uuid4().hex[:8]}"
        unmatched_id = f"msg-{uuid.uuid4().hex[:8]}"

        with patch("revenue_os.services.credentials_vault.load_credentials",
                   return_value={"client_id": "x", "client_secret": "y", "refresh_token": "z"}), \
             patch.object(gs, "_refresh_access_token", return_value={"ok": True, "access_token": "fake"}), \
             patch.object(gs, "_list_message_ids", return_value=[matched_id, unmatched_id]), \
             patch.object(gs, "_get_message", side_effect=lambda token, mid: (
                 self._fake_message(matched_id, contact_email) if mid == matched_id
                 else self._fake_message(unmatched_id, "stranger@unrelated.com")
             )):
            result = gs.sync_inbox()

        assert result["ok"] is True
        assert result["checked"] == 2
        assert result["matched"] == 1
        assert result["created"] == 1

    def test_sync_is_idempotent_on_rerun(self, cms_client) -> None:
        import revenue_os.integrations.gmail_sync as gs

        create = cms_client.post("/api/v1/crm/contacts", json={
            "first_name": "Gmail", "last_name": "Dedup", "email": f"gmaildedup-{uuid.uuid4().hex[:8]}@example.com",
        })
        contact_email = create.json()["contact"]["email"]
        message_id = f"msg-{uuid.uuid4().hex[:8]}"

        with patch("revenue_os.services.credentials_vault.load_credentials",
                   return_value={"client_id": "x", "client_secret": "y", "refresh_token": "z"}), \
             patch.object(gs, "_refresh_access_token", return_value={"ok": True, "access_token": "fake"}), \
             patch.object(gs, "_list_message_ids", return_value=[message_id]), \
             patch.object(gs, "_get_message", return_value=self._fake_message(message_id, contact_email)):
            first = gs.sync_inbox()
            second = gs.sync_inbox()

        assert first["created"] == 1
        assert second["created"] == 0  # already synced — EmailActivity.message_id dedup

    def test_sync_not_connected_is_honest(self) -> None:
        import revenue_os.integrations.gmail_sync as gs

        with patch("revenue_os.services.credentials_vault.load_credentials", return_value=None):
            result = gs.sync_inbox()
        assert result["ok"] is False
        assert "not connected" in result["reason"].lower()
