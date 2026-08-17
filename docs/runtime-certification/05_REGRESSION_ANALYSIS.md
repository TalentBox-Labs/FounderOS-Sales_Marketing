# 05 — Regression Analysis (Sprint C → Sprint D1)

Date: 2026-08-09  
Scope: certify D0 marketing path repair introduced no regressions

---

## Classification legend

| Label | Meaning |
|-------|---------|
| Resolved | Fixed since Sprint C / by D0 |
| Known | Pre-existing or intentional leave-behind |
| Regression | New breakage introduced by D0 |
| Environment | Host/container/image/config — not D0 code defect |

---

## Resolved

| Issue | Sprint C | Sprint D1 | Class |
|-------|----------|-----------|-------|
| Marketing generate ModuleNotFound `revenue_os.agents.marketing_crew` | Confirmed runtime blocker (A) | Cleared on fixed code — `src.marketing_crew` loads; crew/provider reached | **Resolved** (D0) |
| Full pytest errors (4) | 4 errors | 0 errors | **Resolved** (suite stability; not attributed to new product features) |
| Full pytest passed count | 216 | 220 | **Resolved** (+4) |

---

## Known (remaining)

| Issue | Evidence | Class |
|-------|----------|-------|
| 8 stale unit test failures (QA/editor validate, FileOperations, markdown) | Same 8 as Sprint C leave-behinds | Known |
| Marketing HTML UI 500 — `integration_status` undefined | `ui.py` context vs `templates/marketing.html` | Known |
| `/api/v1/health` shape drift (Docker metrics vs local simple liveness) | Sprint C delta C | Known |
| `RUNNER_API_KEY` often unset (soft auth) | Sprint C | Known |
| Celery worker/beat Docker health unhealthy | Sprint C; ping still OK | Known |
| Content generate write guard / staging path | `Refusing to write into input/WXX/` | Known |
| Full LLM artifact E2E incomplete | Provider/model routing 404 despite host Ollama tags | Known / Environment |
| Alembic revision is empty-DDL head | Architecture GAP-001 | Known |

---

## Environment (not D0 regressions)

| Issue | Evidence | Class |
|-------|----------|-------|
| Docker API still returns marketing ModuleNotFound | Container ~46h; not rebuilt with D0 | Environment |
| Docker `GET /api/v1/crm/contacts` 404 vs local 200 | Image lag / route mismatch | Environment |
| Fresh `compose up` port 5432 conflict (Sprint C) | Still using pre-existing stack | Environment |
| CrewAI storage requires writable home/storage path | Sandbox/home path sensitivity during cert probes | Environment |

---

## Regressions (new since Sprint C attributable to D0)

**None.**

D0 touched only `runner_api_routers/marketing.py`. Observed failures either:

1. match Sprint C Known items, or  
2. are Environment (stale Docker image / provider), or  
3. are improvements (errors cleared, marketing path reaches crew).

**Regression count: 0**

---

## STOP condition evaluation

Sprint D1 stop rule: *If any regression appears → STOP; document; do not fix; do not begin migration.*

| Gate | Result |
|------|--------|
| Automated suite regressions | 0 |
| API contract regressions | 0 |
| Marketing path regressions | 0 (improvement) |
| New production defects from D0 | 0 |

**STOP not triggered.** Proceed to baseline freeze documentation only (no migration implementation in D1).
