"""Authoritative human-mutation authority gate for protected Revenue OS writes.

UI1.1: service-layer enforcement so agents/automation cannot bypass router gates
by calling domain mutation functions directly or spoofing ``requested_by``.
"""

from __future__ import annotations

from src.tools.editorial_approval import is_human_approver


class HumanAuthorityError(ValueError):
    """Raised when a protected mutation lacks a valid human requester."""


def require_human_mutation_authority(
    requested_by: str, *, action: str = "protected mutation"
) -> str:
    """Validate human authority for a canonical mutation. Returns normalized name."""
    name = (requested_by or "").strip()
    if not is_human_approver(name):
        raise HumanAuthorityError(
            f"Human requester required for {action}. "
            "AI/automation identities cannot perform this mutation."
        )
    return name
