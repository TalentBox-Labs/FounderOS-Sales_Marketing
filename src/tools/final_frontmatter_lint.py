"""
Deterministic YAML front-matter schema for `05_Final.md` (canonical or staged).

Used by metadata_checker. No LLMs; same rules for staging overlays via final_path.
"""

from __future__ import annotations

import re
from typing import Final

# Required keys for publish-track finals (schema-style contract).
REQUIRED_KEYS: Final[tuple[str, ...]] = (
    "week_id",
    "article_title",
    "primary_keyword",
    "search_intent",
    "funnel_stage",
    "status",
    "publish_status",
    "canonical_url",
    "cta_type",
)

# Normalised lowercase tokens (values compared after strip + lowercase).
ALLOWED_PUBLISH_STATUS: Final[frozenset[str]] = frozenset(
    {
        "draft",
        "in progress",
        "in review",
        "ready",
        "published",
        "scheduled",
        "archived",
        "pending",
        "not started",
        "approved",
    }
)

BRACKET_TOKEN = re.compile(r"\[[^\]\n]+\]")
HTTP_URL = re.compile(r"^https?://\S+", re.IGNORECASE)

_REQ_SET = frozenset(REQUIRED_KEYS)


def _strip_scalar(raw: str) -> str:
    s = raw.strip()
    if len(s) >= 2 and ((s[0] == s[-1] == '"') or (s[0] == s[-1] == "'")):
        return s[1:-1].strip()
    return s


def lint_final_front_matter(fm: dict[str, str]) -> tuple[list[str], list[str]]:
    """
    Returns (passed_checks, failed_checks) as markdown bullet lines.

    Fails on: missing required keys; bracket placeholders in required fields;
    invalid publish_status; non-http(s) canonical_url; empty cta_type;
    bracket placeholders in any optional front matter key.
    """
    passed: list[str] = []
    failed: list[str] = []

    if not fm:
        failed.append("- [schema] Front matter missing or empty dict")
        return passed, failed

    for key in REQUIRED_KEYS:
        raw = fm.get(key, "")
        val = _strip_scalar(str(raw)) if raw is not None else ""
        if not val:
            failed.append(f"- [schema] Missing or empty required key: `{key}`")
            continue

        if BRACKET_TOKEN.search(val):
            failed.append(f"- [schema] Bracket placeholder in `{key}`: {val!r}")
            continue

        if key == "publish_status":
            token = val.lower().strip()
            if token not in ALLOWED_PUBLISH_STATUS:
                failed.append(
                    f"- [schema] Invalid `publish_status`: {val!r} "
                    f"(allowed: {sorted(ALLOWED_PUBLISH_STATUS)})"
                )
            else:
                passed.append(f"- [schema] `publish_status` allowed ({val!r})")

        elif key == "canonical_url":
            if not HTTP_URL.match(val):
                failed.append(
                    f"- [schema] `canonical_url` must be an http(s) URL, got: {val!r}"
                )
            else:
                passed.append("- [schema] `canonical_url` is URL-shaped")

        elif key == "cta_type":
            passed.append(f"- [schema] `cta_type` present ({val!r})")

        else:
            passed.append(f"- [schema] `{key}` present")

    for k, raw in fm.items():
        if k in _REQ_SET:
            continue
        val = str(raw) if raw is not None else ""
        if BRACKET_TOKEN.search(val):
            failed.append(f"- [schema] Bracket placeholder in optional key `{k}`: {val!r}")

    return passed, failed
