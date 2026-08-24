"""Real, compliant public data sources for the Market Research / Community
Engagement / Brand Monitoring agents.

Reddit and Hacker News both expose free, public, unauthenticated read APIs
that are fine to call for reasonable-volume search — no scraping, no ToS
violation. X/Twitter, LinkedIn conversations, Discord, Slack, GitHub issues,
and Product Hunt have no such compliant free API, so this module doesn't
pretend to cover them: callers should treat those channels as
"not available — no provider configured" rather than get silent gaps.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_UA = "Mozilla/5.0 (compatible; WorkCrewCRM-MarketResearch/1.0)"
_TIMEOUT = 10

UNAVAILABLE_CHANNELS = [
    "X (Twitter)", "LinkedIn conversations", "Discord", "Slack communities",
    "GitHub issues", "Product Hunt", "newsletters (no configured RSS list)",
]


def search_reddit(query: str, subreddit: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
    """Public Reddit search — no auth required. Never raises; returns []
    on any network/rate-limit failure so callers can degrade gracefully."""
    import requests

    url = f"https://www.reddit.com/r/{subreddit}/search.json" if subreddit else "https://www.reddit.com/search.json"
    params = {"q": query, "limit": min(limit, 25), "sort": "relevance"}
    if subreddit:
        params["restrict_sr"] = "1"
    try:
        resp = requests.get(url, params=params, headers={"User-Agent": _UA}, timeout=_TIMEOUT)
        resp.raise_for_status()
        children = resp.json().get("data", {}).get("children", [])
        return [
            {
                "title": c["data"].get("title", ""),
                "body": (c["data"].get("selftext") or "")[:500],
                "subreddit": c["data"].get("subreddit"),
                "score": c["data"].get("score", 0),
                "num_comments": c["data"].get("num_comments", 0),
                "url": f"https://reddit.com{c['data'].get('permalink', '')}",
                "created_utc": c["data"].get("created_utc"),
            }
            for c in children
        ]
    except Exception as e:
        logger.warning(f"Reddit search failed ({query!r}): {e}")
        return []


def search_hackernews(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Hacker News's official public Algolia search API — no auth required."""
    import requests

    try:
        resp = requests.get(
            "https://hn.algolia.com/api/v1/search",
            params={"query": query, "tags": "story", "hitsPerPage": min(limit, 25)},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return [
            {
                "title": h.get("title", ""),
                "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                "points": h.get("points", 0),
                "num_comments": h.get("num_comments", 0),
                "created_at": h.get("created_at"),
            }
            for h in resp.json().get("hits", [])
        ]
    except Exception as e:
        logger.warning(f"Hacker News search failed ({query!r}): {e}")
        return []
