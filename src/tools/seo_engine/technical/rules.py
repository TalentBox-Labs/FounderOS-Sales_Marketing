"""Technical SEO Phase-1 rules (S2). Deterministic, offline, non-mutating."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any
from urllib.parse import urlparse

from src.tools.seo_engine.extract import ExtractedPage
from src.tools.seo_engine.technical.models import TechCategory, TechFinding, TechSeverity
from src.tools.seo_engine.technical.parsers import (
    FeedParseResult,
    SiteArtifactBundle,
    SitemapParseResult,
    slug_from_url,
)
from src.tools.site_origin import (
    PLACEHOLDER_SITE_ORIGIN,
    host_from_url,
    is_deprecated_production_host,
    is_indexing_activation_allowed,
    is_infrastructure_host,
    is_site_origin_ratified,
)

_MALFORMED_HREF = re.compile(r"[\s<>]|^\s*$")


def _f(
    id: str,
    category: TechCategory,
    severity: TechSeverity,
    message: str,
    *,
    artifact: str = "",
    expected: str = "",
    actual: str = "",
    recommendation: str = "",
    evidence: dict[str, Any] | None = None,
    ownership: str = "SEO_ENGINE",
) -> TechFinding:
    return TechFinding(
        id=id,
        category=category,
        severity=severity,
        message=message,
        artifact=artifact,
        expected=expected,
        actual=actual,
        recommendation=recommendation,
        evidence=dict(evidence or {}),
        ownership=ownership,
    )


def analyze_canonical(
    page: ExtractedPage,
    *,
    configured_origin: str,
    canonical_counts: Counter[str],
) -> list[TechFinding]:
    out: list[TechFinding] = []
    url = (page.canonical_url or "").strip()
    art = f"{page.slug}/index.html"
    if not url:
        out.append(
            _f(
                "tech_canonical_missing",
                TechCategory.CANONICAL,
                TechSeverity.ERROR,
                "Canonical link missing",
                artifact=art,
                expected="Absolute https canonical",
                actual="absent",
                recommendation="Website Engine should emit <link rel=canonical>.",
                ownership="WEBSITE_ENGINE",
            )
        )
        return out
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        out.append(
            _f(
                "tech_canonical_invalid",
                TechCategory.CANONICAL,
                TechSeverity.ERROR,
                "Canonical URL syntax invalid",
                artifact=art,
                expected="https://host/path",
                actual=url,
                ownership="WEBSITE_ENGINE",
            )
        )
        return out
    host = host_from_url(url)
    if is_deprecated_production_host(host):
        out.append(
            _f(
                "tech_canonical_deprecated_host",
                TechCategory.CANONICAL,
                TechSeverity.DOMAIN_BLOCKED,
                f"Canonical uses deprecated host {host!r}",
                artifact=art,
                expected="Ratified production origin",
                actual=url,
                recommendation="Migrate canonicals after Founder domain ratification.",
                ownership="DOMAIN",
            )
        )
    elif is_infrastructure_host(host):
        out.append(
            _f(
                "tech_canonical_infra_host",
                TechCategory.CANONICAL,
                TechSeverity.DOMAIN_BLOCKED,
                f"Canonical uses infrastructure host {host!r}",
                artifact=art,
                expected="Branded ratified origin",
                actual=url,
                ownership="DOMAIN",
            )
        )
    elif host == host_from_url(PLACEHOLDER_SITE_ORIGIN):
        out.append(
            _f(
                "tech_canonical_placeholder",
                TechCategory.CANONICAL,
                TechSeverity.DOMAIN_BLOCKED,
                "Canonical uses placeholder origin example.invalid",
                artifact=art,
                expected="Ratified production origin",
                actual=url,
                ownership="DOMAIN",
            )
        )
    else:
        cfg_host = host_from_url(configured_origin)
        if cfg_host and host != cfg_host:
            out.append(
                _f(
                    "tech_canonical_origin_mismatch",
                    TechCategory.CANONICAL,
                    TechSeverity.WARNING,
                    "Canonical host differs from configured SITE_ORIGIN",
                    artifact=art,
                    expected=cfg_host,
                    actual=host,
                    ownership="CONTENT",
                )
            )
        else:
            out.append(
                _f(
                    "tech_canonical_ok",
                    TechCategory.CANONICAL,
                    TechSeverity.PASS,
                    "Canonical syntax valid",
                    artifact=art,
                    actual=url,
                )
            )

    if not is_site_origin_ratified() or not is_indexing_activation_allowed():
        out.append(
            _f(
                "tech_canonical_unratified",
                TechCategory.CANONICAL,
                TechSeverity.DOMAIN_BLOCKED,
                "Production origin unratified — indexing activation blocked",
                artifact=art,
                expected="FOUNDER_SITE_ORIGIN_RATIFIED + safe origin",
                actual=configured_origin,
                ownership="DOMAIN",
            )
        )

    if page.slug and slug_from_url(url) and slug_from_url(url) != page.slug:
        out.append(
            _f(
                "tech_canonical_identity_mismatch",
                TechCategory.CANONICAL,
                TechSeverity.ERROR,
                "Canonical path slug does not match page identity",
                artifact=art,
                expected=page.slug,
                actual=slug_from_url(url),
                ownership="CONTENT",
            )
        )

    if url and canonical_counts[url] > 1:
        out.append(
            _f(
                "tech_canonical_duplicate",
                TechCategory.CANONICAL,
                TechSeverity.CRITICAL,
                f"Duplicate canonical shared by {canonical_counts[url]} pages",
                artifact=art,
                expected="Unique canonical per page",
                actual=url,
                ownership="CONTENT",
            )
        )
    return out


def analyze_robots(page: ExtractedPage, *, robots_txt_present: bool) -> list[TechFinding]:
    out: list[TechFinding] = []
    art = f"{page.slug}/index.html"
    robots = (page.robots or "").lower().strip()
    del robots_txt_present  # site-level signal handled in run_site_technical_rules
    if not robots:
        out.append(
            _f(
                "tech_robots_meta_absent",
                TechCategory.ROBOTS,
                TechSeverity.INFO,
                "No page-level robots meta (Website Engine default)",
                artifact=art,
                expected="Optional; staging should prefer noindex until activation",
                actual="absent",
                ownership="WEBSITE_ENGINE",
            )
        )
    else:
        directives = {d.strip() for d in robots.replace(",", " ").split() if d.strip()}
        if "index" in directives and "noindex" in directives:
            out.append(
                _f(
                    "tech_robots_conflict",
                    TechCategory.ROBOTS,
                    TechSeverity.CRITICAL,
                    "Conflicting index/noindex robots directives",
                    artifact=art,
                    expected="Single clear directive",
                    actual=page.robots,
                    ownership="WEBSITE_ENGINE",
                )
            )
        elif "noindex" in directives:
            out.append(
                _f(
                    "tech_robots_noindex",
                    TechCategory.ROBOTS,
                    TechSeverity.INFO,
                    "Page marked noindex",
                    artifact=art,
                    actual=page.robots,
                    ownership="EXPECTED",
                )
            )
        else:
            out.append(
                _f(
                    "tech_robots_indexable_signal",
                    TechCategory.ROBOTS,
                    TechSeverity.WARNING,
                    "Page robots allow indexing while production activation blocked",
                    artifact=art,
                    expected="noindex on staging/unratified deployments",
                    actual=page.robots,
                    recommendation="Prefer noindex until domain ratification.",
                    ownership="WEBSITE_ENGINE",
                )
            )
    # Accidental indexability: no robots + deprecated/infra host canonical
    host = host_from_url(page.canonical_url)
    if not robots and (is_infrastructure_host(host) or is_deprecated_production_host(host)):
        out.append(
            _f(
                "tech_robots_accidental_index_risk",
                TechCategory.ROBOTS,
                TechSeverity.WARNING,
                "No noindex on staging/deprecated-host page — accidental index risk",
                artifact=art,
                expected="noindex for non-production hosts",
                actual="robots meta absent",
                ownership="WEBSITE_ENGINE",
            )
        )
    return out


def analyze_sitemap_site(
    sitemap: SitemapParseResult,
    pages: list[ExtractedPage],
    *,
    configured_origin: str,
) -> list[TechFinding]:
    out: list[TechFinding] = []
    if not sitemap.present:
        out.append(
            _f(
                "tech_sitemap_absent",
                TechCategory.SITEMAP,
                TechSeverity.WARNING,
                "sitemap.xml absent",
                artifact="sitemap.xml",
                ownership="WEBSITE_ENGINE",
            )
        )
        return out
    if not sitemap.ok:
        out.append(
            _f(
                "tech_sitemap_malformed",
                TechCategory.SITEMAP,
                TechSeverity.CRITICAL,
                "sitemap.xml not parseable",
                artifact="sitemap.xml",
                actual=sitemap.error,
                ownership="WEBSITE_ENGINE",
            )
        )
        return out
    out.append(
        _f(
            "tech_sitemap_parse_ok",
            TechCategory.SITEMAP,
            TechSeverity.PASS,
            f"Sitemap parseable with {len(sitemap.urls)} URL(s)",
            artifact="sitemap.xml",
        )
    )
    counts = Counter(sitemap.urls)
    for url, n in counts.items():
        if n > 1:
            out.append(
                _f(
                    "tech_sitemap_duplicate_url",
                    TechCategory.SITEMAP,
                    TechSeverity.ERROR,
                    f"Duplicate sitemap URL ({n}x)",
                    artifact="sitemap.xml",
                    actual=url,
                    ownership="WEBSITE_ENGINE",
                )
            )
        host = host_from_url(url)
        if is_deprecated_production_host(host):
            out.append(
                _f(
                    "tech_sitemap_deprecated_host",
                    TechCategory.SITEMAP,
                    TechSeverity.DOMAIN_BLOCKED,
                    "Sitemap URL uses deprecated host",
                    artifact="sitemap.xml",
                    actual=url,
                    ownership="DOMAIN",
                )
            )
        elif is_infrastructure_host(host):
            out.append(
                _f(
                    "tech_sitemap_infra_host",
                    TechCategory.SITEMAP,
                    TechSeverity.DOMAIN_BLOCKED,
                    "Sitemap URL uses infrastructure host",
                    artifact="sitemap.xml",
                    actual=url,
                    ownership="DOMAIN",
                )
            )
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            out.append(
                _f(
                    "tech_sitemap_malformed_url",
                    TechCategory.SITEMAP,
                    TechSeverity.ERROR,
                    "Malformed sitemap URL",
                    artifact="sitemap.xml",
                    actual=url,
                    ownership="WEBSITE_ENGINE",
                )
            )

    page_by_slug = {p.slug: p for p in pages}
    sitemap_slugs = {slug_from_url(u) for u in sitemap.urls if slug_from_url(u)}
    for p in pages:
        noindex = "noindex" in (p.robots or "").lower()
        if noindex and p.slug in sitemap_slugs:
            out.append(
                _f(
                    "tech_sitemap_includes_noindex",
                    TechCategory.SITEMAP,
                    TechSeverity.ERROR,
                    f"noindex page {p.slug!r} included in sitemap",
                    artifact="sitemap.xml",
                    expected="Exclude noindex pages",
                    actual=p.slug,
                    ownership="WEBSITE_ENGINE",
                )
            )
        if not noindex and p.slug not in sitemap_slugs:
            out.append(
                _f(
                    "tech_sitemap_missing_eligible",
                    TechCategory.SITEMAP,
                    TechSeverity.WARNING,
                    f"Eligible page {p.slug!r} missing from sitemap",
                    artifact="sitemap.xml",
                    expected=p.slug,
                    actual="absent",
                    ownership="WEBSITE_ENGINE",
                )
            )
    for slug in sitemap_slugs:
        if slug and slug not in page_by_slug:
            out.append(
                _f(
                    "tech_sitemap_unknown_slug",
                    TechCategory.SITEMAP,
                    TechSeverity.WARNING,
                    f"Sitemap references unknown local slug {slug!r}",
                    artifact="sitemap.xml",
                    actual=slug,
                    ownership="WEBSITE_ENGINE",
                )
            )
    return out


def analyze_structured_data(page: ExtractedPage) -> list[TechFinding]:
    out: list[TechFinding] = []
    art = f"{page.slug}/index.html"
    if page.json_ld_parse_errors:
        out.append(
            _f(
                "tech_jsonld_malformed",
                TechCategory.STRUCTURED_DATA,
                TechSeverity.CRITICAL,
                "Malformed JSON-LD",
                artifact=art,
                expected="Valid JSON",
                actual=f"{page.json_ld_parse_errors} parse error(s)",
                ownership="WEBSITE_ENGINE",
            )
        )
    if not page.json_ld:
        out.append(
            _f(
                "tech_jsonld_absent",
                TechCategory.STRUCTURED_DATA,
                TechSeverity.WARNING,
                "No JSON-LD blocks",
                artifact=art,
                ownership="WEBSITE_ENGINE",
            )
        )
        return out

    def walk_types(node: Any) -> list[str]:
        found: list[str] = []
        if isinstance(node, dict):
            t = node.get("@type")
            if isinstance(t, str):
                found.append(t)
            elif isinstance(t, list):
                found.extend(str(x) for x in t)
            for v in node.values():
                found.extend(walk_types(v))
        elif isinstance(node, list):
            for x in node:
                found.extend(walk_types(x))
        return found

    def walk_urls(node: Any) -> list[str]:
        urls: list[str] = []
        if isinstance(node, dict):
            for k, v in node.items():
                if k in {"url", "@id"} and isinstance(v, str):
                    urls.append(v)
                else:
                    urls.extend(walk_urls(v))
        elif isinstance(node, list):
            for x in node:
                urls.extend(walk_urls(x))
        return urls

    types: list[str] = []
    for doc in page.json_ld:
        if isinstance(doc, dict) and "@context" not in doc:
            out.append(
                _f(
                    "tech_jsonld_missing_context",
                    TechCategory.STRUCTURED_DATA,
                    TechSeverity.WARNING,
                    "JSON-LD missing @context",
                    artifact=art,
                    ownership="WEBSITE_ENGINE",
                )
            )
        types.extend(walk_types(doc))
        for u in walk_urls(doc):
            if page.canonical_url and u.rstrip("/") != page.canonical_url.rstrip("/"):
                # only flag absolute http URLs
                if u.startswith("http"):
                    out.append(
                        _f(
                            "tech_jsonld_url_mismatch",
                            TechCategory.STRUCTURED_DATA,
                            TechSeverity.WARNING,
                            "Structured data URL differs from canonical",
                            artifact=art,
                            expected=page.canonical_url,
                            actual=u,
                            ownership="WEBSITE_ENGINE",
                        )
                    )
            host = host_from_url(u) if u.startswith("http") else ""
            if host and is_deprecated_production_host(host):
                out.append(
                    _f(
                        "tech_jsonld_deprecated_host",
                        TechCategory.STRUCTURED_DATA,
                        TechSeverity.DOMAIN_BLOCKED,
                        "Structured data URL uses deprecated host",
                        artifact=art,
                        actual=u,
                        ownership="DOMAIN",
                    )
                )
    if not types:
        out.append(
            _f(
                "tech_jsonld_missing_type",
                TechCategory.STRUCTURED_DATA,
                TechSeverity.ERROR,
                "JSON-LD missing @type",
                artifact=art,
                ownership="WEBSITE_ENGINE",
            )
        )
    elif "Article" in types:
        out.append(
            _f(
                "tech_jsonld_article_ok",
                TechCategory.STRUCTURED_DATA,
                TechSeverity.PASS,
                "Article JSON-LD present",
                artifact=art,
            )
        )
    else:
        out.append(
            _f(
                "tech_jsonld_type_present",
                TechCategory.STRUCTURED_DATA,
                TechSeverity.INFO,
                f"JSON-LD @type present: {', '.join(sorted(set(types)))}",
                artifact=art,
            )
        )
    if len(page.json_ld) > 1:
        out.append(
            _f(
                "tech_jsonld_multiple_blocks",
                TechCategory.STRUCTURED_DATA,
                TechSeverity.INFO,
                f"Multiple JSON-LD blocks ({len(page.json_ld)})",
                artifact=art,
            )
        )
    return out


def analyze_open_graph(page: ExtractedPage) -> list[TechFinding]:
    out: list[TechFinding] = []
    art = f"{page.slug}/index.html"
    og = page.og or {}
    required = ("og:title", "og:description", "og:url", "og:type")
    missing = [k for k in required if not og.get(k)]
    if missing:
        out.append(
            _f(
                "tech_og_missing_fields",
                TechCategory.OPEN_GRAPH,
                TechSeverity.WARNING,
                f"Missing OG fields: {', '.join(missing)}",
                artifact=art,
                actual=",".join(missing),
                ownership="WEBSITE_ENGINE",
            )
        )
    else:
        out.append(
            _f(
                "tech_og_core_ok",
                TechCategory.OPEN_GRAPH,
                TechSeverity.PASS,
                "Core Open Graph fields present",
                artifact=art,
            )
        )
    og_url = og.get("og:url", "")
    if og_url:
        parsed = urlparse(og_url)
        if parsed.scheme and parsed.scheme not in {"http", "https"}:
            out.append(
                _f(
                    "tech_og_url_malformed",
                    TechCategory.OPEN_GRAPH,
                    TechSeverity.ERROR,
                    "og:url malformed",
                    artifact=art,
                    actual=og_url,
                    ownership="WEBSITE_ENGINE",
                )
            )
        if page.canonical_url and og_url.rstrip("/") != page.canonical_url.rstrip("/"):
            out.append(
                _f(
                    "tech_og_url_mismatch",
                    TechCategory.OPEN_GRAPH,
                    TechSeverity.WARNING,
                    "og:url differs from canonical",
                    artifact=art,
                    expected=page.canonical_url,
                    actual=og_url,
                    ownership="WEBSITE_ENGINE",
                )
            )
        host = host_from_url(og_url)
        if is_deprecated_production_host(host):
            out.append(
                _f(
                    "tech_og_deprecated_host",
                    TechCategory.OPEN_GRAPH,
                    TechSeverity.DOMAIN_BLOCKED,
                    "og:url uses deprecated host",
                    artifact=art,
                    actual=og_url,
                    ownership="DOMAIN",
                )
            )
    if "og:image" not in og:
        out.append(
            _f(
                "tech_og_image_na",
                TechCategory.OPEN_GRAPH,
                TechSeverity.NOT_APPLICABLE,
                "og:image not required in Phase 1 policy",
                artifact=art,
                ownership="EXPECTED",
            )
        )
    return out


def analyze_internal_links(
    page: ExtractedPage,
    *,
    known_slugs: set[str],
    inbound: dict[str, int],
) -> list[TechFinding]:
    out: list[TechFinding] = []
    art = f"{page.slug}/index.html"
    internal = 0
    for href in page.hrefs:
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        if _MALFORMED_HREF.search(href) or href.startswith("javascript:"):
            out.append(
                _f(
                    "tech_link_malformed",
                    TechCategory.INTERNAL_LINKS,
                    TechSeverity.ERROR,
                    "Malformed internal/href link",
                    artifact=art,
                    actual=href,
                    ownership="CONTENT",
                )
            )
            continue
        parsed = urlparse(href)
        host = (parsed.netloc or "").lower()
        if host and is_deprecated_production_host(host):
            out.append(
                _f(
                    "tech_link_deprecated_host",
                    TechCategory.INTERNAL_LINKS,
                    TechSeverity.DOMAIN_BLOCKED,
                    "Link points to deprecated host",
                    artifact=art,
                    actual=href,
                    ownership="CONTENT",
                )
            )
            continue
        if host and is_infrastructure_host(host):
            out.append(
                _f(
                    "tech_link_infra_host",
                    TechCategory.INTERNAL_LINKS,
                    TechSeverity.WARNING,
                    "Link points to infrastructure host",
                    artifact=art,
                    actual=href,
                    ownership="CONTENT",
                )
            )
        is_internal = not host or True  # relative always; absolute treated below
        if host and not is_deprecated_production_host(host) and not is_infrastructure_host(host):
            # external absolute — skip broken-target checks
            if not href.startswith("/") and host:
                continue
        path = parsed.path.rstrip("/")
        segment = path.split("/")[-1] if path else ""
        if segment == page.slug and (not host or True):
            if href.startswith("/") or not host:
                out.append(
                    _f(
                        "tech_link_self",
                        TechCategory.INTERNAL_LINKS,
                        TechSeverity.INFO,
                        "Self-referential internal link",
                        artifact=art,
                        actual=href,
                    )
                )
        if (not host or is_infrastructure_host(host) or is_deprecated_production_host(host) is False) and segment:
            if not host or href.startswith("/") or is_infrastructure_host(host):
                internal += 1
                if known_slugs and segment not in known_slugs and not path.endswith(".xml"):
                    if href.startswith("/") or not host:
                        out.append(
                            _f(
                                "tech_link_broken",
                                TechCategory.INTERNAL_LINKS,
                                TechSeverity.WARNING,
                                "Internal link target not in local inventory",
                                artifact=art,
                                expected="known slug",
                                actual=href,
                                ownership="CONTENT",
                            )
                        )
    if inbound.get(page.slug, 0) == 0 and len(known_slugs) > 1:
        out.append(
            _f(
                "tech_link_orphan_candidate",
                TechCategory.INTERNAL_LINKS,
                TechSeverity.INFO,
                "Orphan candidate: no inbound internal links from other pages",
                artifact=art,
                actual=page.slug,
            )
        )
    if internal == 0 and not any(f.id == "tech_link_malformed" for f in out):
        out.append(
            _f(
                "tech_link_none",
                TechCategory.INTERNAL_LINKS,
                TechSeverity.INFO,
                "No internal links on page",
                artifact=art,
            )
        )
    elif not any(f.severity in {TechSeverity.ERROR, TechSeverity.WARNING, TechSeverity.DOMAIN_BLOCKED} and f.category == TechCategory.INTERNAL_LINKS for f in out):
        out.append(
            _f(
                "tech_link_ok",
                TechCategory.INTERNAL_LINKS,
                TechSeverity.PASS,
                "Internal links inspected",
                artifact=art,
            )
        )
    return out


def analyze_crawlability(page: ExtractedPage, *, in_sitemap: bool | None) -> list[TechFinding]:
    out: list[TechFinding] = []
    art = f"{page.slug}/index.html"
    noindex = "noindex" in (page.robots or "").lower()
    has_canonical = bool(page.canonical_url)
    discoverable = in_sitemap is True
    if noindex:
        out.append(
            _f(
                "tech_crawl_noindex",
                TechCategory.CRAWLABILITY,
                TechSeverity.INFO,
                "Page not indexable per robots — crawlability limited by design",
                artifact=art,
                ownership="EXPECTED",
            )
        )
        return out
    if has_canonical and discoverable:
        out.append(
            _f(
                "tech_crawl_ok",
                TechCategory.CRAWLABILITY,
                TechSeverity.PASS,
                "Local evidence supports crawl discovery (sitemap + canonical)",
                artifact=art,
            )
        )
    elif has_canonical and in_sitemap is False:
        out.append(
            _f(
                "tech_crawl_not_in_sitemap",
                TechCategory.CRAWLABILITY,
                TechSeverity.WARNING,
                "Canonical page not listed in sitemap — reduced discoverability",
                artifact=art,
                ownership="WEBSITE_ENGINE",
            )
        )
    elif not has_canonical:
        out.append(
            _f(
                "tech_crawl_no_canonical",
                TechCategory.CRAWLABILITY,
                TechSeverity.WARNING,
                "Missing canonical weakens crawl/index interpretation",
                artifact=art,
                ownership="WEBSITE_ENGINE",
            )
        )
    else:
        out.append(
            _f(
                "tech_crawl_partial",
                TechCategory.CRAWLABILITY,
                TechSeverity.INFO,
                "Crawlability assessed from partial local evidence only",
                artifact=art,
            )
        )
    return out


def analyze_http_routing(bundle: SiteArtifactBundle) -> list[TechFinding]:
    out: list[TechFinding] = []
    # Duplicate slug dirs already unique by filesystem; check missing index
    for slug in bundle.slug_dirs_missing_index:
        out.append(
            _f(
                "tech_route_missing_index",
                TechCategory.HTTP_ROUTING,
                TechSeverity.ERROR,
                f"Slug directory missing index.html: {slug}",
                artifact=f"{slug}/",
                expected="index.html",
                actual="absent",
                ownership="WEBSITE_ENGINE",
            )
        )
    # Conflicting outputs: same canonical path slug appearing twice already covered
    slugs = [p.slug for p in bundle.pages]
    if len(slugs) != len(set(slugs)):
        out.append(
            _f(
                "tech_route_duplicate_slug",
                TechCategory.HTTP_ROUTING,
                TechSeverity.CRITICAL,
                "Duplicate slug identities in inventory",
                artifact=str(bundle.root),
                ownership="WEBSITE_ENGINE",
            )
        )
    for p in bundle.pages:
        if re.search(r"[^\w.\-]", p.slug) or ".." in p.slug:
            out.append(
                _f(
                    "tech_route_malformed_path",
                    TechCategory.HTTP_ROUTING,
                    TechSeverity.ERROR,
                    f"Malformed public slug path {p.slug!r}",
                    artifact=p.slug,
                    ownership="CONTENT",
                )
            )
    if not bundle.pages and bundle.root.is_dir():
        out.append(
            _f(
                "tech_route_no_pages",
                TechCategory.HTTP_ROUTING,
                TechSeverity.INFO,
                "No page artifacts discovered",
                artifact=str(bundle.root),
            )
        )
    elif bundle.pages and not any(f.severity.value in {"ERROR", "CRITICAL"} for f in out):
        out.append(
            _f(
                "tech_route_ok",
                TechCategory.HTTP_ROUTING,
                TechSeverity.PASS,
                "Static routing artifacts look consistent locally",
                artifact=str(bundle.root),
            )
        )
    return out


def analyze_feed(
    feed: FeedParseResult,
    pages: list[ExtractedPage],
    *,
    configured_origin: str,
) -> list[TechFinding]:
    out: list[TechFinding] = []
    if not feed.present:
        out.append(
            _f(
                "tech_feed_absent",
                TechCategory.FEED,
                TechSeverity.INFO,
                "rss.xml absent",
                artifact="rss.xml",
                ownership="WEBSITE_ENGINE",
            )
        )
        return out
    if not feed.ok:
        out.append(
            _f(
                "tech_feed_malformed",
                TechCategory.FEED,
                TechSeverity.CRITICAL,
                "rss.xml not parseable",
                artifact="rss.xml",
                actual=feed.error,
                ownership="WEBSITE_ENGINE",
            )
        )
        return out
    out.append(
        _f(
            "tech_feed_parse_ok",
            TechCategory.FEED,
            TechSeverity.PASS,
            f"Feed parseable with {len(feed.item_links)} item(s)",
            artifact="rss.xml",
        )
    )
    if feed.channel_link:
        host = host_from_url(feed.channel_link)
        if is_deprecated_production_host(host):
            out.append(
                _f(
                    "tech_feed_channel_deprecated",
                    TechCategory.FEED,
                    TechSeverity.DOMAIN_BLOCKED,
                    "Feed channel link uses deprecated host",
                    artifact="rss.xml",
                    actual=feed.channel_link,
                    ownership="DOMAIN",
                )
            )
        cfg_host = host_from_url(configured_origin)
        if cfg_host and host and host != cfg_host and not is_deprecated_production_host(host):
            out.append(
                _f(
                    "tech_feed_origin_mismatch",
                    TechCategory.FEED,
                    TechSeverity.WARNING,
                    "Feed channel host differs from configured origin",
                    artifact="rss.xml",
                    expected=cfg_host,
                    actual=host,
                )
            )
    counts = Counter(feed.item_links)
    for link, n in counts.items():
        if n > 1:
            out.append(
                _f(
                    "tech_feed_duplicate_item",
                    TechCategory.FEED,
                    TechSeverity.ERROR,
                    "Duplicate feed item URL",
                    artifact="rss.xml",
                    actual=link,
                    ownership="WEBSITE_ENGINE",
                )
            )
        if is_deprecated_production_host(host_from_url(link)):
            out.append(
                _f(
                    "tech_feed_item_deprecated",
                    TechCategory.FEED,
                    TechSeverity.DOMAIN_BLOCKED,
                    "Feed item URL uses deprecated host",
                    artifact="rss.xml",
                    actual=link,
                    ownership="DOMAIN",
                )
            )
    # Canonical consistency vs feed items
    by_slug = {p.slug: p for p in pages}
    for link in feed.item_links:
        slug = slug_from_url(link)
        page = by_slug.get(slug)
        if page and page.canonical_url and page.canonical_url.rstrip("/") != link.rstrip("/"):
            out.append(
                _f(
                    "tech_feed_canonical_conflict",
                    TechCategory.FEED,
                    TechSeverity.WARNING,
                    f"Feed item URL differs from page canonical for {slug}",
                    artifact="rss.xml",
                    expected=page.canonical_url,
                    actual=link,
                    ownership="WEBSITE_ENGINE",
                )
            )
    return out


def analyze_consistency(
    page: ExtractedPage,
    *,
    sitemap_urls: list[str],
) -> list[TechFinding]:
    out: list[TechFinding] = []
    art = f"{page.slug}/index.html"
    canon = (page.canonical_url or "").rstrip("/")
    # Sitemap conflict
    matching = [u for u in sitemap_urls if slug_from_url(u) == page.slug]
    if canon and matching:
        for u in matching:
            if u.rstrip("/") != canon:
                out.append(
                    _f(
                        "tech_consistency_canonical_sitemap",
                        TechCategory.CONSISTENCY,
                        TechSeverity.ERROR,
                        "Canonical and sitemap URL disagree for page",
                        artifact=art,
                        expected=canon,
                        actual=u,
                        ownership="WEBSITE_ENGINE",
                    )
                )
    og_url = (page.og or {}).get("og:url", "").rstrip("/")
    if canon and og_url and og_url != canon:
        out.append(
            _f(
                "tech_consistency_canonical_og",
                TechCategory.CONSISTENCY,
                TechSeverity.WARNING,
                "Canonical and og:url disagree",
                artifact=art,
                expected=canon,
                actual=og_url,
                ownership="WEBSITE_ENGINE",
            )
        )
    # Structured data already emits url mismatch; add explicit consistency if Article url differs
    # Index vs sitemap exclusion
    noindex = "noindex" in (page.robots or "").lower()
    in_sm = any(slug_from_url(u) == page.slug for u in sitemap_urls)
    if not noindex and matching and canon:
        # if robots absent (implicit index) and sitemap matches — ok signal
        if all(u.rstrip("/") == canon for u in matching):
            out.append(
                _f(
                    "tech_consistency_ok",
                    TechCategory.CONSISTENCY,
                    TechSeverity.PASS,
                    "Canonical/sitemap/OG cross-checks completed",
                    artifact=art,
                )
            )
    elif noindex and in_sm:
        out.append(
            _f(
                "tech_consistency_index_sitemap",
                TechCategory.CONSISTENCY,
                TechSeverity.ERROR,
                "Page noindex but present in sitemap",
                artifact=art,
                ownership="WEBSITE_ENGINE",
            )
        )
    return out


def build_inbound_counts(pages: list[ExtractedPage]) -> dict[str, int]:
    inbound: dict[str, int] = defaultdict(int)
    known = {p.slug for p in pages}
    for p in pages:
        for href in p.hrefs:
            parsed = urlparse(href)
            if parsed.netloc and not href.startswith("/"):
                # only count clearly internal relative-ish
                if not is_deprecated_production_host(parsed.netloc) and not is_infrastructure_host(
                    parsed.netloc
                ):
                    continue
            segment = (parsed.path or "").rstrip("/").split("/")[-1]
            if segment in known and segment != p.slug:
                inbound[segment] += 1
    return dict(inbound)


def run_page_technical_rules(
    page: ExtractedPage,
    *,
    configured_origin: str,
    bundle: SiteArtifactBundle,
    canonical_counts: Counter[str],
    inbound: dict[str, int],
) -> list[TechFinding]:
    findings: list[TechFinding] = []
    findings.extend(
        analyze_canonical(
            page, configured_origin=configured_origin, canonical_counts=canonical_counts
        )
    )
    findings.extend(analyze_robots(page, robots_txt_present=bundle.robots_txt_present))
    findings.extend(analyze_structured_data(page))
    findings.extend(analyze_open_graph(page))
    findings.extend(
        analyze_internal_links(page, known_slugs=bundle.known_slugs, inbound=inbound)
    )
    in_sm = page.slug in {slug_from_url(u) for u in bundle.sitemap.urls} if bundle.sitemap.ok else None
    findings.extend(analyze_crawlability(page, in_sitemap=in_sm))
    findings.extend(analyze_consistency(page, sitemap_urls=bundle.sitemap.urls if bundle.sitemap.ok else []))
    return findings


def run_site_technical_rules(
    bundle: SiteArtifactBundle,
    *,
    configured_origin: str,
) -> list[TechFinding]:
    findings: list[TechFinding] = []
    if not bundle.robots_txt_present:
        findings.append(
            _f(
                "tech_robots_txt_absent",
                TechCategory.ROBOTS,
                TechSeverity.INFO,
                "Site robots.txt not present in static artifacts",
                artifact="robots.txt",
                expected="Optional for Phase 1; Website Engine does not emit robots.txt",
                actual="absent",
                ownership="WEBSITE_ENGINE",
            )
        )
    findings.extend(
        analyze_sitemap_site(bundle.sitemap, bundle.pages, configured_origin=configured_origin)
    )
    findings.extend(analyze_feed(bundle.feed, bundle.pages, configured_origin=configured_origin))
    findings.extend(analyze_http_routing(bundle))
    return findings
