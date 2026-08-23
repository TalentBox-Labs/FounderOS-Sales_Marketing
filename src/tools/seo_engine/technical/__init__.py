"""Technical SEO Engine Phase 1 (S2) — additive under SEO Engine.

Consumes Website Engine artifacts. Does not mutate S1.5 readiness contract.
Does not render, publish, index, or submit to search engines.
"""

from __future__ import annotations

from src.tools.seo_engine.technical.audit import write_technical_audit
from src.tools.seo_engine.technical.engine import (
    analyze_technical_page,
    analyze_technical_site,
)
from src.tools.seo_engine.technical.models import (
    TechCategory,
    TechFinding,
    TechSeverity,
    TechnicalPageReport,
    TechnicalSiteReport,
)

__all__ = [
    "TechCategory",
    "TechFinding",
    "TechSeverity",
    "TechnicalPageReport",
    "TechnicalSiteReport",
    "analyze_technical_page",
    "analyze_technical_site",
    "write_technical_audit",
]
