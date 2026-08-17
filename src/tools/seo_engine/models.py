"""SEO readiness result models (S1 Phase 1).

Compatible with S0 FindingLevel (ERROR/WARNING/INFO) while normalizing
operator-facing statuses: PASS, WARNING, ERROR, DOMAIN_BLOCKED, NOT_APPLICABLE.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.tools.seo_engine.readiness import FindingLevel, ReadinessFinding


class CheckStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DOMAIN_BLOCKED = "DOMAIN_BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INFO = "INFO"


class OverallStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DOMAIN_BLOCKED = "DOMAIN_BLOCKED"


@dataclass(frozen=True)
class CheckResult:
    """Single deterministic check outcome."""

    id: str
    status: CheckStatus
    message: str
    field_name: str = ""
    recommendation: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status.value,
            "message": self.message,
            "field": self.field_name,
            "recommendation": self.recommendation,
            "evidence": dict(self.evidence),
        }


@dataclass
class ScoreBreakdown:
    base: int
    error_penalty: int
    warning_penalty: int
    error_count: int
    warning_count: int
    domain_block_count: int
    final: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "base": self.base,
            "error_penalty_per": self.error_penalty,
            "warning_penalty_per": self.warning_penalty,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "domain_block_count": self.domain_block_count,
            "final": self.final,
            "note": (
                "DOMAIN_BLOCKED does not reduce score; it gates overall status "
                "independently so a high score cannot override domain blockers."
            ),
        }


@dataclass
class PageReadinessResult:
    """Phase-1 page readiness report."""

    slug: str
    canonical_url: str
    configured_origin: str
    status: OverallStatus
    score: int
    score_breakdown: ScoreBreakdown
    checks: list[CheckResult] = field(default_factory=list)
    title: str = ""
    description: str = ""
    indexing_activation_allowed: bool = False

    @property
    def errors(self) -> list[CheckResult]:
        return [c for c in self.checks if c.status == CheckStatus.ERROR]

    @property
    def warnings(self) -> list[CheckResult]:
        return [c for c in self.checks if c.status == CheckStatus.WARNING]

    @property
    def domain_blockers(self) -> list[CheckResult]:
        return [c for c in self.checks if c.status == CheckStatus.DOMAIN_BLOCKED]

    @property
    def info(self) -> list[CheckResult]:
        return [c for c in self.checks if c.status == CheckStatus.INFO]

    @property
    def ok(self) -> bool:
        """True when no ERROR and no DOMAIN_BLOCKED (S0-compatible readiness)."""
        return self.status in {OverallStatus.PASS, OverallStatus.WARNING}

    @property
    def seo_ready(self) -> bool:
        """Strict: PASS only (no warnings, no domain blockers)."""
        return self.status == OverallStatus.PASS

    def to_s0_findings(self) -> list[ReadinessFinding]:
        """Map Phase-1 checks back to S0 FindingLevel for compatibility."""
        out: list[ReadinessFinding] = []
        for c in self.checks:
            level: FindingLevel | None
            match c.status:
                case CheckStatus.PASS | CheckStatus.NOT_APPLICABLE:
                    level = None
                case CheckStatus.ERROR:
                    level = FindingLevel.ERROR
                case CheckStatus.DOMAIN_BLOCKED:
                    # S0 used WARNING for deprecated hosts; Phase-1 keeps DOMAIN_BLOCKED.
                    level = FindingLevel.WARNING
                case CheckStatus.WARNING:
                    level = FindingLevel.WARNING
                case CheckStatus.INFO:
                    level = FindingLevel.INFO
                case _ as unreachable:
                    raise AssertionError(f"unhandled status: {unreachable}")
            if level is None:
                continue
            out.append(
                ReadinessFinding(
                    level=level,
                    code=c.id,
                    message=c.message,
                    field=c.field_name,
                )
            )
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "canonical_url": self.canonical_url,
            "configured_origin": self.configured_origin,
            "status": self.status.value,
            "score": self.score,
            "score_breakdown": self.score_breakdown.to_dict(),
            "ok": self.ok,
            "seo_ready": self.seo_ready,
            "indexing_activation_allowed": self.indexing_activation_allowed,
            "title": self.title,
            "description": self.description,
            "errors": [c.to_dict() for c in self.errors],
            "warnings": [c.to_dict() for c in self.warnings],
            "domain_blockers": [c.to_dict() for c in self.domain_blockers],
            "info": [c.to_dict() for c in self.info],
            "checks": {c.id: c.to_dict() for c in self.checks},
            "read_only": True,
            "mutates_content": False,
            "submits_to_search_engines": False,
        }


@dataclass
class SiteReadinessResult:
    """Batch analysis over a bounded artifact root."""

    artifact_root: str
    configured_origin: str
    pages: list[PageReadinessResult] = field(default_factory=list)
    truncated: bool = False
    max_pages: int = 0

    def to_dict(self) -> dict[str, Any]:
        statuses = {p.status.value for p in self.pages}
        if OverallStatus.DOMAIN_BLOCKED.value in statuses:
            overall = OverallStatus.DOMAIN_BLOCKED.value
        elif OverallStatus.ERROR.value in statuses:
            overall = OverallStatus.ERROR.value
        elif OverallStatus.WARNING.value in statuses:
            overall = OverallStatus.WARNING.value
        elif self.pages:
            overall = OverallStatus.PASS.value
        else:
            overall = OverallStatus.WARNING.value
        return {
            "artifact_root": self.artifact_root,
            "configured_origin": self.configured_origin,
            "status": overall,
            "page_count": len(self.pages),
            "truncated": self.truncated,
            "max_pages": self.max_pages,
            "pages": [p.to_dict() for p in self.pages],
            "read_only": True,
            "mutates_content": False,
            "submits_to_search_engines": False,
        }
