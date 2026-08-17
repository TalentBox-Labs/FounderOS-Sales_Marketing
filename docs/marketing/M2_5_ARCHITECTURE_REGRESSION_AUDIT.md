# M2.5 — Architecture Regression & Boundary Audit

**Status:** COMPLETE  
**Date:** 2026-08-10  
**Agent:** C — Regression & Boundary Audit (GOVERNANCE)  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
**Architecture:** v2.1 (ADR-002)  
**Prior audit:** [M2_ARCHITECTURE_REGRESSION_AUDIT.md](M2_ARCHITECTURE_REGRESSION_AUDIT.md)  
**Implementation under audit:** Website Engine Core + Publishing Engine orchestration (M2 freeze)  
**Publishing baseline:** [M1_5_PUBLISHING_BASELINE.md](M1_5_PUBLISHING_BASELINE.md) / [Publishing_API_Contract.md](Publishing_API_Contract.md)

**Audit mode:** Read-only code verification + test runs.  
**Write scope:** This document only. Application code was not modified.

---

## Final verdict

| Gate | Result |
|------|--------|
| **Architecture** | **PASS** |
| **New Regressions** | **0** |
| **Boundary Violations** | **0** |
| Publishing API contract change | **NONE** |
| DB / Alembic changes from M2 | **NONE** |
| External HTTP publish dependency | **NONE** |
| SEO scoring leak into website_engine | **NONE** |
| Social / Campaign logic in M2 engines | **NONE** |

---

## 1. Scope verified

| Item | Evidence |
|------|----------|
| Publishing Engine orchestration-only | `src/tools/publishing_engine.py` |
| Website Engine package | `src/tools/website_engine/` (9 modules) |
| Publishing API surface | `runner_api_routers/publishing.py` + `docs/marketing/Publishing_API_Contract.md` |
| Focused suites | website / publishing / editorial / content_studio_ui |
| Full suite | `tests/` |
| No app-code writes by Agent C | Confirmed — audit doc only |

---

## 2. Architecture boundary checks

### 2.1 Publishing Engine orchestration-only — PASS

Verified in `src/tools/publishing_engine.py`:

- Module docstring declares orchestration-only ownership (jobs, queue, state, audit, channel registry, human requester gate).
- Explicitly excludes website render, social APIs, email, campaigns, Celery/n8n, scheduling, AI publishing.
- Imports: stdlib + `editorial_approval` + `runtime_paths` only — **no** `src.tools.website_engine`.
- `_adapter_website` remains M1 PLACEHOLDER:
  - `status: "PLACEHOLDER"`
  - `website_engine_invoked: False`
  - `rendering_performed: False`
- Social/newsletter adapters remain `NOT_IMPLEMENTED` with `external_api_called: False`.
- Job flags: `orchestration_only: True`, `website_engine: False`, `social_engine: False`, `campaign_engine: False`.
- `runner_api_routers/publishing.py` does not import Website Engine.

Bridge readiness (`publish_from_job`) remains **inside Website Engine only**; wiring into `_adapter_website` is still deferred. Not a boundary violation.

### 2.2 Website Engine owns website behavior — PASS

Package owns site-specific concerns:

| Concern | Module |
|---------|--------|
| Bundle → content model (`input/{week}/05_Final.md`) | `content_model.py` |
| Slug + canonical URL | `urls.py` |
| Title/description/OG/Schema.org Article | `metadata.py` |
| Markdown → HTML (stdlib converter) | `render.py` |
| Sitemap + RSS contracts | `feeds.py` |
| Provider interface + in-process stub | `provider.py` |
| Channel-compatible result shape | `publish_result.py` |
| Site publish entrypoints | `engine.py` |

Consumers of `src.tools.website_engine` in application code: **none** outside the package itself (only `tests/test_website_engine.py`). Stub provider writes under `output/website/` only.

### 2.3 No SEO Engine scoring logic in website_engine — PASS

Grep across `src/tools/website_engine/` for scoring / keyword-optimization implementation found **documentation exclusions only**:

- `metadata.py` states SEO Engine owns scoring / keyword optimization — not implemented here.
- `content_model._seo_description_hint` reads SEO plan text for a **description hint only** (CTA/notes lines) — not scoring, ranking, or optimization.

Allowed site metadata (OpenGraph + Schema.org Article) remains Website Engine ownership per v2.1.

### 2.4 No Social / Campaign logic — PASS

- Website Engine modules contain no LinkedIn/Twitter/Instagram/newsletter delivery, campaign orchestration, or social API clients.
- Publishing social/newsletter channel adapters are `NOT_IMPLEMENTED` placeholders owned by Social/Email engines.
- Job creation flags keep `social_engine: False` and `campaign_engine: False`.

### 2.5 No external HTTP publish dependency — PASS

Across `src/tools/website_engine/` and `src/tools/publishing_engine.py`:

- No `httpx`, `requests`, `aiohttp`, `urllib.request`, or `http.client` publish clients.
- No WordPress / Ghost SDK or HTTP adapter implementations.
- `StubWebsiteProvider` sets `external_http: False` and writes filesystem artifacts only.
- Sole `urllib` usage is `urllib.parse.urlparse` in `urls.py` (URL parsing, not HTTP).

### 2.6 No Publishing API contract change — PASS

Contract doc prefix `/api/v1/publishing` matches router. Endpoints unchanged:

| Method | Path | Present |
|--------|------|---------|
| GET | `/channels` | YES |
| GET | `/jobs` | YES |
| POST | `/jobs` | YES |
| GET | `/{job_id}` | YES |
| POST | `/{job_id}/publish` | YES |
| POST | `/{job_id}/retry` | YES |
| POST | `/{job_id}/cancel` | YES |

No Website Engine routes added under Publishing. Job views still expose orchestration flags (`orchestration_only`, `website_engine`, `social_engine`). Focused publishing suite green (16 passed).

### 2.7 No DB / Alembic changes from M2 — PASS

- `alembic.ini` present; **`alembic/` directory absent** (no `alembic/versions` revisions).
- Git status shows **no** M2-related Alembic revision adds/modifies.
- Website Engine consumes filesystem editorial bundles; invents no CMS/DB publish schema.

---

## 3. Test results

**Environment:**

```bash
SECRET_KEY=test-secret-key-m25-freeze HEARTBEAT_ENABLED=0
.venv/bin/python -m pytest
```

### 3.1 Focused suites

| Suite | Result |
|-------|--------|
| `tests/test_website_engine.py` | **12 passed** |
| `tests/test_publishing_engine.py` | **16 passed** |
| `tests/test_editorial_approval.py` | **19 passed** |
| `tests/test_content_studio_ui.py` | **13 passed** |
| **Combined focused** | **60 passed / 60 total** |

### 3.2 Full suite (`tests/`)

| Metric | M2 / implied baseline | M2.5 audit run | Delta |
|--------|----------------------|----------------|-------|
| Passed | 308 | **308** | 0 |
| Failed | 8 | **8** | 0 |
| Errors | 4 | **4** | 0 |
| Total | 320 | **320** | 0 |
| New regressions | 0 | **0** | — |

**Full line:** `8 failed, 308 passed, 26 warnings, 4 errors in 11.68s`

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
Classification as historical requires exact ID match to the known crews_unit (3) / utilities_unit (5) / orchestration_api (2) / prospecting_ui (2) set — satisfied.

---

## 4. Checklist summary

| # | Check | Verdict |
|---|-------|---------|
| 1 | Publishing Engine orchestration-only | **PASS** |
| 2 | Website Engine owns website behavior | **PASS** |
| 3 | No SEO Engine scoring in website_engine | **PASS** |
| 4 | No Social / Campaign logic | **PASS** |
| 5 | No external HTTP publish (WordPress/Ghost) | **PASS** |
| 6 | No Publishing API contract change | **PASS** |
| 7 | No DB / Alembic changes from M2 | **PASS** |
| 8 | Focused suites green | **PASS** (60/60) |
| 9 | Full suite — zero new regressions | **PASS** (308/320; 8 failed; 4 errors) |

---

## 5. One-line certification

**M2.5 architecture boundaries hold: Publishing remains orchestration-only PLACEHOLDER; Website Engine owns site behavior without SEO scoring, social/campaign, or HTTP CMS clients; Publishing API and DB unchanged; 0 new regressions.**
