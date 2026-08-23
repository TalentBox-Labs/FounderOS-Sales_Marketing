"""HTML / metadata field extraction for SEO inspection (read-only)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

_CANONICAL_RE = re.compile(
    r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
    re.I,
)
_META_NAME_RE = re.compile(
    r'<meta[^>]+name=["\']([^"\']+)["\'][^>]+content=["\']([^"\']*)["\']',
    re.I,
)
_META_NAME_RE_ALT = re.compile(
    r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']([^"\']+)["\']',
    re.I,
)
_OG_RE = re.compile(
    r'<meta[^>]+property=["\'](og:[^"\']+)["\'][^>]+content=["\']([^"\']*)["\']',
    re.I,
)
_OG_RE_ALT = re.compile(
    r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+property=["\'](og:[^"\']+)["\']',
    re.I,
)
_JSONLD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.I | re.S,
)
_H_RE = re.compile(r"<h([1-6])[^>]*>", re.I)
_LINK_RE = re.compile(r'<a[^>]+href=["\']([^"\']+)["\']', re.I)
_TITLE_TAG_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)


class _TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data


@dataclass
class ExtractedPage:
    """Parsed SEO-relevant fields from a rendered HTML document."""

    html: str = ""
    title: str = ""
    description: str = ""
    canonical_url: str = ""
    robots: str = ""
    slug: str = ""
    og: dict[str, str] = field(default_factory=dict)
    json_ld: list[Any] = field(default_factory=list)
    json_ld_parse_errors: int = 0
    headings: list[int] = field(default_factory=list)  # levels in order
    h1_count: int = 0
    hrefs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    in_sitemap: bool | None = None
    in_rss: bool | None = None


def extract_title(html: str) -> str:
    parser = _TitleParser()
    try:
        parser.feed(html)
    except Exception:
        pass
    if parser.title.strip():
        return parser.title.strip()
    m = _TITLE_TAG_RE.search(html)
    return (m.group(1).strip() if m else "")


def extract_meta_name(html: str, name: str) -> str:
    name_l = name.lower()
    for m in _META_NAME_RE.finditer(html):
        if m.group(1).lower() == name_l:
            return m.group(2).strip()
    for m in _META_NAME_RE_ALT.finditer(html):
        if m.group(2).lower() == name_l:
            return m.group(1).strip()
    return ""


def extract_og(html: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in _OG_RE.finditer(html):
        out[m.group(1).lower()] = m.group(2).strip()
    for m in _OG_RE_ALT.finditer(html):
        out[m.group(2).lower()] = m.group(1).strip()
    return out


def extract_json_ld(html: str) -> tuple[list[Any], int]:
    docs: list[Any] = []
    errors = 0
    for m in _JSONLD_RE.finditer(html):
        raw = m.group(1).strip()
        if not raw:
            errors += 1
            continue
        try:
            docs.append(json.loads(raw))
        except json.JSONDecodeError:
            errors += 1
    return docs, errors


def extract_page(
    html: str, *, slug: str = "", metadata: dict[str, Any] | None = None
) -> ExtractedPage:
    title = extract_title(html)
    description = extract_meta_name(html, "description")
    robots = extract_meta_name(html, "robots")
    canon_m = _CANONICAL_RE.search(html)
    canonical = canon_m.group(1).strip() if canon_m else ""
    og = extract_og(html)
    json_ld, jl_err = extract_json_ld(html)
    heading_levels = [int(m.group(1)) for m in _H_RE.finditer(html)]
    h1_count = sum(1 for h in heading_levels if h == 1)
    hrefs = _LINK_RE.findall(html)
    return ExtractedPage(
        html=html,
        title=title,
        description=description,
        canonical_url=canonical,
        robots=robots,
        slug=slug,
        og=og,
        json_ld=json_ld,
        json_ld_parse_errors=jl_err,
        headings=heading_levels,
        h1_count=h1_count,
        hrefs=hrefs,
        metadata=dict(metadata or {}),
    )


def path_from_url(url: str) -> str:
    return urlparse((url or "").strip()).path.rstrip("/")
