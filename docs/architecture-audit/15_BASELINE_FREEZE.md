# 15 — Architecture Baseline Freeze

Sprint A.6 — Evidence Correction & Architecture Baseline Freeze  
Repository: `TB-FounderOS-Sales_Marketing` (local only)  
No runtime code changes. No Git operations.

---

# Executive Summary

## Architecture Baseline

**FROZEN**

**ARCHITECTURE BASELINE v1.0 FROZEN**

Sprint A.5 discrepancies (router include count wording, GAP-010 characterization, marketing crew module reference) have been closed with repository-backed corrections documented in this file and in `14_ROUTER_INVENTORY.md`. Remaining items are recorded as known evidence risks, not unresolved inventory errors.

---

# Corrections Applied

## 1. Router inventory count

| Prior claim (Sprint A SUMMARY) | Corrected evidence |
|--------------------------------|--------------------|
| “25 (`include_router` list)” | **26** live `app.include_router(...)` calls on `runner_api:app` = **25 domain routers + 1 UI router** |

Canonical inventory: `docs/architecture-audit/14_ROUTER_INVENTORY.md`.

## 2. GAP-010 (webhooks) — evidence reclassification

| Question | Finding | Classification |
|----------|---------|----------------|
| Webhook support exists? | Yes — `WebhookManager`, `WebhookEventType`, delivery helpers in `revenue_os/integrations/webhooks.py` | CONFIRMED |
| Webhook HTTP endpoints exist? | Yes on `runner_api` — `POST/GET/DELETE /api/v1/integrations/webhooks/*` in `runner_api_routers/integrations.py`; also n8n `/webhooks/n8n/*` | CONFIRMED |
| Webhook infrastructure exists? | Yes — manager + integrations router import/use; in-memory subscription store | CONFIRMED |
| Webhook runtime reachable on primary app? | Yes — `integrations_router` is included on `runner_api:app` (line 231) | CONFIRMED |
| `webhooks.py` `APIRouter` itself expose routes? | No `@router` decorators; file comment states CMS HTTP routes live in `integrations.py`; empty router mounted only on `revenue_os.main` | PARTIALLY CONFIRMED |

**Sprint A GAP-010 “empty shim” wording: INCORRECT**  
**Corrected overall GAP-010 status: PARTIALLY CONFIRMED**  
(Infrastructure + reachable endpoints on primary app; standalone `webhooks.router` has no endpoints.)

## 3. Marketing crew reference `revenue_os.agents.marketing_crew`

| Question | Evidence |
|----------|----------|
| Does `revenue_os.agents.marketing_crew` exist as a module file? | **No.** `revenue_os/agents/` contains `execution.py`, `orchestration.py`, `recruiter_agent.py`, `safeguards.py`, `sdr_agent.py`, `__init__.py` only. |
| Does an implementation exist elsewhere? | **Yes.** `src/marketing_crew.py` defines `MarketingCrew` and `if __name__ == "__main__"`. |
| Who references the missing path? | `runner_api_routers/marketing.py` subprocess: `python -m revenue_os.agents.marketing_crew` |
| Who references the existing path? | `runner_api.py` `@app.post("/marketing/generate")` uses `python -m src.marketing_crew`; `go_to_market_orchestrator.py` uses `"src.marketing_crew"`; tests import `src.marketing_crew` |

**Classification (evidence only, no repair):**

**Stale import / Incomplete migration** on the **included** marketing router path, with concurrent **duplicate** `@app` handler still using the valid `src.marketing_crew` module.

Because `marketing_router` is `include_router`’d **before** the `@app` duplicate handlers, the first-registered `/marketing/generate` path is the router implementation that references the missing module.

Not classified as intentional removal (no removal evidence found).  
Not classified as unused reference (path is invoked by included router).  
Runtime defect potential: **repository-supported** for the included-router path only.

## 4. Validation matrix updates (Sprint A.5 → A.6)

| Item | A.5 status | A.6 status |
|------|------------|------------|
| Router include count | PARTIAL | Corrected / frozen in `14_ROUTER_INVENTORY.md` |
| GAP-010 | Incorrect / Incomplete | PARTIALLY CONFIRMED (see above) |
| Marketing module path | Confirmed missing file | Classified: stale import / incomplete migration |

---

# Remaining Evidence Risks

Repository-backed only:

| Risk | Evidence |
|------|----------|
| Included `/marketing/generate` targets missing module | `runner_api_routers/marketing.py` vs absent `revenue_os/agents/marketing_crew.py` |
| Duplicate marketing/prospecting/orchestration handlers | `@app` routes in `runner_api.py` after router includes |
| Alembic revision has empty DDL | `migrations/versions/e8278e1169e6_full_schema.py` `pass` only |
| Celery Beat service with no `beat_schedule` | compose `beat` service; no `beat_schedule` in repo `*.py` |
| Auth disabled when `RUNNER_API_KEY` unset | `_verify_api_key` returns `None` |
| CI installs `requirements.txt` only; Docker installs three requirement files | `.github/workflows/test.yml` vs `Dockerfile` |
| CrewAI pin differs across requirement files | `>=0.80.0` vs `>=1.9.0` |
| Dual FastAPI apps | `runner_api:app` (Docker) and `revenue_os.main:app` |
| Cross-package router imports of `src` crews | `hermes.py`, `csm.py`, `metrics.py` |

These risks are **frozen into the baseline as known facts**, not treated as open inventory discrepancies.

---

# Runtime Confidence

**Medium**

Explanation (evidence):

**Verified present:**

| Runtime element | Evidence |
|-----------------|----------|
| FastAPI primary app | `runner_api:app`; Dockerfile `uvicorn runner_api:app` |
| FastAPI secondary app module | `revenue_os.main:app` |
| Celery worker | compose service `worker` → `celery -A revenue_os.tasks.celery_app worker` |
| Celery Beat process | compose service `beat` → `celery -A revenue_os.tasks.celery_app beat` |
| Compose services | `db`, `redis`, `api`, `worker`, `beat` (5) |
| Database configuration | `DATABASE_URL` in `revenue_os/config.py` + compose Postgres 14 |
| Redis configuration | `REDIS_URL` in config + compose Redis 7; Celery broker/backend |
| AI provider configuration | `WORKCREW_CREWAI_*`, `OPENAI_*`, `GEMINI_API_KEY` in config / `.env.example`; `src/base_crew.py::_build_llm` |
| Crew runtime | Crew classes under `src/`; pipeline subprocess to `src.generation_crew` / `src.editor_crew`; marketing via `src.marketing_crew` in some call sites |
| Heartbeat scheduler | `initialize_heartbeat()` on `runner_api` startup |

**Confidence not High because:** Beat schedule map absent; marketing included-router path points at missing module; Alembic empty; auth optional without key; dual app/route duplication.

---

# Implementation Readiness

**READY FOR SPRINT B**

Evidence: inventory discrepancies identified in Sprint A.5 are corrected and frozen; primary runtime entry points and module map are evidenced; known defects/risks are explicitly listed rather than unresolved as “unknown inventory.”

Not stated as READY FOR PHASE 6 (no Phase 6 evidence package requested here).  
Not BASELINE REQUIRES FURTHER CORRECTION (router count, GAP-010, marketing classification closed for evidence purposes).

---

# Baseline Freeze

**ARCHITECTURE BASELINE v1.0 FROZEN**

Sprint A documentation under `docs/architecture-audit/` — including Sprint A.5 validation and Sprint A.6 corrections (`14_ROUTER_INVENTORY.md`, `15_BASELINE_FREEZE.md`) — becomes the **canonical repository evidence package** until superseded by future approved engineering work.

### Canonical package index (frozen)

| Document | Role |
|----------|------|
| `01_REPOSITORY_INVENTORY.md` | Inventory |
| `02_MODULE_MAP.md` | Modules |
| `03_DEPENDENCY_GRAPH.md` | Dependencies |
| `04_RUNTIME_TOPOLOGY.md` | Runtime |
| `05_API_SURFACE.md` | API surface |
| `06_DATABASE_MODEL.md` | Database |
| `07_DOMAIN_BOUNDARIES.md` | Domains |
| `08_AI_RUNTIME.md` | AI runtime |
| `09_MARKETING_OS.md` | Marketing |
| `10_REVENUE_OS.md` | Revenue |
| `11_SHARED_PLATFORM.md` | Shared |
| `12_TESTING.md` | Testing |
| `13_ARCHITECTURE_GAPS.md` | Gaps (read with A.6 GAP-010 correction) |
| `SUMMARY.md` | Summary (router count superseded by `14_`) |
| `SPRINT_A5_VALIDATION.md` | Validation |
| `14_ROUTER_INVENTORY.md` | **Corrected router baseline** |
| `15_BASELINE_FREEZE.md` | **This freeze record** |

### Freeze rule

Where Sprint A prose conflicts with Sprint A.6 corrections, **Sprint A.6 evidence wins** for:

1. Router include count (**26** = 25 domain + UI)  
2. GAP-010 status (**PARTIALLY CONFIRMED**, not empty shim)  
3. Marketing crew path classification (**stale import / incomplete migration**; module absent at `revenue_os.agents.marketing_crew`; present at `src.marketing_crew`)
