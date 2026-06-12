from __future__ import annotations

from dataclasses import dataclass

import pytest

from revenue_os.models.contact import ContactSource, ContactStatus
from revenue_os.services.lead_prospecting_service import build_prospecting_plan


@dataclass
class _DummyContact:
    id: str
    first_name: str
    last_name: str
    designation: str
    linkedin_url: str
    lead_score: int
    status: ContactStatus
    source: ContactSource

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class _DummyQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def limit(self, n: int):
        self.rows = self.rows[:n]
        return self

    def all(self):
        return self.rows


class _DummyDB:
    def __init__(self, rows):
        self._rows = rows

    def query(self, _model):
        return _DummyQuery(self._rows)


def test_plan_uses_free_then_scraper_then_mcp(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROSPECT_FREE_LIMIT", "2")
    monkeypatch.setenv("PROSPECT_SCRAPER_LIMIT", "3")
    monkeypatch.setenv("PROSPECT_MCP_LIMIT", "4")
    monkeypatch.setenv("PROSPECT_GLOBAL_MAX", "20")
    monkeypatch.setenv("SCRAPER_PROVIDER_URL", "https://scraper.local")
    monkeypatch.setenv("APOLLO_MCP_API_KEY", "apollo-key")

    db = _DummyDB(
        [
            _DummyContact(
                id="1",
                first_name="A",
                last_name="One",
                designation="Founder",
                linkedin_url="https://linkedin.com/in/a-one",
                lead_score=80,
                status=ContactStatus.LEAD,
                source=ContactSource.LINKEDIN,
            ),
            _DummyContact(
                id="2",
                first_name="B",
                last_name="Two",
                designation="VP Sales",
                linkedin_url="https://linkedin.com/in/b-two",
                lead_score=75,
                status=ContactStatus.PROSPECT,
                source=ContactSource.LINKEDIN,
            ),
        ]
    )

    plan = build_prospecting_plan(
        db,
        target_count=8,
        min_score=20,
        statuses=[ContactStatus.LEAD, ContactStatus.PROSPECT],
        allow_scraper=True,
        allow_mcp=True,
    )

    assert plan["target_count"] == 8
    assert plan["stages"][0]["used"] == 2
    assert plan["stages"][1]["used"] == 3
    assert plan["stages"][2]["used"] == 3
    assert plan["unfilled_after_limits"] == 0
    assert len(plan["selected_existing_linkedin_contacts"]) == 2


def test_plan_respects_disabled_or_unconfigured_stages(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROSPECT_FREE_LIMIT", "1")
    monkeypatch.setenv("PROSPECT_SCRAPER_LIMIT", "5")
    monkeypatch.setenv("PROSPECT_MCP_LIMIT", "10")
    monkeypatch.delenv("SCRAPER_PROVIDER_URL", raising=False)
    monkeypatch.delenv("APOLLO_MCP_API_KEY", raising=False)
    monkeypatch.delenv("LINKEDIN_SALES_NAVIGATOR_MCP_TOKEN", raising=False)

    db = _DummyDB(
        [
            _DummyContact(
                id="1",
                first_name="A",
                last_name="One",
                designation="Founder",
                linkedin_url="https://linkedin.com/in/a-one",
                lead_score=80,
                status=ContactStatus.LEAD,
                source=ContactSource.LINKEDIN,
            )
        ]
    )

    plan = build_prospecting_plan(
        db,
        target_count=7,
        min_score=20,
        statuses=[ContactStatus.LEAD, ContactStatus.PROSPECT],
        allow_scraper=False,
        allow_mcp=True,
    )

    assert plan["stages"][0]["used"] == 1
    assert plan["stages"][1]["used"] == 0
    assert plan["stages"][2]["used"] == 0
    assert plan["unfilled_after_limits"] == 6
