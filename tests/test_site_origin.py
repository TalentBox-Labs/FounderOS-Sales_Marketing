"""Tests for configurable site origin (S0)."""

from __future__ import annotations

import os

import pytest

from src.tools.site_origin import (
    PLACEHOLDER_SITE_ORIGIN,
    get_configured_site_origin,
    get_site_base,
    is_indexing_activation_allowed,
)
from src.tools.website_engine import build_canonical_url, build_rss
from src.tools.website_engine.feeds import FeedItem


@pytest.fixture(autouse=True)
def _clear_origin_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FOUNDER_SITE_ORIGIN", raising=False)
    monkeypatch.delenv("FOUNDER_SITE_BASE_PATH", raising=False)
    monkeypatch.delenv("FOUNDER_SITE_ORIGIN_RATIFIED", raising=False)


def test_default_origin_is_placeholder() -> None:
    assert get_configured_site_origin() == PLACEHOLDER_SITE_ORIGIN
    assert get_site_base() == f"{PLACEHOLDER_SITE_ORIGIN}/blog"


def test_env_origin_changes_site_base(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOUNDER_SITE_ORIGIN", "https://example.invalid")
    monkeypatch.setenv("FOUNDER_SITE_BASE_PATH", "/blog")
    assert get_site_base() == "https://example.invalid/blog"


def test_build_canonical_url_uses_configured_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOUNDER_SITE_ORIGIN", "https://example.invalid")
    url = build_canonical_url("modern-hiring")
    assert url == "https://example.invalid/blog/modern-hiring"


def test_front_matter_canonical_unchanged_by_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOUNDER_SITE_ORIGIN", "https://example.invalid")
    fm = {"canonical_url": "https://workcrew.ai/blog/hiring-systems"}
    url = build_canonical_url("hiring-systems", front_matter=fm)
    assert url == "https://workcrew.ai/blog/hiring-systems"


def test_rss_default_link_follows_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOUNDER_SITE_ORIGIN", "https://example.invalid")
    items = [
        FeedItem(
            title="Example",
            link="https://example.invalid/blog/example",
            description="desc",
            slug="example",
        )
    ]
    rss = build_rss(items)
    assert "https://example.invalid/blog" in rss.link


def test_indexing_blocked_without_ratification(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOUNDER_SITE_ORIGIN", "https://future-brand.example")
    assert is_indexing_activation_allowed() is False


def test_indexing_blocked_on_placeholder_even_if_ratified(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FOUNDER_SITE_ORIGIN_RATIFIED", "true")
    assert is_indexing_activation_allowed() is False


def test_indexing_allowed_only_with_ratified_non_infra_origin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FOUNDER_SITE_ORIGIN", "https://future-brand.example")
    monkeypatch.setenv("FOUNDER_SITE_ORIGIN_RATIFIED", "1")
    assert is_indexing_activation_allowed() is True
