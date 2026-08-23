# M4 — Sentinel Regression Report

**Status:** COMPLETE  
**Date:** 2026-08-10  
**Agent:** Sentinel — Regression (M4)  
**Sprint:** M4 (Website deployment-mode decision — **docs-only**)  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
**Owned file:** this document only  
**Code / API / DB / runtime / git application changes by Sentinel:** **NONE**

**Architecture:** v2.1 / v2.2 (ADR-002 lineage)  
**Prior regression baseline:** [M3_5_ARCHITECTURE_REGRESSION_AUDIT.md](M3_5_ARCHITECTURE_REGRESSION_AUDIT.md)  
**Static baseline:** [M3_5_STATIC_PROVIDER_BASELINE.md](M3_5_STATIC_PROVIDER_BASELINE.md)  
**Peer M4 analysis (docs-only):** [M4_ATLAS_ARCHITECTURE_VALIDATION.md](M4_ATLAS_ARCHITECTURE_VALIDATION.md), [M4_HERMES_PUBLISHING_COMPATIBILITY.md](M4_HERMES_PUBLISHING_COMPATIBILITY.md), [M4_NOVA_DEPLOYMENT_REQUIREMENTS.md](M4_NOVA_DEPLOYMENT_REQUIREMENTS.md), [M4_SCOUT_DEPLOYMENT_COMPARISON.md](M4_SCOUT_DEPLOYMENT_COMPARISON.md)

**Audit mode:** Read-only code verification + test runs.  
**Write scope:** This document only. Application code was not modified.

---

## Final verdict

| Gate | Result |
|------|--------|
| **Regression** | **PASS** |
| **New Regressions** | **0** |
| M4 deployment code introduced | **NONE** (docs-only sprint) |
| Publishing orchestration-only | **PASS** (PLACEHOLDER retained) |
| Website Engine deploy surface | **UNCHANGED** (no deploy hooks) |
| Focused suites | **40/40** |
| Full suite | **320/332; 8 failed; 4 errors** |

```
Regression: PASS
New Regressions: 0
Focused: 40/40
Full: 320/332; 8 failed; 4 errors
```

---

## 1. Mission

Verify that M4 (deployment-mode decision sprint) did **not** introduce runtime/deploy regressions:

1. No deployment code introduced in M4 (docs-only).
2. Publishing Engine remains orchestration-only.
3. Website Engine remains unchanged for deploy (filesystem static path only).
4. Focused + full test suites match historical baseline with **0 new regressions**.

---

## 2. M4 scope verification — docs-only / no deploy code — PASS

| Check | Evidence |
|-------|----------|
| Peer M4 deliverables | Analysis markdown only under `docs/marketing/M4_*.md` (Atlas / Hermes / Nova / Scout) |
| Each peer doc declares | “Code / API / DB / runtime / git changes: **NONE**” or equivalent |
| Website Engine package | Still 11 modules; no new deploy/hook/transport module |
| Deploy clients in `website_engine/` | **NONE** — no rsync/SSH/CDN/S3/Netlify/Vercel/FTP clients |
| Registry | Still `static` + `stub` only; no hosting/CMS providers |
| `external_http` | Still `False` on static + stub success/failure paths |
| Alembic | `alembic.ini` present; **`alembic/` directory absent** — no schema for deploy |

Mentions of “deploy” in `src/tools/website_engine/` and `publishing_engine.py` remain **exclusion / documentation strings only** (e.g. “no deploy”, “does NOT … deploy”). No executable deploy path.

Unrelated pre-existing `boto3` usage in `revenue_os/reporting/delivery.py` is outside Marketing OS Website/Publishing engines and is not M4 work.

---

## 3. Publishing Engine — orchestration-only — PASS

Verified in `src/tools/publishing_engine.py` + `runner_api_routers/publishing.py`:

| Contract | Status |
|----------|--------|
| Module mission | Orchestration ONLY (jobs, queue, channel, state, audit, manual publish) |
| Imports Website Engine | **No** — no `src.tools.website_engine` import |
| `_adapter_website` | `status: "PLACEHOLDER"`, `website_engine_invoked: False`, `rendering_performed: False` |
| Job flags | `orchestration_only: True`, `website_engine: False`, `social_engine: False`, `campaign_engine: False` |
| Deploy / hosting in Publishing | **None** — PLACEHOLDER message still disclaims Markdown/HTML/SEO/deploy |
| Publishing API | Exposes `website_engine: False`; does not import Website Engine |

M4 does **not** move deploy ownership into Publishing. Compatible with Hermes M4 compatibility analysis.

---

## 4. Website Engine — deploy surface unchanged — PASS

Verified across `src/tools/website_engine/`:

| Concern | M4 status |
|---------|-----------|
| Core (content / slug / metadata / render / feeds / provider protocol) | Unchanged |
| Static Provider v1.0 | Filesystem write under `output/website/` only |
| Deploy hooks / CDN / cache invalidation | **Not implemented** (still PREPARE / out of Core) |
| WordPress / Ghost HTTP adapters | **Not registered** |
| Network publish | **None** (`external_http=False`) |
| Consumers outside package | Tests only; Publishing does not call Website Engine |

Artifact contract unchanged:

```text
output/website/
├── {slug}/index.html | metadata.json | source.md
├── sitemap.xml
└── rss.xml
```

Compatible with Nova M4 requirements: deploy remains **outside** frozen Core / Static Provider contracts.

---

## 5. Test results

**Environment:**

```bash
SECRET_KEY=test-secret-m4-decision HEARTBEAT_ENABLED=0
.venv/bin/python -m pytest …
```

### 5.1 Focused suites (required)

| Suite | Result |
|-------|--------|
| `tests/test_static_provider.py` | **12 passed** |
| `tests/test_website_engine.py` | **12 passed** |
| `tests/test_publishing_engine.py` | **16 passed** |
| **Combined focused** | **40 passed / 40 total** |

**Focused line:** `40 passed, 9 warnings in 3.39s`

### 5.2 Full suite (`tests/`)

| Metric | Baseline (M3.5) | M4 Sentinel run | Delta |
|--------|-----------------|-----------------|-------|
| Passed | 320 | **320** | 0 |
| Failed | 8 | **8** | 0 |
| Errors | 4 | **4** | 0 |
| Total | 332 | **332** | 0 |
| New regressions | 0 | **0** | — |

**Full line:** `8 failed, 320 passed, 26 warnings, 4 errors in 11.01s`

### 5.3 Failing / error test IDs (historical — exact ID match)

**FAILED (8)** — crews_unit (3) + utilities_unit (5):

1. `tests/test_crews_unit.py::TestQACrew::test_qa_crew_validates_output_format`
2. `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_validates_output`
3. `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_rejects_output_without_frontmatter`
4. `tests/test_utilities_unit.py::TestFileOperations::test_read_file_returns_content`
5. `tests/test_utilities_unit.py::TestFileOperations::test_read_file_raises_on_missing_file`
6. `tests/test_utilities_unit.py::TestFileOperations::test_save_file_creates_directories`
7. `tests/test_utilities_unit.py::TestFileOperations::test_save_file_overwrites_existing`
8. `tests/test_utilities_unit.py::TestDataValidation::test_markdown_structure_validation`

**ERROR (4)** — orchestration_api (2) + prospecting_ui (2); historical Postgres auth setup failures:

1. `tests/test_orchestration_api.py::test_orchestration_plan_endpoint_returns_strategy`
2. `tests/test_orchestration_api.py::test_orchestration_run_with_mocked_backend_and_audit_persistence`
3. `tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads`
4. `tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score`

**New failing tests vs historical known set:** **none**.  
Distribution unchanged: crews_unit 3, utilities_unit 5, orchestration_api 2 err, prospecting_ui 2 err.

---

## 6. Checklist summary

| # | Check | Verdict |
|---|-------|---------|
| 1 | M4 docs-only — no deployment code introduced | **PASS** |
| 2 | Publishing Engine orchestration-only | **PASS** |
| 3 | Website Engine deploy surface unchanged | **PASS** |
| 4 | No WordPress / Ghost / hosting adapters added | **PASS** |
| 5 | No external HTTP publish path | **PASS** |
| 6 | Focused suites green | **PASS** (40/40) |
| 7 | Full suite — zero new regressions | **PASS** (320/332; 8 failed; 4 errors) |

---

## 7. One-line certification

**M4 is regression-clean: docs-only deployment-mode decision; no deploy code; Publishing remains PLACEHOLDER orchestration-only; Website Engine static filesystem path unchanged; 0 new regressions (40/40 focused; 320/332 full).**
