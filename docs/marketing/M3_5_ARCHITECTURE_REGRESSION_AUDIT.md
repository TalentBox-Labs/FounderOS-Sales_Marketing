# M3.5 — Architecture Regression & Boundary Audit

**Status:** COMPLETE  
**Date:** 2026-08-10  
**Agent:** C — Architecture / Regression Audit (GOVERNANCE)  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
**Architecture:** v2.1 (ADR-002)  
**Prior audits:** [M3_ARCHITECTURE_REGRESSION_AUDIT.md](M3_ARCHITECTURE_REGRESSION_AUDIT.md), [M2_5_ARCHITECTURE_REGRESSION_AUDIT.md](M2_5_ARCHITECTURE_REGRESSION_AUDIT.md)  
**Implementation under audit:** Static Website Provider freeze (M3.5) + M1/M2 contract compatibility  
**Static baseline:** [M3_5_STATIC_PROVIDER_BASELINE.md](M3_5_STATIC_PROVIDER_BASELINE.md)  
**Deployment readiness (reference):** [M3_5_M4_DEPLOYMENT_READINESS.md](M3_5_M4_DEPLOYMENT_READINESS.md)

**Audit mode:** Read-only code verification + test runs.  
**Write scope:** This document only. Application code was not modified.

---

## Final verdict

| Gate | Result |
|------|--------|
| **Architecture** | **PASS** |
| **New Regressions** | **0** |
| **Boundary Violations** | **0** |
| Publishing website adapter | **PLACEHOLDER retained** (M1 compatible) |
| WordPress / Ghost / deploy / hosting | **NONE** in code |
| Social / Campaign / SEO scoring leaks | **NONE** |
| DB / Alembic changes | **NONE** |
| External HTTP publish | **NONE** (`external_http=False`) |
| M1 / M2 contracts | **COMPATIBLE** |

```
Architecture: PASS
New Regressions: 0
Boundary Violations: 0
Focused: 72/72
Full: 320/332; 8 failed; 4 errors
```

---

## 1. Scope verified

| Item | Evidence |
|------|----------|
| Publishing Engine orchestration-only | `src/tools/publishing_engine.py` |
| Website Engine package + static adapter | `src/tools/website_engine/` (11 modules) |
| Publishing API surface | `runner_api_routers/publishing.py` |
| Focused suites | static / website / publishing / editorial / content_studio_ui |
| Full suite | `tests/` (332 collected) |
| No app-code writes by Agent C | Confirmed — audit doc only |

---

## 2. Architecture boundary checks (10)

### 2.1 Publishing Engine orchestration-only — PASS

Verified in `src/tools/publishing_engine.py`:

- Module docstring: orchestration ONLY; excludes website render, social APIs, email, campaigns, Celery/n8n, scheduling, AI publishing.
- Imports: stdlib + `editorial_approval` + `runtime_paths` only — **no** `src.tools.website_engine`.
- `_adapter_website` remains M1 PLACEHOLDER:
  - `status: "PLACEHOLDER"`
  - `website_engine_invoked: False`
  - `rendering_performed: False`
- Job flags: `orchestration_only: True`, `website_engine: False`, `social_engine: False`, `campaign_engine: False`.
- `runner_api_routers/publishing.py`: orchestration endpoints only; exposes `website_engine: False`; does not import Website Engine.

Bridge readiness (`publish_from_job`) remains inside Website Engine only. Not wired into `_adapter_website`. Not a boundary violation.

### 2.2 Website Engine owns website behavior — PASS

Website Engine continues to own site-specific concerns:

| Concern | Module |
|---------|--------|
| Bundle → content model | `content_model.py` |
| Slug + canonical URL | `urls.py` |
| Title/description/OG/Schema.org | `metadata.py` |
| Markdown → HTML | `render.py` |
| Sitemap + RSS | `feeds.py` |
| Provider protocol + stub | `provider.py` |
| Channel-compatible result | `publish_result.py` |
| Entrypoints (`publish_content`, `publish_from_job`) | `engine.py` |
| Named registry (`static`, `stub`) | `registry.py` |
| Production-intent local adapter | `static_provider.py` |

Application consumers of `src.tools.website_engine` outside the package: **none** (tests only). Publishing does not call Website Engine.

### 2.3 Static is adapter only — PASS

`StaticWebsiteProvider` (`name="static"`) responsibilities only:

- Validate request fields / safe slug
- Write `output/website/{slug}/index.html`, `source.md`, `metadata.json`
- Write site-level `sitemap.xml` / `rss.xml` via existing `feeds.py`
- Always `external_http=False`

Static does **not** own: Publishing state machine, editorial approval, slug/URL builders, Markdown→HTML conversion, SEO scoring, social/campaign, deploy/hosting, or DB.

Default provider name remains `static` (`engine.py: DEFAULT_PROVIDER_NAME`); stub retained for M2 backward compatibility (`list_providers()` → `['static', 'stub']`).

### 2.4 No deploy / hosting leaks — PASS

Across `website_engine/` and `publishing_engine.py`:

- Artifacts are local filesystem writes under configured `output_dir` / `output/website/` only.
- No CDN, cache invalidation, SSH/rsync, container registry, or hosting-provider clients.
- Docstrings and result messages explicitly state “no deploy.”

### 2.5 No WordPress / Ghost assumptions — PASS

- No WordPress/Ghost SDK, API client, or registered provider.
- Registry: `static` + `stub` only; `get_provider("wordpress")` raises `KeyError` (`tests/test_static_provider.py`).
- Mentions of WordPress/Ghost appear only as **exclusion / future** documentation strings (protocol remains provider-neutral).

### 2.6 No Social Engine leak — PASS

- Publishing social adapters (`linkedin` / `twitter` / `instagram`) remain `NOT_IMPLEMENTED` with `external_api_called: False`.
- `website_engine` contains no social API delivery, OAuth, or post scheduling.
- Job flag `social_engine: False` unchanged.

### 2.7 No Campaign Engine leak — PASS

- No campaign orchestration, drip, or attribution logic in Publishing or Website Engine.
- Job flag `campaign_engine: False` unchanged.
- Website Engine package docstring excludes campaigns.

### 2.8 No SEO scoring leak — PASS

- Website Engine emits / persists WebsiteMetadata (title, description, OG, Schema.org Article) only.
- No SEO scoring, keyword-density, ranking, or Lighthouse implementation under `website_engine/` (ripgrep: no matches).
- Publishing PLACEHOLDER message still disclaims Markdown/HTML/SEO/deploy work at the orchestration layer.

### 2.9 No DB / Alembic — PASS

- `alembic.ini` present; **`alembic/` directory absent** (no revisions).
- Website Engine / static provider / publishing engine: no SQLAlchemy models, sessions, or schema migrations.
- Artifacts are filesystem-only (`output/website/`, `output/publishing/`).

### 2.10 No external HTTP — PASS

- Website Engine imports: stdlib + in-package modules + `runtime_paths` only.
- Sole `urllib` usage: `urllib.parse.urlparse` in `urls.py` (parse-only; not an HTTP client).
- No `httpx` / `requests` / `aiohttp` / `urllib.request` publish clients in `website_engine/`.
- Static + stub providers set `external_http=False` on success and failure paths.
- `WebsitePublishResult.external_api_called` remains `False` on success/failure helpers.
- Requirements files unchanged by this audit sprint (no new network deps introduced for M3/M3.5).

### Contract compatibility (M1 / M2) — PASS

| Contract | Status |
|----------|--------|
| M1 Publishing PLACEHOLDER website adapter shape | Unchanged (`ok`, `status=PLACEHOLDER`, channel/owner flags, `website_engine_invoked=False`) |
| M1 social/newsletter `NOT_IMPLEMENTED` | Unchanged |
| M2 Core exports (`publish_from_job`, metadata/render/feeds/urls) | Retained; stub provider still registered |
| M2 channel-compatible `to_channel_result()` fields | Retained (`ok`, `status`, `channel`, `owner_engine`, `message`, invoke/render flags, `external_api_called`) |
| M3 static default + registry | Compatible with M2 stub; Publishing still not bridged |

M3.5 freeze adds **no** code changes; contracts remain those certified at M3.

---

## 3. Test results

**Environment:**

```bash
SECRET_KEY=test-secret-m35-freeze HEARTBEAT_ENABLED=0
.venv/bin/python -m pytest
```

### 3.1 Focused suites

| Suite | Result |
|-------|--------|
| `tests/test_static_provider.py` | **12 passed** |
| `tests/test_website_engine.py` | **12 passed** |
| `tests/test_publishing_engine.py` | **16 passed** |
| `tests/test_editorial_approval.py` | **19 passed** |
| `tests/test_content_studio_ui.py` | **13 passed** |
| **Combined focused** | **72 passed / 72 total** |

### 3.2 Full suite (`tests/`)

| Metric | Baseline (M3) | M3.5 audit run | Delta |
|--------|---------------|----------------|-------|
| Passed | 320 | **320** | 0 |
| Failed | 8 | **8** | 0 |
| Errors | 4 | **4** | 0 |
| Total | 332 | **332** | 0 |
| New regressions | 0 | **0** | — |

**Full line:** `8 failed, 320 passed, 26 warnings, 4 errors in 17.98s`

### 3.3 Failing / error test IDs (historical — exact ID match)

**FAILED (8)** — crews_unit (3) + utilities_unit (5):

1. `tests/test_crews_unit.py::TestQACrew::test_qa_crew_validates_output_format`
2. `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_validates_output`
3. `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_rejects_output_without_frontmatter`
4. `tests/test_utilities_unit.py::TestFileOperations::test_read_file_returns_content`
5. `tests/test_utilities_unit.py::TestFileOperations::test_read_file_raises_on_missing_file`
6. `tests/test_utilities_unit.py::TestFileOperations::test_save_file_creates_directories`
7. `tests/test_utilities_unit.py::TestFileOperations::test_save_file_overwrites_existing`
8. `tests/test_utilities_unit.py::TestDataValidation::test_markdown_structure_validation`

**ERROR (4)** — orchestration_api (2) + prospecting_ui (2); setup fails with Postgres auth (`psycopg2.OperationalError: fe_sendauth: no password supplied`):

1. `tests/test_orchestration_api.py::test_orchestration_plan_endpoint_returns_strategy`
2. `tests/test_orchestration_api.py::test_orchestration_run_with_mocked_backend_and_audit_persistence`
3. `tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads`
4. `tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score`

**New failing tests vs historical known set:** **none**.  
Historical distribution unchanged: crews_unit 3, utilities_unit 5, orchestration_api 2 err, prospecting_ui 2 err.

---

## 4. Checklist summary

| # | Check | Verdict |
|---|-------|---------|
| 1 | Publishing Engine orchestration-only | **PASS** |
| 2 | Website Engine owns website behavior | **PASS** |
| 3 | Static is adapter only | **PASS** |
| 4 | No deploy / hosting leaks | **PASS** |
| 5 | No WordPress / Ghost assumptions | **PASS** |
| 6 | No Social Engine leak | **PASS** |
| 7 | No Campaign Engine leak | **PASS** |
| 8 | No SEO scoring leak | **PASS** |
| 9 | No DB / Alembic | **PASS** |
| 10 | No external HTTP | **PASS** |
| — | M1 / M2 contracts compatible | **PASS** |
| — | Focused suites green | **PASS** (72/72) |
| — | Full suite — zero new regressions | **PASS** (320/332; 8 failed; 4 errors) |

---

## 5. One-line certification

**M3.5 Static Provider freeze is architecture-compliant: Publishing remains PLACEHOLDER-orchestrated; Website Engine owns site behavior with filesystem-only static adapter; no deploy/hosting/WP/Ghost/Social/Campaign/SEO/DB/HTTP leaks; M1/M2 contracts intact; 0 new regressions (72/72 focused; 320/332 full).**
