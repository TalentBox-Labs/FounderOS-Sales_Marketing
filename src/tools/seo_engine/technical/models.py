"""Technical SEO result models (S2). Independent of frozen S1 scoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TechSeverity(str, Enum):
    DOMAIN_BLOCKED = "DOMAIN_BLOCKED"
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    PASS = "PASS"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class TechCategory(str, Enum):
    CANONICAL = "CANONICAL"
    ROBOTS = "ROBOTS"
    SITEMAP = "SITEMAP"
    STRUCTURED_DATA = "STRUCTURED_DATA"
    OPEN_GRAPH = "OPEN_GRAPH"
    INTERNAL_LINKS = "INTERNAL_LINKS"
    CRAWLABILITY = "CRAWLABILITY"
    HTTP_ROUTING = "HTTP_ROUTING"
    FEED = "FEED"
    CONSISTENCY = "CONSISTENCY"


class OverallTechStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    DOMAIN_BLOCKED = "DOMAIN_BLOCKED"


@dataclass(frozen=True)
class TechFinding:
    id: str
    category: TechCategory
    severity: TechSeverity
    message: str
    artifact: str = ""
    expected: str = ""
    actual: str = ""
    recommendation: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    ownership: str = "SEO_ENGINE"  # SEO_ENGINE | WEBSITE_ENGINE | CONTENT | DOMAIN | EXPECTED

    @property
    def blocking(self) -> bool:
        return self.severity in {
            TechSeverity.DOMAIN_BLOCKED,
            TechSeverity.CRITICAL,
            TechSeverity.ERROR,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "artifact": self.artifact,
            "expected": self.expected,
            "actual": self.actual,
            "recommendation": self.recommendation,
            "evidence": dict(self.evidence),
            "ownership": self.ownership,
            "blocking": self.blocking,
        }


@dataclass
class TechScoreBreakdown:
    base: int
    critical_penalty: int
    error_penalty: int
    warning_penalty: int
    critical_count: int
    error_count: int
    warning_count: int
    domain_block_count: int
    final: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "base": self.base,
            "critical_penalty_per": self.critical_penalty,
            "error_penalty_per": self.error_penalty,
            "warning_penalty_per": self.warning_penalty,
            "critical_count": self.critical_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "domain_block_count": self.domain_block_count,
            "final": self.final,
            "note": (
                "Technical score is independent of frozen S1 readiness scoring. "
                "DOMAIN_BLOCKED does not reduce score; it gates overall status."
            ),
        }


@dataclass
class TechnicalPageReport:
    slug: str
    configured_origin: str
    status: OverallTechStatus
    score: int
    score_breakdown: TechScoreBreakdown
    findings: list[TechFinding] = field(default_factory=list)
    canonical_url: str = ""
    crawlable: bool | None = None

    def _by(self, sev: TechSeverity) -> list[TechFinding]:
        return [f for f in self.findings if f.severity == sev]

    @property
    def domain_blockers(self) -> list[TechFinding]:
        return self._by(TechSeverity.DOMAIN_BLOCKED)

    @property
    def critical(self) -> list[TechFinding]:
        return self._by(TechSeverity.CRITICAL)

    @property
    def errors(self) -> list[TechFinding]:
        return self._by(TechSeverity.ERROR)

    @property
    def warnings(self) -> list[TechFinding]:
        return self._by(TechSeverity.WARNING)

    @property
    def info(self) -> list[TechFinding]:
        return self._by(TechSeverity.INFO)

    def to_dict(self) -> dict[str, Any]:
        by_cat: dict[str, list[dict[str, Any]]] = {}
        for f in self.findings:
            by_cat.setdefault(f.category.value, []).append(f.to_dict())
        return {
            "slug": self.slug,
            "configured_origin": self.configured_origin,
            "status": self.status.value,
            "score": self.score,
            "score_breakdown": self.score_breakdown.to_dict(),
            "canonical_url": self.canonical_url,
            "crawlable": self.crawlable,
            "domain_blockers": [f.to_dict() for f in self.domain_blockers],
            "critical": [f.to_dict() for f in self.critical],
            "errors": [f.to_dict() for f in self.errors],
            "warnings": [f.to_dict() for f in self.warnings],
            "info": [f.to_dict() for f in self.info],
            "findings_by_category": by_cat,
            "findings": [f.to_dict() for f in self.findings],
            "read_only": True,
            "mutates_content": False,
            "submits_to_search_engines": False,
            "s1_readiness_contract": "UNCHANGED",
        }


@dataclass
class TechnicalSiteReport:
    artifact_root: str
    configured_origin: str
    status: OverallTechStatus
    score: int
    score_breakdown: TechScoreBreakdown
    pages: list[TechnicalPageReport] = field(default_factory=list)
    site_findings: list[TechFinding] = field(default_factory=list)
    truncated: bool = False
    max_pages: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_root": self.artifact_root,
            "configured_origin": self.configured_origin,
            "status": self.status.value,
            "score": self.score,
            "score_breakdown": self.score_breakdown.to_dict(),
            "page_count": len(self.pages),
            "truncated": self.truncated,
            "max_pages": self.max_pages,
            "site_findings": [f.to_dict() for f in self.site_findings],
            "pages": [p.to_dict() for p in self.pages],
            "read_only": True,
            "mutates_content": False,
            "submits_to_search_engines": False,
            "s1_readiness_contract": "UNCHANGED",
            "production_seo_activation": "BLOCKED",
        }
