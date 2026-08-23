# 02 — Architecture Baseline

**Canonical freeze:** Architecture Baseline v1.0  
**Evidence:** [docs/architecture-audit/15_BASELINE_FREEZE.md](../../architecture-audit/15_BASELINE_FREEZE.md)  
**HEAD at freeze:** `e1efc0892ea13dad856b952110c7cc38d24565c3` (`develop`, tag `v0.1-stable`)

---

## Current architecture

Founder OS is a combined FastAPI application (`runner_api:app`) with:

- Domain routers under `runner_api_routers/`
- Revenue/CRM/automation under `revenue_os/`
- CrewAI content crews under `src/`
- Jinja ops UI under `templates/`
- Optional React CRM under `frontend/`
- Content SoT: `tracker.csv` + `input/` + `data/week_runtime/`

Full inventory: [01_REPOSITORY_INVENTORY.md](../../architecture-audit/01_REPOSITORY_INVENTORY.md), [SUMMARY.md](../../architecture-audit/SUMMARY.md).

---

## Layer boundaries

| Layer | Owner modules | Reference |
|-------|---------------|-----------|
| API / Runner | `runner_api.py`, `runner_api_routers/*` | [02_MODULE_MAP.md](../../architecture-audit/02_MODULE_MAP.md) |
| Domain services | `revenue_os/services`, models, automation | [10_REVENUE_OS.md](../../architecture-audit/10_REVENUE_OS.md) |
| Marketing crews / pipeline tools | `src/*`, `src/tools/*` | [09_MARKETING_OS.md](../../architecture-audit/09_MARKETING_OS.md) |
| Shared platform | DB, auth helpers, middleware, compose | [11_SHARED_PLATFORM.md](../../architecture-audit/11_SHARED_PLATFORM.md) |
| AI runtime | CrewAI LLM via env; crews | [08_AI_RUNTIME.md](../../architecture-audit/08_AI_RUNTIME.md) |

---

## Module ownership

See [02_MODULE_MAP.md](../../architecture-audit/02_MODULE_MAP.md). Marketing OS Content Studio read API (E2) owns `runner_api_routers/content_studio.py` only; SoT remains tracker/filesystem.

---

## Domain boundaries

See [07_DOMAIN_BOUNDARIES.md](../../architecture-audit/07_DOMAIN_BOUNDARIES.md). Content Studio is under **Marketing OS**. Publishing, Social, Campaign, SEO engines remain separate slices ([03_MIGRATION_SLICES.md](../03_MIGRATION_SLICES.md)).

---

## Dependency direction

See [03_DEPENDENCY_GRAPH.md](../../architecture-audit/03_DEPENDENCY_GRAPH.md).

Rule preserved through migration: CMS is capability source only; Founder does not import Flask/Sheets/OpenClaw as runtimes ([06_DEPENDENCY_BOUNDARY.md](../content-studio/06_DEPENDENCY_BOUNDARY.md)).

---

## Runtime topology

See [04_RUNTIME_TOPOLOGY.md](../../architecture-audit/04_RUNTIME_TOPOLOGY.md) and live verification [02_RUNTIME_TOPOLOGY.md](../../runtime-verification/02_RUNTIME_TOPOLOGY.md).

Compose services: API, Postgres, Redis, Celery worker, Celery beat.

---

## Router inventory

See [14_ROUTER_INVENTORY.md](../../architecture-audit/14_ROUTER_INVENTORY.md).

At Architecture freeze: **26** `include_router` calls (25 domain + UI).  
Post-E2: additive `content_studio_router` included on `runner_api:app` ([E2_IMPLEMENTATION.md](../content-studio/E2_IMPLEMENTATION.md)) — no redesign of existing routers.

---

## Migration statement

# Architecture unchanged during migration.

D0 corrected marketing subprocess wiring only.  
E2 added a read-only Content Studio router.  
No domain redesign, no CMS runtime import, no SoT change.
