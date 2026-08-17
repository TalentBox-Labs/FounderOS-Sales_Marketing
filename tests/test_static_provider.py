"""Focused tests for StaticWebsiteProvider (Sprint M3)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.tools.website_engine import (
    StaticWebsiteProvider,
    StubWebsiteProvider,
    get_provider,
    list_providers,
    publish_content,
)
from src.tools.website_engine.metadata import build_metadata
from src.tools.website_engine.provider import (
    WebsitePublicationRequest,
    WebsiteProviderResult,
)
from src.tools.website_engine.render import RenderResult


def _request(
    *,
    slug: str = "hiring-systems",
    title: str = "Hiring Systems for Modern Teams",
    html: str = "<p>Structured hiring beats ad-hoc sourcing.</p>\n",
    markdown: str = "Structured hiring beats ad-hoc sourcing.\n",
    content_id: str = "W99",
) -> WebsitePublicationRequest:
    canonical = f"https://workcrew.ai/blog/{slug}"
    metadata = build_metadata(
        title=title,
        description="Structured hiring beats ad-hoc sourcing for growing teams.",
        canonical_url=canonical,
        slug=slug,
        primary_keyword="hiring systems",
    )
    return WebsitePublicationRequest(
        content_id=content_id,
        slug=slug,
        canonical_url=canonical,
        title=title,
        html=html,
        markdown=markdown,
        metadata=metadata,
        render=RenderResult(html=html),
    )


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
        "Structured hiring beats ad-hoc sourcing for growing teams.\n",
        encoding="utf-8",
    )
    return bundle


class TestRegistry:
    def test_register_static_listed_and_resolvable(self) -> None:
        names = list_providers()
        assert "static" in names
        assert "stub" in names
        provider = get_provider("static")
        assert isinstance(provider, StaticWebsiteProvider)
        assert provider.name == "static"

    def test_get_provider_stub_backward_compat(self) -> None:
        provider = get_provider("stub")
        assert isinstance(provider, StubWebsiteProvider)
        assert provider.name == "stub"

    def test_get_provider_unknown_raises(self) -> None:
        with pytest.raises(KeyError, match="Unknown website provider"):
            get_provider("wordpress")


class TestStaticPublishArtifacts:
    def test_publish_artifacts_exist(self, tmp_path: Path) -> None:
        out = tmp_path / "output" / "website"
        provider = StaticWebsiteProvider(output_dir=out)
        result = provider.publish(_request())

        assert result.ok is True
        assert result.provider == "static"
        assert result.external_http is False
        html_path = Path(result.artifact_paths["html_path"])
        meta_path = Path(result.artifact_paths["metadata_path"])
        md_path = Path(result.artifact_paths["markdown_path"])
        assert html_path.is_file()
        assert meta_path.is_file()
        assert md_path.is_file()
        assert html_path.name == "index.html"
        assert meta_path.name == "metadata.json"
        assert md_path.name == "source.md"
        html = html_path.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in html
        assert "<article>" in html
        assert "og:title" in html
        assert (out / "sitemap.xml").is_file()
        assert (out / "rss.xml").is_file()
        assert "sitemap_urls" in result.details
        assert result.details["rss_item_count"] == 1

    def test_publish_result_fields(self, tmp_path: Path) -> None:
        out = tmp_path / "site"
        result = StaticWebsiteProvider(output_dir=out).publish(_request())
        payload = result.to_dict()
        assert set(payload) >= {
            "ok",
            "provider",
            "message",
            "artifact_paths",
            "external_http",
            "details",
        }
        assert payload["ok"] is True
        assert payload["provider"] == "static"
        assert payload["external_http"] is False
        assert "html_path" in payload["artifact_paths"]
        assert "sitemap_path" in payload["artifact_paths"]
        assert "rss_path" in payload["artifact_paths"]

    def test_no_external_http(self, tmp_path: Path) -> None:
        result = StaticWebsiteProvider(output_dir=tmp_path).publish(_request())
        assert isinstance(result, WebsiteProviderResult)
        assert result.external_http is False
        assert result.ok is True


class TestIdempotentOverwrite:
    def test_idempotent_overwrite_same_slug(self, tmp_path: Path) -> None:
        out = tmp_path / "output" / "website"
        provider = StaticWebsiteProvider(output_dir=out)
        first = provider.publish(
            _request(html="<p>version-one</p>\n", markdown="version-one\n")
        )
        assert first.ok is True
        html_path = Path(first.artifact_paths["html_path"])
        assert "version-one" in html_path.read_text(encoding="utf-8")

        second = provider.publish(
            _request(html="<p>version-two</p>\n", markdown="version-two\n")
        )
        assert second.ok is True
        assert Path(second.artifact_paths["html_path"]) == html_path
        body = html_path.read_text(encoding="utf-8")
        assert "version-two" in body
        assert "version-one" not in body
        assert (out / "hiring-systems" / "source.md").read_text(
            encoding="utf-8"
        ) == "version-two\n"


class TestErrorPaths:
    def test_missing_fields_safe_error(self, tmp_path: Path) -> None:
        provider = StaticWebsiteProvider(output_dir=tmp_path)
        bad = _request(slug="", title="")
        result = provider.publish(bad)
        assert result.ok is False
        assert result.provider == "static"
        assert result.external_http is False
        assert "missing required fields" in result.message.lower()
        assert not any(tmp_path.iterdir())

    def test_invalid_slug_path_safe_error(self, tmp_path: Path) -> None:
        provider = StaticWebsiteProvider(output_dir=tmp_path)
        result = provider.publish(_request(slug="../escape"))
        assert result.ok is False
        assert result.external_http is False
        assert "rejected" in result.message.lower()

    def test_write_failure_safe_error(self, tmp_path: Path) -> None:
        blocker = tmp_path / "not-a-dir"
        blocker.write_text("file", encoding="utf-8")
        provider = StaticWebsiteProvider(output_dir=blocker)
        result = provider.publish(_request())
        assert result.ok is False
        assert result.provider == "static"
        assert result.external_http is False
        assert "write failed" in result.message.lower()


class TestEngineDefaultStatic:
    def test_publish_content_defaults_to_static(self, tmp_path: Path) -> None:
        _write_bundle(tmp_path)
        out = tmp_path / "output" / "website"
        result = publish_content("W99", repo_root=tmp_path, output_dir=out)
        assert result.ok is True
        assert result.details["provider"]["provider"] == "static"
        assert result.details["provider"]["external_http"] is False
        assert (out / "hiring-systems" / "index.html").is_file()

    def test_publish_content_provider_name(self, tmp_path: Path) -> None:
        _write_bundle(tmp_path)
        out = tmp_path / "out_stub"
        result = publish_content(
            "W99",
            repo_root=tmp_path,
            provider_name="stub",
            output_dir=out,
        )
        assert result.ok is True
        assert result.details["provider"]["provider"] == "stub"
