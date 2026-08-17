"""Deterministic SEO readiness/read model (S0)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from src.tools.site_origin import (
    get_configured_site_origin,
    get_site_base,
    host_from_url,
    is_deprecated_production_host,
    is_infrastructure_host,
)

_CANONICAL_RE = re.compile(
    r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
    re.I,
)
_META_DESC_RE = re.compile(
    r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']',
    re.I,
)
_OG_URL_RE = re.compile(
    r'<meta[^>]+property=["\']og:url["\'][^>]+content=["\']([^"\']+)["\']',
    re.I,
)
_H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.I | re.S)
_H2_RE = re.compile(r"<h2[^>]*>", re.I)
_LINK_RE = re.compile(r'<a[^>]+href=["\']([^"\']+)["\']', re.I)


class FindingLevel(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass(frozen=True)
class ReadinessFinding:
    level: FindingLevel
    code: str
    message: str
    field: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "level": self.level.value,
            "code": self.code,
            "message": self.message,
            "field": self.field,
        }


@dataclass
class ReadinessReport:
    slug: str = ""
    canonical_url: str = ""
    configured_origin: str = ""
    findings: list[ReadinessFinding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(f.level == FindingLevel.ERROR for f in self.findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "canonical_url": self.canonical_url,
            "configured_origin": self.configured_origin,
            "ok": self.ok,
            "findings": [f.to_dict() for f in self.findings],
        }


class _TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if getattr(self, "_in_title", False):
            self.title += data


def _extract_title(html: str) -> str:
    parser = _TitleParser()
    parser._in_title = False
    try:
        parser.feed(html)
    except Exception:
        return ""
    if parser.title.strip():
        return parser.title.strip()
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    return (m.group(1).strip() if m else "")


def _origin_alignment_findings(url: str, *, configured_origin: str) -> list[ReadinessFinding]:
    if not url:
        return [
            ReadinessFinding(
                FindingLevel.ERROR,
                "canonical_missing",
                "Canonical URL is missing",
                "canonical_url",
            )
        ]
    host = host_from_url(url)
    cfg_host = host_from_url(configured_origin)
    findings: list[ReadinessFinding] = []
    if is_deprecated_production_host(host):
        findings.append(
            ReadinessFinding(
                FindingLevel.WARNING,
                "deprecated_host",
                f"URL uses deprecated production host {host!r}",
                "canonical_url",
            )
        )
    if is_infrastructure_host(host):
        findings.append(
            ReadinessFinding(
                FindingLevel.INFO,
                "infrastructure_host",
                f"URL uses infrastructure host {host!r}",
                "canonical_url",
            )
        )
    if cfg_host and host and host != cfg_host and not is_deprecated_production_host(host):
        # FM may intentionally differ until ratification — warn, not error in S0
        if host != cfg_host:
            findings.append(
                ReadinessFinding(
                    FindingLevel.WARNING,
                    "origin_mismatch",
                    f"URL host {host!r} differs from configured origin host {cfg_host!r}",
                    "canonical_url",
                )
            )
    return findings


def evaluate_html_readiness(
    html: str,
    *,
    slug: str = "",
    configured_origin: str | None = None,
) -> ReadinessReport:
    origin = configured_origin or get_configured_site_origin()
    report = ReadinessReport(slug=slug, configured_origin=origin)

    title = _extract_title(html)
    if not title:
        report.findings.append(
            ReadinessFinding(FindingLevel.ERROR, "title_missing", "Missing <title>", "title")
        )
    elif len(title) < 10:
        report.findings.append(
            ReadinessFinding(FindingLevel.WARNING, "title_short", "Title is very short", "title")
        )

    desc_m = _META_DESC_RE.search(html)
    if not desc_m or not desc_m.group(1).strip():
        report.findings.append(
            ReadinessFinding(
                FindingLevel.ERROR,
                "description_missing",
                "Missing meta description",
                "description",
            )
        )
    elif len(desc_m.group(1).strip()) > 160:
        report.findings.append(
            ReadinessFinding(
                FindingLevel.WARNING,
                "description_long",
                "Meta description exceeds ~160 characters",
                "description",
            )
        )

    canon_m = _CANONICAL_RE.search(html)
    canonical = canon_m.group(1).strip() if canon_m else ""
    report.canonical_url = canonical
    report.findings.extend(_origin_alignment_findings(canonical, configured_origin=origin))

    og_m = _OG_URL_RE.search(html)
    if og_m and canonical and og_m.group(1).strip() != canonical:
        report.findings.append(
            ReadinessFinding(
                FindingLevel.WARNING,
                "og_url_mismatch",
                "og:url differs from canonical link",
                "og:url",
            )
        )

    if '"@type": "Article"' not in html and '"@type":"Article"' not in html:
        report.findings.append(
            ReadinessFinding(
                FindingLevel.WARNING,
                "schema_article_missing",
                "Schema.org Article JSON-LD not detected",
                "schema_org",
            )
        )

    h1_count = len(_H1_RE.findall(html))
    if h1_count == 0:
        report.findings.append(
            ReadinessFinding(FindingLevel.ERROR, "h1_missing", "No H1 heading", "headings")
        )
    elif h1_count > 1:
        report.findings.append(
            ReadinessFinding(
                FindingLevel.WARNING,
                "h1_multiple",
                f"Multiple H1 headings ({h1_count})",
                "headings",
            )
        )

    h2_count = len(_H2_RE.findall(html))
    if h2_count == 0:
        report.findings.append(
            ReadinessFinding(
                FindingLevel.INFO,
                "h2_absent",
                "No H2 headings (optional structure signal)",
                "headings",
            )
        )

    internal = 0
    for href in _LINK_RE.findall(html):
        if href.startswith("#") or href.startswith("mailto:"):
            continue
        parsed = urlparse(href)
        if not parsed.netloc or parsed.netloc == host_from_url(get_site_base()):
            internal += 1
    if internal == 0:
        report.findings.append(
            ReadinessFinding(
                FindingLevel.INFO,
                "no_internal_links",
                "No internal links detected",
                "internal_links",
            )
        )

    return report


def evaluate_artifact_readiness(
    artifact_root: Path,
    *,
    slug: str,
    configured_origin: str | None = None,
) -> ReadinessReport:
    html_path = artifact_root / slug / "index.html"
    if not html_path.is_file():
        return ReadinessReport(
            slug=slug,
            configured_origin=configured_origin or get_configured_site_origin(),
            findings=[
                ReadinessFinding(
                    FindingLevel.ERROR,
                    "html_missing",
                    f"Missing {slug}/index.html",
                    "artifact",
                )
            ],
        )
    html = html_path.read_text(encoding="utf-8")
    report = evaluate_html_readiness(html, slug=slug, configured_origin=configured_origin)

    meta_path = artifact_root / slug / "metadata.json"
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("slug") and meta.get("slug") != slug:
            report.findings.append(
                ReadinessFinding(
                    FindingLevel.WARNING,
                    "slug_dir_mismatch",
                    "metadata slug differs from directory name",
                    "slug",
                )
            )

    sitemap = artifact_root / "sitemap.xml"
    rss = artifact_root / "rss.xml"
    if sitemap.is_file() and slug not in sitemap.read_text(encoding="utf-8"):
        report.findings.append(
            ReadinessFinding(
                FindingLevel.WARNING,
                "sitemap_missing_slug",
                "Slug not referenced in sitemap.xml",
                "sitemap",
            )
        )
    if rss.is_file() and slug not in rss.read_text(encoding="utf-8"):
        report.findings.append(
            ReadinessFinding(
                FindingLevel.WARNING,
                "rss_missing_slug",
                "Slug not referenced in rss.xml",
                "rss",
            )
        )

    return report
