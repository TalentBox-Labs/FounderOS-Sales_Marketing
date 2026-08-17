"""Deterministic Phase-1 SEO rules (HERMES).

Each public check_* function returns CheckResult(s). Thresholds live in policy.py.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Iterable
from urllib.parse import urlparse

from src.tools.seo_engine.extract import ExtractedPage, path_from_url
from src.tools.seo_engine.models import CheckResult, CheckStatus
from src.tools.seo_engine.policy import (
    DESC_MAX_LEN,
    DESC_MIN_LEN,
    HEADING_MAX_SKIP,
    SLUG_MAX_LEN,
    SLUG_PATTERN,
    TITLE_MAX_LEN,
    TITLE_MIN_LEN,
)
from src.tools.site_origin import (
    PLACEHOLDER_SITE_ORIGIN,
    get_configured_site_origin,
    get_site_base_path,
    host_from_url,
    is_deprecated_production_host,
    is_indexing_activation_allowed,
    is_infrastructure_host,
    is_site_origin_ratified,
)

_SLUG_RE = re.compile(SLUG_PATTERN)
_MALFORMED_HREF = re.compile(r"[\s<>]|^\s*$")


def check_title(page: ExtractedPage, *, duplicate_titles: Counter[str] | None = None) -> list[CheckResult]:
    out: list[CheckResult] = []
    title = (page.title or "").strip()
    if not title:
        out.append(
            CheckResult(
                id="title_missing",
                status=CheckStatus.ERROR,
                message="Missing or empty <title>",
                field_name="title",
                recommendation="Add a unique, descriptive HTML title.",
            )
        )
        return out
    if len(title) < TITLE_MIN_LEN:
        out.append(
            CheckResult(
                id="title_too_short",
                status=CheckStatus.ERROR,
                message=f"Title length {len(title)} < minimum {TITLE_MIN_LEN}",
                field_name="title",
                recommendation=f"Expand title to at least {TITLE_MIN_LEN} characters.",
                evidence={"length": len(title), "min": TITLE_MIN_LEN},
            )
        )
    elif len(title) > TITLE_MAX_LEN:
        out.append(
            CheckResult(
                id="title_too_long",
                status=CheckStatus.WARNING,
                message=f"Title length {len(title)} > recommended max {TITLE_MAX_LEN}",
                field_name="title",
                recommendation=f"Shorten title to ≤{TITLE_MAX_LEN} characters.",
                evidence={"length": len(title), "max": TITLE_MAX_LEN},
            )
        )
    else:
        out.append(
            CheckResult(
                id="title_present",
                status=CheckStatus.PASS,
                message="Title present within length policy",
                field_name="title",
                evidence={"length": len(title)},
            )
        )
    if duplicate_titles and title and duplicate_titles[title] > 1:
        out.append(
            CheckResult(
                id="title_duplicate",
                status=CheckStatus.WARNING,
                message=f"Duplicate title across {duplicate_titles[title]} pages",
                field_name="title",
                recommendation="Make titles unique per page.",
                evidence={"count": duplicate_titles[title]},
            )
        )
    return out


def check_description(
    page: ExtractedPage, *, duplicate_descriptions: Counter[str] | None = None
) -> list[CheckResult]:
    out: list[CheckResult] = []
    desc = (page.description or "").strip()
    if not desc:
        out.append(
            CheckResult(
                id="description_missing",
                status=CheckStatus.ERROR,
                message="Missing or empty meta description",
                field_name="description",
                recommendation="Add a unique meta description.",
            )
        )
        return out
    if len(desc) < DESC_MIN_LEN:
        out.append(
            CheckResult(
                id="description_too_short",
                status=CheckStatus.WARNING,
                message=f"Description length {len(desc)} < recommended min {DESC_MIN_LEN}",
                field_name="description",
                recommendation=f"Expand description to ≥{DESC_MIN_LEN} characters.",
                evidence={"length": len(desc), "min": DESC_MIN_LEN},
            )
        )
    elif len(desc) > DESC_MAX_LEN:
        out.append(
            CheckResult(
                id="description_too_long",
                status=CheckStatus.WARNING,
                message=f"Description length {len(desc)} > max {DESC_MAX_LEN}",
                field_name="description",
                recommendation=f"Shorten description to ≤{DESC_MAX_LEN} characters.",
                evidence={"length": len(desc), "max": DESC_MAX_LEN},
            )
        )
    else:
        out.append(
            CheckResult(
                id="description_present",
                status=CheckStatus.PASS,
                message="Meta description within length policy",
                field_name="description",
                evidence={"length": len(desc)},
            )
        )
    if duplicate_descriptions and desc and duplicate_descriptions[desc] > 1:
        out.append(
            CheckResult(
                id="description_duplicate",
                status=CheckStatus.WARNING,
                message=f"Duplicate description across {duplicate_descriptions[desc]} pages",
                field_name="description",
                recommendation="Make meta descriptions unique per page.",
                evidence={"count": duplicate_descriptions[desc]},
            )
        )
    return out


def check_slug(page: ExtractedPage, *, duplicate_slugs: Counter[str] | None = None) -> list[CheckResult]:
    out: list[CheckResult] = []
    slug = (page.slug or "").strip()
    meta_slug = str((page.metadata or {}).get("slug") or "").strip()
    if not slug:
        out.append(
            CheckResult(
                id="slug_missing",
                status=CheckStatus.ERROR,
                message="Slug missing",
                field_name="slug",
                recommendation="Provide a stable URL-safe slug.",
            )
        )
        return out
    if len(slug) > SLUG_MAX_LEN:
        out.append(
            CheckResult(
                id="slug_too_long",
                status=CheckStatus.ERROR,
                message=f"Slug exceeds max length {SLUG_MAX_LEN}",
                field_name="slug",
                recommendation="Shorten slug.",
            )
        )
    elif not _SLUG_RE.match(slug):
        # Allow uppercase dirs that normalize; flag obvious malformed patterns
        if re.search(r"[A-Z_\s/?#]|--|^-|-$", slug) or not re.match(
            r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,200}$", slug
        ):
            out.append(
                CheckResult(
                    id="slug_malformed",
                    status=CheckStatus.ERROR,
                    message=f"Slug {slug!r} is not URL-safe under policy",
                    field_name="slug",
                    recommendation="Use lowercase alphanumeric + hyphens only.",
                )
            )
        else:
            out.append(
                CheckResult(
                    id="slug_case_or_dot",
                    status=CheckStatus.WARNING,
                    message=f"Slug {slug!r} uses non-preferred characters",
                    field_name="slug",
                    recommendation="Prefer lowercase alphanumeric + single hyphens.",
                )
            )
    else:
        out.append(
            CheckResult(
                id="slug_valid",
                status=CheckStatus.PASS,
                message="Slug is URL-safe",
                field_name="slug",
            )
        )
    if meta_slug and meta_slug != slug:
        out.append(
            CheckResult(
                id="slug_dir_mismatch",
                status=CheckStatus.WARNING,
                message="metadata.slug differs from directory name",
                field_name="slug",
                recommendation="Align metadata slug with artifact directory.",
                evidence={"dir": slug, "metadata": meta_slug},
            )
        )
    if duplicate_slugs and slug and duplicate_slugs[slug] > 1:
        out.append(
            CheckResult(
                id="slug_duplicate",
                status=CheckStatus.ERROR,
                message=f"Duplicate slug {slug!r}",
                field_name="slug",
                recommendation="Ensure each page has a unique slug.",
            )
        )
    return out


def check_canonical(
    page: ExtractedPage,
    *,
    configured_origin: str,
    duplicate_canonicals: Counter[str] | None = None,
) -> list[CheckResult]:
    out: list[CheckResult] = []
    url = (page.canonical_url or "").strip()
    if not url:
        out.append(
            CheckResult(
                id="canonical_missing",
                status=CheckStatus.ERROR,
                message="Canonical URL missing",
                field_name="canonical_url",
                recommendation="Emit <link rel=canonical> derived from SITE_ORIGIN.",
            )
        )
        return out
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        out.append(
            CheckResult(
                id="canonical_invalid",
                status=CheckStatus.ERROR,
                message=f"Canonical URL structure invalid: {url!r}",
                field_name="canonical_url",
                recommendation="Use absolute https URL with host + path.",
            )
        )
        return out
    host = host_from_url(url)
    cfg_host = host_from_url(configured_origin)
    if is_deprecated_production_host(host):
        out.append(
            CheckResult(
                id="canonical_deprecated_host",
                status=CheckStatus.DOMAIN_BLOCKED,
                message=f"Canonical uses deprecated host {host!r}",
                field_name="canonical_url",
                recommendation=(
                    "Replace workcrew.ai canonicals after Founder domain ratification. "
                    "Do not treat as production identity."
                ),
                evidence={"host": host},
            )
        )
    elif is_infrastructure_host(host):
        out.append(
            CheckResult(
                id="canonical_infrastructure_host",
                status=CheckStatus.DOMAIN_BLOCKED,
                message=f"Canonical uses infrastructure host {host!r}",
                field_name="canonical_url",
                recommendation="pages.dev is temporary infrastructure, not branded canonical.",
                evidence={"host": host},
            )
        )
    elif configured_origin.rstrip("/") == PLACEHOLDER_SITE_ORIGIN or host == host_from_url(
        PLACEHOLDER_SITE_ORIGIN
    ):
        if host == host_from_url(PLACEHOLDER_SITE_ORIGIN):
            out.append(
                CheckResult(
                    id="canonical_placeholder_origin",
                    status=CheckStatus.DOMAIN_BLOCKED,
                    message="Canonical uses placeholder origin example.invalid",
                    field_name="canonical_url",
                    recommendation="Safe for local/dev analysis only; not production.",
                )
            )
    elif cfg_host and host != cfg_host:
        out.append(
            CheckResult(
                id="canonical_origin_mismatch",
                status=CheckStatus.WARNING,
                message=f"Canonical host {host!r} differs from configured {cfg_host!r}",
                field_name="canonical_url",
                recommendation="Align canonical with FOUNDER_SITE_ORIGIN once ratified.",
            )
        )
    else:
        out.append(
            CheckResult(
                id="canonical_structure_ok",
                status=CheckStatus.PASS,
                message="Canonical URL structure valid",
                field_name="canonical_url",
            )
        )

    # Unratified origin always surfaces as domain gate (independent of score)
    if not is_site_origin_ratified() or not is_indexing_activation_allowed():
        out.append(
            CheckResult(
                id="canonical_origin_unratified",
                status=CheckStatus.DOMAIN_BLOCKED,
                message="Production origin not ratified — indexing activation blocked",
                field_name="canonical_url",
                recommendation="Await Founder domain ratification (FDR-N05).",
                evidence={
                    "configured_origin": configured_origin,
                    "ratified": is_site_origin_ratified(),
                    "indexing_activation_allowed": is_indexing_activation_allowed(),
                },
            )
        )

    if duplicate_canonicals and url and duplicate_canonicals[url] > 1:
        out.append(
            CheckResult(
                id="canonical_duplicate",
                status=CheckStatus.ERROR,
                message=f"Duplicate canonical URL across {duplicate_canonicals[url]} pages",
                field_name="canonical_url",
                recommendation="Ensure each page has a unique canonical URL.",
            )
        )
    # Path should include site base path when using configured base
    base_path = get_site_base_path()
    path = path_from_url(url)
    if page.slug and path and not path.endswith(f"/{page.slug}") and path != f"/{page.slug}":
        out.append(
            CheckResult(
                id="canonical_slug_path_mismatch",
                status=CheckStatus.WARNING,
                message="Canonical path does not end with page slug",
                field_name="canonical_url",
                evidence={"path": path, "slug": page.slug, "base_path": base_path},
                recommendation="Align canonical path with slug.",
            )
        )
    return out


def check_indexability(page: ExtractedPage, *, configured_origin: str) -> list[CheckResult]:
    out: list[CheckResult] = []
    robots = (page.robots or "").lower()
    activation = is_indexing_activation_allowed()
    origin = configured_origin or get_configured_site_origin()
    host = host_from_url(page.canonical_url) if page.canonical_url else host_from_url(origin)

    if "noindex" in robots:
        out.append(
            CheckResult(
                id="robots_noindex",
                status=CheckStatus.INFO,
                message="robots meta includes noindex",
                field_name="robots",
                recommendation="Expected for staging; remove only after production activation.",
                evidence={"robots": page.robots},
            )
        )
    elif not page.robots:
        out.append(
            CheckResult(
                id="robots_absent",
                status=CheckStatus.INFO,
                message="No robots meta directive (Website Engine does not emit one yet)",
                field_name="robots",
                recommendation="S1.5/S2 may add noindex for staging builds.",
            )
        )

    if is_infrastructure_host(host) or is_deprecated_production_host(host):
        out.append(
            CheckResult(
                id="indexability_unsafe_host",
                status=CheckStatus.DOMAIN_BLOCKED,
                message="Indexability blocked for staging/deprecated host",
                field_name="indexability",
                recommendation="Do not authorize search indexing until ratified production origin.",
            )
        )
    elif not activation:
        out.append(
            CheckResult(
                id="indexability_activation_blocked",
                status=CheckStatus.DOMAIN_BLOCKED,
                message="Indexing activation not allowed (unratified / placeholder origin)",
                field_name="indexability",
                recommendation="Keep production SEO blocked until FOUNDER_SITE_ORIGIN_RATIFIED.",
                evidence={"configured_origin": origin},
            )
        )
    else:
        out.append(
            CheckResult(
                id="indexability_gates_pass",
                status=CheckStatus.PASS,
                message="Indexing activation gates pass (still no auto-submit)",
                field_name="indexability",
            )
        )
    return out


def check_open_graph(page: ExtractedPage) -> list[CheckResult]:
    out: list[CheckResult] = []
    og = page.og or {}
    required = ("og:title", "og:description", "og:url", "og:type")
    missing = [k for k in required if not og.get(k)]
    if missing:
        out.append(
            CheckResult(
                id="og_fields_missing",
                status=CheckStatus.WARNING,
                message=f"Missing Open Graph fields: {', '.join(missing)}",
                field_name="open_graph",
                recommendation="Emit og:title, og:description, og:url, og:type.",
                evidence={"missing": missing},
            )
        )
    else:
        out.append(
            CheckResult(
                id="og_core_present",
                status=CheckStatus.PASS,
                message="Core Open Graph fields present",
                field_name="open_graph",
            )
        )
    if "og:image" not in og or not og.get("og:image"):
        out.append(
            CheckResult(
                id="og_image_absent",
                status=CheckStatus.NOT_APPLICABLE,
                message="og:image not required by S0/S1 contract",
                field_name="open_graph",
            )
        )
    if og.get("og:url") and page.canonical_url and og["og:url"] != page.canonical_url:
        out.append(
            CheckResult(
                id="og_url_mismatch",
                status=CheckStatus.WARNING,
                message="og:url differs from canonical",
                field_name="og:url",
                recommendation="Keep og:url identical to canonical URL.",
            )
        )
    return out


def _has_article_type(node: object) -> bool:
    if isinstance(node, dict):
        t = node.get("@type")
        if t == "Article" or (isinstance(t, list) and "Article" in t):
            return True
        for v in node.values():
            if _has_article_type(v):
                return True
    elif isinstance(node, list):
        return any(_has_article_type(x) for x in node)
    return False


def check_structured_data(page: ExtractedPage) -> list[CheckResult]:
    out: list[CheckResult] = []
    if page.json_ld_parse_errors:
        out.append(
            CheckResult(
                id="jsonld_invalid",
                status=CheckStatus.ERROR,
                message=f"Invalid JSON-LD blocks: {page.json_ld_parse_errors}",
                field_name="schema_org",
                recommendation="Fix JSON-LD so it parses as JSON (offline).",
            )
        )
    if not page.json_ld:
        out.append(
            CheckResult(
                id="schema_article_missing",
                status=CheckStatus.WARNING,
                message="No JSON-LD structured data detected",
                field_name="schema_org",
                recommendation="Emit Schema.org Article JSON-LD.",
            )
        )
        return out
    if any(_has_article_type(doc) for doc in page.json_ld):
        out.append(
            CheckResult(
                id="schema_article_present",
                status=CheckStatus.PASS,
                message="Schema.org Article JSON-LD detected",
                field_name="schema_org",
            )
        )
    else:
        out.append(
            CheckResult(
                id="schema_article_type_missing",
                status=CheckStatus.WARNING,
                message="JSON-LD present but Article @type not found",
                field_name="schema_org",
                recommendation="Include @type Article in JSON-LD.",
            )
        )
    return out


def check_headings(page: ExtractedPage) -> list[CheckResult]:
    out: list[CheckResult] = []
    if page.h1_count == 0:
        out.append(
            CheckResult(
                id="h1_missing",
                status=CheckStatus.ERROR,
                message="Missing H1 heading",
                field_name="headings",
                recommendation="Include exactly one H1.",
            )
        )
    elif page.h1_count > 1:
        out.append(
            CheckResult(
                id="h1_multiple",
                status=CheckStatus.WARNING,
                message=f"Multiple H1 headings ({page.h1_count})",
                field_name="headings",
                recommendation="Use a single primary H1.",
                evidence={"count": page.h1_count},
            )
        )
    else:
        out.append(
            CheckResult(
                id="h1_ok",
                status=CheckStatus.PASS,
                message="Single H1 present",
                field_name="headings",
            )
        )
    # Hierarchy skip detection
    prev = None
    for level in page.headings:
        if prev is not None and level > prev + HEADING_MAX_SKIP:
            out.append(
                CheckResult(
                    id="heading_hierarchy_skip",
                    status=CheckStatus.WARNING,
                    message=f"Heading level jumps from H{prev} to H{level}",
                    field_name="headings",
                    recommendation="Avoid skipping heading levels.",
                )
            )
            break
        prev = level
    if not any(h == 2 for h in page.headings):
        out.append(
            CheckResult(
                id="h2_absent",
                status=CheckStatus.INFO,
                message="No H2 headings (optional structure signal)",
                field_name="headings",
            )
        )
    return out


def check_internal_links(
    page: ExtractedPage,
    *,
    known_slugs: set[str] | None = None,
    configured_origin: str,
) -> list[CheckResult]:
    out: list[CheckResult] = []
    known = known_slugs or set()
    cfg_host = host_from_url(configured_origin)
    internal_count = 0
    issues = 0
    for href in page.hrefs:
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        if _MALFORMED_HREF.search(href) or href.startswith("javascript:"):
            issues += 1
            out.append(
                CheckResult(
                    id="internal_link_malformed",
                    status=CheckStatus.ERROR,
                    message=f"Malformed link href: {href!r}",
                    field_name="internal_links",
                    recommendation="Fix or remove malformed href.",
                    evidence={"href": href},
                )
            )
            continue
        parsed = urlparse(href)
        host = (parsed.netloc or "").lower()
        if host and is_deprecated_production_host(host):
            issues += 1
            out.append(
                CheckResult(
                    id="internal_link_deprecated_host",
                    status=CheckStatus.DOMAIN_BLOCKED,
                    message=f"Link points to deprecated host: {href}",
                    field_name="internal_links",
                    recommendation="Remove workcrew.ai absolute links from content.",
                    evidence={"href": href},
                )
            )
            continue
        if host and is_infrastructure_host(host):
            out.append(
                CheckResult(
                    id="internal_link_infra_host",
                    status=CheckStatus.WARNING,
                    message=f"Link uses infrastructure host: {href}",
                    field_name="internal_links",
                    recommendation="Prefer relative paths for internal navigation.",
                    evidence={"href": href},
                )
            )
        is_internal = (not host) or (cfg_host and host == cfg_host)
        if not is_internal:
            continue
        internal_count += 1
        path = parsed.path.rstrip("/")
        if not path or path == "/":
            continue
        # Extract last segment as candidate slug
        segment = path.split("/")[-1]
        if known and segment and segment not in known and not path.endswith(".xml"):
            out.append(
                CheckResult(
                    id="internal_link_broken",
                    status=CheckStatus.WARNING,
                    message=f"Internal link target not in local inventory: {href}",
                    field_name="internal_links",
                    recommendation="Point to a known published slug or add the target page.",
                    evidence={"href": href, "segment": segment},
                )
            )
            issues += 1
    if internal_count == 0 and issues == 0:
        out.append(
            CheckResult(
                id="no_internal_links",
                status=CheckStatus.INFO,
                message="No internal links detected",
                field_name="internal_links",
            )
        )
    elif issues == 0:
        out.append(
            CheckResult(
                id="internal_links_ok",
                status=CheckStatus.PASS,
                message=f"{internal_count} internal link(s) inspected",
                field_name="internal_links",
                evidence={"count": internal_count},
            )
        )
    return out


def check_sitemap_eligibility(page: ExtractedPage) -> list[CheckResult]:
    robots = (page.robots or "").lower()
    noindex = "noindex" in robots
    if noindex:
        return [
            CheckResult(
                id="sitemap_ineligible_noindex",
                status=CheckStatus.INFO,
                message="Page not sitemap-eligible due to noindex",
                field_name="sitemap",
                recommendation="Exclude noindex pages from sitemap.",
            )
        ]
    if page.in_sitemap is None:
        return [
            CheckResult(
                id="sitemap_file_absent",
                status=CheckStatus.NOT_APPLICABLE,
                message="No sitemap.xml in artifact root",
                field_name="sitemap",
            )
        ]
    if page.in_sitemap:
        return [
            CheckResult(
                id="sitemap_eligible_present",
                status=CheckStatus.PASS,
                message="Page referenced in sitemap.xml",
                field_name="sitemap",
            )
        ]
    return [
        CheckResult(
            id="sitemap_missing_slug",
            status=CheckStatus.WARNING,
            message="Indexable page not referenced in sitemap.xml",
            field_name="sitemap",
            recommendation="Include eligible pages in sitemap (do not submit to search engines).",
        )
    ]


def check_feed_eligibility(page: ExtractedPage) -> list[CheckResult]:
    if page.in_rss is None:
        return [
            CheckResult(
                id="rss_file_absent",
                status=CheckStatus.NOT_APPLICABLE,
                message="No rss.xml in artifact root",
                field_name="rss",
            )
        ]
    if page.in_rss:
        return [
            CheckResult(
                id="feed_eligible_present",
                status=CheckStatus.PASS,
                message="Page referenced in rss.xml",
                field_name="rss",
            )
        ]
    return [
        CheckResult(
            id="rss_missing_slug",
            status=CheckStatus.WARNING,
            message="Page not referenced in rss.xml",
            field_name="rss",
            recommendation="Include feed-eligible articles in RSS.",
        )
    ]


def check_duplicate_risk(
    page: ExtractedPage,
    *,
    duplicate_titles: Counter[str] | None = None,
    duplicate_descriptions: Counter[str] | None = None,
    duplicate_canonicals: Counter[str] | None = None,
    duplicate_slugs: Counter[str] | None = None,
) -> list[CheckResult]:
    """Aggregate duplicate-risk INFO/PASS when no duplicates (detail checks emit WARN/ERROR)."""
    signals = 0
    title = (page.title or "").strip()
    desc = (page.description or "").strip()
    canon = (page.canonical_url or "").strip()
    slug = (page.slug or "").strip()
    if duplicate_titles and title and duplicate_titles[title] > 1:
        signals += 1
    if duplicate_descriptions and desc and duplicate_descriptions[desc] > 1:
        signals += 1
    if duplicate_canonicals and canon and duplicate_canonicals[canon] > 1:
        signals += 1
    if duplicate_slugs and slug and duplicate_slugs[slug] > 1:
        signals += 1
    if signals:
        return [
            CheckResult(
                id="duplicate_risk_detected",
                status=CheckStatus.WARNING,
                message=f"{signals} duplicate-risk signal(s) for this page",
                field_name="duplicate_risk",
                recommendation="Resolve duplicate title/description/canonical/slug.",
                evidence={"signals": signals},
            )
        ]
    return [
        CheckResult(
            id="duplicate_risk_clear",
            status=CheckStatus.PASS,
            message="No local duplicate-risk signals",
            field_name="duplicate_risk",
        )
    ]


def run_all_checks(
    page: ExtractedPage,
    *,
    configured_origin: str,
    known_slugs: set[str] | None = None,
    duplicate_titles: Counter[str] | None = None,
    duplicate_descriptions: Counter[str] | None = None,
    duplicate_canonicals: Counter[str] | None = None,
    duplicate_slugs: Counter[str] | None = None,
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    checks.extend(check_title(page, duplicate_titles=duplicate_titles))
    checks.extend(check_description(page, duplicate_descriptions=duplicate_descriptions))
    checks.extend(check_slug(page, duplicate_slugs=duplicate_slugs))
    checks.extend(
        check_canonical(
            page,
            configured_origin=configured_origin,
            duplicate_canonicals=duplicate_canonicals,
        )
    )
    checks.extend(check_indexability(page, configured_origin=configured_origin))
    checks.extend(check_open_graph(page))
    checks.extend(check_structured_data(page))
    checks.extend(check_headings(page))
    checks.extend(
        check_internal_links(
            page, known_slugs=known_slugs, configured_origin=configured_origin
        )
    )
    checks.extend(check_sitemap_eligibility(page))
    checks.extend(check_feed_eligibility(page))
    checks.extend(
        check_duplicate_risk(
            page,
            duplicate_titles=duplicate_titles,
            duplicate_descriptions=duplicate_descriptions,
            duplicate_canonicals=duplicate_canonicals,
            duplicate_slugs=duplicate_slugs,
        )
    )
    return checks


def build_duplicate_indexes(
    pages: Iterable[ExtractedPage],
) -> tuple[Counter[str], Counter[str], Counter[str], Counter[str]]:
    titles: Counter[str] = Counter()
    descs: Counter[str] = Counter()
    canons: Counter[str] = Counter()
    slugs: Counter[str] = Counter()
    for p in pages:
        if p.title.strip():
            titles[p.title.strip()] += 1
        if p.description.strip():
            descs[p.description.strip()] += 1
        if p.canonical_url.strip():
            canons[p.canonical_url.strip()] += 1
        if p.slug.strip():
            slugs[p.slug.strip()] += 1
    return titles, descs, canons, slugs
