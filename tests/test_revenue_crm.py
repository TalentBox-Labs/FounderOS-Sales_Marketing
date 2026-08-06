"""Core CRM regression coverage: contacts, deals, activities/tasks.

Uses the shared cms_client fixture (auth bypassed via dependency override)
and the session-scoped test database from conftest.py. Tests share that DB
within a session, so assertions key off IDs created in the test itself,
never fixed row counts.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def _create_contact(client: TestClient, **overrides) -> dict:
    payload = {
        "first_name": "Ada", "last_name": "Lovelace", "email": f"ada-{id(overrides)}@example.com",
        "status": "prospect",
    }
    payload.update(overrides)
    res = client.post("/api/v1/crm/contacts", json=payload)
    assert res.status_code == 200, res.text
    return res.json()["contact"]


class TestContacts:
    def test_create_and_get_contact(self, cms_client: TestClient) -> None:
        contact = _create_contact(cms_client, email="create-get@example.com")
        assert contact["email"] == "create-get@example.com"
        assert contact["status"] == "prospect"

        res = cms_client.get(f"/api/v1/crm/contacts/{contact['id']}")
        assert res.status_code == 200
        assert res.json()["contact"]["id"] == contact["id"]

    def test_create_contact_rejects_duplicate_email(self, cms_client: TestClient) -> None:
        _create_contact(cms_client, email="dupe@example.com")
        res = cms_client.post("/api/v1/crm/contacts", json={
            "first_name": "Second", "email": "dupe@example.com",
        })
        assert res.status_code == 409

    def test_create_contact_maps_title_to_designation(self, cms_client: TestClient) -> None:
        """Regression: title used to be silently dropped — Contact has no
        `title` column, only `designation`. See runner_api_routers/crm.py
        create_contact()."""
        contact = _create_contact(cms_client, email="title-map@example.com", title="VP of Sales")
        assert contact["designation"] == "VP of Sales"
        assert contact["title"] == "VP of Sales"  # _contact_dict aliases designation -> title too

    def test_create_contact_stores_linkedin_url(self, cms_client: TestClient) -> None:
        contact = _create_contact(cms_client, email="li@example.com", linkedin_url="https://linkedin.com/in/ada")
        assert contact["linkedin_url"] == "https://linkedin.com/in/ada"

    def test_get_contact_404_for_unknown_id(self, cms_client: TestClient) -> None:
        res = cms_client.get("/api/v1/crm/contacts/00000000-0000-0000-0000-000000000000")
        assert res.status_code == 404

    def test_list_contacts_includes_created(self, cms_client: TestClient) -> None:
        contact = _create_contact(cms_client, email="list-me@example.com")
        res = cms_client.get("/api/v1/crm/contacts", params={"limit": 500})
        assert res.status_code == 200
        ids = {c["id"] for c in res.json()["contacts"]}
        assert contact["id"] in ids


class TestDeals:
    def test_create_deal_for_contact(self, cms_client: TestClient) -> None:
        contact = _create_contact(cms_client, email="deal-owner@example.com")
        res = cms_client.post("/api/v1/crm/deals", json={
            "name": "Acme expansion", "value": 15000, "stage": "discovery", "contact_id": contact["id"],
        })
        assert res.status_code == 200, res.text
        deal = res.json()["deal"]
        assert deal["name"] == "Acme expansion"
        assert deal["contact_id"] == contact["id"]

        res = cms_client.get(f"/api/v1/crm/deals/{deal['id']}")
        assert res.status_code == 200
        assert res.json()["deal"]["value"] == 15000

    def test_pipeline_reflects_created_deal(self, cms_client: TestClient) -> None:
        contact = _create_contact(cms_client, email="pipeline@example.com")
        before = cms_client.get("/api/v1/crm/pipeline").json()["pipeline"]["total_deals"]

        cms_client.post("/api/v1/crm/deals", json={
            "name": "Pipeline check deal", "value": 5000, "stage": "proposal", "contact_id": contact["id"],
        })

        res = cms_client.get("/api/v1/crm/pipeline")
        assert res.status_code == 200
        pipeline = res.json()["pipeline"]
        assert pipeline["total_deals"] == before + 1
        assert "proposal" in pipeline["by_stage"]


class TestActivitiesAndTasks:
    def test_create_note_activity(self, cms_client: TestClient) -> None:
        contact = _create_contact(cms_client, email="activity@example.com")
        res = cms_client.post("/api/v1/crm/activities", json={
            "contact_id": contact["id"], "activity_type": "note", "subject": "Called", "body": "Left voicemail",
        })
        assert res.status_code == 200, res.text
        activity = res.json()["activity"]
        assert activity["subject"] == "Called"

        res = cms_client.get("/api/v1/crm/activities", params={"contact_id": contact["id"]})
        assert res.status_code == 200
        subjects = {a["subject"] for a in res.json()["activities"]}
        assert "Called" in subjects

    def test_complete_task_activity(self, cms_client: TestClient) -> None:
        contact = _create_contact(cms_client, email="task@example.com")
        res = cms_client.post("/api/v1/crm/activities", json={
            "contact_id": contact["id"], "activity_type": "task", "subject": "Follow up call",
        })
        activity_id = res.json()["activity"]["id"]

        res = cms_client.post(f"/api/v1/crm/activities/{activity_id}/complete")
        assert res.status_code == 200
        assert res.json()["activity"]["is_completed"] is True
