"""Focused Phase-1 SEO Readiness Engine tests (SENTINEL — S1).

Offline fixtures only. Origins use https://example.invalid.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.tools.seo_engine import (
    CheckStatus,
    OverallStatus,
    analyze_html,
    analyze_page_artifact,
    analyze_site,
    evaluate_html_readiness,
    write_page_audit,
    write_site_audit,
)
from src.tools.site_origin import PLACEHOLDER_SITE_ORIGIN, is_indexing_activation_allowed


def _html(
    *,
    title: str = "Healthy Sample Page Title",
    description: str = "A sufficiently long meta description for SEO readiness testing purposes here.",
    canonical: str = "https://example.invalid/blog/healthy-page",
    slug_in_links: str | None = None,
    h1: str | None = "Healthy Sample Page Title",
    extra_h1: bool = False,
    robots: str | None = None,
    og: bool = True,
    json_ld: str | None = '{"@context":"https://schema.org","@type":"Article","headline":"Healthy"}',
    body_extra: str = "",
) -> str:
    robots_tag = (
        f'  <meta name="robots" content="{robots}" />\n' if robots is not None else ""
    )
    og_block = ""
    if og:
        og_block = (
            f'  <meta property="og:type" content="article" />\n'
            f'  <meta property="og:title" content="{title}" />\n'
            f'  <meta property="og:description" content="{description}" />\n'
            f'  <meta property="og:url" content="{canonical}" />\n'
        )
    jl = ""
    if json_ld is not None:
        jl = f'  <script type="application/ld+json">{json_ld}</script>\n'
    h1_html = f"<h1>{h1}</h1>\n" if h1 is not None else ""
    if extra_h1:
        h1_html += "<h1>Second H1</h1>\n"
    link = ""
    if slug_in_links:
        link = f'<p><a href="/blog/{slug_in_links}">Related</a></p>\n'
    return (
        "<!DOCTYPE html><html lang=\"en\"><head>\n"
        f"  <title>{title}</title>\n"
        f'  <meta name="description" content="{description}" />\n'
        f'  <link rel="canonical" href="{canonical}" />\n'
        f"{robots_tag}{og_block}{jl}"
        "</head><body><article>\n"
        f"{h1_html}<h2>Section</h2>\n{link}{body_extra}"
        "</article></body></html>"
    )


@pytest.fixture(autouse=True)
def _clear_origin_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FOUNDER_SITE_ORIGIN", raising=False)
    monkeypatch.delenv("FOUNDER_SITE_BASE_PATH", raising=False)
    monkeypatch.delenv("FOUNDER_SITE_ORIGIN_RATIFIED", raising=False)
    monkeypatch.setenv("FOUNDER_SITE_ORIGIN", "https://example.invalid")


def _write_page(
    root: Path,
    slug: str,
    html: str,
    *,
    meta: dict | None = None,
    sitemap: bool = True,
    rss: bool = True,
) -> None:
    page_dir = root / slug
    page_dir.mkdir(parents=True, exist_ok=True)
    (page_dir / "index.html").write_text(html, encoding="utf-8")
    payload = meta or {
        "slug": slug,
        "title": "t",
        "description": "d",
        "canonical_url": f"https://example.invalid/blog/{slug}",
    }
    (page_dir / "metadata.json").write_text(json.dumps(payload), encoding="utf-8")
    if sitemap:
        sm = root / "sitemap.xml"
        existing = sm.read_text(encoding="utf-8") if sm.exists() else '<?xml version="1.0"?><urlset>'
        if "</urlset>" in existing:
            existing = existing.replace(
                "</urlset>",
                f"<url><loc>https://example.invalid/blog/{slug}</loc></url></urlset>",
            )
        else:
            existing = (
                '<?xml version="1.0"?><urlset>'
                f"<url><loc>https://example.invalid/blog/{slug}</loc></url></urlset>"
            )
        sm.write_text(existing, encoding="utf-8")
    if rss:
        rf = root / "rss.xml"
        existing = rf.read_text(encoding="utf-8") if rf.exists() else "<rss><channel>"
        if "</channel>" in existing:
            existing = existing.replace(
                "</channel>",
                f"<item><link>https://example.invalid/blog/{slug}</link></item></channel>",
            )
        else:
            existing = (
                f"<rss><channel><item><link>https://example.invalid/blog/{slug}</link>"
                "</item></channel></rss>"
            )
        rf.write_text(existing, encoding="utf-8")


def _ids(result) -> set[str]:
    return {c.id for c in result.checks}


def _statuses(result, check_id: str) -> list[CheckStatus]:
    return [c.status for c in result.checks if c.id == check_id]


class TestHealthyAndBasics:
    def test_healthy_page_technical_checks(self) -> None:
        result = analyze_html(
            _html(slug_in_links="other"),
            slug="healthy-page",
            configured_origin="https://example.invalid",
            known_slugs={"healthy-page", "other"},
        )
        assert "title_present" in _ids(result) or "title_too_short" not in _ids(result)
        assert not result.errors
        # Placeholder origin always domain-blocks production activation
        assert result.status == OverallStatus.DOMAIN_BLOCKED
        assert result.domain_blockers
        assert result.score >= 70
        assert result.to_dict()["mutates_content"] is False
        assert result.to_dict()["submits_to_search_engines"] is False

    def test_missing_title(self) -> None:
        html = _html().replace("<title>Healthy Sample Page Title</title>", "<title></title>")
        result = analyze_html(html, slug="x", configured_origin="https://example.invalid")
        assert "title_missing" in _ids(result)
        assert any(c.status == CheckStatus.ERROR for c in result.errors)

    def test_missing_description(self) -> None:
        html = _html().replace(
            'content="A sufficiently long meta description for SEO readiness testing purposes here."',
            'content=""',
        )
        result = analyze_html(html, slug="x", configured_origin="https://example.invalid")
        assert "description_missing" in _ids(result)

    def test_bad_slug(self) -> None:
        result = analyze_html(_html(), slug="Bad Slug!!", configured_origin="https://example.invalid")
        assert "slug_malformed" in _ids(result)

    def test_missing_h1(self) -> None:
        result = analyze_html(
            _html(h1=None), slug="page", configured_origin="https://example.invalid"
        )
        assert "h1_missing" in _ids(result)

    def test_multiple_h1(self) -> None:
        result = analyze_html(
            _html(extra_h1=True), slug="page", configured_origin="https://example.invalid"
        )
        assert "h1_multiple" in _ids(result)
        assert CheckStatus.WARNING in _statuses(result, "h1_multiple")


class TestDuplicates:
    def test_duplicate_title_description_canonical(self, tmp_path: Path) -> None:
        root = tmp_path / "website"
        shared_title = "Shared Duplicate Title Page"
        shared_desc = "Shared duplicate description text that is long enough for policy."
        html_a = _html(
            title=shared_title,
            description=shared_desc,
            canonical="https://example.invalid/blog/page-a",
        )
        html_b = _html(
            title=shared_title,
            description=shared_desc,
            canonical="https://example.invalid/blog/page-a",  # intentional dup canonical
        )
        _write_page(root, "page-a", html_a)
        _write_page(root, "page-b", html_b)
        site = analyze_site(root, configured_origin="https://example.invalid")
        codes = set()
        for p in site.pages:
            codes |= _ids(p)
        assert "title_duplicate" in codes
        assert "description_duplicate" in codes
        assert "canonical_duplicate" in codes


class TestOriginSafety:
    def test_deprecated_workcrew_reference(self) -> None:
        result = analyze_html(
            _html(canonical="https://workcrew.ai/blog/page"),
            slug="page",
            configured_origin="https://example.invalid",
        )
        assert "canonical_deprecated_host" in _ids(result)
        assert result.status == OverallStatus.DOMAIN_BLOCKED

    def test_unratified_site_origin(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FOUNDER_SITE_ORIGIN", "https://future-brand.example")
        monkeypatch.delenv("FOUNDER_SITE_ORIGIN_RATIFIED", raising=False)
        assert is_indexing_activation_allowed() is False
        result = analyze_html(
            _html(canonical="https://future-brand.example/blog/page"),
            slug="page",
            configured_origin="https://future-brand.example",
        )
        assert "canonical_origin_unratified" in _ids(result) or "indexability_activation_blocked" in _ids(
            result
        )
        assert result.status == OverallStatus.DOMAIN_BLOCKED

    def test_safe_placeholder_origin_cannot_authorize(self) -> None:
        assert PLACEHOLDER_SITE_ORIGIN == "https://example.invalid"
        assert is_indexing_activation_allowed() is False
        result = analyze_html(
            _html(), slug="page", configured_origin="https://example.invalid"
        )
        assert result.indexing_activation_allowed is False
        assert result.domain_blockers

    def test_pages_dev_canonical_blocked(self) -> None:
        result = analyze_html(
            _html(canonical="https://founderos-staging.pages.dev/blog/page"),
            slug="page",
            configured_origin="https://example.invalid",
        )
        assert "canonical_infrastructure_host" in _ids(result)

    def test_no_workcrew_runtime_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("FOUNDER_SITE_ORIGIN", raising=False)
        from src.tools.site_origin import get_configured_site_origin, get_site_base

        assert "workcrew.ai" not in get_configured_site_origin()
        assert "workcrew.ai" not in get_site_base()


class TestLinksAndFeeds:
    def test_malformed_internal_link(self) -> None:
        html = _html(body_extra='<a href="javascript:alert(1)">x</a>')
        result = analyze_html(html, slug="page", configured_origin="https://example.invalid")
        assert "internal_link_malformed" in _ids(result)

    def test_broken_internal_link(self) -> None:
        result = analyze_html(
            _html(slug_in_links="missing-target"),
            slug="page",
            configured_origin="https://example.invalid",
            known_slugs={"page"},
        )
        assert "internal_link_broken" in _ids(result)

    def test_deprecated_host_in_link(self) -> None:
        html = _html(body_extra='<a href="https://workcrew.ai/blog/old">old</a>')
        result = analyze_html(html, slug="page", configured_origin="https://example.invalid")
        assert "internal_link_deprecated_host" in _ids(result)

    def test_index_blocked_page(self) -> None:
        result = analyze_html(
            _html(robots="noindex,nofollow"),
            slug="page",
            configured_origin="https://example.invalid",
        )
        assert "robots_noindex" in _ids(result)

    def test_sitemap_and_feed_eligibility(self, tmp_path: Path) -> None:
        root = tmp_path / "website"
        _write_page(root, "in-feeds", _html(canonical="https://example.invalid/blog/in-feeds"))
        # page missing from feeds
        page_dir = root / "orphan"
        page_dir.mkdir()
        (page_dir / "index.html").write_text(
            _html(canonical="https://example.invalid/blog/orphan"), encoding="utf-8"
        )
        (page_dir / "metadata.json").write_text(
            json.dumps({"slug": "orphan"}), encoding="utf-8"
        )
        site = analyze_site(root, configured_origin="https://example.invalid")
        by_slug = {p.slug: p for p in site.pages}
        assert "sitemap_eligible_present" in _ids(by_slug["in-feeds"])
        assert "feed_eligible_present" in _ids(by_slug["in-feeds"])
        assert "sitemap_missing_slug" in _ids(by_slug["orphan"])
        assert "rss_missing_slug" in _ids(by_slug["orphan"])


class TestJsonLd:
    def test_valid_json_ld(self) -> None:
        result = analyze_html(_html(), slug="page", configured_origin="https://example.invalid")
        assert "schema_article_present" in _ids(result)

    def test_invalid_json_ld(self) -> None:
        result = analyze_html(
            _html(json_ld="{not-json"),
            slug="page",
            configured_origin="https://example.invalid",
        )
        assert "jsonld_invalid" in _ids(result)


class TestAuditAndS0Compat:
    def test_audit_write_does_not_touch_input(self, tmp_path: Path) -> None:
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        marker = input_dir / "W99" / "05_Final.md"
        marker.parent.mkdir()
        marker.write_text("unchanged", encoding="utf-8")
        result = analyze_html(_html(), slug="page", configured_origin="https://example.invalid")
        out = write_page_audit(result, output_dir=tmp_path / "seo")
        assert out.is_file()
        assert marker.read_text(encoding="utf-8") == "unchanged"
        site = analyze_site(tmp_path / "empty_site", configured_origin="https://example.invalid")
        write_site_audit(site, output_dir=tmp_path / "seo")
        assert (tmp_path / "seo" / "site.json").is_file()

    def test_s0_evaluate_still_works(self) -> None:
        report = evaluate_html_readiness(
            _html(), slug="page", configured_origin="https://example.invalid"
        )
        assert report.ok or any(f.code == "deprecated_host" for f in report.findings) or True
        # S0 healthy path: title/desc/h1 present → ok True (domain is WARNING in S0)
        assert report.ok

    def test_analyze_page_artifact_missing(self, tmp_path: Path) -> None:
        result = analyze_page_artifact(tmp_path, "missing")
        assert "html_missing" in _ids(result)
        assert result.status == OverallStatus.ERROR

    def test_score_cannot_override_domain_block(self) -> None:
        result = analyze_html(
            _html(canonical="https://workcrew.ai/blog/page"),
            slug="page",
            configured_origin="https://example.invalid",
        )
        assert result.score >= 0
        assert result.status == OverallStatus.DOMAIN_BLOCKED
        assert not result.seo_ready
