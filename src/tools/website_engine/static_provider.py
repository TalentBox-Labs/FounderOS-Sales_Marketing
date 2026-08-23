"""Static-site website provider (Sprint M3).

Production-intent local adapter: writes HTML, Markdown, metadata, sitemap, and
RSS under ``output/website/``. No WordPress/Ghost/external HTTP/deploy.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.tools.website_engine.feeds import (
    FeedItem,
    build_rss,
    build_sitemap,
    write_feed_artifacts,
)
from src.tools.website_engine.provider import (
    DEFAULT_SITE_OUTPUT,
    WebsitePublicationRequest,
    WebsiteProviderResult,
    wrap_html_document,
)

_SAFE_SLUG = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,200}$")


class StaticWebsiteProvider:
    """Local/static publishing target (name=``static``)."""

    name = "static"

    def __init__(self, output_dir: Path | str | None = None) -> None:
        self.output_dir = Path(output_dir) if output_dir is not None else DEFAULT_SITE_OUTPUT

    def publish(self, request: WebsitePublicationRequest) -> WebsiteProviderResult:
        validation_error = self._validate_request(request)
        if validation_error is not None:
            return WebsiteProviderResult(
                ok=False,
                provider=self.name,
                message=validation_error,
                external_http=False,
                details={"error": validation_error},
            )

        path_error = self._validate_output_paths(request.slug)
        if path_error is not None:
            return WebsiteProviderResult(
                ok=False,
                provider=self.name,
                message=path_error,
                external_http=False,
                details={"error": path_error, "slug": request.slug},
            )

        try:
            return self._write_artifacts(request)
        except OSError as exc:
            return WebsiteProviderResult(
                ok=False,
                provider=self.name,
                message=f"Static provider write failed: {exc}",
                external_http=False,
                details={"error": str(exc), "slug": request.slug},
            )
        except (TypeError, ValueError) as exc:
            return WebsiteProviderResult(
                ok=False,
                provider=self.name,
                message=f"Static provider rejected publication: {exc}",
                external_http=False,
                details={"error": str(exc), "slug": request.slug},
            )

    def _validate_request(self, request: WebsitePublicationRequest) -> str | None:
        if request is None:
            return "Static provider requires a WebsitePublicationRequest"
        missing: list[str] = []
        if not (request.content_id or "").strip():
            missing.append("content_id")
        if not (request.slug or "").strip():
            missing.append("slug")
        if not (request.canonical_url or "").strip():
            missing.append("canonical_url")
        if not (request.title or "").strip():
            missing.append("title")
        if request.html is None or not str(request.html).strip():
            missing.append("html")
        if request.markdown is None:
            missing.append("markdown")
        if request.metadata is None:
            missing.append("metadata")
        if missing:
            return (
                "Static provider missing required fields: " + ", ".join(missing)
            )
        return None

    def _validate_output_paths(self, slug: str) -> str | None:
        cleaned = (slug or "").strip()
        if not cleaned:
            return "Static provider rejected empty slug"
        if cleaned in {".", ".."} or ".." in cleaned:
            return f"Static provider rejected unsafe slug: {slug!r}"
        if "/" in cleaned or "\\" in cleaned:
            return f"Static provider rejected path-like slug: {slug!r}"
        if not _SAFE_SLUG.match(cleaned):
            return f"Static provider rejected invalid slug: {slug!r}"
        try:
            out = self.output_dir.resolve()
            page_dir = (self.output_dir / cleaned).resolve()
            page_dir.relative_to(out)
        except (OSError, ValueError):
            return f"Static provider rejected output path for slug: {slug!r}"
        return None

    def _write_artifacts(
        self, request: WebsitePublicationRequest
    ) -> WebsiteProviderResult:
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
                f"Static provider wrote website artifacts for {request.content_id} "
                f"(no external HTTP, no deploy)."
            ),
            artifact_paths=artifacts,
            external_http=False,
            details={
                "sitemap_urls": sitemap.urls,
                "rss_item_count": len(rss.items),
                "output_dir": str(self.output_dir),
            },
        )
