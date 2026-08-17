"""Central SEO Phase-1 policy thresholds (no magic numbers in rules)."""

from __future__ import annotations

# Title
TITLE_MIN_LEN = 10
TITLE_MAX_LEN = 70
TITLE_WARN_SHORT = 20  # soft floor for warnings beyond hard ERROR min

# Meta description
DESC_MIN_LEN = 50
DESC_MAX_LEN = 160
DESC_HARD_EMPTY = 1  # non-empty after strip

# Slug
SLUG_MAX_LEN = 200
# URL-safe: lowercase alnum, hyphen; no leading/trailing hyphen
SLUG_PATTERN = r"^[a-z0-9]([a-z0-9-]{0,198}[a-z0-9])?$"

# Scoring (transparent, inspectable)
SCORE_BASE = 100
SCORE_ERROR_PENALTY = 25
SCORE_WARNING_PENALTY = 8
SCORE_DOMAIN_BLOCK_PENALTY = 0  # domain blockers do not reduce score; they gate status
SCORE_INFO_PENALTY = 0
SCORE_MIN = 0

# Heading hierarchy: jump of more than this levels is a warning
HEADING_MAX_SKIP = 1

# Batch scan bound
MAX_PAGES_PER_BATCH = 200
