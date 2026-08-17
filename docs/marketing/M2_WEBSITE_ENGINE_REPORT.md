# M2 — Website Engine Core Implementation Report

Date: 2026-08-09  
Canonical repository: `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
Architecture: **v2.1** ([Architecture_ADR_002.md](../architecture/Architecture_ADR_002.md))  
Sprint: M2 — Website Engine Core  
Prerequisite: Publishing Engine v1.0 FROZEN ([M1_5_PUBLISHING_BASELINE.md](M1_5_PUBLISHING_BASELINE.md))

---

## Summary

Website Engine Core delivers **canonical website ownership contracts** only:

- Filesystem content model from `input/{week}/` editorial bundles (`05_Final.md`)
- Slug + canonical URL resolution
- Metadata model (title, description, OpenGraph, Schema.org Article)
- Markdown → HTML rendering contract (stdlib converter; no new dependencies)
- Sitemap + RSS builders (in-memory XML; optional write under `output/website/`)
- Provider-neutral publication interface with in-process **stub** provider
- Publish result shape compatible with Publishing channel adapter fields

**Not implemented (by design):** WordPress/Ghost adapters, social/email/campaign logic, SEO scoring, external HTTP publish, cache invalidation, deploy automation, Publishing API expansion, state-machine changes.

---

## Files created

| Path | Change |
|------|--------|
| `src/tools/website_engine/__init__.py` | **NEW** — public package exports |
| `src/tools/website_engine/content_model.py` | **NEW** — bundle → `WebsiteContent` |
| `src/tools/website_engine/urls.py` | **NEW** — slug + canonical URL |
| `src/tools/website_engine/metadata.py` | **NEW** — metadata / OG / Schema.org |
| `src/tools/website_engine/render.py` | **NEW** — Markdown→HTML contract |
| `src/tools/website_engine/feeds.py` | **NEW** — sitemap + RSS contracts |
| `src/tools/website_engine/provider.py` | **NEW** — provider interface + stub |
| `src/tools/website_engine/publish_result.py` | **NEW** — channel-compatible result |
| `src/tools/website_engine/engine.py` | **NEW** — publish orchestration entrypoints |
| `tests/test_website_engine.py` | **NEW** — focused M2 contract tests |
| `docs/marketing/M2_WEBSITE_ENGINE_REPORT.md` | **NEW** — this report |

**Intentionally untouched:** `src/tools/publishing_engine.py` (`_adapter_website` remains M1 `PLACEHOLDER` so Publishing v1.0 baseline tests stay green), templates, UI routers, Editorial/Content Studio, `runner_api.py`, frontend.

Bridge readiness: `publish_from_job(job) -> dict` returns the frozen channel fields (`ok`, `status`, `channel`, `owner_engine`, `message`) plus `website_engine_invoked` / `rendering_performed`. Wiring into `_adapter_website` is deferred to a coordinated follow-up that also updates Publishing baseline tests.

---

## Architecture compliance (v2.1)

| Rule | Compliance |
|------|------------|
| Website Engine owns canonical website render/URLs/metadata/site publish | **YES** |
| Publishing Engine owns orchestration / state machine only | **YES** — not modified |
| No social / email / campaign ownership | **YES** |
| No SEO Engine scoring / keyword optimization ownership | **YES** — emits metadata contracts only |
| No WordPress/Ghost/external HTTP publish | **YES** — stub provider only |
| No deploy / cache invalidation automation | **YES** |
| Consumes editorial filesystem bundles (not CMS DB) | **YES** — `input/{week}/` |
| Channel result compatible with Publishing adapter shape | **YES** |
| No new paid dependencies | **YES** — stdlib + existing repo paths |

**Architecture Boundary: PASS**

---

## Module map

```
Publishing Engine (orchestration; unchanged PLACEHOLDER adapter)
        │  (future thin bridge)
        ▼
Website Engine
  content_model  → load input/{week}/05_Final.md
  urls           → slug + canonical_url
  metadata       → title/description/OG/Schema.org
  render         → Markdown → HTML
  feeds          → sitemap.xml + rss.xml contracts
  provider       → StubWebsiteProvider (output/website/)
  publish_result → ok/status/channel/owner_engine/message
```

---

## Content source contract

| Artifact | Role |
|----------|------|
| `input/{content_id}/05_Final.md` | Canonical article (front matter + Markdown body) |
| `input/{content_id}/02_SEO_Plan.md` | Optional description hint only |
| Job `bundle` field | Optional override path (`input/{week}`) |

No CMS database invented. No parallel publish queue.

---

## Publish result contract

Required Publishing channel fields:

- `ok` (bool)
- `status` (`RENDERED` on success, `FAILED` on error — future codes beyond M1 `PLACEHOLDER`)
- `channel` = `website`
- `owner_engine` = `Website Engine`
- `message` (string)

Website Engine additions:

- `website_engine_invoked`: `true`
- `rendering_performed`: `true` on success
- `external_api_called`: `false`
- `slug`, `canonical_url`, `content_id`, `artifact_paths`, `metadata`

---

## Acceptance checklist (M2 Core)

| Gate | Status |
|------|--------|
| Canonical content from editorial bundles | **DONE** |
| Provider-neutral interface + in-process stub | **DONE** |
| Slug + canonical URL | **DONE** |
| Metadata (+ OG + Schema.org contracts) | **DONE** |
| Markdown→HTML render contract | **DONE** |
| Sitemap + RSS contracts | **DONE** |
| Channel-compatible publish result | **DONE** |
| Focused tests | **DONE** |
| No WordPress/Ghost/social/campaign/SEO business logic | **DONE** |
| No Publishing API / state-machine string changes | **DONE** |

---

## Tests

Focused suite: `tests/test_website_engine.py`

Covers: content load, slug/canonical, metadata/OG/schema, render, sitemap/RSS, stub publish artifacts, `publish_from_job` channel shape, failure path, optional W01 smoke.

---

## Follow-ups (out of M2 Core)

1. Thin `_adapter_website` bridge calling `publish_from_job` + update Publishing M1 placeholder assertions in a new baseline.
2. Real static-site / WordPress / Ghost providers (still behind `WebsiteProvider`).
3. Deploy hooks / cache invalidation (Website Engine ownership, later sprint).
