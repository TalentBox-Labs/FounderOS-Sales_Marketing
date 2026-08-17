"""Focused tests for Website Engine Core (Sprint M2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.tools.website_engine import (
    StubWebsiteProvider,
    build_canonical_url,
    build_metadata,
    build_rss,
    build_sitemap,
    build_slug,
    load_website_content,
    markdown_to_html,
    publish_content,
    publish_from_job,
    slugify,
)
from src.tools.website_engine.feeds import FeedItem
from src.tools.website_engine.publish_result import STATUS_RENDERED


def _write_bundle(root: Path, content_id: str = "W99") -> Path:
    bundle = root / "input" / content_id
    bundle.mkdir(parents=True)
    (bundle / "05_Final.md").write_text(
        "---\n"
        f"week_id: {content_id}\n"
        "article_title: Hiring Systems for Modern Teams\n"
        "primary_keyword: hiring systems\n"
        "search_intent: informational\n"
        "funnel_stage: consideration\n"
        "status: approved\n"
        "publish_status: ready\n"
        "canonical_url: https://workcrew.ai/blog/hiring-systems\n"
        "cta_type: free-trial\n"
        "---\n"
        "\n"
        "# Hiring Systems for Modern Teams\n"
        "\n"
        "Structured hiring beats ad-hoc sourcing for growing teams.\n"
        "\n"
        "## Why Systems Matter\n"
        "\n"
        "- Faster time-to-hire\n"
        "- Better candidate quality\n"
        "\n"
        "Try **WorkCrew** today.\n",
        encoding="utf-8",
    )
    (bundle / "02_SEO_Plan.md").write_text(
        "# SEO Plan\n\n## CTA Strategy\nTry WorkCrew free.\n",
        encoding="utf-8",
    )
    return bundle


class TestContentModel:
    def test_load_from_filesystem_bundle(self, tmp_path: Path) -> None:
        _write_bundle(tmp_path)
        content = load_website_content("W99", repo_root=tmp_path)
        assert content.content_id == "W99"
        assert content.title == "Hiring Systems for Modern Teams"
        assert content.primary_keyword == "hiring systems"
        assert "Structured hiring" in content.markdown_body
        assert content.bundle_path == "input/W99"
        assert content.front_matter["canonical_url"].endswith("/hiring-systems")

    def test_missing_final_raises(self, tmp_path: Path) -> None:
        (tmp_path / "input" / "W98").mkdir(parents=True)
        with pytest.raises(FileNotFoundError):
            load_website_content("W98", repo_root=tmp_path)


class TestSlugAndCanonical:
    def test_slugify_and_build_from_keyword(self) -> None:
        assert slugify("Hiring Systems!") == "hiring-systems"
        assert build_slug(primary_keyword="hiring systems") == "hiring-systems"

    def test_prefers_front_matter_canonical(self) -> None:
        fm = {"canonical_url": "https://workcrew.ai/blog/hiring-systems"}
        slug = build_slug(title="Other Title", front_matter=fm)
        assert slug == "hiring-systems"
        url = build_canonical_url(slug, front_matter=fm)
        assert url == "https://workcrew.ai/blog/hiring-systems"

    def test_builds_canonical_when_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FOUNDER_SITE_ORIGIN", "https://example.invalid")
        url = build_canonical_url("modern-hiring")
        assert url == "https://example.invalid/blog/modern-hiring"


class TestMetadata:
    def test_metadata_includes_og_and_schema(self) -> None:
        meta = build_metadata(
            title="Hiring Systems for Modern Teams",
            description="Structured hiring beats ad-hoc sourcing for growing teams.",
            canonical_url="https://workcrew.ai/blog/hiring-systems",
            slug="hiring-systems",
            primary_keyword="hiring systems",
        )
        assert meta.title.startswith("Hiring Systems")
        assert meta.og["og:type"] == "article"
        assert meta.og["og:url"].endswith("/hiring-systems")
        assert meta.schema_org["@type"] == "Article"
        assert meta.schema_org["keywords"] == "hiring systems"
        assert '"@context"' in meta.schema_org_json()


class TestRenderContract:
    def test_markdown_to_html_headings_lists_inline(self) -> None:
        md = (
            "# Title\n\n"
            "Hello **bold** and *italic*.\n\n"
            "## Section\n\n"
            "- one\n"
            "- two\n"
        )
        html = markdown_to_html(md)
        assert "<h1>Title</h1>" in html
        assert "<h2>Section</h2>" in html
        assert "<strong>bold</strong>" in html
        assert "<em>italic</em>" in html
        assert "<ul>" in html
        assert "<li>one</li>" in html


class TestFeeds:
    def test_sitemap_and_rss_contracts(self) -> None:
        items = [
            FeedItem(
                title="Hiring Systems for Modern Teams",
                link="https://workcrew.ai/blog/hiring-systems",
                description="Structured hiring",
                slug="hiring-systems",
            )
        ]
        sitemap = build_sitemap(items)
        rss = build_rss(items)
        assert sitemap.urls[0]["loc"].endswith("/hiring-systems")
        assert "<urlset" in sitemap.xml
        assert "<loc>https://workcrew.ai/blog/hiring-systems</loc>" in sitemap.xml
        assert rss.items[0]["title"].startswith("Hiring Systems")
        assert "<rss" in rss.xml
        assert "<item>" in rss.xml


class TestPublishResultAndProvider:
    def test_publish_content_stub_provider(self, tmp_path: Path) -> None:
        _write_bundle(tmp_path)
        out = tmp_path / "output" / "website"
        result = publish_content(
            "W99",
            repo_root=tmp_path,
            provider=StubWebsiteProvider(output_dir=out),
        )
        channel = result.to_channel_result()
        assert channel["ok"] is True
        assert channel["status"] == STATUS_RENDERED
        assert channel["channel"] == "website"
        assert channel["owner_engine"] == "Website Engine"
        assert channel["website_engine_invoked"] is True
        assert channel["rendering_performed"] is True
        assert channel["external_api_called"] is False
        assert channel["slug"] == "hiring-systems"
        assert channel["canonical_url"].endswith("/hiring-systems")
        html_path = Path(channel["artifact_paths"]["html_path"])
        assert html_path.is_file()
        html = html_path.read_text(encoding="utf-8")
        assert "<article>" in html
        assert "og:title" in html
        assert (out / "sitemap.xml").is_file()
        assert (out / "rss.xml").is_file()

    def test_publish_from_job_channel_shape(self, tmp_path: Path) -> None:
        _write_bundle(tmp_path)
        out = tmp_path / "site_out"
        channel = publish_from_job(
            {
                "content_id": "W99",
                "bundle": "input/W99",
                "channel": "website",
            },
            repo_root=tmp_path,
            provider=StubWebsiteProvider(output_dir=out),
        )
        assert set(channel) >= {
            "ok",
            "status",
            "channel",
            "owner_engine",
            "message",
            "website_engine_invoked",
            "rendering_performed",
        }
        assert channel["ok"] is True
        assert channel["rendering_performed"] is True

    def test_publish_failure_missing_bundle(self, tmp_path: Path) -> None:
        result = publish_content("W97", repo_root=tmp_path)
        channel = result.to_channel_result()
        assert channel["ok"] is False
        assert channel["status"] == "FAILED"
        assert channel["website_engine_invoked"] is True
        assert channel["rendering_performed"] is False


class TestRepoArtifactSmoke:
    """Smoke: real approved-style bundle when present in the repo."""

    def test_load_w01_if_present(self) -> None:
        from src.tools.runtime_paths import REPO_ROOT

        final = REPO_ROOT / "input" / "W01" / "05_Final.md"
        if not final.is_file():
            pytest.skip("input/W01/05_Final.md not present")
        content = load_website_content("W01")
        assert content.content_id == "W01"
        assert content.title
        slug = build_slug(
            title=content.title,
            primary_keyword=content.primary_keyword,
            front_matter=content.front_matter,
        )
        assert slug
        assert "linkedin" in slug or "recruiter" in slug or len(slug) > 3
