# 06 — Architecture Runtime Delta

Compared against Architecture Baseline v1.0 + Sprint B ownership decisions.  
Only material **verified** differences.

Classification legend:  
A PRODUCTION BLOCKER · B HARDENING ISSUE · C ARCHITECTURAL DRIFT · D OBSERVABILITY/TEST GAP · E MIGRATION BACKLOG · F TRANSITIONAL/EXPECTED · G NOT VERIFIED

---

| # | Difference | Class | Evidence |
|---|------------|-------|----------|
| 1 | Live `/marketing/generate` invokes missing `revenue_os.agents.marketing_crew` | A | HTTP 200 body `ok:false`, stderr module not found; OpenAPI registers path |
| 2 | Duplicate `@app` marketing handler with `src.marketing_crew` shadowed / not live | F / C | Source has both; runtime error matches included router only |
| 3 | `/api/v1/health` returns metrics-style `{overall,components…}` not UI liveness contract claimed in earlier repair narrative | C | Live GET response body |
| 4 | `/health/debug` 404 on running API | C / G | Live 404; may differ from local `ui.py` if container image ≠ HEAD tree |
| 5 | Running stack container names/project prefix differ from current compose project; new compose up blocked on :5432 | F | `docker ps`; compose bind error |
| 6 | Celery Beat unhealthy / no schedule; worker Docker unhealthy but ping OK | B | docker health + inspect ping |
| 7 | API container missing CrewAI/Ollama/OpenAI provider env; host Ollama present | B | printenv presence; host `:11434` |
| 8 | `RUNNER_API_KEY` MISSING → auth disabled | B | Container env; `_verify_api_key` behaviour from baseline |
| 9 | Alembic head empty DDL still current | F | `alembic current` = `e8278e1169e6` |
| 10 | Stale unit tests still failing (8) + 4 errors in full suite | D | pytest full run |
| 11 | CMS Content Studio / Publishing migration not started | E | Sprint B backlog; out of Sprint C scope |
| 12 | Webhook manager + `/api/v1/integrations/webhooks/*` working on runner_api | F | Confirms GAP-010 PARTIALLY CONFIRMED → runtime OK for integrations path |

---

## Non-differences (confirmed aligned)

| Item | Evidence |
|------|----------|
| Primary entry `uvicorn runner_api:app` | Container command / health |
| Postgres + Redis up | pg_isready, redis PING |
| 26 include_router calls in **local** HEAD source | `rg` on `runner_api.py` |
| Founder remains canonical product runtime | Live API serves WorkCrew CMS OS API OpenAPI title |
