"""Sitemap and RSS contract builders (in-memory / optional local write).

Does not deploy or call external HTTP endpoints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from xml.etree.ElementTree import Element, SubElement, tostring

from src.tools.runtime_paths import REPO_ROOT
from src.tools.site_origin import (
    DEFAULT_FEED_DESCRIPTION,
    DEFAULT_FEED_TITLE,
    get_site_base,
)

DEFAULT_OUTPUT_DIR = REPO_ROOT / "output" / "website"


@dataclass(frozen=True)
class FeedItem:
    title: str
    link: str
    description: str = ""
    pub_date: str = ""
    slug: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "link": self.link,
            "description": self.description,
            "pub_date": self.pub_date,
            "slug": self.slug,
        }


@dataclass(frozen=True)
class SitemapDocument:
    urls: list[dict[str, str]] = field(default_factory=list)
    xml: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"urls": list(self.urls), "xml": self.xml}


@dataclass(frozen=True)
class RssDocument:
    title: str
    link: str
    description: str
    items: list[dict[str, str]] = field(default_factory=list)
    xml: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "link": self.link,
            "description": self.description,
            "items": list(self.items),
            "xml": self.xml,
        }


def _utc_now_rfc822() -> str:
    return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")


def _xml_bytes(root: Element) -> str:
    return tostring(root, encoding="unicode", xml_declaration=False)


def build_sitemap(items: Iterable[FeedItem]) -> SitemapDocument:
    """Build sitemap URL set + XML string."""
    urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    urls: list[dict[str, str]] = []
    for item in items:
        loc = item.link.strip()
        if not loc:
            continue
        entry = {"loc": loc}
        if item.pub_date:
            entry["lastmod"] = item.pub_date
        urls.append(entry)
        node = SubElement(urlset, "url")
        SubElement(node, "loc").text = loc
        if item.pub_date:
            SubElement(node, "lastmod").text = item.pub_date
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + _xml_bytes(urlset) + "\n"
    return SitemapDocument(urls=urls, xml=xml)


def build_rss(
    items: Iterable[FeedItem],
    *,
    title: str = DEFAULT_FEED_TITLE,
    link: str | None = None,
    description: str = DEFAULT_FEED_DESCRIPTION,
) -> RssDocument:
    """Build RSS 2.0 channel + XML string."""
    channel_link = link if link is not None else get_site_base()
    item_list = list(items)
    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = title
    SubElement(channel, "link").text = channel_link
    SubElement(channel, "description").text = description
    serialized_items: list[dict[str, str]] = []
    for item in item_list:
        node = SubElement(channel, "item")
        SubElement(node, "title").text = item.title
        SubElement(node, "link").text = item.link
        SubElement(node, "description").text = item.description or item.title
        pub = item.pub_date or _utc_now_rfc822()
        SubElement(node, "pubDate").text = pub
        if item.slug:
            SubElement(node, "guid", isPermaLink="false").text = item.slug
        serialized_items.append(
            {
                "title": item.title,
                "link": item.link,
                "description": item.description or item.title,
                "pub_date": pub,
                "slug": item.slug,
            }
        )
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + _xml_bytes(rss) + "\n"
    return RssDocument(
        title=title,
        link=channel_link,
        description=description,
        items=serialized_items,
        xml=xml,
    )


def write_feed_artifacts(
    *,
    sitemap: SitemapDocument,
    rss: RssDocument,
    output_dir: Path | None = None,
) -> dict[str, str]:
    """Optionally persist sitemap/RSS under ``output/website/`` (no deploy)."""
    out = output_dir or DEFAULT_OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    sitemap_path = out / "sitemap.xml"
    rss_path = out / "rss.xml"
    sitemap_path.write_text(sitemap.xml, encoding="utf-8")
    rss_path.write_text(rss.xml, encoding="utf-8")
    return {
        "sitemap_path": str(sitemap_path),
        "rss_path": str(rss_path),
    }
