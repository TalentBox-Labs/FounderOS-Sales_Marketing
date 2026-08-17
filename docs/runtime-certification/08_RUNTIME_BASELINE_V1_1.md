# 08 — Founder Runtime Baseline v1.1 (Frozen)

Sprint D1.5 — Production Readiness Review  
Canonical repository: `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
Documentation-only freeze. No git tag created in this sprint (per no-change / no-tag rule).

Predecessor certification: `docs/runtime-certification/06_BASELINE_V1_1.md`  
Readiness review: `docs/runtime-certification/07_PRODUCTION_READINESS_REVIEW.md`

---

## Baseline identity

| Field | Value |
|-------|-------|
| Repository branch | `develop` |
| Repository SHA | `e1efc0892ea13dad856b952110c7cc38d24565c3` |
| Architecture Baseline | **v1.0 FROZEN** — `docs/architecture-audit/15_BASELINE_FREEZE.md` @ tag `v0.1-stable` |
| Certified working-tree app delta | D0 repair in `runner_api_routers/marketing.py` (`src.marketing_crew` + CLI flags); not yet committed |
| Runtime status | **PARTIAL** |
| AI status | **PASS** (controlled path: crew + provider + prompt + response; no fallback) |
| Marketing route status | **PASS** on fixed code / TestClient; Docker `:8000` image lags until rebuild (**Environment**) |
| Test totals | **220 passed / 8 failed / 0 errors** (228); integration **18/18** |

---

## Known non-blocking issues

1. Celery worker/beat Docker health labels **unhealthy** while `inspect ping` and task registration succeed  
2. Marketing HTML UI `GET /marketing` → 500 (`integration_status` undefined)  
3. Soft auth when `RUNNER_API_KEY` unset  
4. `/api/v1/health` response-shape drift on live Docker metrics path  
5. Eight stale unit-test failures (QA/Editor validate_output contracts; abstract `BaseCrew` FileOperations; markdown structure via Editor)  
6. Full LLM artifact E2E incomplete (provider/model routing / generate write-guard) — Environment / Known  

---

## Known deferred issues

1. Rebuild/restart Docker API so live `:8000` serves D0 `src.marketing_crew` wiring  
2. Align or retire the 8 stale unit tests (out of scope for D0/D1/D1.5)  
3. Marketing UI template context completion  
4. Celery Docker healthcheck hardening  
5. Content Studio migration implementation (explicitly deferred; baseline allows start)  

---

## Regression status

**D0 REGRESSION = NO**  
**Regression count vs Sprint C attributable to D0 = 0**

---

## Freeze statement

# FOUNDER RUNTIME BASELINE v1.1 FROZEN

Frozen meaning for operators and migration work:

- Architecture Baseline v1.0 remains the architectural freeze.  
- Runtime Baseline v1.1 records certified runtime/test evidence after D0, with Runtime PARTIAL fully explained and non-blocking.  
- Content Studio migration may proceed against this baseline; live Docker must be rebuilt before treating container marketing generate as D0-equivalent.
