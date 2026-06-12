from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import runner_api
from runner_api import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_mcp_template_contains_hub_sections() -> None:
    template = Path(__file__).resolve().parent.parent / "templates" / "mcp.html"
    text = template.read_text(encoding="utf-8")
    assert "MCP Hub" in text
    assert "Capability Map" in text
    assert "Messaging Channels" in text
    assert "/api/v1/mcp/hub" in text


def test_mcp_hub_api_reports_configured_integrations(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runner_api.settings, "OPENAI_API_KEY", "openai-key")
    monkeypatch.setattr(runner_api.settings, "OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setattr(runner_api.settings, "GEMINI_API_KEY", "gemini-key")
    monkeypatch.setattr(runner_api.settings, "WORKCREW_CREWAI_MODEL", "ollama/llama3.1:8b")
    monkeypatch.setattr(runner_api.settings, "GMAIL_CREDENTIALS_PATH", "/tmp/gmail.json")
    monkeypatch.setattr(runner_api.settings, "WHATSAPP_API_TOKEN", "wa-token")
    monkeypatch.setattr(runner_api.settings, "WHATSAPP_PHONE_NUMBER_ID", "123456")
    monkeypatch.setattr(runner_api.settings, "N8N_API_KEY", "n8n-key")
    monkeypatch.setattr(runner_api.settings, "N8N_WEBHOOK_BASE_URL", "http://localhost:5678/webhook")
    monkeypatch.setattr(runner_api, "backend_status", lambda: {"hermes": True, "openclaw": False})
    monkeypatch.setattr(
        runner_api,
        "provider_status",
        lambda: {"apollo_mcp": True, "linkedin_sales_navigator_mcp": True, "scraper": True},
    )
    monkeypatch.setenv("HASHNODE_ACCESS_TOKEN", "hashnode-token")
    monkeypatch.setenv("LINKEDIN_ACCESS_TOKEN", "linkedin-token")
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "instagram-token")
    monkeypatch.setenv("YOUTUBE_API_KEY", "youtube-key")

    r = client.get("/api/v1/mcp/hub")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True

    hub = body["hub"]
    assert hub["models"]["primary_llm"] == "gpt-4o-mini"
    assert hub["models"]["crewai_model"] == "ollama/llama3.1:8b"
    assert hub["backends"]["hermes"] is True
    assert hub["sales"]["mcp_provider_ready"]["apollo_mcp"] is True
    assert hub["marketing"]["linkedin"] is True
    assert hub["marketing"]["youtube"] is True
    assert hub["messaging"]["whatsapp"] is True
    assert hub["messaging"]["email"] is True
    assert len(hub["entrypoints"]) >= 4


def test_mcp_hub_groups_include_sales_marketing_research_and_messaging(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runner_api, "backend_status", lambda: {"hermes": False, "openclaw": False})
    monkeypatch.setattr(runner_api, "provider_status", lambda: {"apollo_mcp": False, "linkedin_sales_navigator_mcp": False, "scraper": False})
    r = client.get("/api/v1/mcp/hub")
    assert r.status_code == 200
    hub = r.json()["hub"]
    assert set(hub.keys()) >= {"models", "backends", "sales", "marketing", "research", "messaging", "entrypoints"}
    assert hub["sales"]["prospecting"] is True
    assert hub["marketing"]["social_publishing"] is True
    assert hub["research"]["knowledge_base"] is True
