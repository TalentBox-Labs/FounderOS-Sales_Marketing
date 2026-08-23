"""SEO Readiness Engine orchestration + scoring (ATLAS — S1).

READ / ANALYZE / CLASSIFY / REPORT / RECOMMEND only.
Never mutates source content, publishes, or submits to search engines.
"""

from __future__ import annotations

from pathlib import Path

from src.tools.seo_engine.artifacts import (
    default_artifact_root,
    list_page_slugs,
    load_page_artifact,
    load_site_inventory,
)
from src.tools.seo_engine.extract import ExtractedPage, extract_page
from src.tools.seo_engine.models import (
    CheckResult,
    CheckStatus,
    OverallStatus,
    PageReadinessResult,
    ScoreBreakdown,
    SiteReadinessResult,
)
from src.tools.seo_engine.policy import (
    MAX_PAGES_PER_BATCH,
    SCORE_BASE,
    SCORE_ERROR_PENALTY,
    SCORE_MIN,
    SCORE_WARNING_PENALTY,
)
from src.tools.seo_engine.rules import build_duplicate_indexes, run_all_checks
from src.tools.site_origin import get_configured_site_origin, is_indexing_activation_allowed


def compute_score(checks: list[CheckResult]) -> ScoreBreakdown:
    errors = sum(1 for c in checks if c.status == CheckStatus.ERROR)
    warnings = sum(1 for c in checks if c.status == CheckStatus.WARNING)
    domain_blocks = sum(1 for c in checks if c.status == CheckStatus.DOMAIN_BLOCKED)
    final = SCORE_BASE - (errors * SCORE_ERROR_PENALTY) - (warnings * SCORE_WARNING_PENALTY)
    if final < SCORE_MIN:
        final = SCORE_MIN
    return ScoreBreakdown(
        base=SCORE_BASE,
        error_penalty=SCORE_ERROR_PENALTY,
        warning_penalty=SCORE_WARNING_PENALTY,
        error_count=errors,
        warning_count=warnings,
        domain_block_count=domain_blocks,
        final=final,
    )


def derive_overall_status(checks: list[CheckResult]) -> OverallStatus:
    """Domain blockers gate status independently of numeric score."""
    if any(c.status == CheckStatus.DOMAIN_BLOCKED for c in checks):
        return OverallStatus.DOMAIN_BLOCKED
    if any(c.status == CheckStatus.ERROR for c in checks):
        return OverallStatus.ERROR
    if any(c.status == CheckStatus.WARNING for c in checks):
        return OverallStatus.WARNING
    return OverallStatus.PASS


def analyze_extracted_page(
    page: ExtractedPage,
    *,
    configured_origin: str | None = None,
    known_slugs: set[str] | None = None,
    duplicate_titles=None,
    duplicate_descriptions=None,
    duplicate_canonicals=None,
    duplicate_slugs=None,
) -> PageReadinessResult:
    origin = configured_origin or get_configured_site_origin()
    checks = run_all_checks(
        page,
        configured_origin=origin,
        known_slugs=known_slugs,
        duplicate_titles=duplicate_titles,
        duplicate_descriptions=duplicate_descriptions,
        duplicate_canonicals=duplicate_canonicals,
        duplicate_slugs=duplicate_slugs,
    )
    breakdown = compute_score(checks)
    status = derive_overall_status(checks)
    return PageReadinessResult(
        slug=page.slug,
        canonical_url=page.canonical_url,
        configured_origin=origin,
        status=status,
        score=breakdown.final,
        score_breakdown=breakdown,
        checks=checks,
        title=page.title,
        description=page.description,
        indexing_activation_allowed=is_indexing_activation_allowed(),
    )


def analyze_html(
    html: str,
    *,
    slug: str = "",
    configured_origin: str | None = None,
    known_slugs: set[str] | None = None,
) -> PageReadinessResult:
    page = extract_page(html, slug=slug)
    return analyze_extracted_page(
        page,
        configured_origin=configured_origin,
        known_slugs=known_slugs,
    )


def analyze_page_artifact(
    artifact_root: Path | str,
    slug: str,
    *,
    configured_origin: str | None = None,
    known_slugs: set[str] | None = None,
) -> PageReadinessResult:
    root = Path(artifact_root)
    page = load_page_artifact(root, slug)
    origin = configured_origin or get_configured_site_origin()
    if page is None:
        checks = [
            CheckResult(
                id="html_missing",
                status=CheckStatus.ERROR,
                message=f"Missing {slug}/index.html",
                field_name="artifact",
                recommendation="Publish Website Engine artifacts before SEO analysis.",
            )
        ]
        breakdown = compute_score(checks)
        return PageReadinessResult(
            slug=slug,
            canonical_url="",
            configured_origin=origin,
            status=OverallStatus.ERROR,
            score=breakdown.final,
            score_breakdown=breakdown,
            checks=checks,
            indexing_activation_allowed=is_indexing_activation_allowed(),
        )
    inventory = known_slugs
    if inventory is None:
        slugs, _ = list_page_slugs(root)
        inventory = set(slugs)
    return analyze_extracted_page(
        page, configured_origin=origin, known_slugs=inventory
    )


def analyze_site(
    artifact_root: Path | str | None = None,
    *,
    configured_origin: str | None = None,
    max_pages: int = MAX_PAGES_PER_BATCH,
) -> SiteReadinessResult:
    root = Path(artifact_root) if artifact_root is not None else default_artifact_root()
    origin = configured_origin or get_configured_site_origin()
    pages, known, truncated = load_site_inventory(root, max_pages=max_pages)
    titles, descs, canons, slugs = build_duplicate_indexes(pages)
    results = [
        analyze_extracted_page(
            page,
            configured_origin=origin,
            known_slugs=known,
            duplicate_titles=titles,
            duplicate_descriptions=descs,
            duplicate_canonicals=canons,
            duplicate_slugs=slugs,
        )
        for page in pages
    ]
    return SiteReadinessResult(
        artifact_root=str(root),
        configured_origin=origin,
        pages=results,
        truncated=truncated,
        max_pages=max_pages,
    )
