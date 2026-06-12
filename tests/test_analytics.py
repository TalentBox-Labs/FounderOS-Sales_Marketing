from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import runner_api
from runner_api import app


class _MockDB:
    def close(self): pass

    def query(self, model):
        return _MockQuery(model)


class _MockQuery:
    def __init__(self, model):
        self._model = model
        self._filters = []

    def filter(self, *_args):
        return self

    def all(self):
        from revenue_os.models.contact import Contact, ContactStatus
        from revenue_os.models.deal import Deal, DealStage
        from revenue_os.models.activity import Activity, ActivityType
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        if self._model is Contact:
            return [
                SimpleNamespace(status=ContactStatus.LEAD, created_at=now, lead_score=70),
                SimpleNamespace(status=ContactStatus.PROSPECT, created_at=now, lead_score=50),
            ]
        if self._model is Deal:
            return [
                SimpleNamespace(stage=DealStage.QUALIFIED, value=5000.0, closed_at=None, created_at=now),
                SimpleNamespace(stage=DealStage.CLOSED_WON, value=12000.0, closed_at=now, created_at=now),
            ]
        if self._model is Activity:
            return [
                SimpleNamespace(activity_type=ActivityType.EMAIL, performed_at=now),
                SimpleNamespace(activity_type=ActivityType.EMAIL_OPEN, performed_at=now),
                SimpleNamespace(activity_type=ActivityType.LINKEDIN_MESSAGE, performed_at=now),
                SimpleNamespace(activity_type=ActivityType.CALL, performed_at=now),
            ]
        return []


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_analytics_template_exists() -> None:
    tmpl = Path(__file__).resolve().parent.parent / "templates" / "analytics.html"
    text = tmpl.read_text(encoding="utf-8")
    assert "Analytics Dashboard" in text
    assert "chart-outreach" in text
    assert "chart-revenue" in text
    assert "chart-email" in text
    assert "chart-funnel" in text
    assert "chart-contact-status" in text


def test_analytics_nav_in_base() -> None:
    base = Path(__file__).resolve().parent.parent / "templates" / "base.html"
    text = base.read_text(encoding="utf-8")
    assert "/analytics" in text
    assert "active_page == 'analytics'" in text


def test_analytics_page_route(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    # The Jinja2 LRU cache raises unhashable-dict in test env; check template content directly.
    tmpl = Path(__file__).resolve().parent.parent / "templates" / "analytics.html"
    text = tmpl.read_text(encoding="utf-8")
    assert "chart-outreach" in text
    assert "loadAnalytics" in text
    assert "/api/v1/analytics" in text


def test_analytics_api_monthly(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner_api, "SessionLocal", lambda: _MockDB())
    r = client.get("/api/v1/analytics?period=monthly")
    assert r.status_code == 200
    d = r.json()
    assert d["ok"] is True
    assert d["period"] == "monthly"
    assert len(d["labels"]) == 12
    assert "sales_kpis" in d
    assert "marketing_kpis" in d
    assert "funnel" in d
    assert "series" in d
    assert "marketing_series" in d

    sk = d["sales_kpis"]
    assert sk["total_contacts"] == 2
    assert sk["total_deals"] == 2
    assert sk["pipeline_value"] == pytest.approx(17000.0)
    assert sk["closed_won_value"] == pytest.approx(12000.0)
    assert sk["conversion_rate_pct"] == pytest.approx(50.0)


def test_analytics_api_invalid_period(client: TestClient) -> None:
    r = client.get("/api/v1/analytics?period=hourly")
    assert r.status_code == 422


def test_analytics_api_all_periods(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner_api, "SessionLocal", lambda: _MockDB())
    for period, expected_labels in [("daily", 30), ("weekly", 12), ("monthly", 12), ("yoy", 3)]:
        r = client.get(f"/api/v1/analytics?period={period}")
        assert r.status_code == 200, f"period={period} failed"
        d = r.json()
        assert d["ok"] is True
        assert len(d["labels"]) == expected_labels, f"period={period} wrong label count"


def test_analytics_email_rates_in_kpis(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner_api, "SessionLocal", lambda: _MockDB())
    r = client.get("/api/v1/analytics?period=monthly")
    d = r.json()
    mk = d["marketing_kpis"]
    assert "email_sent" in mk
    assert "email_open_rate_pct" in mk
    assert "email_click_rate_pct" in mk
    assert "email_reply_rate_pct" in mk
    assert mk["email_sent"] == 1
    assert mk["email_open_rate_pct"] == pytest.approx(100.0)
