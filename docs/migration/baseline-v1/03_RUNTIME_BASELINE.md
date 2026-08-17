# 03 — Runtime Baseline

**Canonical freeze:** Founder Runtime Baseline v1.1  
**Evidence:** [08_RUNTIME_BASELINE_V1_1.md](../../runtime-certification/08_RUNTIME_BASELINE_V1_1.md), [03_RUNTIME_HEALTH.md](../../runtime-certification/03_RUNTIME_HEALTH.md), [07_PRODUCTION_READINESS_REVIEW.md](../../runtime-certification/07_PRODUCTION_READINESS_REVIEW.md)

---

## Runtime status

**PARTIAL** — core healthy; non-blocking gaps classified (0 production blockers unexplained).

---

## Docker status

| Service | Status (D1/D1.5 evidence) |
|---------|---------------------------|
| API | Healthy |
| Postgres (db) | Healthy — `pg_isready` accepting connections |
| Redis | Healthy — `PONG` |
| Celery worker | Running; Docker health **unhealthy**; `inspect ping` OK |
| Celery beat | Running; Docker health **unhealthy** |

Note: Live Docker API image may lag uncommitted D0/E2 working-tree deltas until rebuild ([03_RUNTIME_HEALTH.md](../../runtime-certification/03_RUNTIME_HEALTH.md)).

---

## API status

| Check | Status |
|-------|--------|
| `GET /health` | PASS |
| Marketing generate (fixed code) | PASS path (D0/D1) |
| Content Studio list/detail (E2) | PASS ([E2_IMPLEMENTATION.md](../content-studio/E2_IMPLEMENTATION.md)) |
| Marketing HTML `GET /marketing` | Known 500 (`integration_status`) — non-blocking |
| Auth soft-open without `RUNNER_API_KEY` | Known hardening gap |

---

## Redis

CONNECTED / HEALTHY — `PONG`.

---

## Celery

| Check | Status |
|-------|--------|
| App module | `revenue_os.tasks.celery_app` |
| Worker ping | PASS |
| Registered tasks | 5 (leads/outreach/agents) |
| Docker health labels | unhealthy (non-blocking) |

---

## AI runtime

| Check | Status |
|-------|--------|
| Controlled path (crew + provider + prompt + response) | **PASS** (D1) |
| Full artifact E2E | Known/Environment incomplete |
| Fallback falsely succeeding | Not observed on certified path |

Evidence: [04_AI_RUNTIME_CERTIFICATION.md](../../runtime-certification/04_AI_RUNTIME_CERTIFICATION.md).

---

## Current test counts

| Suite | Passed | Failed | Errors | Source |
|-------|-------:|-------:|-------:|--------|
| Full pytest (E2) | **228** | **8** | **0** | [E2_IMPLEMENTATION.md](../content-studio/E2_IMPLEMENTATION.md) |
| Integration routers | **18** | 0 | 0 | Same |
| Content Studio focused | **8** | 0 | 0 | Same |
| D1.5 baseline (pre-E2) | 220 | 8 | 0 | [08_RUNTIME_BASELINE_V1_1.md](../../runtime-certification/08_RUNTIME_BASELINE_V1_1.md) |
| Sprint C | 216 | 8 | 4 | [03_TEST_RESULTS.md](../../runtime-verification/03_TEST_RESULTS.md) |

---

## Regression counts

| Comparison | Result |
|------------|--------|
| D0 vs Sprint C | 0 D0 regressions ([05_REGRESSION_ANALYSIS.md](../../runtime-certification/05_REGRESSION_ANALYSIS.md)) |
| E2 vs D1.5 | +8 passed (new tests); same 8 failures; **0 new failures** |

---

## Known failures (intentional leave-behinds)

Eight stale unit tests (QA/Editor `validate_output`, abstract `BaseCrew` FileOperations, markdown structure). Classified non-blocking in [07_PRODUCTION_READINESS_REVIEW.md](../../runtime-certification/07_PRODUCTION_READINESS_REVIEW.md).

---

## Known non-blocking issues

1. Celery Docker health labels unhealthy  
2. Marketing HTML UI 500  
3. Soft auth when API key unset  
4. `/api/v1/health` shape drift on some live paths  
5. Docker image lag until rebuild  
6. Full LLM artifact E2E Environment gaps  
7. Eight stale unit-test failures  

Blocking issues count at D1.5 freeze: **0**.
