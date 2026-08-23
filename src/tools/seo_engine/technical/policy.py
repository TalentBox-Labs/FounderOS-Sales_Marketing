"""Technical SEO Phase-1 policy (independent of frozen S1 readiness policy)."""

from __future__ import annotations

TECH_SCORE_BASE = 100
TECH_CRITICAL_PENALTY = 35
TECH_ERROR_PENALTY = 20
TECH_WARNING_PENALTY = 6
TECH_SCORE_MIN = 0

MAX_TECH_PAGES = 200
MAX_SITEMAP_BYTES = 2_000_000
MAX_FEED_BYTES = 2_000_000
MAX_HTML_BYTES = 2_000_000
