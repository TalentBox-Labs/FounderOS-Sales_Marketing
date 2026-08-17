# M2.5 — Website Engine Contract Baseline Freeze

**Baseline name:** Website Engine Core **v1.0**  
**Status:** **FROZEN**  
**Sprint:** M2.5  
**Date:** 2026-08-10  
**Architecture:** v2.1 (ADR-002) — authoritative  
**Implementation report:** [M2_WEBSITE_ENGINE_REPORT.md](M2_WEBSITE_ENGINE_REPORT.md)  
**Publishing prerequisite:** Publishing Engine v1.0 FROZEN ([M1_5_PUBLISHING_BASELINE.md](M1_5_PUBLISHING_BASELINE.md))  
**Publishing channel boundary:** [Publishing_Channel_Interface.md](Publishing_Channel_Interface.md)

**Nature:** Governance certification only.  
**Code / API / DB / runtime / git changes in M2.5:** **NONE** (this document only).

**Rule:** Do not expand interfaces in this baseline. Changes require a new baseline version (e.g. v1.1) and governance note — not silent edits.

---

## Package SoT (frozen file set)

| Path | Role |
|------|------|
| `src/tools/website_engine/__init__.py` | Public package exports (`__all__`) |
| `src/tools/website_engine/content_model.py` | Canonical content model |
| `src/tools/website_engine/provider.py` | Provider-neutral publication interface + stub |
| `src/tools/website_engine/urls.py` | Slug + canonical URL |
| `src/tools/website_engine/metadata.py` | Metadata / OG / Schema.org |
| `src/tools/website_engine/render.py` | Markdown → HTML render contract |
| `src/tools/website_engine/feeds.py` | Sitemap + RSS contracts |
| `src/tools/website_engine/publish_result.py` | Channel-compatible publish result |
| `src/tools/website_engine/engine.py` | Site-publish orchestration entrypoints |

Focused certification tests (reference only; not modified by this freeze): `tests/test_website_engine.py`.

---

## Explicit non-ownership (frozen)

Website Engine Core v1.0 does **NOT** own:

| Domain | Boundary |
|--------|----------|
| Publishing orchestration / state machine | Publishing Engine (`src/tools/publishing_engine.py`); Website Engine does not mutate job state |
| SEO Engine scoring / keyword optimization | Emits metadata contracts only; no scoring |
| Social / Campaign / Email | Out of module |
| WordPress / Ghost HTTP adapters | Stub provider only (`StubWebsiteProvider`); no external HTTP publish |
| Deploy / cache invalidation automation | Not implemented |
| CMS database / parallel publish queue | Consumes `input/{week}/` filesystem bundles only |

**Publishing channel boundary (M1.5):** Channel id `website` remains registered under Publishing Engine. Replacing the Publishing adapter `PLACEHOLDER` with a thin call to `publish_from_job` is a coordinated follow-up outside this freeze. Website Engine already returns channel-compatible fields; Publishing still owns orchestration.

---

## Public exports (frozen)

From `src.tools.website_engine` (`__all__`):

`DEFAULT_SITE_BASE`, `FeedItem`, `RenderResult`, `RssDocument`, `SitemapDocument`, `StubWebsiteProvider`, `WebsiteContent`, `WebsiteMetadata`, `WebsiteProvider`, `WebsitePublishResult`, `build_canonical_url`, `build_metadata`, `build_rss`, `build_sitemap`, `build_slug`, `load_website_content`, `markdown_to_html`, `prepare_website_page`, `publish_content`, `publish_from_job`, `render_markdown`, `slugify`

Supporting types used by the provider contract (module-local, not in `__all__`): `WebsitePublicationRequest`, `WebsiteProviderResult`.

---

## 1. Canonical website content model — FROZEN

**Module:** `src/tools/website_engine/content_model.py`  
**Type:** `WebsiteContent` (frozen dataclass)  
**Loader:** `load_website_content(content_id, *, bundle=None, repo_root=None) -> WebsiteContent`  
**Helpers:** `normalize_content_id`, `resolve_bundle_dir`, `split_front_matter`

### Source artifacts

| Artifact | Role |
|----------|------|
| `input/{content_id}/05_Final.md` | Required canonical article (front matter + Markdown body) |
| `input/{content_id}/02_SEO_Plan.md` | Optional description hint only |
| Job `bundle` field | Optional override path (`input/{week}` or absolute/relative dir) |

`content_id` pattern: `^W\d{2}[A-Z]?$` (normalized uppercase).

### `WebsiteContent` fields

| Field | Type | Responsibility |
|-------|------|----------------|
| `content_id` | str | Normalized week id |
| `bundle_path` | str | Resolved bundle directory (repo-relative when possible) |
| `title` | str | From front matter `article_title` / `title`, else `#` heading, else `content_id` |
| `markdown_body` | str | Body after front-matter split |
| `front_matter` | dict[str, str] | Flat string key/values from YAML-like header |
| `primary_keyword` | str | From front matter |
| `description_hint` | str | First paragraph of body; SEO plan CTA/notes used only if body hint empty |
| `source_final_path` | str | Path to `05_Final.md` |

Serialization: `WebsiteContent.to_dict()`.

---

## 2. Provider-neutral publication interface — FROZEN

**Module:** `src/tools/website_engine/provider.py`  
**Protocol:** `WebsiteProvider` (`name: str`; `publish(request) -> WebsiteProviderResult`)  
**Stub:** `StubWebsiteProvider` (`name = "stub"`; default output `output/website/`)

### `WebsitePublicationRequest` fields

| Field | Type |
|-------|------|
| `content_id` | str |
| `slug` | str |
| `canonical_url` | str |
| `title` | str |
| `html` | str |
| `markdown` | str |
| `metadata` | `WebsiteMetadata` |
| `render` | `RenderResult` |

### `WebsiteProviderResult` fields

| Field | Type | Notes |
|-------|------|-------|
| `ok` | bool | |
| `provider` | str | e.g. `"stub"` |
| `message` | str | |
| `artifact_paths` | dict[str, str] | Stub writes `html_path`, `metadata_path`, `markdown_path`, plus feed paths |
| `external_http` | bool | Stub: always `false` |
| `details` | dict | Stub may include `sitemap_urls`, `rss_item_count` |

**Stub responsibility:** Write `{output_dir}/{slug}/index.html`, `metadata.json`, `source.md`; build and optionally write sitemap/RSS under `output/website/`. No external HTTP, no deploy.

**Orchestration entrypoints** (`engine.py`):

| Function | Signature / return |
|----------|--------------------|
| `prepare_website_page` | `(content, *, site_base=None) -> (slug, canonical_url, WebsiteMetadata, RenderResult)` |
| `publish_content` | `(content_id, *, bundle, repo_root, provider, site_base, output_dir) -> WebsitePublishResult` |
| `publish_from_job` | `(job: dict, *, ...) -> dict` — channel result via `to_channel_result()`; does not mutate job |

---

## 3. Slug / canonical URL contract — FROZEN

**Module:** `src/tools/website_engine/urls.py`  
**Constant:** `DEFAULT_SITE_BASE = "https://workcrew.ai/blog"`

| Function | Responsibility |
|----------|----------------|
| `slugify(text)` | Lowercase; non-alnum → `-`; strip edge `-` |
| `build_slug(*, title, primary_keyword, front_matter)` | Priority: FM `slug` → slug from FM `canonical_url` path → `primary_keyword` → `title`; else `ValueError` |
| `build_canonical_url(slug, *, front_matter, site_base)` | Prefer FM `canonical_url` (rstrip `/`); else `{site_base}/{slug}` |
| `slug_from_canonical_url(canonical_url)` | Trailing path segment helper |

---

## 4. Metadata contract — FROZEN

**Module:** `src/tools/website_engine/metadata.py`  
**Type:** `WebsiteMetadata` (frozen dataclass)  
**Builder:** `build_metadata(*, title, description, canonical_url, slug, primary_keyword="", site_name="WorkCrew") -> WebsiteMetadata`

### Fields

| Field | Type | Notes |
|-------|------|-------|
| `title` | str | |
| `description` | str | Truncated (~160 chars) |
| `canonical_url` | str | |
| `slug` | str | |
| `primary_keyword` | str | Optional; mirrored into Schema.org `keywords` when set |
| `og` | dict[str, str] | `og:type=article`, `og:title`, `og:description`, `og:url`, `og:site_name` |
| `schema_org` | dict | Schema.org `Article` (`@context`, `@type`, `headline`, `description`, `mainEntityOfPage`, `url`) |

Methods: `to_dict()`, `schema_org_json()`.

**Non-ownership:** No SEO scoring or keyword optimization.

---

## 5. Render contract — FROZEN

**Module:** `src/tools/website_engine/render.py`  
**Type:** `RenderResult` (frozen dataclass)  
**Entrypoints:** `render_markdown(markdown) -> RenderResult`; `markdown_to_html(markdown) -> str`

### `RenderResult` fields

| Field | Default / value |
|-------|-----------------|
| `html` | Converted HTML string |
| `content_type` | `text/html; charset=utf-8` |
| `renderer` | `website_engine.stdlib_markdown` |
| `source_format` | `markdown` |

**Scope:** Stdlib subset converter (headings, ul/ol, paragraphs, bold/italic/code/links). No new dependencies. No external HTTP.

---

## 6. Sitemap contract — FROZEN

**Module:** `src/tools/website_engine/feeds.py`  
**Types:** `FeedItem`, `SitemapDocument`  
**Builder:** `build_sitemap(items: Iterable[FeedItem]) -> SitemapDocument`  
**Optional write:** `write_feed_artifacts(..., output_dir) -> {"sitemap_path", "rss_path"}` (default dir `output/website/`)

### `FeedItem` fields

`title`, `link`, `description`, `pub_date`, `slug`

### `SitemapDocument` fields

| Field | Responsibility |
|-------|----------------|
| `urls` | list of `{loc[, lastmod]}` (`lastmod` from `FeedItem.pub_date` when set) |
| `xml` | XML URL set (`xmlns` sitemap 0.9) with declaration |

No deploy; no external HTTP.

---

## 7. RSS contract — FROZEN

**Module:** `src/tools/website_engine/feeds.py`  
**Type:** `RssDocument`  
**Builder:** `build_rss(items, *, title="WorkCrew Blog", link="https://workcrew.ai/blog", description="WorkCrew website feed") -> RssDocument`

### `RssDocument` fields

| Field | Responsibility |
|-------|----------------|
| `title` / `link` / `description` | Channel metadata |
| `items` | Serialized item dicts: `title`, `link`, `description`, `pub_date`, `slug` |
| `xml` | RSS 2.0 XML with declaration |

Per-item: `pubDate` defaults to UTC now (RFC822) when `pub_date` empty; `guid` uses `slug` with `isPermaLink="false"` when slug set.

Optional persistence via `write_feed_artifacts` → `rss.xml` under `output/website/`.

---

## 8. Website publish result contract — FROZEN

**Module:** `src/tools/website_engine/publish_result.py`  
**Type:** `WebsitePublishResult`  
**Channel constants:** `CHANNEL_WEBSITE = "website"`; `OWNER_ENGINE = "Website Engine"`  
**Statuses:** `RENDERED` (success); `FAILED` (error)  
**Helpers:** `success_result(...)`, `failure_result(...)`  
**Serialization:** `to_channel_result() -> dict` (Publishing adapter boundary shape)

### Required Publishing channel fields

| Field | Type / value |
|-------|----------------|
| `ok` | bool |
| `status` | `RENDERED` \| `FAILED` |
| `channel` | `website` |
| `owner_engine` | `Website Engine` |
| `message` | str |

### Website Engine additions

| Field | Contract |
|-------|----------|
| `website_engine_invoked` | `true` |
| `rendering_performed` | `true` on success; `false` on failure |
| `external_api_called` | `false` |
| `slug`, `canonical_url`, `content_id` | Present when set (omitted from dict if empty) |
| `artifact_paths`, `metadata`, `details` | Present when non-empty |

Compatible with Publishing Channel Interface required fields (`ok`, `status`, `channel`, `owner_engine`, `message`). Publishing M1.5 website adapter remains `PLACEHOLDER` until a coordinated bridge; this freeze documents Website Engine’s side of the contract only.

---

## Architecture compliance (v2.1)

| Rule | Status |
|------|--------|
| Website Engine owns canonical website render / URLs / metadata / site publish contracts | **FROZEN** |
| Publishing Engine owns orchestration / state machine | **FROZEN** (unchanged by Website Engine) |
| No social / email / campaign ownership | **FROZEN** |
| No SEO Engine scoring ownership | **FROZEN** |
| No WordPress / Ghost / external HTTP publish | **FROZEN** (stub only) |
| No deploy / cache invalidation | **FROZEN** |
| Filesystem editorial bundles as content source | **FROZEN** |
| Channel-compatible publish result | **FROZEN** |
| Interfaces not expanded beyond M2 Core | **FROZEN** |

**Architecture Boundary:** PASS  
**Website Engine Core v1.0:** **FROZEN**
