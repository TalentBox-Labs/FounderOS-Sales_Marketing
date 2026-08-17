# M3.5 — Static Website Output Integrity

**Role:** Agent B — Output Integrity Audit (GOVERNANCE)  
**Sprint:** M3.5  
**Date:** 2026-08-10  
**Prior audit (re-verified):** [M3_STATIC_OUTPUT_AUDIT.md](M3_STATIC_OUTPUT_AUDIT.md)  
**Baseline contracts:** [M2_5_WEBSITE_ENGINE_BASELINE.md](M2_5_WEBSITE_ENGINE_BASELINE.md)  
**Owned file:** this document only  
**Code / API / DB changes:** **NONE**

---

## Verdict

| Field | Value |
|-------|--------|
| **Output Integrity** | **PASS** |
| **Contract failures** | **0** |

Independent re-verification of `StaticWebsiteProvider` artifacts against M2.5 frozen Core contracts and M3 audit claims. Evidence: code review, `tests/test_static_provider.py` (**12 passed**), and live tmp `publish_content` + direct provider publish (path safety / overwrite / idempotence).

---

## Method

1. Re-read M3 output audit findings; re-checked `static_provider.py`, `provider.py` (`wrap_html_document`), `engine.py`, `feeds.py`, `urls.py`, `metadata.py`, `render.py`, `registry.py`.
2. Ran `.venv/bin/pytest tests/test_static_provider.py -q` → **12 passed**.
3. Live integrity harness into isolated tmp tree (`publish_content("W99", …)` → `{tmp}/output/website/`), then second identical publish, unsafe-slug probes, and same-slug overwrite.
4. Confirmed no writes outside provider `output_dir`; input bundle + sentinel file unchanged.
5. Scanned static provider imports/body for SEO Engine / Publishing Engine / HTTP / CMS leakage.

---

## Contract area results

### 1. Canonical URLs — **PASS**

| Expectation | Evidence |
|-------------|----------|
| Canonical owned by Core `build_canonical_url` before provider | `engine.prepare_website_page` → `build_canonical_url` |
| HTML `<link rel="canonical">` = metadata canonical | `wrap_html_document` emits `meta.canonical_url` |
| OG `og:url` = canonical | Live `metadata.json` + HTML |
| Sitemap `loc` = canonical | Live `sitemap.xml` |
| RSS item `link` = canonical | Live `rss.xml`; `FeedItem(link=request.canonical_url)` |
| Live value | `https://workcrew.ai/blog/hiring-systems` consistent across result, HTML, metadata, sitemap, RSS |

---

### 2. Slug stability — **PASS**

| Expectation | Evidence |
|-------------|----------|
| Slug from Core `build_slug` (FM canonical path) | Live slug `hiring-systems` from FM `canonical_url` |
| Provider writes `{output_dir}/{slug}/` only | `page_dir = self.output_dir / request.slug` |
| Re-publish keeps same slug / page path | Second `publish_content` → identical slug + paths |
| Provider does not re-own slug rules | Consumes request slug; path-safety only |

---

### 3. Metadata — **PASS**

| Expectation | Evidence |
|-------------|----------|
| `WebsiteMetadata` via Core `build_metadata` | Built in `prepare_website_page` |
| Persisted `{slug}/metadata.json` via `to_dict()` | Live keys: `title`, `description`, `canonical_url`, `slug`, `primary_keyword`, `og`, `schema_org` |
| OG + Schema.org Article in HTML head | DOCTYPE wrap + JSON-LD present |
| No SEO scoring / keyword optimization | Absent from static publish path; `metadata.py` documents non-ownership |

---

### 4. HTML — **PASS**

| Expectation | Evidence |
|-------------|----------|
| Full document: doctype, description, canonical, OG, JSON-LD, `<article>` | Live `index.html` |
| Body from pre-rendered `request.html` (Core `render_markdown`) | Provider does not re-convert Markdown |
| Byte-identical on identical re-publish | Live hash compare publish1 ≡ publish2 |

---

### 5. Markdown — **PASS**

| Expectation | Evidence |
|-------------|----------|
| `{slug}/source.md` = raw `request.markdown` | Write path in `_write_artifacts` |
| Body content present | Live contains article body text |
| Overwrite replaces prior body | Direct provider: `version-alpha` → `version-beta` |

---

### 6. Sitemap — **PASS**

| Expectation | Evidence |
|-------------|----------|
| Core `build_sitemap` → xmlns 0.9 URL set | Live XML |
| Persist `sitemap.xml` at `output_dir` root | `write_feed_artifacts` |
| `loc` = absolute canonical HTTPS URL | Live; no relative/`..` locs |
| `details["sitemap_urls"]` populated | Provider result details |
| Byte-identical on identical re-publish | Live hash compare |

---

### 7. RSS — **PASS**

| Expectation | Evidence |
|-------------|----------|
| Core `build_rss` → RSS 2.0 | Live `version="2.0"` |
| Persist `rss.xml` | Feed write helper |
| Item title/link/description; `guid` = slug, `isPermaLink=false` | Live contract holds |
| Structural stability on re-publish | link/guid stable; see note below |

**Non-blocking note:** `feeds.build_rss` stamps `pubDate` with UTC-now when `FeedItem.pub_date` is empty, so RSS XML bytes may differ across back-to-back publishes. Page artifacts + sitemap remain byte-identical; RSS **contract fields** (link/guid/title) stay stable. Inherited Core feed helper behavior; not an M3.5 static-adapter regression.

---

### 8. No malformed paths — **PASS**

| Check | Result |
|-------|--------|
| Reject empty / `.` / `..` / `../…` / `/` / `\` / overlong / non-`_SAFE_SLUG` | Direct provider probes all rejected; `ok=False`, `external_http=False` |
| Resolved page dir must stay under `output_dir` | `_validate_output_paths` + `relative_to` |
| No escape directories created | Live: no `{tmp}/escape` or sibling escape dirs |
| All `artifact_paths` confined under `output_dir` | Live resolve check |

---

### 9. No hidden mutation outside provider output — **PASS**

| Check | Result |
|-------|--------|
| Exact file set under `output_dir` | `{slug}/index.html`, `{slug}/metadata.json`, `{slug}/source.md`, `sitemap.xml`, `rss.xml` only |
| Input bundle unchanged | SHA-256 of `05_Final.md` stable across publishes |
| Sentinel outside output untouched | Live |
| No writes under `{tmp}/output` outside `website/` | Live |
| Failed validation writes nothing | Tests: missing fields / bad slug leave empty tree |

---

### 10. Repeat execution stable / idempotent — **PASS**

| Check | Result |
|-------|--------|
| Same inputs → same slug/canonical | Live publish ×2 |
| HTML / metadata.json / source.md / sitemap.xml byte-identical | Live hashes |
| File set unchanged | Live |
| Same-slug overwrite replaces content (idempotent upsert) | Test + live `version-alpha`→`version-beta` |
| Focused tests | `TestIdempotentOverwrite` green |

---

### 11. No SEO Engine business logic — **PASS**

| Check | Result |
|-------|--------|
| `static_provider.py` imports | `json`, `re`, `Path`, `feeds`, `provider` only |
| Scoring / keyword optimization / rank APIs | None |
| Site metadata emit (OG / Schema.org / canonical) | Website Engine ownership (v2.1 / M2.5) — emit-only |
| Optional SEO plan file in content load | `content_model` description hint only; not scoring; not in static adapter |

---

## Artifact surface (verified)

```text
{output_dir}/{slug}/index.html
{output_dir}/{slug}/metadata.json
{output_dir}/{slug}/source.md
{output_dir}/sitemap.xml
{output_dir}/rss.xml
```

Provider name `static`; `external_http=False` on success and failure paths.

---

## M3 audit re-verification

| M3 claim | M3.5 status |
|----------|-------------|
| Output Audit PASS, 0 failures | **Reconfirmed** |
| Canonical consistency across HTML/meta/sitemap/RSS | **Reconfirmed** (live) |
| Path-safe slug validation | **Reconfirmed** (expanded probes) |
| No SEO / Publishing / HTTP leakage in static adapter | **Reconfirmed** |
| Single-item sitemap/RSS overwrite per publish | Still true; out of scope; non-blocking |
| 12/12 provider tests | **12 passed** |

---

## Brief findings

1. **StaticWebsiteProvider output integrity holds** for canonical URL, slug stability, metadata, HTML, Markdown, sitemap, and RSS under the frozen M2.5 contracts.
2. **Filesystem hygiene holds:** no malformed/`..` paths, no writes outside `output_dir`, no input/sentinel mutation.
3. **Idempotence holds** for page + sitemap artifacts; RSS `pubDate` may refresh (Core feed helper) without breaking link/guid contracts.
4. **Boundary hygiene holds:** no SEO Engine business logic in the static provider path.
5. **No contract failures;** no Agent A stop conditions.

---

## FINAL

```text
Output Integrity: PASS
Contract failures: 0
```
