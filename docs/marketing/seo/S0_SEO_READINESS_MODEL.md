# S0 — SEO Readiness Model

**Sprint:** S0  
**Agent:** HERMES  
**Implementation:** `src/tools/seo_engine/readiness.py`

---

## 1. Purpose

Deterministic, offline, testable read model for page/content SEO readiness. No network access. No LLM scoring.

---

## 2. API

```python
from src.tools.seo_engine import evaluate_html_readiness, evaluate_artifact_readiness

report = evaluate_html_readiness(html, slug="my-slug", configured_origin="https://example.invalid")
report = evaluate_artifact_readiness(Path("output/website"), slug="hiring-systems")
```

### `ReadinessReport`

| Field | Type | Description |
|-------|------|-------------|
| `slug` | str | Page slug |
| `canonical_url` | str | Extracted canonical |
| `configured_origin` | str | Origin used for alignment checks |
| `findings` | list | Ordered findings |
| `ok` | bool | True iff no ERROR-level findings |

---

## 3. Evaluated signals

| Signal | Levels | Codes |
|--------|--------|-------|
| **Title** | ERROR if missing; WARNING if &lt;10 chars | `title_missing`, `title_short` |
| **Meta description** | ERROR if missing; WARNING if &gt;160 chars | `description_missing`, `description_long` |
| **Slug** | WARNING if metadata slug ≠ directory | `slug_dir_mismatch` |
| **Canonical path** | ERROR if missing; WARNING if origin mismatch / deprecated host; INFO if infra host | `canonical_missing`, `origin_mismatch`, `deprecated_host`, `infrastructure_host` |
| **Indexability** | (S1) robots policy | — |
| **Robots directive** | not evaluated in S0 (not emitted by Website Engine) | — |
| **OpenGraph** | WARNING if `og:url` ≠ canonical | `og_url_mismatch` |
| **Structured data** | WARNING if Article JSON-LD absent | `schema_article_missing` |
| **Heading structure** | ERROR no H1; WARNING multiple H1; INFO no H2 | `h1_missing`, `h1_multiple`, `h2_absent` |
| **Internal links** | INFO if none detected | `no_internal_links` |
| **Sitemap eligibility** | WARNING if slug missing from `sitemap.xml` | `sitemap_missing_slug` |
| **Feed eligibility** | WARNING if slug missing from `rss.xml` | `rss_missing_slug` |
| **Duplicate-risk** | implicit via canonical + slug checks | — |
| **Artifact presence** | ERROR if `index.html` missing | `html_missing` |

---

## 4. Severity rules

| Level | Meaning |
|-------|---------|
| **ERROR** | Blocks SEO readiness (`report.ok == False`) |
| **WARNING** | Should fix before production activation |
| **INFO** | Advisory; does not block readiness |

---

## 5. Origin alignment

When `configured_origin` is set (default: `get_configured_site_origin()`):

- Host `workcrew.ai` → WARNING `deprecated_host`
- Host `*.pages.dev` → INFO `infrastructure_host`
- Host ≠ configured origin (non-deprecated) → WARNING `origin_mismatch`

This supports development against placeholder origins without requiring the future production domain.

---

## 6. Determinism guarantees

- Pure functions over string/path input
- No HTTP, no filesystem beyond explicit artifact paths
- Same input → same findings (stable codes)

---

## 7. Tests

`tests/test_seo_readiness.py` — minimal valid page, missing title, deprecated host warning.

---

## 8. S1 extensions (not in S0)

- Robots / noindex policy evaluation
- Title/description keyword alignment
- Canonical path normalization rules
- Multi-page duplicate detection
- CLI / API exposure
