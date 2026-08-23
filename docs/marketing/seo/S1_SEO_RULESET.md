# S1 — SEO Ruleset (Phase 1)

**Sprint:** S1  
**Agent:** HERMES  
**Implementation:** `src/tools/seo_engine/rules.py` · thresholds in `policy.py`

All rules are deterministic, offline, and non-mutating.

---

## Severity vocabulary

| Status | Meaning |
|--------|---------|
| PASS | Check satisfied |
| WARNING | Fix before production activation |
| ERROR | Blocks technical readiness |
| DOMAIN_BLOCKED | Domain/indexing governance gate (independent of score) |
| NOT_APPLICABLE | Signal not required / artifact absent |
| INFO | Advisory |

---

## Policy thresholds (`policy.py`)

| Constant | Value |
|----------|-------|
| `TITLE_MIN_LEN` | 10 |
| `TITLE_MAX_LEN` | 70 |
| `DESC_MIN_LEN` | 50 |
| `DESC_MAX_LEN` | 160 |
| `SLUG_MAX_LEN` | 200 |
| `SLUG_PATTERN` | `^[a-z0-9]([a-z0-9-]{0,198}[a-z0-9])?$` |
| `SCORE_BASE` | 100 |
| `SCORE_ERROR_PENALTY` | 25 |
| `SCORE_WARNING_PENALTY` | 8 |
| `SCORE_DOMAIN_BLOCK_PENALTY` | 0 (domain blockers do not reduce score) |
| `MAX_PAGES_PER_BATCH` | 200 |

---

## Rules

### TITLE

| ID | Severity | Pass condition | Rationale |
|----|----------|----------------|-----------|
| `title_missing` | ERROR | Non-empty `<title>` | Required SERP signal |
| `title_too_short` | ERROR | length ≥ TITLE_MIN_LEN | Too short titles are non-informative |
| `title_too_long` | WARNING | length ≤ TITLE_MAX_LEN | Truncation risk |
| `title_present` | PASS | Within policy | Healthy |
| `title_duplicate` | WARNING | Unique in batch | Duplicate SERP titles |

**Input:** extracted title; optional duplicate counter from site batch.

### META DESCRIPTION

| ID | Severity | Pass condition |
|----|----------|----------------|
| `description_missing` | ERROR | Non-empty meta description |
| `description_too_short` | WARNING | ≥ DESC_MIN_LEN |
| `description_too_long` | WARNING | ≤ DESC_MAX_LEN |
| `description_present` | PASS | Within policy |
| `description_duplicate` | WARNING | Unique in batch |

### SLUG

| ID | Severity | Pass condition |
|----|----------|----------------|
| `slug_missing` | ERROR | Slug present |
| `slug_too_long` | ERROR | ≤ SLUG_MAX_LEN |
| `slug_malformed` | ERROR | URL-safe pattern |
| `slug_case_or_dot` | WARNING | Prefer lowercase hyphenated |
| `slug_valid` | PASS | Matches policy |
| `slug_dir_mismatch` | WARNING | metadata.slug == directory |
| `slug_duplicate` | ERROR | Unique slug |

### CANONICAL

| ID | Severity | Pass condition |
|----|----------|----------------|
| `canonical_missing` | ERROR | Absolute canonical present |
| `canonical_invalid` | ERROR | http(s) + host |
| `canonical_deprecated_host` | DOMAIN_BLOCKED | Host not workcrew.ai |
| `canonical_infrastructure_host` | DOMAIN_BLOCKED | Host not *.pages.dev |
| `canonical_placeholder_origin` | DOMAIN_BLOCKED | Not example.invalid for production |
| `canonical_origin_mismatch` | WARNING | Host matches FOUNDER_SITE_ORIGIN |
| `canonical_origin_unratified` | DOMAIN_BLOCKED | FOUNDER_SITE_ORIGIN_RATIFIED + activation gates |
| `canonical_structure_ok` | PASS | Valid structure |
| `canonical_duplicate` | ERROR | Unique canonical |
| `canonical_slug_path_mismatch` | WARNING | Path ends with slug |

### INDEXABILITY

| ID | Severity | Pass condition |
|----|----------|----------------|
| `robots_noindex` | INFO | Detected noindex |
| `robots_absent` | INFO | No robots meta (current Website Engine) |
| `indexability_unsafe_host` | DOMAIN_BLOCKED | Not staging/deprecated host |
| `indexability_activation_blocked` | DOMAIN_BLOCKED | `is_indexing_activation_allowed()` |
| `indexability_gates_pass` | PASS | Gates pass (still no auto-submit) |

### OPEN GRAPH

| ID | Severity | Pass condition |
|----|----------|----------------|
| `og_fields_missing` | WARNING | og:title, og:description, og:url, og:type |
| `og_core_present` | PASS | Core fields present |
| `og_image_absent` | NOT_APPLICABLE | og:image not required in S0/S1 |
| `og_url_mismatch` | WARNING | og:url == canonical |

### STRUCTURED DATA

| ID | Severity | Pass condition |
|----|----------|----------------|
| `jsonld_invalid` | ERROR | JSON-LD parses |
| `schema_article_missing` | WARNING | JSON-LD present |
| `schema_article_present` | PASS | `@type` Article |
| `schema_article_type_missing` | WARNING | Article type found |

No network Schema.org validation.

### HEADINGS

| ID | Severity | Pass condition |
|----|----------|----------------|
| `h1_missing` | ERROR | Exactly one H1 preferred; zero = ERROR |
| `h1_multiple` | WARNING | Single H1 |
| `h1_ok` | PASS | Single H1 |
| `heading_hierarchy_skip` | WARNING | No level skip > HEADING_MAX_SKIP |
| `h2_absent` | INFO | Optional H2 |

### INTERNAL LINKS

| ID | Severity | Pass condition |
|----|----------|----------------|
| `internal_link_malformed` | ERROR | Valid href |
| `internal_link_deprecated_host` | DOMAIN_BLOCKED | No workcrew.ai absolute links |
| `internal_link_infra_host` | WARNING | Prefer relative paths |
| `internal_link_broken` | WARNING | Target in local inventory |
| `no_internal_links` | INFO | Advisory |
| `internal_links_ok` | PASS | Inspected without issues |

No external HTTP crawling.

### SITEMAP / FEED

| ID | Severity | Pass condition |
|----|----------|----------------|
| `sitemap_ineligible_noindex` | INFO | noindex → not eligible |
| `sitemap_file_absent` | NOT_APPLICABLE | sitemap.xml missing |
| `sitemap_eligible_present` | PASS | Slug in sitemap |
| `sitemap_missing_slug` | WARNING | Indexable page in sitemap |
| `rss_file_absent` | NOT_APPLICABLE | rss.xml missing |
| `feed_eligible_present` | PASS | Slug in RSS |
| `rss_missing_slug` | WARNING | Page in RSS |

**Never submit sitemap.**

### DUPLICATE RISK

| ID | Severity | Pass condition |
|----|----------|----------------|
| `duplicate_risk_detected` | WARNING | No local dup signals |
| `duplicate_risk_clear` | PASS | Clear |

---

## Scoring

```
score = max(0, 100 - 25*errors - 8*warnings)
```

DOMAIN_BLOCKED does **not** reduce score. Overall status prefers DOMAIN_BLOCKED over score.

---

## Deferred (not S1)

- Keyword strategy / LLM recommendations
- Semantic plagiarism
- Comprehensive Schema.org remote validation
- robots.txt / edge X-Robots-Tag emission
- Search Console / IndexNow
