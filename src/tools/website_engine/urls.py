"""Slug and canonical URL logic for Website Engine (site ownership only)."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from src.tools.site_origin import get_site_base

# Import-time snapshot for backward-compatible imports; prefer get_site_base() at runtime.
DEFAULT_SITE_BASE = get_site_base()

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    """Convert title/keyword text to a URL slug."""
    return _NON_ALNUM.sub("-", (text or "").lower().strip()).strip("-")


def slug_from_canonical_url(canonical_url: str) -> str:
    """Extract trailing path segment as slug from a canonical URL."""
    path = urlparse((canonical_url or "").strip()).path.rstrip("/")
    if not path:
        return ""
    return path.split("/")[-1]


def build_slug(
    *,
    title: str = "",
    primary_keyword: str = "",
    front_matter: dict[str, str] | None = None,
) -> str:
    """Resolve slug: front-matter slug → canonical_url path → keyword → title."""
    fm = front_matter or {}
    explicit = (fm.get("slug") or "").strip()
    if explicit:
        return slugify(explicit)

    canonical = (fm.get("canonical_url") or "").strip()
    from_url = slug_from_canonical_url(canonical)
    if from_url:
        return slugify(from_url)

    if primary_keyword:
        return slugify(primary_keyword)
    if title:
        return slugify(title)
    raise ValueError("Cannot build slug without title, keyword, or canonical_url")


def build_canonical_url(
    slug: str,
    *,
    front_matter: dict[str, str] | None = None,
    site_base: str | None = None,
) -> str:
    """Prefer front-matter canonical_url; otherwise ``{site_base}/{slug}``."""
    fm = front_matter or {}
    existing = (fm.get("canonical_url") or "").strip()
    if existing:
        return existing.rstrip("/")
    base = (site_base or get_site_base()).rstrip("/")
    clean_slug = slugify(slug)
    if not clean_slug:
        raise ValueError("slug is required to build canonical URL")
    return f"{base}/{clean_slug}"
