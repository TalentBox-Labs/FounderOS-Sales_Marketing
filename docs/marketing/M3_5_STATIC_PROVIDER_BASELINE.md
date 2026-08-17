# M3.5 — Static Website Provider Contract Baseline Freeze

**Baseline name:** Static Website Provider **v1.0**  
**Status:** **FROZEN**  
**Sprint:** M3.5  
**Date:** 2026-08-10  
**Architecture:** v2.1 (ADR-002) — authoritative  
**Prerequisite Core baseline:** Website Engine Core v1.0 FROZEN ([M2_5_WEBSITE_ENGINE_BASELINE.md](M2_5_WEBSITE_ENGINE_BASELINE.md))  
**Implementation report:** [M3_STATIC_PROVIDER_REPORT.md](M3_STATIC_PROVIDER_REPORT.md)  
**Output audit (reference):** [M3_STATIC_OUTPUT_AUDIT.md](M3_STATIC_OUTPUT_AUDIT.md)

**Nature:** Governance certification only.  
**Code / API / DB / runtime / git changes in M3.5:** **NONE** (this document only).

**Rule:** Do not expand Static Provider functionality in this baseline. Changes require a new baseline version (e.g. v1.1) and governance note — not silent edits.

---

## Package SoT (frozen file set)

| Path | Role |
|------|------|
| `src/tools/website_engine/static_provider.py` | `StaticWebsiteProvider` adapter (production-intent local/static target) |
| `src/tools/website_engine/registry.py` | Provider name → factory registry (`static`, `stub` defaults) |
| `src/tools/website_engine/provider.py` | `WebsiteProvider` Protocol, `WebsitePublicationRequest`, `WebsiteProviderResult`, `wrap_html_document` |
| `src/tools/website_engine/engine.py` | Orchestration default provider name `static`; resolves via registry |
| `src/tools/website_engine/publish_result.py` | Channel-compatible `WebsitePublishResult` (engine boundary above provider) |
| `src/tools/website_engine/feeds.py` | Sitemap/RSS builders + `write_feed_artifacts` (consumed, not re-owned) |
| `src/tools/website_engine/metadata.py` | `WebsiteMetadata.to_dict()` persistence shape (consumed, not re-owned) |

Focused certification tests (reference only; not modified by this freeze): `tests/test_static_provider.py`.

**Inherited Core (M2.5) — not re-frozen here:** content model, slug/canonical builders (`urls.py`), Markdown render (`render.py`), metadata builders, feed document shapes. Static Provider consumes those contracts; it does not redefine them.

---

## Explicit non-ownership / non-goals (frozen)

Static Website Provider v1.0 does **NOT**:

| Domain | Boundary |
|--------|----------|
| WordPress / Ghost / SaaS HTTP adapters | Not registered; no network publish |
| Deploy / CDN / cache invalidation | Filesystem write only |
| Multi-page sitemap/RSS index across prior publishes | Each successful publish rebuilds feeds from the **current** request item only |
| Publishing Engine state machine | Does not mutate jobs; engine returns channel-compatible results only |
| SEO Engine scoring / keyword optimization | Emits / persists WebsiteMetadata only |
| Slug / URL ownership | Consumes pre-built `slug` / `canonical_url` on the request; adds path-safety validation only |
| Markdown → HTML rendering | Consumes pre-rendered `request.html`; writes raw `request.markdown` to `source.md` |
| Transactional rollback / cleanup of partial writes | See § Rollback boundary |
| Database / CMS storage | Local filesystem under configured `output_dir` only |

`external_http` / `external_api_called` remain **false** on all Static Provider and Website Engine success/failure paths covered by this baseline.

---

## 1. Provider registration — FROZEN

**Module:** `src/tools/website_engine/registry.py`

| API | Contract |
|-----|----------|
| `register_provider(name, factory)` | Key = `name.strip().lower()`; empty name → `ValueError`; replaces existing key |
| `list_providers()` | Sorted registered names |
| `get_provider(name, *, output_dir=None)` | Instantiates factory; unknown name → `KeyError` with known list |
| Factory type | `Callable[[Path \| None], WebsiteProvider]` |

### Default registrations (module import)

| Name | Factory product |
|------|-----------------|
| `static` | `StaticWebsiteProvider(output_dir=…)` |
| `stub` | `StubWebsiteProvider(output_dir=…)` (M2 backward compatibility) |

Defaults are ensured once via `_ensure_defaults()` at import. No WordPress/Ghost/network adapters are registered.

### Engine resolution order (`engine._resolve_provider` / `publish_content`)

1. Explicit `provider=` instance (bypass registry)  
2. Else `provider_name=` (or job `provider` in `publish_from_job`) via `get_provider`  
3. Else `DEFAULT_PROVIDER_NAME = "static"`

Unknown `provider_name` → engine `failure_result` (`status=FAILED`), not an uncaught exception.

**Class identity:** `StaticWebsiteProvider.name = "static"`.

---

## 2. Accepted input contract — FROZEN

**Type:** `WebsitePublicationRequest` (`provider.py`)

| Field | Type | Static validation |
|-------|------|-------------------|
| `content_id` | str | Required; non-empty after strip |
| `slug` | str | Required; non-empty after strip; see § Slug/path |
| `canonical_url` | str | Required; non-empty after strip |
| `title` | str | Required; non-empty after strip |
| `html` | str | Required; not `None`; non-empty after `str(html).strip()` |
| `markdown` | str | Required; not `None` (empty string allowed) |
| `metadata` | `WebsiteMetadata` | Required; not `None` |
| `render` | `RenderResult` | Present on dataclass; **not** validated by Static Provider |

`request is None` → error message: `Static provider requires a WebsitePublicationRequest`.

Missing fields → `WebsiteProviderResult(ok=False, …)` with message  
`Static provider missing required fields: …` (comma-separated field names). No filesystem writes on validation failure.

Static Provider does **not** load bundles, build slugs, render Markdown, or construct metadata — those remain Website Engine Core / `engine.prepare_website_page` responsibilities.

---

## 3. Generated output contract — FROZEN

On successful `StaticWebsiteProvider.publish`:

### Per-page artifacts (`{output_dir}/{slug}/`)

| Key in `artifact_paths` | File | Content |
|-------------------------|------|---------|
| `html_path` | `index.html` | Full HTML document from `wrap_html_document(request)` |
| `metadata_path` | `metadata.json` | `json.dumps(request.metadata.to_dict(), indent=2) + "\n"` |
| `markdown_path` | `source.md` | Raw `request.markdown` (UTF-8) |

### Site-level feed artifacts (`{output_dir}/`)

| Key in `artifact_paths` | File | Builder |
|-------------------------|------|---------|
| `sitemap_path` | `sitemap.xml` | `build_sitemap([FeedItem…])` → `write_feed_artifacts` |
| `rss_path` | `rss.xml` | `build_rss([FeedItem…])` → `write_feed_artifacts` |

**FeedItem mapping (Static Provider):**

| FeedItem field | Source |
|----------------|--------|
| `title` | `request.title` |
| `link` | `request.canonical_url` |
| `description` | `request.metadata.description` |
| `slug` | `request.slug` |
| `pub_date` | omitted (empty; RSS helper supplies UTC-now when writing item) |

**Success `details` (provider):**

| Key | Value |
|-----|-------|
| `sitemap_urls` | `sitemap.urls` from this publish |
| `rss_item_count` | `len(rss.items)` (typically `1`) |
| `output_dir` | `str(self.output_dir)` |

Encoding for all text writes: **UTF-8**.

---

## 4. Canonical output directory — FROZEN

| Item | Value |
|------|-------|
| Default | `REPO_ROOT / "output" / "website"` (`DEFAULT_SITE_OUTPUT` in `provider.py`) |
| Constructor | `StaticWebsiteProvider(output_dir: Path \| str \| None = None)` |
| Registry / engine | `get_provider(..., output_dir=…)` / `publish_content(..., output_dir=…)` pass through to factory |
| Creation | `page_dir.mkdir(parents=True, exist_ok=True)`; feeds `output_dir.mkdir(parents=True, exist_ok=True)` |

No deploy step. Artifacts are local filesystem only.

---

## 5. Slug / path behavior — FROZEN

Static Provider validates `request.slug` before any write (`_validate_output_paths`):

| Rule | Behavior |
|------|----------|
| Empty / whitespace | Reject |
| `.` or `..` as slug, or `..` substring | Reject (`unsafe slug`) |
| `/` or `\` in slug | Reject (`path-like slug`) |
| Character set | Must match `^[a-zA-Z0-9][a-zA-Z0-9._-]{0,200}$` else reject (`invalid slug`) |
| Escape check | `(output_dir / slug).resolve()` must be `relative_to(output_dir.resolve())`; else reject |

Rejected slugs → `ok=False`, `details` include `error` and `slug`; **no writes**.

Page directory layout: `{output_dir}/{slug}/` — slug is a single path segment, not a nested path.

Slug **generation** remains Core `urls.build_slug` (M2.5 §3). Static Provider only enforces filesystem safety on the received value.

---

## 6. HTML / Markdown emission — FROZEN

### HTML (`index.html`)

Uses shared `wrap_html_document(request)` (`provider.py`):

- `<!DOCTYPE html>`, `<html lang="en">`
- Head: charset, `<title>` from `metadata.title`, meta description, canonical link from `metadata.canonical_url`, OG tags from `metadata.og`, JSON-LD from `metadata.schema_org_json()`
- Body: `<article>` wrapping `request.html` (pre-rendered fragment)
- Attribute escaping via `escape_html_attr`

Static Provider does **not** call `render_markdown` / `markdown_to_html`.

### Markdown (`source.md`)

Writes `request.markdown` verbatim (UTF-8). No re-serialization, no front-matter injection.

---

## 7. Metadata propagation — FROZEN

| Surface | Behavior |
|---------|----------|
| `metadata.json` | Full `WebsiteMetadata.to_dict()`: `title`, `description`, `canonical_url`, `slug`, `primary_keyword`, `og`, `schema_org` |
| HTML head | Title, description, canonical, OG properties, Schema.org JSON-LD (from same metadata object) |
| Feeds | Description → RSS/sitemap item description; link → canonical URL |
| Engine success result | `WebsitePublishResult.metadata = metadata.to_dict()` when orchestration succeeds |

No SEO scoring, keyword optimization, or mutation of metadata inside the Static Provider.

---

## 8. Publish result contract — FROZEN

### Provider layer — `WebsiteProviderResult`

Returned by `StaticWebsiteProvider.publish`:

| Field | Success | Failure |
|-------|---------|---------|
| `ok` | `True` | `False` |
| `provider` | `"static"` | `"static"` |
| `message` | Wrote artifacts for `{content_id}` (no external HTTP, no deploy) | Validation / write / rejection message |
| `artifact_paths` | `html_path`, `metadata_path`, `markdown_path`, `sitemap_path`, `rss_path` | `{}` (default) |
| `external_http` | `False` | `False` |
| `details` | `sitemap_urls`, `rss_item_count`, `output_dir` | `error` [+ `slug` when applicable] |

Serialization: `to_dict()` mirrors the fields above.

### Engine layer — `WebsitePublishResult` / channel dict

When `publish_content` / `publish_from_job` use Static Provider:

| Outcome | Contract |
|---------|----------|
| Provider `ok=True` | `success_result` → `status=RENDERED`, `rendering_performed=True`, `external_api_called=False`, `artifact_paths` from provider, `details.provider` = provider `to_dict()` |
| Provider `ok=False` | `failure_result` → `status=FAILED`, `rendering_performed=False`, `details` = provider `to_dict()` |
| Channel shape | `to_channel_result()` per M2.5 §8 (`channel=website`, `owner_engine=Website Engine`) |

Publishing Engine remains owner of job state transitions; this baseline freezes Website Engine / Static Provider result shapes only.

---

## 9. Idempotency / overwrite rules — FROZEN

| Artifact | Re-publish same slug |
|----------|----------------------|
| `{slug}/index.html` | Overwritten in place (`write_text`) |
| `{slug}/metadata.json` | Overwritten in place |
| `{slug}/source.md` | Overwritten in place |
| `sitemap.xml` / `rss.xml` | Overwritten with feeds built from **this** request only |

- Directory creation is idempotent (`exist_ok=True`).
- Same slug → same page paths; content reflects the latest successful publish.
- Prior distinct slugs under `output_dir` are **not** deleted by a new publish.
- Site feeds are **not** a cumulative multi-page index in v1.0 (same behavior as M2 stub).

---

## 10. Error behavior — FROZEN

Expected failures return `WebsiteProviderResult(ok=False)` without leaking uncaught exceptions from `publish`:

| Class | Trigger | Message pattern |
|-------|---------|-----------------|
| Request validation | Missing/empty required fields; `request is None` | `Static provider missing required fields: …` / requires request |
| Path validation | Unsafe / path-like / invalid slug; resolve escape | `Static provider rejected …` |
| `OSError` during write | Filesystem failures | `Static provider write failed: {exc}` |
| `TypeError` / `ValueError` during write path | Rejected publication | `Static provider rejected publication: {exc}` |

Invariants on all Static Provider error returns:

- `provider == "static"`
- `external_http is False`
- `details` includes `error` (and `slug` when path/write related)

Validation failures occur **before** page/feed writes. Engine maps provider failures to `WebsitePublishResult(status=FAILED)` as above.

---

## 11. Rollback boundary — FROZEN

| Phase | Guarantee |
|-------|-----------|
| Pre-write validation failure | **No** artifacts written for that call |
| Mid-write `OSError` / reject after partial `write_text` | **No transactional rollback**; already-written files may remain; subsequent retry overwrites paths that exist |
| Success then later failure of a different publish | Prior successful page dirs retained; feed files reflect last successful feed write |
| Deploy / remote undo | **Out of scope** — no remote publish exists to roll back |

v1.0 explicitly does **not** provide: temp-dir swap, atomic rename of the page directory, deletion of partial artifacts, or multi-file transactions.

---

## Architecture compliance (v2.1)

| Rule | Status |
|------|--------|
| Static provider is local/filesystem only | **FROZEN** |
| Named registry provider `static`; engine default | **FROZEN** |
| Consumes Core publication request; does not own render/slug builders | **FROZEN** |
| Artifact set: HTML + MD + metadata + sitemap + RSS | **FROZEN** |
| `external_http=False` always | **FROZEN** |
| No WordPress / Ghost / deploy / DB | **FROZEN** |
| Idempotent overwrite of same slug; feeds single-item rebuild | **FROZEN** |
| Safe errors via `WebsiteProviderResult` / engine `FAILED` | **FROZEN** |
| No transactional rollback beyond “no write on validation failure” | **FROZEN** |
| Interfaces not expanded beyond M3 Static Provider | **FROZEN** |

**Architecture Boundary:** PASS  
**Static Website Provider v1.0:** **FROZEN**

---

## Final certification

| Item | Value |
|------|-------|
| Baseline name | Static Website Provider v1.0 FROZEN |
| Owned file (this sprint) | `docs/marketing/M3_5_STATIC_PROVIDER_BASELINE.md` |
| Application code changes | **NONE** |
| Functionality expansion | **NONE** (document-only freeze) |

**Static Provider Contract: FROZEN**
