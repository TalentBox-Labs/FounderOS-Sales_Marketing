"""Deterministic markdown contract checks for CrewAI QA output (see src/tasks.yaml)."""

from __future__ import annotations

import re
from typing import Final

_REQUIRED_HEADINGS: Final[tuple[str, ...]] = (
    "## Passed Checks",
    "## Failed Checks",
    "## Observable Issues",
    "## Final Verdict",
)


def qa_report_contract_errors(markdown: str) -> list[str]:
    """
    Return human-readable contract violations (empty list if satisfied).

    Headings are matched case-insensitively on the line prefix.
    Final Verdict must contain a standalone line that is exactly PASS or FAIL.
    """
    if not markdown or not markdown.strip():
        return ["Report is empty"]

    errors: list[str] = []
    lower = markdown.lower()

    for heading in _REQUIRED_HEADINGS:
        key = heading.lower().strip()
        if key not in lower:
            errors.append(f"Missing required section heading: {heading}")

    verdict_key = "## final verdict"
    if verdict_key in lower:
        idx = lower.index(verdict_key)
        tail = markdown[idx:]
        # Allow plain PASS/FAIL or a single markdown list marker (models often emit "- FAIL").
        verdict_line = re.compile(
            r"(?m)^\s*(?:[-*]\s+|\d+\.\s+)?(PASS|FAIL)\s*$"
        )
        if not verdict_line.search(tail):
            errors.append(
                "Final Verdict section must include a line with only PASS or FAIL "
                "(optional leading list marker: -, *, or 1.)"
            )

    return errors


def qa_report_meets_contract(markdown: str) -> bool:
    return len(qa_report_contract_errors(markdown)) == 0
