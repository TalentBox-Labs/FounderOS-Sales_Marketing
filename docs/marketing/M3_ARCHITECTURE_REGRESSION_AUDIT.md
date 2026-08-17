# M3 — Architecture Regression & Boundary Audit

**Status:** COMPLETE  
**Date:** 2026-08-10  
**Agent:** C — Regression / Boundary Auditor (Sprint M3)  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
**Architecture:** v2.1 (ADR-002)  
**Prior audits:** [M2_ARCHITECTURE_REGRESSION_AUDIT.md](M2_ARCHITECTURE_REGRESSION_AUDIT.md), [M2_5_ARCHITECTURE_REGRESSION_AUDIT.md](M2_5_ARCHITECTURE_REGRESSION_AUDIT.md)  
**Implementation under audit:** Static Website Provider (M3) + Website Engine ownership  
**Provider report:** [M3_STATIC_PROVIDER_REPORT.md](M3_STATIC_PROVIDER_REPORT.md)  
**Publishing baseline:** [M1_5_PUBLISHING_BASELINE.md](M1_5_PUBLISHING_BASELINE.md)

**Audit mode:** Read-only code verification + test runs.  
**Write scope:** This document only. Application code was not modified.

---

## Final verdict

| Gate | Result |
|------|--------|
| **Architecture** | **PASS** |
| **New Regressions** | **0** |
| **Boundary Violations** | **0** |
| Publishing website adapter | **PLACEHOLDER retained** |
| WordPress / Ghost assumptions in code | **NONE** (docs-only exclusions / future notes) |
| DB / Alembic changes from M3 | **NONE** |
| New external deps / network side effects | **NONE** |

```
Architecture: PASS
New Regressions: 0
Focused: 72/72
Full: 320/332; 8 failed; 4 errors
```

---

## 1. Scope verified

| Item | Evidence |
|------|----------|
| Publishing Engine orchestration-only | `src/tools/publishing_engine.py` |
| Website Engine package + static adapter | `src/tools/website_engine/` (11 modules incl. `static_provider.py`, `registry.py`) |
| Focused suites | static / website / publishing / editorial / content_studio_ui |
| Full suite | `tests/` (332 collected) |
| No app-code writes by Agent C | Confirmed — audit doc only |

---

## 2. Architecture boundary checks

### 2.1 Publishing Engine orchestration-only; website adapter PLACEHOLDER — PASS

Verified in `src/tools/publishing_engine.py`:

- Module docstring: orchestration ONLY; excludes website render, social APIs, email, campaigns, Celery/n8n, scheduling, AI publishing.
- Imports: stdlib + `editorial_approval` + `runtime_paths` only — **no** `src.tools.website_engine`.
- `_adapter_website` still returns M1 PLACEHOLDER shape:
  - `status: "PLACEHOLDER"`
  - `website_engine_invoked: False`
  - `rendering_performed: False`
- Job flags remain `orchestration_only: True`, `website_engine: False`.
- `runner_api_routers/publishing.py` does not import Website Engine (only exposes `website_engine: False` flag).

Agent A did **not** wire `_adapter_website` → `publish_from_job`. Bridge readiness remains inside Website Engine only. Not a boundary violation.

### 2.2 Website Engine owns website behavior; static is adapter only — PASS

Website Engine continues to own site-specific concerns (content model, slug/URL, metadata/OG/Schema.org, Markdown→HTML, sitemap/RSS, publish result shape, engine entrypoints).

M3 additions stay inside the package:

| Concern | Module |
|---------|--------|
| Production-intent local/static adapter | `static_provider.py` (`StaticWebsiteProvider`, `name="static"`) |
| Named provider registry (`static`, `stub`) | `registry.py` |
| Default provider → `static` | `engine.py` (`DEFAULT_PROVIDER_NAME = "static"`) |
| Shared HTML wrap helpers (Stub + Static) | `provider.py` |

Static adapter responsibilities only:

- Validate request fields / safe slug
- Write `output/website/{slug}/index.html`, `source.md`, `metadata.json`
- Write site-level `sitemap.xml` / `rss.xml` via existing `feeds.py`
- Always `external_http=False`

Static does **not** own Publishing state machine, editorial approval, social/campaign, SEO scoring, or deploy.

### 2.3 No WordPress / Ghost assumptions — PASS

Across `src/tools/website_engine/` and `src/tools/publishing_engine.py`:

- No WordPress/Ghost SDK, API client, or registered provider (`list_providers()` → `static` + `stub` only).
- `tests/test_static_provider.py::TestRegistry::test_get_provider_unknown_raises` asserts `get_provider("wordpress")` raises `KeyError`.
- Mentions of WordPress/Ghost appear only as **exclusion / future** documentation strings (protocol remains provider-neutral).

### 2.4 No DB / Alembic changes — PASS

- `alembic.ini` present; **`alembic/` directory absent** (no revisions).
- Website Engine / static provider: no SQLAlchemy models, sessions, or schema migrations.
- Artifacts are filesystem-only under `output/website/`.

### 2.5 No new external deps / network side effects — PASS

- M3 modules import stdlib + in-package website_engine modules + `runtime_paths` only.
- No `httpx` / `requests` / `aiohttp` / `urllib.request` publish clients in website_engine (sole `urllib.parse.urlparse` in `urls.py` for URL parsing).
- `requirements.txt` / `requirements-api.txt` / `requirements-revenue.txt` unchanged by M3 (pre-existing `httpx` in revenue requirements is out of scope).
- Static + stub providers set `external_http=False` on success and failure paths; no deploy/CDN/HTTP CMS side effects.

### 2.6 No Social / Campaign / SEO scoring leak — PASS

Unchanged from M2.5: website_engine contains no social API delivery, campaign orchestration, or SEO scoring implementation. Publishing social/newsletter adapters remain `NOT_IMPLEMENTED`.

---

## 3. Test results

**Environment:**

```bash
SECRET_KEY=test-secret-key-m3-static HEARTBEAT_ENABLED=0
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

| Metric | Baseline (M2.5) | M3 audit run | Delta |
|--------|-----------------|--------------|-------|
| Passed | 308 | **320** | **+12** (M3 static tests) |
| Failed | 8 | **8** | 0 |
| Errors | 4 | **4** | 0 |
| Total | 320 | **332** | **+12** |
| New regressions | 0 | **0** | — |

**Full line:** `8 failed, 320 passed, 26 warnings, 4 errors in 16.21s`

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
Pass-count increase (+12) is attributable to new M3 `test_static_provider` coverage, not to recovery of historical failures.

---

## 4. Checklist summary

| # | Check | Verdict |
|---|-------|---------|
| 1 | Publishing Engine orchestration-only | **PASS** |
| 2 | Website adapter still PLACEHOLDER | **PASS** |
| 3 | Website Engine owns website behavior | **PASS** |
| 4 | Static is adapter only | **PASS** |
| 5 | No WordPress/Ghost assumptions | **PASS** |
| 6 | No DB / Alembic changes | **PASS** |
| 7 | No new external deps / network side effects | **PASS** |
| 8 | Focused suites green | **PASS** (72/72) |
| 9 | Full suite — zero new regressions | **PASS** (320/332; 8 failed; 4 errors) |

---

## 5. One-line certification

**M3 Static Provider is architecture-compliant: Publishing remains PLACEHOLDER-orchestrated; Website Engine owns site behavior with filesystem-only static adapter; no WP/Ghost/DB/network deps; 0 new regressions (72/72 focused; 320/332 full).**
