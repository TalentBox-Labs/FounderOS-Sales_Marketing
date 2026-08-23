# M3 — Static Website Output Audit

**Role:** Agent B — Website Output Auditor  
**Sprint:** M3  
**Date:** 2026-08-10  
**Baseline:** [M2_5_WEBSITE_ENGINE_BASELINE.md](M2_5_WEBSITE_ENGINE_BASELINE.md) (frozen Core contracts)  
**Implementation report (read-only):** [M3_STATIC_PROVIDER_REPORT.md](M3_STATIC_PROVIDER_REPORT.md)  
**Owned file:** this document only  

---

## Verdict

| Field | Value |
|-------|--------|
| **Output Audit** | **PASS** |
| **Contract failures** | **0** |
| Critical bugs requiring Agent A stop | **None** |

Independent verification: code review of `StaticWebsiteProvider` + frozen Core helpers it consumes, plus a local `publish_content` / direct `StaticWebsiteProvider.publish` into a tmp tree. `tests/test_static_provider.py`: **12 passed**.

---

## Method

1. Read `static_provider.py`, `provider.py` (`wrap_html_document`), `engine.py`, `registry.py`, `feeds.py`, `urls.py`, `metadata.py`, `render.py`, `__init__.py`, and focused M3 tests (no edits to Agent A files).
2. Ran tmp publish via `.venv/bin/python` (`publish_content("W99", …)` → `output/website/`) and inspected `index.html`, `metadata.json`, `source.md`, `sitemap.xml`, `rss.xml`.
3. Ran `.venv/bin/pytest tests/test_static_provider.py -q` (12 passed).
4. Scanned `static_provider.py` imports/body for SEO Engine / Publishing Engine / HTTP / CMS leakage.

---

## Contract area results

### 1. Slug correctness — **PASS**

| Expectation (M2.5 §3) | Evidence |
|----------------------|----------|
| Slug built by Core `urls.build_slug` / `slugify` before provider | `engine.prepare_website_page` → `build_slug(...)`; request carries resolved slug (`engine.py:prepare_website_page`, `engine.py:publish_content`) |
| Provider writes under `{output_dir}/{slug}/` | `StaticWebsiteProvider._write_artifacts` → `page_dir = self.output_dir / request.slug` (`static_provider.py:StaticWebsiteProvider._write_artifacts`) |
| Unsafe / path-like slugs rejected | `StaticWebsiteProvider._validate_output_paths` rejects empty, `..`, `/`, `\`, non-`_SAFE_SLUG` (`static_provider.py:StaticWebsiteProvider._validate_output_paths`) |
| Live tmp check | `slug=hiring-systems` from FM canonical path; page dir `hiring-systems/` |

Provider does **not** re-implement slug ownership; it consumes the frozen URL contract and adds path-safety only. Correct adapter boundary.

---

### 2. Canonical URL contract — **PASS**

| Expectation (M2.5 §3) | Evidence |
|----------------------|----------|
| Canonical from `build_canonical_url` (prefer FM) | `engine.prepare_website_page` → `build_canonical_url` (`engine.py:prepare_website_page`) |
| HTML `<link rel="canonical">` uses metadata canonical | `provider.wrap_html_document` emits `meta.canonical_url` (`provider.py:wrap_html_document`) |
| Feed `link` uses request canonical | `FeedItem(link=request.canonical_url)` (`static_provider.py:StaticWebsiteProvider._write_artifacts`) |
| Live tmp check | `canonical_url=https://workcrew.ai/blog/hiring-systems` in result, `metadata.json`, HTML canonical, sitemap `loc`, RSS item `link` |

---

### 3. Metadata contract — **PASS**

| Expectation (M2.5 §4) | Evidence |
|----------------------|----------|
| `WebsiteMetadata` via `build_metadata` (title/description/OG/Schema.org Article) | Built in `prepare_website_page` (`engine.py:prepare_website_page` + `metadata.py:build_metadata`) |
| Persisted as `metadata.json` via `to_dict()` | `json.dumps(request.metadata.to_dict(), …)` → `{slug}/metadata.json` (`static_provider.py:StaticWebsiteProvider._write_artifacts`) |
| OG + JSON-LD in HTML head | `wrap_html_document` writes OG metas + `schema_org_json()` (`provider.py:wrap_html_document`) |
| Live tmp keys | `title`, `description`, `canonical_url`, `slug`, `primary_keyword`, `og` (`og:type/title/description/url/site_name`), `schema_org` (`@type=Article`) |
| No SEO scoring / keyword optimization | No scoring APIs in provider path; `metadata.py` documents non-ownership |

---

### 4. Rendering contract — **PASS**

| Expectation (M2.5 §5) | Evidence |
|----------------------|----------|
| Markdown→HTML owned by Core `render_markdown` | `prepare_website_page` → `render_markdown(content.markdown_body)` (`engine.py:prepare_website_page`, `render.py:render_markdown`) |
| Provider consumes pre-rendered `request.html`; does not re-convert MD | Writes `wrap_html_document(request)` body from `request.html`; `source.md` is raw `request.markdown` (`static_provider.py:StaticWebsiteProvider._write_artifacts`) |
| Full document wrap: doctype, description, canonical, OG, JSON-LD, `<article>` | `provider.py:wrap_html_document` |
| Live tmp check | DOCTYPE, canonical link, `og:title`, `application/ld+json`, `<article>`, body text present |

---

### 5. Sitemap contract — **PASS**

| Expectation (M2.5 §6) | Evidence |
|----------------------|----------|
| `build_sitemap([FeedItem…])` → URL set + XML (xmlns 0.9) | `static_provider.py:StaticWebsiteProvider._write_artifacts` → `feeds.py:build_sitemap` |
| Persist `sitemap.xml` via `write_feed_artifacts` | `feeds.py:write_feed_artifacts` → `sitemap_path` |
| `loc` = canonical URL | Live: `sitemap locs=['https://workcrew.ai/blog/hiring-systems']` |
| Result details include `sitemap_urls` | `details["sitemap_urls"] = sitemap.urls` (`static_provider.py:StaticWebsiteProvider._write_artifacts`) |
| No deploy / HTTP | Filesystem write only; `external_http=False` |

Note (non-fail): per-publish sitemap is the single current item (same as M2 stub). Matches frozen helper usage; not a multi-page index sprint.

---

### 6. RSS contract — **PASS**

| Expectation (M2.5 §7) | Evidence |
|----------------------|----------|
| `build_rss` → RSS 2.0 + channel defaults | `feeds.py:build_rss`; invoked from `_write_artifacts` |
| Persist `rss.xml` | `write_feed_artifacts` → `rss_path` |
| Item: title/link/description; `guid` = slug, `isPermaLink=false` | Live: title match, link = canonical, `guid=hiring-systems` `isPermaLink=false` |
| `details["rss_item_count"]` | Set to `len(rss.items)` (`static_provider.py:StaticWebsiteProvider._write_artifacts`) |

---

### 7. No SEO Engine business logic leakage — **PASS**

| Check | Result |
|-------|--------|
| Imports in `static_provider.py` | Only `feeds` + `provider` types/helpers — no SEO engine modules |
| Scoring / keyword optimization / rank logic | Absent from provider publish path |
| Site metadata (OG / Schema.org / canonical) | Correctly Website Engine ownership (v2.1 / M2.5); emit-only |
| Docstring “WordPress/Ghost” strings | Negation of scope only; no adapters |

---

### 8. No Publishing Engine business logic leakage — **PASS**

| Check | Result |
|-------|--------|
| `static_provider` ↔ `publishing_engine` | No imports either direction found for Static provider |
| State machine / job mutation | Provider returns `WebsiteProviderResult` only; no status transitions |
| `engine.publish_from_job` | Documents non-mutation of job; Publishing remains owner (`engine.py:publish_from_job`) — orchestration boundary, not leakage into static adapter |
| HTTP / WordPress / Ghost / deploy | Not implemented; `external_http=False` on success and failure paths (`static_provider.py:StaticWebsiteProvider.publish`) |

---

## Artifact surface (tmp publish)

Canonical layout under configurable `output_dir` (default `output/website/`):

```text
{output_dir}/{slug}/index.html
{output_dir}/{slug}/metadata.json
{output_dir}/{slug}/source.md
{output_dir}/sitemap.xml
{output_dir}/rss.xml
```

Observed for `W99` → slug `hiring-systems`: all five artifacts present; `artifact_paths` keys: `html_path`, `metadata_path`, `markdown_path`, `sitemap_path`, `rss_path`. Provider name `static`.

---

## Brief findings

1. **Static provider correctly consumes frozen M2 Core contracts** (slug/canonical via engine + `urls.py`, metadata via `build_metadata`, HTML fragment via `render_markdown`, feeds via `feeds.py`) and persists the M2 stub artifact set under a named production-intent adapter.
2. **Output contracts hold** in tmp publish: slug directory, canonical consistency across HTML/meta/sitemap/RSS, OG + Schema.org Article, RSS guid/slug semantics.
3. **Boundary hygiene holds:** no SEO scoring, no Publishing state machine, no external HTTP/CMS/deploy in the static path.
4. **No critical bugs** found; Agent A files were not modified.
5. **Non-blocking note:** sitemap/RSS remain single-item overwrite per publish (inherited stub semantics). Acceptable under current freeze; multi-URL site index is out of M3 scope.

---

## FINAL

```text
Output Audit: PASS
Contract failures: 0
Brief findings: StaticWebsiteProvider writes correct slug-scoped HTML/MD/metadata plus sitemap/RSS from frozen Core builders; canonical/OG/Schema.org/RSS guid contracts verified in tmp publish; no SEO or Publishing Engine logic leakage; 12/12 M3 provider tests green.
```
