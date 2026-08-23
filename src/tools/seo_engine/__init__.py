"""SEO Engine — readiness and validation (Marketing OS).

S0: foundational read model (FindingLevel / evaluate_*).
S1: Phase-1 readiness engine (analyze_*, rules, scoring, artifacts).
S2: Technical SEO Phase 1 (seo_engine.technical) — additive; S1.5 contract unchanged.

Does NOT render, publish, deploy, mutate content, or submit to search engines.
"""

from src.tools.seo_engine.artifacts import (
    default_artifact_root,
    list_page_slugs,
    load_page_artifact,
    load_site_inventory,
)
from src.tools.seo_engine.audit import write_page_audit, write_site_audit
from src.tools.seo_engine.engine import (
    analyze_html,
    analyze_page_artifact,
    analyze_site,
    compute_score,
    derive_overall_status,
)
from src.tools.seo_engine.models import (
    CheckResult,
    CheckStatus,
    OverallStatus,
    PageReadinessResult,
    ScoreBreakdown,
    SiteReadinessResult,
)
from src.tools.seo_engine.readiness import (
    FindingLevel,
    ReadinessFinding,
    ReadinessReport,
    evaluate_artifact_readiness,
    evaluate_html_readiness,
)
from src.tools.seo_engine.technical import (
    TechCategory,
    TechFinding,
    TechSeverity,
    TechnicalPageReport,
    TechnicalSiteReport,
    analyze_technical_page,
    analyze_technical_site,
    write_technical_audit,
)

__all__ = [
    "CheckResult",
    "CheckStatus",
    "FindingLevel",
    "OverallStatus",
    "PageReadinessResult",
    "ReadinessFinding",
    "ReadinessReport",
    "ScoreBreakdown",
    "SiteReadinessResult",
    "TechCategory",
    "TechFinding",
    "TechSeverity",
    "TechnicalPageReport",
    "TechnicalSiteReport",
    "analyze_html",
    "analyze_page_artifact",
    "analyze_site",
    "analyze_technical_page",
    "analyze_technical_site",
    "compute_score",
    "default_artifact_root",
    "derive_overall_status",
    "evaluate_artifact_readiness",
    "evaluate_html_readiness",
    "list_page_slugs",
    "load_page_artifact",
    "load_site_inventory",
    "write_page_audit",
    "write_site_audit",
    "write_technical_audit",
]
