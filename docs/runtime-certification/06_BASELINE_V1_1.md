# 06 — Runtime Baseline v1.1

Sprint D1 — Runtime Certification & Baseline Freeze  
Repository: `TB-FounderOS-Sales_Marketing` (canonical local)  
No feature work. No architecture redesign. No CMS / Content Studio implementation in this sprint.

---

## Baseline identity

| Field | Value |
|-------|-------|
| Baseline name | **Runtime Baseline v1.1** |
| Predecessor | Architecture Baseline v1.0 (`docs/architecture-audit/15_BASELINE_FREEZE.md`) @ `v0.1-stable` |
| Repository SHA (HEAD) | `e1efc0892ea13dad856b952110c7cc38d24565c3` |
| Branch | `develop` |
| Certified app delta | Uncommitted D0 repair: `runner_api_routers/marketing.py` → `src.marketing_crew` + matching CLI flags |
| Evidence pack | `docs/runtime-certification/` |
| D0 record | `docs/implementation/D0_IMPLEMENTATION.md` |

---

## Test totals

| Suite | Passed | Failed | Errors | Skipped |
|-------|-------:|-------:|-------:|--------:|
| Full `pytest -q` | 220 | 8 | 0 | 0 |
| Integration routers | 18 | 0 | 0 | 0 |

Vs Sprint C: **+4 passed, −4 errors, same 8 known failures.**

---

## Runtime status

**PARTIAL**

- API container healthy; Postgres healthy; Redis healthy  
- Celery worker/beat functionally usable (ping + registered tasks); Docker health labels unhealthy  
- Live Docker API image **not** rebuilt with D0 (Environment lag)

---

## API status

**PASS (fixed code / contracts)** with Known UI gap

- Health, weeks, pipeline, CRM contacts, hermes revenue-summary: PASS on local TestClient  
- Marketing generate contract unchanged; import blocker cleared on fixed code  
- Marketing HTML page: Known 500 (`integration_status`)

---

## Database status

**CONNECTED — no migration required**

- `pg_isready` accepting connections  
- Alembic head `e8278e1169e6`  
- D0 introduced no schema changes

---

## AI status

**PASS** (controlled path)

- Marketing crew loads; provider path reached; prompt/task executes; response returned; no fallback  
- Full artifact file success: Known/Environment (model routing 404)  
- Content generate early guard: Known

---

## Known remaining issues

1. 8 intentional stale unit-test failures (class B)  
2. Marketing HTML `integration_status` template/context gap  
3. Docker API image lag (pre-D0 marketing ModuleNotFound until rebuild)  
4. Celery worker/beat unhealthy Docker health labels  
5. Provider/model routing incomplete for full artifact E2E  
6. Soft auth when `RUNNER_API_KEY` unset  
7. `/api/v1/health` response-shape drift on live metrics path  

---

## Regression status

**0 regressions** from Sprint C attributable to D0.

---

## Architecture status

**Unchanged from Architecture Baseline v1.0**

- No domain redesign  
- No CMS migration executed  
- No Content Studio work  
- Marketing canonical implementation remains `src.marketing_crew`; D0 corrected live router wiring only  

---

## Certification decision

# CERTIFIED FOR CONTENT STUDIO MIGRATION

Rationale:

1. D0 marketing path repair re-verified: stale module error absent; crew and provider reached.  
2. Automated suite improved (220/8/0 vs Sprint C 216/8/4); integration 18/18.  
3. Zero D0-attributable regressions.  
4. Remaining gaps are Known or Environment and do not block starting Content Studio migration planning/implementation under prior Slice strategy.  
5. Operators must **rebuild/restart API** to pick up D0 on the live Docker stack before treating container `:8000` as D0-certified.
