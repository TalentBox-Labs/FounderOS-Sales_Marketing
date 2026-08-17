"""Provider-neutral website publication interface.

Includes in-process StubWebsiteProvider (M2) and shared HTML wrap helpers
used by StaticWebsiteProvider (M3). No WordPress/Ghost/external HTTP publish.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from src.tools.runtime_paths import REPO_ROOT
from src.tools.website_engine.feeds import (
    FeedItem,
    build_rss,
    build_sitemap,
    write_feed_artifacts,
)
from src.tools.website_engine.metadata import WebsiteMetadata
from src.tools.website_engine.render import RenderResult

DEFAULT_SITE_OUTPUT = REPO_ROOT / "output" / "website"


@dataclass(frozen=True)
class WebsitePublicationRequest:
    content_id: str
    slug: str
    canonical_url: str
    title: str
    html: str
    markdown: str
    metadata: WebsiteMetadata
    render: RenderResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "content_id": self.content_id,
            "slug": self.slug,
            "canonical_url": self.canonical_url,
            "title": self.title,
            "html": self.html,
            "markdown": self.markdown,
            "metadata": self.metadata.to_dict(),
            "render": self.render.to_dict(),
        }


@dataclass
class WebsiteProviderResult:
    ok: bool
    provider: str
    message: str
    artifact_paths: dict[str, str] = field(default_factory=dict)
    external_http: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "provider": self.provider,
            "message": self.message,
            "artifact_paths": dict(self.artifact_paths),
            "external_http": self.external_http,
            "details": dict(self.details),
        }


@runtime_checkable
class WebsiteProvider(Protocol):
    """Provider-neutral publication interface (WordPress/Ghost/static later)."""

    name: str

    def publish(self, request: WebsitePublicationRequest) -> WebsiteProviderResult:
        ...


class StubWebsiteProvider:
    """In-process stub: writes HTML + feeds under ``output/website/`` only."""

    name = "stub"

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or DEFAULT_SITE_OUTPUT

    def publish(self, request: WebsitePublicationRequest) -> WebsiteProviderResult:
        page_dir = self.output_dir / request.slug
        page_dir.mkdir(parents=True, exist_ok=True)
        html_path = page_dir / "index.html"
        meta_path = page_dir / "metadata.json"
        md_path = page_dir / "source.md"

        page_html = wrap_html_document(request)
        html_path.write_text(page_html, encoding="utf-8")
        meta_path.write_text(
            json.dumps(request.metadata.to_dict(), indent=2) + "\n",
            encoding="utf-8",
        )
        md_path.write_text(request.markdown, encoding="utf-8")

        feed_item = FeedItem(
            title=request.title,
            link=request.canonical_url,
            description=request.metadata.description,
            slug=request.slug,
        )
        sitemap = build_sitemap([feed_item])
        rss = build_rss([feed_item])
        feed_paths = write_feed_artifacts(
            sitemap=sitemap, rss=rss, output_dir=self.output_dir
        )

        artifacts = {
            "html_path": str(html_path),
            "metadata_path": str(meta_path),
            "markdown_path": str(md_path),
            **feed_paths,
        }
        return WebsiteProviderResult(
            ok=True,
            provider=self.name,
            message=(
                f"Stub provider wrote website artifacts for {request.content_id} "
                f"(no external HTTP, no deploy)."
            ),
            artifact_paths=artifacts,
            external_http=False,
            details={
                "sitemap_urls": sitemap.urls,
                "rss_item_count": len(rss.items),
            },
        )


def wrap_html_document(request: WebsitePublicationRequest) -> str:
    """Wrap article HTML fragment in a full document with meta/OG/JSON-LD."""
    meta = request.metadata
    og_tags = "\n".join(
        f'  <meta property="{key}" content="{escape_html_attr(value)}" />'
        for key, value in meta.og.items()
    )
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8" />\n'
        f"  <title>{escape_html_attr(meta.title)}</title>\n"
        f'  <meta name="description" content="{escape_html_attr(meta.description)}" />\n'
        f'  <link rel="canonical" href="{escape_html_attr(meta.canonical_url)}" />\n'
        f"{og_tags}\n"
        '  <script type="application/ld+json">\n'
        f"{meta.schema_org_json()}\n"
        "  </script>\n"
        "</head>\n"
        "<body>\n"
        f"  <article>\n{request.html}"
        "  </article>\n"
        "</body>\n"
        "</html>\n"
    )


def escape_html_attr(value: str) -> str:
    return (
        (value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# Backward-compatible private aliases (M2 call sites / tests).
_wrap_html_document = wrap_html_document
_esc = escape_html_attr
