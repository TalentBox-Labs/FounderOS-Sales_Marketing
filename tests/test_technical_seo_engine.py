"""Focused Technical SEO Engine Phase 1 tests (SENTINEL — S2).

Offline, deterministic, no external HTTP, uses example.invalid.
Does not modify frozen S1 readiness contract.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.tools.seo_engine import analyze_html, evaluate_html_readiness
from src.tools.seo_engine.technical import (
    analyze_technical_page,
    analyze_technical_site,
    write_technical_audit,
)
from src.tools.seo_engine.technical.models import OverallTechStatus as OTS
from src.tools.seo_engine.technical.parsers import parse_rss, parse_sitemap


def _page_html(
    *,
    title: str = "Technical Sample Page Title",
    description: str = "A sufficiently long meta description for technical SEO fixture coverage.",
    canonical: str = "https://example.invalid/blog/alpha",
    robots: str | None = None,
    og_url: str | None = None,
    json_ld: str | None = None,
    body: str = "<h1>Technical Sample Page Title</h1><h2>Section</h2>",
) -> str:
    robots_tag = f'<meta name="robots" content="{robots}" />\n' if robots else ""
    ou = og_url if og_url is not None else canonical
    if json_ld is None:
        json_ld = json.dumps(
            {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": title,
                "url": canonical,
                "@id": canonical,
            }
        )
    return f"""<!DOCTYPE html><html><head>
<title>{title}</title>
<meta name="description" content="{description}" />
<link rel="canonical" href="{canonical}" />
{robots_tag}
<meta property="og:type" content="article" />
<meta property="og:title" content="{title}" />
<meta property="og:description" content="{description}" />
<meta property="og:url" content="{ou}" />
<script type="application/ld+json">{json_ld}</script>
</head><body><article>{body}</article></body></html>"""


def _write_site(
    root: Path,
    pages: dict[str, str],
    *,
    sitemap_urls: list[str] | None = None,
    sitemap_raw: str | None = None,
    rss_items: list[str] | None = None,
    rss_raw: str | None = None,
    rss_channel: str = "https://example.invalid/blog",
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for slug, html in pages.items():
        d = root / slug
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(html, encoding="utf-8")
        (d / "metadata.json").write_text(
            json.dumps({"slug": slug, "canonical_url": f"https://example.invalid/blog/{slug}"}),
            encoding="utf-8",
        )
    if sitemap_raw is not None:
        (root / "sitemap.xml").write_text(sitemap_raw, encoding="utf-8")
    else:
        urls = sitemap_urls
        if urls is None:
            urls = [f"https://example.invalid/blog/{s}" for s in pages]
        body = "".join(f"<url><loc>{u}</loc></url>" for u in urls)
        (root / "sitemap.xml").write_text(
            f'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>',
            encoding="utf-8",
        )
    if rss_raw is not None:
        (root / "rss.xml").write_text(rss_raw, encoding="utf-8")
    else:
        items = rss_items
        if items is None:
            items = [f"https://example.invalid/blog/{s}" for s in pages]
        item_xml = "".join(f"<item><title>t</title><link>{u}</link></item>" for u in items)
        (root / "rss.xml").write_text(
            f'<?xml version="1.0"?><rss version="2.0"><channel>'
            f"<title>t</title><link>{rss_channel}</link><description>d</description>"
            f"{item_xml}</channel></rss>",
            encoding="utf-8",
        )


@pytest.fixture(autouse=True)
def _origin_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOUNDER_SITE_ORIGIN", "https://example.invalid")
    monkeypatch.delenv("FOUNDER_SITE_ORIGIN_RATIFIED", raising=False)


def _ids(report) -> set[str]:
    findings = getattr(report, "findings", None)
    if findings is None:
        findings = list(report.site_findings)
        for p in report.pages:
            findings.extend(p.findings)
    return {f.id for f in findings}


class TestCanonical:
    def test_correct_and_unratified(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(root, {"alpha": _page_html()})
        site = analyze_technical_site(root)
        assert "tech_canonical_unratified" in _ids(site)
        assert site.status == OTS.DOMAIN_BLOCKED

    def test_missing_canonical(self, tmp_path: Path) -> None:
        html = _page_html().replace(
            '<link rel="canonical" href="https://example.invalid/blog/alpha" />', ""
        )
        root = tmp_path / "w"
        _write_site(root, {"alpha": html})
        page = analyze_technical_page(root, "alpha")
        assert "tech_canonical_missing" in _ids(page)

    def test_duplicate_canonical(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        shared = "https://example.invalid/blog/shared"
        _write_site(
            root,
            {
                "a": _page_html(canonical=shared),
                "b": _page_html(canonical=shared, title="Other Title Page Here"),
            },
            sitemap_urls=[shared, shared],
        )
        site = analyze_technical_site(root)
        assert "tech_canonical_duplicate" in _ids(site)

    def test_mismatched_identity(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(
            root,
            {"alpha": _page_html(canonical="https://example.invalid/blog/other-slug")},
            sitemap_urls=["https://example.invalid/blog/other-slug"],
        )
        page = analyze_technical_page(root, "alpha")
        assert "tech_canonical_identity_mismatch" in _ids(page)

    def test_deprecated_workcrew(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(
            root,
            {"alpha": _page_html(canonical="https://workcrew.ai/blog/alpha")},
            sitemap_urls=["https://workcrew.ai/blog/alpha"],
            rss_items=["https://workcrew.ai/blog/alpha"],
            rss_channel="https://workcrew.ai/blog",
        )
        page = analyze_technical_page(root, "alpha")
        assert "tech_canonical_deprecated_host" in _ids(page)
        assert page.status == OTS.DOMAIN_BLOCKED

    def test_pages_dev_canonical(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(
            root,
            {"alpha": _page_html(canonical="https://founderos-staging.pages.dev/blog/alpha")},
            sitemap_urls=["https://founderos-staging.pages.dev/blog/alpha"],
        )
        page = analyze_technical_page(root, "alpha")
        assert "tech_canonical_infra_host" in _ids(page)


class TestRobots:
    def test_noindex(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(root, {"alpha": _page_html(robots="noindex,nofollow")}, sitemap_urls=[])
        page = analyze_technical_page(root, "alpha")
        assert "tech_robots_noindex" in _ids(page)

    def test_conflict(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(root, {"alpha": _page_html(robots="index, noindex")})
        page = analyze_technical_page(root, "alpha")
        assert "tech_robots_conflict" in _ids(page)

    def test_staging_protection_signal(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(
            root,
            {
                "alpha": _page_html(
                    canonical="https://founderos-staging.pages.dev/blog/alpha",
                    robots=None,
                )
            },
            sitemap_urls=["https://founderos-staging.pages.dev/blog/alpha"],
        )
        page = analyze_technical_page(root, "alpha")
        assert "tech_robots_accidental_index_risk" in _ids(page)


class TestSitemap:
    def test_valid(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(root, {"alpha": _page_html()})
        assert parse_sitemap(root / "sitemap.xml").ok

    def test_malformed(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(root, {"alpha": _page_html()}, sitemap_raw="<not-xml")
        site = analyze_technical_site(root)
        assert "tech_sitemap_malformed" in _ids(site)

    def test_duplicate_and_unsafe(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(
            root,
            {"alpha": _page_html(canonical="https://workcrew.ai/blog/alpha")},
            sitemap_urls=[
                "https://workcrew.ai/blog/alpha",
                "https://workcrew.ai/blog/alpha",
            ],
        )
        site = analyze_technical_site(root)
        assert "tech_sitemap_duplicate_url" in _ids(site)
        assert "tech_sitemap_deprecated_host" in _ids(site)

    def test_missing_eligible(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(root, {"alpha": _page_html()}, sitemap_urls=[])
        site = analyze_technical_site(root)
        assert "tech_sitemap_missing_eligible" in _ids(site)

    def test_noindex_included(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(
            root,
            {"alpha": _page_html(robots="noindex")},
            sitemap_urls=["https://example.invalid/blog/alpha"],
        )
        site = analyze_technical_site(root)
        assert "tech_sitemap_includes_noindex" in _ids(site)


class TestStructuredData:
    def test_valid(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(root, {"alpha": _page_html()})
        page = analyze_technical_page(root, "alpha")
        assert "tech_jsonld_article_ok" in _ids(page)

    def test_malformed(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(root, {"alpha": _page_html(json_ld="{bad")})
        page = analyze_technical_page(root, "alpha")
        assert "tech_jsonld_malformed" in _ids(page)

    def test_missing_type(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(
            root,
            {
                "alpha": _page_html(
                    json_ld='{"@context":"https://schema.org","headline":"x"}'
                )
            },
        )
        page = analyze_technical_page(root, "alpha")
        assert "tech_jsonld_missing_type" in _ids(page)

    def test_url_mismatch(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(
            root,
            {
                "alpha": _page_html(
                    json_ld=json.dumps(
                        {
                            "@context": "https://schema.org",
                            "@type": "Article",
                            "url": "https://example.invalid/blog/other",
                        }
                    )
                )
            },
        )
        page = analyze_technical_page(root, "alpha")
        assert "tech_jsonld_url_mismatch" in _ids(page)


class TestOpenGraph:
    def test_og_url_mismatch(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(
            root,
            {
                "alpha": _page_html(
                    og_url="https://example.invalid/blog/other",
                )
            },
        )
        page = analyze_technical_page(root, "alpha")
        assert "tech_og_url_mismatch" in _ids(page)
        assert "tech_consistency_canonical_og" in _ids(page)


class TestLinks:
    def test_broken_and_malformed_and_deprecated(self, tmp_path: Path) -> None:
        body = (
            "<h1>Technical Sample Page Title</h1>"
            '<a href="/blog/missing">x</a>'
            '<a href="javascript:alert(1)">y</a>'
            '<a href="https://workcrew.ai/blog/old">z</a>'
        )
        root = tmp_path / "w"
        _write_site(
            root,
            {
                "alpha": _page_html(body=body),
                "beta": _page_html(
                    title="Beta Page Title Here Now",
                    canonical="https://example.invalid/blog/beta",
                ),
            },
        )
        page = analyze_technical_page(root, "alpha")
        assert "tech_link_broken" in _ids(page)
        assert "tech_link_malformed" in _ids(page)
        assert "tech_link_deprecated_host" in _ids(page)

    def test_orphan_candidate(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(
            root,
            {
                "alpha": _page_html(),
                "beta": _page_html(
                    title="Beta Page Title Here Now",
                    canonical="https://example.invalid/blog/beta",
                ),
            },
        )
        site = analyze_technical_site(root)
        assert "tech_link_orphan_candidate" in _ids(site)


class TestFeed:
    def test_valid(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(root, {"alpha": _page_html()})
        assert parse_rss(root / "rss.xml").ok

    def test_malformed(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(root, {"alpha": _page_html()}, rss_raw="<rss")
        site = analyze_technical_site(root)
        assert "tech_feed_malformed" in _ids(site)

    def test_duplicate_and_origin(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(
            root,
            {"alpha": _page_html()},
            rss_items=[
                "https://example.invalid/blog/alpha",
                "https://example.invalid/blog/alpha",
            ],
            rss_channel="https://other.example/blog",
        )
        site = analyze_technical_site(root)
        assert "tech_feed_duplicate_item" in _ids(site)
        assert "tech_feed_origin_mismatch" in _ids(site)


class TestConsistencyAndSafety:
    def test_canonical_sitemap_conflict(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(
            root,
            {"alpha": _page_html(canonical="https://example.invalid/blog/alpha")},
        )
        (root / "sitemap.xml").write_text(
            '<?xml version="1.0"?><urlset><url>'
            "<loc>https://example.invalid/blog/alpha?x=1</loc></url></urlset>",
            encoding="utf-8",
        )
        site = analyze_technical_site(root)
        assert "tech_consistency_canonical_sitemap" in _ids(site)

    def test_audit_does_not_mutate_artifacts(self, tmp_path: Path) -> None:
        root = tmp_path / "w"
        _write_site(root, {"alpha": _page_html()})
        before = (root / "alpha" / "index.html").read_text(encoding="utf-8")
        site = analyze_technical_site(root)
        write_technical_audit(site, output_dir=tmp_path / "out")
        assert (root / "alpha" / "index.html").read_text(encoding="utf-8") == before
        assert (tmp_path / "out" / "site.json").is_file()
        assert site.to_dict()["s1_readiness_contract"] == "UNCHANGED"
        assert site.to_dict()["submits_to_search_engines"] is False

    def test_s1_readiness_untouched(self) -> None:
        html = _page_html()
        r = evaluate_html_readiness(
            html, slug="alpha", configured_origin="https://example.invalid"
        )
        assert r.ok
        pr = analyze_html(html, slug="alpha", configured_origin="https://example.invalid")
        assert pr.domain_blockers
