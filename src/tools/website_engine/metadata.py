"""Website metadata model: title, description, OpenGraph, Schema.org.

Website Engine emits site metadata contracts. SEO Engine owns scoring /
keyword optimization (Architecture v2.1) — not implemented here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class WebsiteMetadata:
    title: str
    description: str
    canonical_url: str
    slug: str
    primary_keyword: str = ""
    og: dict[str, str] = field(default_factory=dict)
    schema_org: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "canonical_url": self.canonical_url,
            "slug": self.slug,
            "primary_keyword": self.primary_keyword,
            "og": dict(self.og),
            "schema_org": dict(self.schema_org),
        }

    def schema_org_json(self) -> str:
        return json.dumps(self.schema_org, ensure_ascii=False, indent=2)


def _truncate_description(text: str, max_len: int = 160) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= max_len:
        return cleaned
    cut = cleaned[: max_len - 1].rsplit(" ", 1)[0]
    return (cut or cleaned[: max_len - 1]).rstrip(".,;:") + "…"


def build_metadata(
    *,
    title: str,
    description: str,
    canonical_url: str,
    slug: str,
    primary_keyword: str = "",
    site_name: str = "WorkCrew",
) -> WebsiteMetadata:
    """Build title/description + OpenGraph + Schema.org Article contracts."""
    desc = _truncate_description(description or title)
    og = {
        "og:type": "article",
        "og:title": title,
        "og:description": desc,
        "og:url": canonical_url,
        "og:site_name": site_name,
    }
    schema_org: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": desc,
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": canonical_url,
        },
        "url": canonical_url,
    }
    if primary_keyword:
        schema_org["keywords"] = primary_keyword
    return WebsiteMetadata(
        title=title,
        description=desc,
        canonical_url=canonical_url,
        slug=slug,
        primary_keyword=primary_keyword,
        og=og,
        schema_org=schema_org,
    )
