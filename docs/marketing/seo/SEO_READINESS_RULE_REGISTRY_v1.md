# SEO Readiness Rule Registry v1.0

**Sprint:** S1.5 freeze  
**Agent:** HERMES  
**Source of truth:** `src/tools/seo_engine/rules.py` + `policy.py`  
**Status:** FROZEN

---

## Count verification

| Metric | Count | Notes |
|--------|-------|-------|
| Check categories (`check_*` in `run_all_checks`) | **12** | Matches S1 “Checks Implemented: 12” |
| Outcome rule IDs in `rules.py` | **60** | Individual PASS/WARN/ERROR/etc. codes |
| Engine-only gate | **1** | `html_missing` in `engine.py` |

**Do not fabricate alignment.** S1 “12” refers to categories, not outcome IDs.

---

## Scoring impact (all rules)

| Severity | Score impact | Blocks overall status |
|----------|--------------|------------------------|
| ERROR | −25 each | Yes → overall ERROR (unless DOMAIN_BLOCKED present) |
| WARNING | −8 each | Yes → overall WARNING (if no ERROR/DOMAIN_BLOCKED) |
| DOMAIN_BLOCKED | 0 | Yes → overall DOMAIN_BLOCKED (highest precedence) |
| INFO / PASS / NOT_APPLICABLE | 0 | No |

---

## Category 1 — Title (`check_title`)

| Rule ID | Severity | Input | PASS condition | Failure / emit condition | Blocker |
|---------|----------|-------|----------------|--------------------------|---------|
| `title_missing` | ERROR | extracted title | non-empty | empty/absent | no (ERROR) |
| `title_too_short` | ERROR | title length | ≥ `TITLE_MIN_LEN` (10) | length &lt; 10 | no |
| `title_too_long` | WARNING | title length | ≤ `TITLE_MAX_LEN` (70) | length &gt; 70 | no |
| `title_present` | PASS | title | within min/max | — | no |
| `title_duplicate` | WARNING | batch title counter | unique | count &gt; 1 | no |

**Applicability:** always when page analyzed.

---

## Category 2 — Meta description (`check_description`)

| Rule ID | Severity | Input | PASS / emit |
|---------|----------|-------|-------------|
| `description_missing` | ERROR | meta description | empty |
| `description_too_short` | WARNING | length | &lt; `DESC_MIN_LEN` (50) |
| `description_too_long` | WARNING | length | &gt; `DESC_MAX_LEN` (160) |
| `description_present` | PASS | length | within 50–160 |
| `description_duplicate` | WARNING | batch counter | count &gt; 1 |

---

## Category 3 — Slug (`check_slug`)

| Rule ID | Severity | Notes |
|---------|----------|-------|
| `slug_missing` | ERROR | empty slug |
| `slug_too_long` | ERROR | &gt; `SLUG_MAX_LEN` (200) |
| `slug_malformed` | ERROR | not URL-safe |
| `slug_case_or_dot` | WARNING | non-preferred chars but loosely safe |
| `slug_valid` | PASS | matches `SLUG_PATTERN` |
| `slug_dir_mismatch` | WARNING | metadata.slug ≠ directory |
| `slug_duplicate` | ERROR | batch slug count &gt; 1 |

---

## Category 4 — Canonical (`check_canonical`)

| Rule ID | Severity | Blocker |
|---------|----------|---------|
| `canonical_missing` | ERROR | no |
| `canonical_invalid` | ERROR | no |
| `canonical_deprecated_host` | DOMAIN_BLOCKED | **yes** (workcrew.ai) |
| `canonical_infrastructure_host` | DOMAIN_BLOCKED | **yes** (*.pages.dev) |
| `canonical_placeholder_origin` | DOMAIN_BLOCKED | **yes** (example.invalid) |
| `canonical_origin_mismatch` | WARNING | no |
| `canonical_structure_ok` | PASS | no |
| `canonical_origin_unratified` | DOMAIN_BLOCKED | **yes** |
| `canonical_duplicate` | ERROR | no |
| `canonical_slug_path_mismatch` | WARNING | no |

---

## Category 5 — Indexability (`check_indexability`)

| Rule ID | Severity | Blocker |
|---------|----------|---------|
| `robots_noindex` | INFO | no |
| `robots_absent` | INFO | no |
| `indexability_unsafe_host` | DOMAIN_BLOCKED | **yes** |
| `indexability_activation_blocked` | DOMAIN_BLOCKED | **yes** |
| `indexability_gates_pass` | PASS | no (still no auto-submit) |

---

## Category 6 — Open Graph (`check_open_graph`)

| Rule ID | Severity | Notes |
|---------|----------|-------|
| `og_fields_missing` | WARNING | missing og:title/description/url/type |
| `og_core_present` | PASS | core fields present |
| `og_image_absent` | NOT_APPLICABLE | og:image not required |
| `og_url_mismatch` | WARNING | og:url ≠ canonical |

---

## Category 7 — Structured data (`check_structured_data`)

| Rule ID | Severity | Notes |
|---------|----------|-------|
| `jsonld_invalid` | ERROR | JSON parse failure |
| `schema_article_missing` | WARNING | no JSON-LD |
| `schema_article_present` | PASS | `@type` Article |
| `schema_article_type_missing` | WARNING | JSON-LD without Article |

Offline only — no remote Schema.org validation.

---

## Category 8 — Headings (`check_headings`)

| Rule ID | Severity |
|---------|----------|
| `h1_missing` | ERROR |
| `h1_multiple` | WARNING |
| `h1_ok` | PASS |
| `heading_hierarchy_skip` | WARNING |
| `h2_absent` | INFO |

---

## Category 9 — Internal links (`check_internal_links`)

| Rule ID | Severity | Blocker |
|---------|----------|---------|
| `internal_link_malformed` | ERROR | no |
| `internal_link_deprecated_host` | DOMAIN_BLOCKED | **yes** |
| `internal_link_infra_host` | WARNING | no |
| `internal_link_broken` | WARNING | no (local inventory) |
| `no_internal_links` | INFO | no |
| `internal_links_ok` | PASS | no |

No external HTTP crawling.

---

## Category 10 — Sitemap eligibility (`check_sitemap_eligibility`)

| Rule ID | Severity |
|---------|----------|
| `sitemap_ineligible_noindex` | INFO |
| `sitemap_file_absent` | NOT_APPLICABLE |
| `sitemap_eligible_present` | PASS |
| `sitemap_missing_slug` | WARNING |

Never submits sitemap.

---

## Category 11 — Feed eligibility (`check_feed_eligibility`)

| Rule ID | Severity |
|---------|----------|
| `rss_file_absent` | NOT_APPLICABLE |
| `feed_eligible_present` | PASS |
| `rss_missing_slug` | WARNING |

---

## Category 12 — Duplicate risk (`check_duplicate_risk`)

| Rule ID | Severity |
|---------|----------|
| `duplicate_risk_detected` | WARNING |
| `duplicate_risk_clear` | PASS |

---

## Engine gate (not a category)

| Rule ID | Severity | Where |
|---------|----------|-------|
| `html_missing` | ERROR | `engine.analyze_page_artifact` when `index.html` absent |

---

## Policy thresholds (frozen)

| Constant | Value | Used? |
|----------|-------|-------|
| `TITLE_MIN_LEN` | 10 | yes |
| `TITLE_MAX_LEN` | 70 | yes |
| `TITLE_WARN_SHORT` | 20 | **no (unused)** |
| `DESC_MIN_LEN` | 50 | yes |
| `DESC_MAX_LEN` | 160 | yes |
| `DESC_HARD_EMPTY` | 1 | **no (unused)** |
| `SLUG_MAX_LEN` | 200 | yes |
| `SLUG_PATTERN` | lowercase hyphenated | yes |
| `HEADING_MAX_SKIP` | 1 | yes |
| `MAX_PAGES_PER_BATCH` | 200 | yes |

Unused constants are recorded; enabling them requires a new sprint (not silent).
