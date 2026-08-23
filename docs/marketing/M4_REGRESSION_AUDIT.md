# M4 — Regression Audit

**Status:** COMPLETE  
**Date:** 2026-08-10  
**Agent:** Sentinel — Regression (M4)  
**Sprint:** M4 (Website deployment-mode decision — **docs-only**)  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
**Owned file:** this document only  
**Code / API / DB / runtime / git application changes by Sentinel:** **NONE**

**Architecture:** v2.2 ([Architecture_v2.2.md](../architecture/Architecture_v2.2.md), [Marketing_OS_v2.2.md](../architecture/Marketing_OS_v2.2.md))  
**Prior regression baseline:** [M3_5_ARCHITECTURE_REGRESSION_AUDIT.md](M3_5_ARCHITECTURE_REGRESSION_AUDIT.md)  
**Static baseline:** [M3_5_STATIC_PROVIDER_BASELINE.md](M3_5_STATIC_PROVIDER_BASELINE.md)  
**Peer M4 analysis (docs-only):** [M4_ATLAS_ARCHITECTURE_VALIDATION.md](M4_ATLAS_ARCHITECTURE_VALIDATION.md), [M4_HERMES_PUBLISHING_COMPATIBILITY.md](M4_HERMES_PUBLISHING_COMPATIBILITY.md), [M4_NOVA_DEPLOYMENT_REQUIREMENTS.md](M4_NOVA_DEPLOYMENT_REQUIREMENTS.md), [M4_SCOUT_DEPLOYMENT_COMPARISON.md](M4_SCOUT_DEPLOYMENT_COMPARISON.md)  
**Companion Sentinel note:** [M4_SENTINEL_REGRESSION.md](M4_SENTINEL_REGRESSION.md)

**Audit mode:** Read-only code verification + test runs.  
**Write scope:** This document only. Application code was not modified.

---

## Final verdict

| Gate | Result |
|------|--------|
| **Regression** | **PASS** |
| **New Regressions** | **0** |
| Architecture v2.2 respect (docs-only sprint) | **PASS** |
| Publishing / Website boundaries | **PASS** |
| M4 runtime / DB / API changes | **NONE** |
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

Verify that M4 (deployment-mode decision sprint) remains regression-clean:

1. Architecture v2.2 respected — M4 is decision/governance only; no Core / Static expansion.
2. Publishing Engine stays orchestration-only; Website Engine retains website publish ownership; deploy stays outside frozen Core.
3. No runtime / DB / API changes introduced by M4.
4. Focused + full suites match historical baseline with **0 new regressions**.

---

## 2. Architecture v2.2 respect — PASS

| v2.2 / Marketing OS constraint | M4 evidence |
|--------------------------------|-------------|
| Website Engine SHIPPED (Core + Static); M4 = **Deploy mode decision** | Peer Atlas doc + Architecture v2.2 §6; no new Website Engine modules |
| Publishing = orchestration only; does not own website render | `_adapter_website` still PLACEHOLDER; no `website_engine` import in Publishing |
| Website Engine owns content/render/provider; future CMS/deploy hooks | Registry still `static` + `stub`; no deploy hooks implemented |
| Deploy outside Core / Static Provider contracts | Static still filesystem-only; `external_http=False`; “no deploy” in result messages |
| Human gates preserved | No bypass of Editorial / Publishing production-publish paths |

M4 peer deliverables are markdown under `docs/marketing/M4_*.md` and declare **Code / API / DB / runtime / git changes: NONE** (or equivalent). Sprint does not expand frozen M2.5 Core or M3.5 Static baselines.

---

## 3. Publishing / Website boundaries — PASS

### 3.1 Publishing Engine — orchestration-only

Verified in `src/tools/publishing_engine.py` + `runner_api_routers/publishing.py`:

| Contract | Status |
|----------|--------|
| Imports `src.tools.website_engine` | **No** |
| `_adapter_website` | `status: "PLACEHOLDER"`, `website_engine_invoked: False`, `rendering_performed: False` |
| Job flags | `orchestration_only: True`, `website_engine: False`, `social_engine: False`, `campaign_engine: False` |
| Publishing API | Exposes `website_engine: False`; does not import Website Engine |
| Deploy / hosting ownership | **None** in Publishing |

### 3.2 Website Engine — deploy surface unchanged

Package still 11 modules (`content_model`, `urls`, `metadata`, `render`, `feeds`, `provider`, `publish_result`, `engine`, `registry`, `static_provider`, `__init__`).

| Concern | M4 status |
|---------|-----------|
| Registry | `static` + `stub` only |
| WordPress / Ghost / hosting adapters | **Not registered** |
| Deploy clients (rsync/SSH/CDN/S3/Netlify/Vercel/FTP) | **None** |
| Network publish | **None** (`external_http=False`) |
| Artifact path | `output/website/{slug}/` + site `sitemap.xml` / `rss.xml` |

Bridge readiness (`publish_from_job`) remains inside Website Engine only — not wired into Publishing `_adapter_website`. Not a boundary violation.

---

## 4. No M4 runtime / DB / API changes — PASS

| Surface | Evidence |
|---------|----------|
| M4 sprint writes | Docs under `docs/marketing/M4_*.md` only (decision / validation / compatibility) |
| Website Engine / Publishing Engine from M4 | **No M4 code delta** — engines unchanged for deploy; no new deploy module |
| Alembic / schema | `alembic.ini` present; **`alembic/` directory absent** — no deploy schema |
| External HTTP publish | Still false on static + stub paths |
| Sentinel write scope | This file only |

Unrelated pre-existing workspace changes (e.g. UI / marketing routers outside M4) are out of M4 ownership and were not introduced by this audit. M4 itself remains docs-only for deployment-mode decision.

---

## 5. Test results

**Environment:**

```bash
SECRET_KEY=test-secret-m4b HEARTBEAT_ENABLED=0
.venv/bin/python -m pytest …
```

### 5.1 Focused suites (required)

| Suite | Result |
|-------|--------|
| `tests/test_website_engine.py` | collected + passed (part of 40) |
| `tests/test_static_provider.py` | collected + passed (part of 40) |
| `tests/test_publishing_engine.py` | collected + passed (part of 40) |
| **Combined focused** | **40 passed / 40 total** |

**Focused line:** `40 passed, 9 warnings in 3.42s`

### 5.2 Full suite (`tests/`)

| Metric | Baseline (M3.5 / brief) | M4 Sentinel run | Delta |
|--------|-------------------------|-----------------|-------|
| Passed | 320 | **320** | 0 |
| Failed | 8 | **8** | 0 |
| Errors | 4 | **4** | 0 |
| Total | 332 | **332** | 0 |
| New regressions | 0 | **0** | — |

**Full line:** `8 failed, 320 passed, 26 warnings, 4 errors in 13.52s`  
**Collected:** `332 tests collected`

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

**New failing tests vs baseline known set:** **none**.

---

## 6. Checklist summary

| # | Check | Verdict |
|---|-------|---------|
| 1 | Architecture v2.2 respect (docs-only M4) | **PASS** |
| 2 | Publishing orchestration-only / Website boundaries | **PASS** |
| 3 | No M4 runtime / DB / API / deploy code | **PASS** |
| 4 | No WordPress / Ghost / hosting adapters added | **PASS** |
| 5 | No external HTTP publish path | **PASS** |
| 6 | Focused suites green | **PASS** (40/40) |
| 7 | Full suite — zero new regressions | **PASS** (320/332; 8 failed; 4 errors) |

---

## 7. One-line certification

**M4 is regression-clean under Architecture v2.2: docs-only deployment-mode decision; Publishing remains PLACEHOLDER orchestration-only; Website Engine static filesystem path unchanged; no runtime/DB/API/deploy code; 0 new regressions (40/40 focused; 320/332 full).**
