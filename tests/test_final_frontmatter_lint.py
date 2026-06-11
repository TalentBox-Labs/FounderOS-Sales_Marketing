"""Deterministic 05_Final front matter schema."""

from __future__ import annotations

import pytest

from src.tools.final_frontmatter_lint import (
    ALLOWED_PUBLISH_STATUS,
    REQUIRED_KEYS,
    lint_final_front_matter,
)


def test_required_keys_constant_complete():
    assert "canonical_url" in REQUIRED_KEYS
    assert "cta_type" in REQUIRED_KEYS
    assert "ready" in ALLOWED_PUBLISH_STATUS


def test_passes_minimal_valid_fm():
    fm = {
        "week_id": "W05",
        "article_title": "Hello",
        "primary_keyword": "kw",
        "search_intent": "informational",
        "funnel_stage": "awareness",
        "status": "Approved",
        "publish_status": "Ready",
        "canonical_url": "https://example.com/a",
        "cta_type": "try_workcrew_free",
    }
    p, f = lint_final_front_matter(fm)
    assert not f
    assert any("canonical_url" in x for x in p)


def test_fails_missing_canonical_and_cta():
    fm = {
        "week_id": "W05",
        "article_title": "Hello",
        "primary_keyword": "kw",
        "search_intent": "informational",
        "funnel_stage": "awareness",
        "status": "Approved",
        "publish_status": "Ready",
    }
    _, f = lint_final_front_matter(fm)
    assert any("canonical_url" in x for x in f)
    assert any("cta_type" in x for x in f)


def test_fails_bracket_in_optional_key():
    fm = {
        "week_id": "W05",
        "article_title": "Hello",
        "primary_keyword": "kw",
        "search_intent": "informational",
        "funnel_stage": "awareness",
        "status": "Approved",
        "publish_status": "Ready",
        "canonical_url": "https://example.com/a",
        "cta_type": "primary",
        "extra": "[BAD]",
    }
    _, f = lint_final_front_matter(fm)
    assert any("optional" in x and "extra" in x for x in f)


def test_fails_invalid_publish_status():
    fm = {
        "week_id": "W05",
        "article_title": "Hello",
        "primary_keyword": "kw",
        "search_intent": "informational",
        "funnel_stage": "awareness",
        "status": "Approved",
        "publish_status": "AbsolutelyNotAStatus",
        "canonical_url": "https://example.com/a",
        "cta_type": "primary",
    }
    _, f = lint_final_front_matter(fm)
    assert any("publish_status" in x for x in f)


def test_fails_bad_url():
    fm = {
        "week_id": "W05",
        "article_title": "Hello",
        "primary_keyword": "kw",
        "search_intent": "informational",
        "funnel_stage": "awareness",
        "status": "Approved",
        "publish_status": "Ready",
        "canonical_url": "/relative-only",
        "cta_type": "primary",
    }
    _, f = lint_final_front_matter(fm)
    assert any("canonical_url" in x for x in f)


@pytest.mark.parametrize(
    "url", ["https://x.com/y", "http://x.com/z"]
)
def test_url_accepted(url: str):
    fm = {
        "week_id": "W05",
        "article_title": "Hello",
        "primary_keyword": "kw",
        "search_intent": "informational",
        "funnel_stage": "awareness",
        "status": "Approved",
        "publish_status": "Ready",
        "canonical_url": url,
        "cta_type": "primary",
    }
    _, f = lint_final_front_matter(fm)
    assert not any("canonical_url must" in x for x in f)
