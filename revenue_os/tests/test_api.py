"""Integration tests for Revenue OS API endpoints.

Run with: pytest revenue_os/tests/test_api.py -v
"""
# NOTE: avoid hard-coded sys.path modifications; run pytest from the repo root so `revenue_os` is importable.
import pytest
from fastapi.testclient import TestClient
from revenue_os.main import app
from revenue_os.database import engine
from revenue_os.models.base import Base
from revenue_os.models import *  # noqa: register all models

Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def _login(client):
    r = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123",
    })
    if r.status_code not in (200, 201):
        r = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User",
        })
    assert r.status_code in (200, 201), f"auth: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def token(client):
    return _login(client)


@pytest.fixture(scope="module")
def headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def contact_id(client, headers):
    r = client.post("/api/v1/contacts", headers=headers, json={
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
        "designation": "CEO",
    })
    assert r.status_code == 201, f"create contact: {r.text}"
    return r.json()["id"]


@pytest.fixture(scope="module")
def seq_id(client, headers):
    r = client.post("/api/v1/outreach/sequences", headers=headers, json={
        "name": "Test Sequence",
        "channel": "email",
    })
    assert r.status_code == 201
    return r.json()["id"]


class TestAuth:
    def test_register(self, client):
        import uuid
        email = f"new-{uuid.uuid4().hex[:8]}@test.com"
        r = client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "pass123",
            "full_name": "New User",
        })
        assert r.status_code == 201
        data = r.json()
        assert "access_token" in data
        assert data["email"] == email

    def test_login(self, client):
        r = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "testpass123",
        })
        assert r.status_code in (200, 201)
        assert "access_token" in r.json()

    def test_me(self, client, headers):
        r = client.get("/api/v1/auth/me", headers=headers)
        assert r.status_code == 200
        assert r.json()["email"] == "test@example.com"


class TestContacts:
    def test_create(self, client, headers):
        r = client.post("/api/v1/contacts", headers=headers, json={
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@test.com",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["first_name"] == "John"
        assert data["email"] == "john@test.com"

    def test_list(self, client, headers, contact_id):
        r = client.get("/api/v1/contacts", headers=headers)
        assert r.status_code == 200
        ids = [c["id"] for c in r.json()]
        assert contact_id in ids

    def test_get(self, client, headers, contact_id):
        r = client.get(f"/api/v1/contacts/{contact_id}", headers=headers)
        assert r.status_code == 200
        assert r.json()["email"] == "jane@example.com"

    def test_timeline_empty(self, client, headers, contact_id):
        r = client.get(f"/api/v1/contacts/{contact_id}/timeline", headers=headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_update(self, client, headers, contact_id):
        r = client.put(f"/api/v1/contacts/{contact_id}", headers=headers, json={
            "designation": "CTO",
        })
        assert r.status_code == 200
        assert r.json()["designation"] == "CTO"


class TestSequences:
    def test_create(self, client, headers):
        r = client.post("/api/v1/outreach/sequences", headers=headers, json={
            "name": "Campaign A",
            "channel": "email",
        })
        assert r.status_code == 201
        assert r.json()["name"] == "Campaign A"

    def test_list(self, client, headers, seq_id):
        r = client.get("/api/v1/outreach/sequences", headers=headers)
        assert r.status_code == 200
        ids = [s["id"] for s in r.json()]
        assert seq_id in ids

    def test_create_step(self, client, headers, seq_id):
        r = client.post(f"/api/v1/outreach/sequences/{seq_id}/steps", headers=headers, json={
            "step_order": 1,
            "delay_days": 0,
            "subject": "Hello {company}",
            "template": "Hi {name}, ...",
            "action_type": "send_email",
        })
        assert r.status_code == 201
        assert r.json()["step_order"] == 1

    def test_list_steps(self, client, headers, seq_id):
        client.post(f"/api/v1/outreach/sequences/{seq_id}/steps", headers=headers, json={
            "step_order": 1, "delay_days": 0, "subject": "Test", "template": "...",
        })
        r = client.get(f"/api/v1/outreach/sequences/{seq_id}/steps", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_enroll(self, client, headers, seq_id, contact_id):
        r = client.post(f"/api/v1/outreach/sequences/{seq_id}/enroll", headers=headers, json={
            "contact_ids": [contact_id],
        })
        assert r.status_code == 200
        data = r.json()
        assert data["enrolled"] == 1
        assert data["results"][0]["status"] == "enrolled"

    def test_list_enrollments(self, client, headers, seq_id, contact_id):
        client.post(f"/api/v1/outreach/sequences/{seq_id}/enroll", headers=headers, json={
            "contact_ids": [contact_id],
        })
        r = client.get(f"/api/v1/outreach/sequences/{seq_id}/enrollments", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["contact_id"] == contact_id
        assert data[0]["contact_name"] is not None  # join works

    def test_preview(self, client, headers, contact_id):
        r = client.post("/api/v1/outreach/preview", headers=headers, json={
            "contact_id": contact_id,
        })
        assert r.status_code == 200
        data = r.json()
        assert "subject" in data
        assert "body" in data


class TestReports:
    def test_outreach_summary(self, client, headers):
        r = client.get("/api/v1/reports/outreach-summary", headers=headers)
        assert r.status_code == 200
        assert "total_sent" in r.json()

    def test_campaigns(self, client, headers):
        r = client.get("/api/v1/reports/campaigns", headers=headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_hook_performance(self, client, headers):
        r = client.get("/api/v1/reports/hook-performance", headers=headers)
        assert r.status_code == 200

    def test_pipeline_funnel(self, client, headers):
        r = client.get("/api/v1/reports/pipeline-funnel", headers=headers)
        assert r.status_code == 200

    def test_revenue_trend(self, client, headers):
        r = client.get("/api/v1/reports/revenue-trend", headers=headers)
        assert r.status_code == 200

    def test_lead_sources(self, client, headers):
        r = client.get("/api/v1/reports/lead-sources", headers=headers)
        assert r.status_code == 200


class TestTracking:
    def test_open_pixel(self, client, headers, seq_id, contact_id):
        # Create an activity first
        r = client.post("/api/v1/outreach/activities", headers=headers, json={
            "contact_id": contact_id,
            "activity_type": "email",
            "subject": "Test",
            "direction": "outbound",
        })
        assert r.status_code == 201
        aid = r.json()["id"]
        r2 = client.get(f"/track/open/{aid}.png")
        assert r2.status_code == 200
        assert r2.headers["content-type"] == "image/gif"

    def test_click_redirect(self, client, headers, seq_id, contact_id):
        r = client.post("/api/v1/outreach/activities", headers=headers, json={
            "contact_id": contact_id,
            "activity_type": "email",
            "subject": "Test",
            "direction": "outbound",
        })
        aid = r.json()["id"]
        r2 = client.get(f"/track/click/{aid}", params={"url": "https://example.com"})
        assert r2.status_code in (200, 302, 307)


class TestActivities:
    def test_create(self, client, headers, contact_id):
        r = client.post("/api/v1/outreach/activities", headers=headers, json={
            "contact_id": contact_id,
            "activity_type": "note",
            "subject": "Had a good call",
            "direction": "outbound",
        })
        assert r.status_code == 201
        assert r.json()["activity_type"] == "note"

    def test_list(self, client, headers, contact_id):
        client.post("/api/v1/outreach/activities", headers=headers, json={
            "contact_id": contact_id, "activity_type": "note", "direction": "outbound",
        })
        r = client.get(f"/api/v1/outreach/activities?contact_id={contact_id}", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_timeline_populated(self, client, headers, contact_id):
        client.post("/api/v1/outreach/activities", headers=headers, json={
            "contact_id": contact_id, "activity_type": "email", "subject": "Follow up", "direction": "outbound",
        })
        r = client.get(f"/api/v1/contacts/{contact_id}/timeline", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) >= 1
        assert r.json()[0]["subject"] == "Follow up"
