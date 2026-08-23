"""Technical artifact parsers (NOVA — S2). Read-only, bounded."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from src.tools.seo_engine.artifacts import (
    default_artifact_root,
    list_page_slugs,
    load_page_artifact,
    load_site_inventory,
)
from src.tools.seo_engine.extract import ExtractedPage
from src.tools.seo_engine.technical.policy import (
    MAX_FEED_BYTES,
    MAX_HTML_BYTES,
    MAX_SITEMAP_BYTES,
    MAX_TECH_PAGES,
)


@dataclass
class SitemapParseResult:
    ok: bool
    urls: list[str] = field(default_factory=list)
    error: str = ""
    path: str = ""
    present: bool = False


@dataclass
class FeedParseResult:
    ok: bool
    channel_link: str = ""
    item_links: list[str] = field(default_factory=list)
    error: str = ""
    path: str = ""
    present: bool = False


@dataclass
class SiteArtifactBundle:
    """Bounded local view of Website Engine static output."""

    root: Path
    pages: list[ExtractedPage]
    known_slugs: set[str]
    truncated: bool
    sitemap: SitemapParseResult
    feed: FeedParseResult
    robots_txt_present: bool
    index_html_at_root: bool
    slug_dirs_missing_index: list[str] = field(default_factory=list)


def _strip_ns(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def parse_sitemap(path: Path) -> SitemapParseResult:
    result = SitemapParseResult(ok=False, path=str(path), present=path.is_file())
    if not path.is_file():
        result.error = "sitemap.xml absent"
        return result
    try:
        size = path.stat().st_size
        if size > MAX_SITEMAP_BYTES:
            result.error = f"sitemap exceeds bound ({size} bytes)"
            return result
        text = path.read_text(encoding="utf-8")
        root = ET.fromstring(text)
    except (OSError, ET.ParseError, UnicodeError) as exc:
        result.error = f"sitemap parse failure: {exc}"
        return result
    urls: list[str] = []
    for el in root.iter():
        if _strip_ns(el.tag) == "loc" and el.text:
            urls.append(el.text.strip())
    result.ok = True
    result.urls = urls
    return result


def parse_rss(path: Path) -> FeedParseResult:
    result = FeedParseResult(ok=False, path=str(path), present=path.is_file())
    if not path.is_file():
        result.error = "rss.xml absent"
        return result
    try:
        size = path.stat().st_size
        if size > MAX_FEED_BYTES:
            result.error = f"rss exceeds bound ({size} bytes)"
            return result
        text = path.read_text(encoding="utf-8")
        root = ET.fromstring(text)
    except (OSError, ET.ParseError, UnicodeError) as exc:
        result.error = f"rss parse failure: {exc}"
        return result
    channel_link = ""
    item_links: list[str] = []
    for el in root.iter():
        name = _strip_ns(el.tag)
        if name == "channel":
            for child in list(el):
                if _strip_ns(child.tag) == "link" and child.text and not channel_link:
                    # first channel-level link (before items typically)
                    # Prefer direct channel children
                    pass
        if name == "item":
            for child in list(el):
                if _strip_ns(child.tag) == "link" and child.text:
                    item_links.append(child.text.strip())
    # Channel link: first /rss/channel/link not inside item
    for ch in root.iter():
        if _strip_ns(ch.tag) != "channel":
            continue
        for child in list(ch):
            if _strip_ns(child.tag) == "link" and child.text:
                channel_link = child.text.strip()
                break
        break
    result.ok = True
    result.channel_link = channel_link
    result.item_links = item_links
    return result


def load_technical_bundle(
    artifact_root: Path | str | None = None,
    *,
    max_pages: int = MAX_TECH_PAGES,
) -> SiteArtifactBundle:
    root = Path(artifact_root) if artifact_root is not None else default_artifact_root()
    pages, known, truncated = load_site_inventory(root, max_pages=max_pages)
    # Bound HTML size already read; skip oversized in future — pages already loaded
    filtered: list[ExtractedPage] = []
    for p in pages:
        if len(p.html.encode("utf-8")) <= MAX_HTML_BYTES:
            filtered.append(p)
    slug_dirs_missing: list[str] = []
    if root.is_dir():
        for child in sorted(root.iterdir()):
            if child.is_dir() and not (child / "index.html").is_file():
                # ignore feed/meta dirs that aren't page dirs with metadata
                if (child / "metadata.json").is_file() or any(child.iterdir()):
                    # only flag dirs that look like slug dirs without index
                    if child.name not in {".", ".."} and not child.name.startswith("."):
                        if list(child.glob("*")) and not (child / "index.html").exists():
                            # skip empty-ish; if has files but no index
                            if any(x.is_file() for x in child.iterdir()):
                                slug_dirs_missing.append(child.name)
    return SiteArtifactBundle(
        root=root,
        pages=filtered,
        known_slugs=known,
        truncated=truncated,
        sitemap=parse_sitemap(root / "sitemap.xml"),
        feed=parse_rss(root / "rss.xml"),
        robots_txt_present=(root / "robots.txt").is_file(),
        index_html_at_root=(root / "index.html").is_file(),
        slug_dirs_missing_index=slug_dirs_missing,
    )


def slug_from_url(url: str) -> str:
    path = urlparse((url or "").strip()).path.rstrip("/")
    if not path:
        return ""
    return path.split("/")[-1]


# Re-export for technical package convenience
__all__ = [
    "FeedParseResult",
    "SiteArtifactBundle",
    "SitemapParseResult",
    "default_artifact_root",
    "list_page_slugs",
    "load_page_artifact",
    "load_technical_bundle",
    "parse_rss",
    "parse_sitemap",
    "slug_from_url",
]
