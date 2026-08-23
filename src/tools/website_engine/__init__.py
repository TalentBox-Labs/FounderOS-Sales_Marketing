"""Marketing OS — Website Engine Core (Sprint M2 + M3 static provider).

Architecture v2.1 (ADR-002): owns canonical Founder website rendering and
website publishing contracts.

Does NOT own: Publishing state machine, social APIs, email, campaigns,
SEO scoring, WordPress/Ghost HTTP adapters, or deploy automation.
"""

from src.tools.website_engine.content_model import WebsiteContent, load_website_content
from src.tools.website_engine.engine import (
    prepare_website_page,
    publish_content,
    publish_from_job,
)
from src.tools.website_engine.feeds import (
    FeedItem,
    RssDocument,
    SitemapDocument,
    build_rss,
    build_sitemap,
)
from src.tools.website_engine.metadata import WebsiteMetadata, build_metadata
from src.tools.website_engine.provider import StubWebsiteProvider, WebsiteProvider
from src.tools.website_engine.publish_result import WebsitePublishResult
from src.tools.website_engine.registry import get_provider, list_providers, register_provider
from src.tools.website_engine.render import RenderResult, markdown_to_html, render_markdown
from src.tools.website_engine.static_provider import StaticWebsiteProvider
from src.tools.website_engine.urls import (
    DEFAULT_SITE_BASE,
    build_canonical_url,
    build_slug,
    slugify,
)

__all__ = [
    "DEFAULT_SITE_BASE",
    "FeedItem",
    "RenderResult",
    "RssDocument",
    "SitemapDocument",
    "StaticWebsiteProvider",
    "StubWebsiteProvider",
    "WebsiteContent",
    "WebsiteMetadata",
    "WebsiteProvider",
    "WebsitePublishResult",
    "build_canonical_url",
    "build_metadata",
    "build_rss",
    "build_sitemap",
    "build_slug",
    "get_provider",
    "list_providers",
    "load_website_content",
    "markdown_to_html",
    "prepare_website_page",
    "publish_content",
    "publish_from_job",
    "register_provider",
    "render_markdown",
    "slugify",
]
