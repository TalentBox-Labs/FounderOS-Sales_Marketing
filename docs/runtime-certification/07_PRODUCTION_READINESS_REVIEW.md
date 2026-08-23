# 07 — Production Readiness Review (Sprint D1.5)

Date: 2026-08-09  
Repository: `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
HEAD: `e1efc0892ea13dad856b952110c7cc38d24565c3` (`develop`)  
Scope: explain Runtime PARTIAL + remaining 8 tests; freeze decision only  
No source, test, config, Docker, or migration changes.

Evidence sources: `docs/runtime-certification/`, `docs/runtime-verification/`, `docs/architecture-audit/`, `docs/migration/`, re-run of the 8 failing tests, live Docker probes (2026-08-09).

---

# Executive Summary

## Runtime PARTIAL explanation

Sprint D1 marked runtime **PARTIAL** because core services (API/DB/Redis) are healthy while several **non-blocking** gaps remain simultaneously: Celery worker/beat Docker health labels are **unhealthy** despite functional `inspect ping` + registered tasks; the live Docker API image (~47h) still runs **pre-D0** marketing wiring (`ModuleNotFound: revenue_os.agents.marketing_crew`); and `GET /marketing` returns **500** from a Jinja context gap (`integration_status` undefined). No single component alone defines PARTIAL—the rating reflects this multi-gap profile with healthy core path.

## Remaining 8 tests explanation

All 8 non-passing tests are **FAILED** (0 errors, 0 skipped). They are the same intentional leave-behinds recorded in Sprint C / D1: three QA/Editor `validate_output` contract mismatches against current production validators, four FileOperations tests that instantiate abstract `BaseCrew`, and one markdown-structure test that reuses the Editor length/frontmatter contract. None were introduced by D0 (`runner_api_routers/marketing.py` only).

## Counts

| Category | Count |
|----------|------:|
| Blocking issues (production blockers unexplained) | **0** |
| Non-blocking issues (runtime PARTIAL contributors + 8 tests + known hardening) | **11+** (see matrices) |

## Confidence

**HIGH**

Re-ran the exact 8 failures with assertion evidence; live Docker health/marketing probes refreshed; D0 delta confirmed as sole app code change vs HEAD.

---

# Runtime Partial Matrix

| Component | Status | Evidence | Classification | Blocking |
|-----------|--------|----------|----------------|----------|
| API process (Docker) | Healthy | `docker ps`: api Up (healthy); `GET /health` → 200 | — (healthy core) | No |
| Postgres | Healthy | `pg_isready` accepting connections (D1 + stack still up) | — | No |
| Redis | Healthy | `redis-cli ping` → `PONG` | — | No |
| Celery worker | Functional / label unhealthy | `celery -A revenue_os.tasks.celery_app inspect ping` → `pong`; 5 registered tasks; Docker Status **unhealthy** | **B. NON-BLOCKING HARDENING ISSUE** | NON-BLOCKING |
| Celery beat | Process up / label unhealthy | Container Up (unhealthy); CMD `celery -A revenue_os.tasks.celery_app beat` | **B. NON-BLOCKING HARDENING ISSUE** | NON-BLOCKING |
| Docker API image vs D0 working tree | Lagging | Live `POST /marketing/generate` stderr still `No module named revenue_os.agents.marketing_crew` (probe 2026-08-09); working tree uses `src.marketing_crew` | **D. ENVIRONMENT / CONFIGURATION** (image not rebuilt) + **F. KNOWN TRANSITIONAL STATE** | NON-BLOCKING for baseline freeze of repo+D0 delta; rebuild required before treating `:8000` as D0-live |
| Marketing HTML UI | 500 | `GET /marketing` → 500; Jinja `UndefinedError: 'integration_status' is undefined` (`templates/marketing.html` vs `ui.py` context) | **B. NON-BLOCKING HARDENING ISSUE** | NON-BLOCKING (does not invalidate `POST /marketing/generate` on fixed code) |
| Marketing generate (fixed code / TestClient) | PASS path | D1: HTTP 200; no ModuleNotFound; crew/provider reached | — (certified) | No |
| AI controlled path | PASS | D1: crew loads, provider attempted, prompt/task stdout, no fallback | — | No |
| Full AI artifact E2E | Incomplete | Provider model routing `404` / write-guard on `/generate` (D1 docs) | **D. ENVIRONMENT / CONFIGURATION** / optional completion gap | NON-BLOCKING |
| Auth soft-open | Soft | `RUNNER_API_KEY` often unset (Sprint C/D1) | **B. NON-BLOCKING HARDENING ISSUE** | NON-BLOCKING |
| `/api/v1/health` shape (Docker vs local) | Drift | Docker metrics-shaped body vs local simple liveness (Sprint C/D1) | **E. OBSERVABILITY GAP** | NON-BLOCKING |

**Explicit statement:** PARTIAL is **not** caused by only one component. It is the aggregate of Celery health-label gaps + Docker image lag + marketing UI 500 (with healthy API/DB/Redis).

---

# Remaining Test Matrix

Re-run (2026-08-09):  
`pytest` on the 8 named tests → **8 failed**, 0 errors, 0 skipped.

| Test | Outcome | Root Cause (evidence) | Classification | Blocking |
|------|---------|----------------------|----------------|----------|
| `tests/test_crews_unit.py::TestQACrew::test_qa_crew_validates_output_format` | FAILED | Fixture omits `## Passed Checks`; live `qa_report_contract_errors` returns `Missing required section heading: ## Passed Checks` (`src/crew_contract.py` / `QACrew.validate_output`) | **B. STALE / OBSOLETE CONTRACT** | NON-BLOCKING |
| `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_validates_output` | FAILED | Fixture markdown length &lt; 100 chars; `EditorCrew.validate_output` returns `Edited content is too short` | **B. STALE / OBSOLETE CONTRACT** | NON-BLOCKING |
| `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_rejects_output_without_frontmatter` | FAILED | Errors are `Edited content is too short` + `Missing YAML front matter (---)`; assertion looks for substring `"frontmatter"` which does **not** appear in `"front matter"` | **B. STALE / OBSOLETE CONTRACT** | NON-BLOCKING |
| `tests/test_utilities_unit.py::TestFileOperations::test_read_file_returns_content` | FAILED | `TypeError: Can't instantiate abstract class BaseCrew without … 'build_agents_and_tasks', 'validate_output'` | **B. STALE / OBSOLETE CONTRACT** + **E. ARCHITECTURE DEBT** (tests assume concrete BaseCrew) | NON-BLOCKING |
| `tests/test_utilities_unit.py::TestFileOperations::test_read_file_raises_on_missing_file` | FAILED | Same abstract `BaseCrew(...)` instantiation | **B** + **E** | NON-BLOCKING |
| `tests/test_utilities_unit.py::TestFileOperations::test_save_file_creates_directories` | FAILED | Same abstract `BaseCrew(...)` instantiation | **B** + **E** | NON-BLOCKING |
| `tests/test_utilities_unit.py::TestFileOperations::test_save_file_overwrites_existing` | FAILED | Same abstract `BaseCrew(...)` instantiation | **B** + **E** | NON-BLOCKING |
| `tests/test_utilities_unit.py::TestDataValidation::test_markdown_structure_validation` | FAILED | Uses `EditorCrew.validate_output`; short frontmatter sample fails min-length (`Edited content is too short`) | **B. STALE / OBSOLETE CONTRACT** | NON-BLOCKING |

Sprint C listed these same 8 failures as class B leave-behinds (`docs/runtime-verification/03_TEST_RESULTS.md`). Suite totals D1: **220 passed / 8 failed / 0 errors**.

---

# Regression Check

## D0 REGRESSION: **NO**

Evidence:

1. Sole app code delta vs HEAD: `runner_api_routers/marketing.py` (`+10/-1`) — D0 marketing module/flags only (`git diff --stat HEAD`).
2. Sprint C already recorded these **same 8** failures (`docs/runtime-verification/03_TEST_RESULTS.md`, `07_SPRINT_C_VERDICT.md`).
3. D1 suite improved vs Sprint C (216→220 passed; 4→0 errors); failure set did not grow.
4. D0 does not touch `src/qa_crew.py`, `src/editor_crew.py`, `src/base_crew.py`, or the failing test modules.

---

# Readiness Decision

## READY TO FREEZE RUNTIME BASELINE v1.1

Gate check:

| Gate | Result |
|------|--------|
| AI runtime still passes | YES (D1 controlled path) |
| Marketing route still passes (fixed code) | YES |
| No D0 regressions | YES (`D0 REGRESSION = NO`) |
| Remaining test issues classified | YES (matrix above) |
| No unexplained production blocker | YES (0 blockers; PARTIAL items classified B/D/E/F) |
