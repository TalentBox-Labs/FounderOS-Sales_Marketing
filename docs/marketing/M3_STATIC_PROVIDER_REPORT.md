# M3 — Static Website Provider Report

**Status:** IMPLEMENTED  
**Sprint:** M3 (Static Provider Builder)  
**Date:** 2026-08-10  
**Architecture:** v2.1 frozen · Website Engine Core v1.0 frozen  
**Prerequisite readiness:** [M2_5_WEBSITE_PROVIDER_READINESS.md](M2_5_WEBSITE_PROVIDER_READINESS.md) (recommended: **STATIC**)

---

## 1. Mission outcome

First real Website Engine provider adapter: **local/static publishing target**.

| Item | Value |
|------|-------|
| Provider class | `StaticWebsiteProvider` |
| Registry name | `static` |
| Default for `publish_content` | `static` |
| External HTTP | **No** (`external_http=False`) |
| WordPress / Ghost / social / deploy / DB | **Not implemented** (by design) |

---

## 2. Files delivered

| Path | Role |
|------|------|
| `src/tools/website_engine/static_provider.py` | **NEW** — production-intent static adapter |
| `src/tools/website_engine/registry.py` | **NEW** — `register_provider` / `get_provider` / `list_providers` |
| `src/tools/website_engine/provider.py` | Minimal — export shared `wrap_html_document` / `escape_html_attr`; keep Protocol + Stub |
| `src/tools/website_engine/engine.py` | Default provider → static; optional `provider_name` |
| `src/tools/website_engine/__init__.py` | Export `StaticWebsiteProvider` + registry helpers |
| `tests/test_static_provider.py` | **NEW** — focused M3 tests |
| `docs/marketing/M3_STATIC_PROVIDER_REPORT.md` | This report |

**Not touched:** `publishing_engine.py`, templates, runner_api, editorial, content_studio.

---

## 3. Artifact contract

Canonical root: `output/website/` (ctor-configurable).

Per slug (`{output_dir}/{slug}/`):

| Artifact | File |
|----------|------|
| Wrapped HTML document | `index.html` |
| Source Markdown | `source.md` |
| Metadata (JSON) | `metadata.json` |

Site-level feeds (via existing `feeds.py` helpers):

| Artifact | File |
|----------|------|
| Sitemap | `sitemap.xml` |
| RSS | `rss.xml` |

Re-publish of the same slug **overwrites** page artifacts idempotently.

---

## 4. Safety / errors

Expected failures return `WebsiteProviderResult(ok=False)` without leaking uncaught exceptions:

- Missing required fields (`content_id`, `slug`, `canonical_url`, `title`, `html`, `markdown`, `metadata`)
- Invalid / path-like slugs (`..`, `/`, `\`, unsafe characters)
- Filesystem write failures (`OSError`)

`external_http` remains `False` on success and failure paths.

---

## 5. Registry & defaults

```text
list_providers() → ["static", "stub", ...]
get_provider("static") → StaticWebsiteProvider
get_provider("stub")   → StubWebsiteProvider   # M2 backward compat
```

`publish_content(...)` resolution order:

1. Explicit `provider=` instance  
2. Else `provider_name=` via registry  
3. Else `StaticWebsiteProvider` (default)

`StubWebsiteProvider` (`name="stub"`) retained for M2 tests and explicit opt-in.

---

## 6. Shared helpers

`wrap_html_document` / `escape_html_attr` live in `provider.py` and are reused by Stub + Static to avoid HTML-document duplication. Private aliases `_wrap_html_document` / `_esc` kept for compatibility.

---

## 7. Test focus (M3)

`tests/test_static_provider.py` covers:

- Register / resolve `static` (and stub compat)
- Publish artifacts exist (HTML/MD/metadata + sitemap/RSS)
- Idempotent overwrite of same slug
- Publish result fields + `external_http=False`
- Error paths (missing fields, unsafe slug, write failure)
- Engine default + `provider_name` wiring

M2 suite `tests/test_website_engine.py` remains green with explicit `StubWebsiteProvider` usage unchanged.

---

## 8. Explicit non-goals (M3)

- WordPress / Ghost HTTP adapters
- Deploy hooks / CDN sync
- Network calls of any kind
- Database-backed CMS
- Changes to Publishing Engine state machine

---

## 9. Attestation

| Item | Value |
|------|-------|
| Recommended provider (M2.5) | STATIC |
| Implemented provider | `StaticWebsiteProvider` (`static`) |
| Paid SaaS assumed | **NO** |
| Confidence | **HIGH** — promotes M2 stub artifact surface behind a named production-intent adapter |
