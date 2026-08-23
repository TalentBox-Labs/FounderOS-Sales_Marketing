# S0 — Current Website SEO Baseline

**Sprint:** S0  
**Agent:** SENTINEL  
**Evidence source:** Live code + `output/website/hiring-systems/` artifacts (not documentation alone)

---

## 1. Audit method

Inspected:

- `src/tools/website_engine/metadata.py`, `provider.py`, `feeds.py`, `urls.py`
- `output/website/hiring-systems/index.html`
- `output/website/sitemap.xml`, `output/website/rss.xml`
- `output/website/hiring-systems/metadata.json`

Sample page published via Static Provider with FM canonical `https://workcrew.ai/blog/hiring-systems`.

---

## 2. Capability matrix

| Capability | Status | Evidence |
|------------|--------|----------|
| **Title** | PASS | `<title>` in `wrap_html_document` |
| **Meta description** | PASS | `<meta name="description">` |
| **Canonical** | PARTIAL | Emitted; values from FM (historical `workcrew.ai`) — **DOMAIN BLOCKED** for production alignment |
| **Robots directive** | NOT IMPLEMENTED | No `<meta name="robots">` or `X-Robots-Tag` |
| **Sitemap** | PASS | `sitemap.xml` at site root |
| **RSS** | PASS | `rss.xml` at site root |
| **OpenGraph** | PASS | `og:type`, `og:title`, `og:description`, `og:url`, `og:site_name` |
| **Schema.org** | PASS | JSON-LD `Article` with headline, description, `@id`, url, keywords |
| **Slugs** | PASS | Directory-per-slug (`/{slug}/index.html`), FM-driven |
| **Internal links** | PARTIAL | Renderer supports `<a>` in markdown; sample page has no internal links |

---

## 3. Origin / domain state

| Check | Result |
|-------|--------|
| Public deploy host | `founderos-staging.pages.dev` (infrastructure) |
| Embedded canonical in artifacts | `workcrew.ai` (deprecated for future production) |
| Runtime default (post-S0) | `https://example.invalid/blog` when env unset |
| Production canonical ratified | **DOMAIN BLOCKED** — FDR-N05 open |

**Canonical mismatch:** Live host ≠ embedded canonical. This is expected until domain ratification and content/origin migration.

---

## 4. SEO readiness on sample artifact

Running readiness model against `output/website/hiring-systems/index.html` with `configured_origin=https://example.invalid`:

| Finding | Level |
|---------|-------|
| `deprecated_host` | WARNING |
| `no_internal_links` | INFO |

Technical metadata (title, description, H1, schema) present → no ERROR-level blockers except domain policy.

---

## 5. Overall baseline verdict

| Dimension | Verdict |
|-----------|---------|
| **Technical metadata emission** | PASS |
| **Feed artifacts** | PASS |
| **Origin / canonical alignment** | FAIL (domain blocked) |
| **Indexing controls** | NOT IMPLEMENTED |
| **Overall Current SEO Baseline** | **PARTIAL** |

---

## 6. Gaps for S1+

1. Robots / noindex for staging and preview hosts
2. Origin-aware canonical rewrite at publish (when domain ratified)
3. SEO readiness API/CLI integration
4. Internal linking guidance in content pipeline
5. `og:site_name` decouple from legacy "WorkCrew" brand default
