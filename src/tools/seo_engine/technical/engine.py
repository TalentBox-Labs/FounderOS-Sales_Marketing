"""Technical SEO Engine orchestration (ATLAS — S2).

Independent of frozen S1 readiness scoring/semantics.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from src.tools.seo_engine.technical.models import (
    OverallTechStatus,
    TechCategory,
    TechFinding,
    TechScoreBreakdown,
    TechSeverity,
    TechnicalPageReport,
    TechnicalSiteReport,
)
from src.tools.seo_engine.technical.parsers import load_page_artifact, load_technical_bundle
from src.tools.seo_engine.technical.policy import (
    MAX_TECH_PAGES,
    TECH_CRITICAL_PENALTY,
    TECH_ERROR_PENALTY,
    TECH_SCORE_BASE,
    TECH_SCORE_MIN,
    TECH_WARNING_PENALTY,
)
from src.tools.seo_engine.technical.rules import (
    build_inbound_counts,
    run_page_technical_rules,
    run_site_technical_rules,
)
from src.tools.site_origin import get_configured_site_origin


def compute_tech_score(findings: list[TechFinding]) -> TechScoreBreakdown:
    critical = sum(1 for f in findings if f.severity == TechSeverity.CRITICAL)
    errors = sum(1 for f in findings if f.severity == TechSeverity.ERROR)
    warnings = sum(1 for f in findings if f.severity == TechSeverity.WARNING)
    domain = sum(1 for f in findings if f.severity == TechSeverity.DOMAIN_BLOCKED)
    final = (
        TECH_SCORE_BASE
        - critical * TECH_CRITICAL_PENALTY
        - errors * TECH_ERROR_PENALTY
        - warnings * TECH_WARNING_PENALTY
    )
    if final < TECH_SCORE_MIN:
        final = TECH_SCORE_MIN
    return TechScoreBreakdown(
        base=TECH_SCORE_BASE,
        critical_penalty=TECH_CRITICAL_PENALTY,
        error_penalty=TECH_ERROR_PENALTY,
        warning_penalty=TECH_WARNING_PENALTY,
        critical_count=critical,
        error_count=errors,
        warning_count=warnings,
        domain_block_count=domain,
        final=final,
    )


def derive_tech_status(findings: list[TechFinding]) -> OverallTechStatus:
    if any(f.severity == TechSeverity.DOMAIN_BLOCKED for f in findings):
        return OverallTechStatus.DOMAIN_BLOCKED
    if any(f.severity == TechSeverity.CRITICAL for f in findings):
        return OverallTechStatus.CRITICAL
    if any(f.severity == TechSeverity.ERROR for f in findings):
        return OverallTechStatus.ERROR
    if any(f.severity == TechSeverity.WARNING for f in findings):
        return OverallTechStatus.WARNING
    return OverallTechStatus.PASS


def _crawlable_flag(findings: list[TechFinding]) -> bool | None:
    ids = {f.id for f in findings}
    if "tech_crawl_noindex" in ids:
        return False
    if "tech_crawl_ok" in ids:
        return True
    if "tech_crawl_not_in_sitemap" in ids or "tech_crawl_no_canonical" in ids:
        return False
    return None


def analyze_technical_site(
    artifact_root: Path | str | None = None,
    *,
    configured_origin: str | None = None,
    max_pages: int = MAX_TECH_PAGES,
) -> TechnicalSiteReport:
    origin = configured_origin or get_configured_site_origin()
    bundle = load_technical_bundle(artifact_root, max_pages=max_pages)
    site_findings = run_site_technical_rules(bundle, configured_origin=origin)
    canonical_counts: Counter[str] = Counter(
        p.canonical_url.strip() for p in bundle.pages if p.canonical_url.strip()
    )
    inbound = build_inbound_counts(bundle.pages)
    pages: list[TechnicalPageReport] = []
    for page in bundle.pages:
        findings = run_page_technical_rules(
            page,
            configured_origin=origin,
            bundle=bundle,
            canonical_counts=canonical_counts,
            inbound=inbound,
        )
        breakdown = compute_tech_score(findings)
        pages.append(
            TechnicalPageReport(
                slug=page.slug,
                configured_origin=origin,
                status=derive_tech_status(findings),
                score=breakdown.final,
                score_breakdown=breakdown,
                findings=findings,
                canonical_url=page.canonical_url,
                crawlable=_crawlable_flag(findings),
            )
        )
    all_findings = list(site_findings)
    for p in pages:
        all_findings.extend(p.findings)
    site_breakdown = compute_tech_score(all_findings)
    return TechnicalSiteReport(
        artifact_root=str(bundle.root),
        configured_origin=origin,
        status=derive_tech_status(all_findings),
        score=site_breakdown.final,
        score_breakdown=site_breakdown,
        pages=pages,
        site_findings=site_findings,
        truncated=bundle.truncated,
        max_pages=max_pages,
    )


def analyze_technical_page(
    artifact_root: Path | str,
    slug: str,
    *,
    configured_origin: str | None = None,
) -> TechnicalPageReport:
    origin = configured_origin or get_configured_site_origin()
    root = Path(artifact_root)
    bundle = load_technical_bundle(root)
    page = load_page_artifact(root, slug)
    if page is None:
        findings = [
            TechFinding(
                id="tech_html_missing",
                category=TechCategory.HTTP_ROUTING,
                severity=TechSeverity.ERROR,
                message=f"Missing {slug}/index.html",
                artifact=f"{slug}/index.html",
                expected="index.html present",
                actual="absent",
                ownership="WEBSITE_ENGINE",
            )
        ]
        breakdown = compute_tech_score(findings)
        return TechnicalPageReport(
            slug=slug,
            configured_origin=origin,
            status=OverallTechStatus.ERROR,
            score=breakdown.final,
            score_breakdown=breakdown,
            findings=findings,
        )
    canonical_counts: Counter[str] = Counter(
        p.canonical_url.strip() for p in bundle.pages if p.canonical_url.strip()
    )
    inbound = build_inbound_counts(bundle.pages)
    findings = run_page_technical_rules(
        page,
        configured_origin=origin,
        bundle=bundle,
        canonical_counts=canonical_counts,
        inbound=inbound,
    )
    breakdown = compute_tech_score(findings)
    return TechnicalPageReport(
        slug=page.slug,
        configured_origin=origin,
        status=derive_tech_status(findings),
        score=breakdown.final,
        score_breakdown=breakdown,
        findings=findings,
        canonical_url=page.canonical_url,
        crawlable=_crawlable_flag(findings),
    )
