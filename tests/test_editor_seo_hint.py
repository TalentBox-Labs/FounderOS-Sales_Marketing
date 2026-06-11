"""Deterministic SEO canonical extraction for Phase 2B editor prompt."""

from __future__ import annotations

from src.editor_crew import extract_canonical_url_from_seo_plan


def test_extract_canonical_bold_backticks():
    text = """
## 1. URL slug
**Canonical URL:** `https://workcrew.ai/blog/example-slug`
"""
    assert (
        extract_canonical_url_from_seo_plan(text)
        == "https://workcrew.ai/blog/example-slug"
    )


def test_extract_canonical_plain_label():
    text = "- Canonical URL: `https://workcrew.com/blog/other-post`\n"
    assert extract_canonical_url_from_seo_plan(text) == "https://workcrew.com/blog/other-post"


def test_extract_canonical_returns_none_when_missing():
    assert extract_canonical_url_from_seo_plan("no url here") is None


def test_seo_canonical_section_missing_file(tmp_path, monkeypatch):
    from src import editor_crew

    fake_repo = tmp_path
    monkeypatch.setattr(editor_crew, "BASE_DIR", fake_repo)
    out = editor_crew._seo_canonical_section("output/generated/W99")
    assert "No `output/generated/W99/02_SEO_Plan.md`" in out


def test_seo_canonical_section_with_url(tmp_path, monkeypatch):
    from src import editor_crew
    from src.crew import BASE_DIR

    root = tmp_path / "output/generated/W99"
    root.mkdir(parents=True)
    (root / "02_SEO_Plan.md").write_text(
        "**Canonical URL:** `https://workcrew.com/blog/x`\n", encoding="utf-8"
    )
    monkeypatch.setattr(editor_crew, "BASE_DIR", tmp_path)
    out = editor_crew._seo_canonical_section("output/generated/W99")
    assert "https://workcrew.com/blog/x" in out

