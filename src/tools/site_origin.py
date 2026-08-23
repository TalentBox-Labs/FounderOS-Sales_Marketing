"""Configurable public site origin (Marketing OS / Website / SEO boundary).

S0: Origin abstraction without assigning a ratified production domain.
Historical content may still embed deprecated hosts in front matter; runtime
defaults use a neutral placeholder until Founder ratifies FOUNDER_SITE_ORIGIN.

Does NOT activate production SEO or search-engine submission.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

# RFC 2606 / documentation placeholder — not a production domain.
PLACEHOLDER_SITE_ORIGIN = "https://example.invalid"
DEFAULT_SITE_BASE_PATH = "/blog"
DEFAULT_FEED_TITLE = "Founder Website"
DEFAULT_FEED_DESCRIPTION = "Founder OS website feed"

ENV_SITE_ORIGIN = "FOUNDER_SITE_ORIGIN"
ENV_SITE_BASE_PATH = "FOUNDER_SITE_BASE_PATH"
ENV_SITE_ORIGIN_RATIFIED = "FOUNDER_SITE_ORIGIN_RATIFIED"

# Hosts deprecated for future Founder OS production canonical use (governance S0).
DEPRECATED_PRODUCTION_HOSTS = frozenset(
    {
        "workcrew.ai",
        "www.workcrew.ai",
        "blog.workcrew.ai",
    }
)

# Infrastructure hosts — not branded canonical origins.
INFRASTRUCTURE_HOSTS = frozenset(
    {
        "founderos-staging.pages.dev",
    }
)


def get_configured_site_origin() -> str:
    """Return configured origin (scheme + host, no trailing slash)."""
    raw = (os.environ.get(ENV_SITE_ORIGIN) or "").strip()
    if raw:
        parsed = urlparse(raw if "://" in raw else f"https://{raw}")
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    return PLACEHOLDER_SITE_ORIGIN


def get_site_base_path() -> str:
    path = (os.environ.get(ENV_SITE_BASE_PATH) or DEFAULT_SITE_BASE_PATH).strip()
    if not path.startswith("/"):
        path = f"/{path}"
    return path.rstrip("/") or DEFAULT_SITE_BASE_PATH


def get_site_base() -> str:
    """Canonical blog/base URL for path-relative page URLs."""
    return f"{get_configured_site_origin()}{get_site_base_path()}"


def is_site_origin_ratified() -> bool:
    """True only when Founder explicitly marks origin as ratified for production SEO."""
    return os.environ.get(ENV_SITE_ORIGIN_RATIFIED, "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def host_from_url(url: str) -> str:
    return (urlparse((url or "").strip()).netloc or "").lower()


def is_deprecated_production_host(host: str) -> bool:
    h = host.lower().removeprefix("www.")
    return h in DEPRECATED_PRODUCTION_HOSTS or any(
        h.endswith(f".{d}") for d in DEPRECATED_PRODUCTION_HOSTS if "." in d
    )


def is_infrastructure_host(host: str) -> bool:
    h = host.lower()
    if h in INFRASTRUCTURE_HOSTS:
        return True
    return h.endswith(".pages.dev")


def is_indexing_activation_allowed() -> bool:
    """Production SEO / search submission requires ratified origin."""
    if not is_site_origin_ratified():
        return False
    origin = get_configured_site_origin()
    if origin == PLACEHOLDER_SITE_ORIGIN:
        return False
    host = host_from_url(origin)
    if is_infrastructure_host(host) or is_deprecated_production_host(host):
        return False
    return True
