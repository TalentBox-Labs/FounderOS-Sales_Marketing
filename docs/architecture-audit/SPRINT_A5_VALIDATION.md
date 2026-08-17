# Sprint A.5 — Evidence Review Package

Repository: `TB-FounderOS-Sales_Marketing` (local only)  
Scope: validate Sprint A docs under `docs/architecture-audit/` against repository evidence  
Constraints observed: no source modifications, no commits, no git operations, no redesign

---

# Executive Summary

**Confidence level for Sprint A: Medium**

Explanation (evidence-backed):

- Core quantitative claims in `SUMMARY.md` re-measured and match for Python file count (227), SQLAlchemy `Base` models (44), test modules (41), test functions (223), Docker Compose services (5), and primary entry `uvicorn runner_api:app`.
- Module directories, CrewAI/YAML presence, dual FastAPI apps, Alembic empty revision, marketing subprocess module path absence, CI installing only `requirements.txt`, and auth-disabled-when-unset behavior are confirmed in code.
- Confidence is not High because: (1) Sprint A `SUMMARY.md` table wording for router counts is imprecise relative to actual `include_router` call count; (2) GAP-010 characterizes `revenue_os/integrations/webhooks.py` inaccurately relative to file contents; (3) Sprint A domain names do not map 1:1 to the named OS labels in Task 4 of this sprint; (4) AI “provider abstraction,” CrewAI tool bindings, and agent “memory” layers are only partially present as described.

---

# Validation Matrix

| Sprint A document | Status | Evidence basis (summary) |
|-------------------|--------|---------------------------|
| SUMMARY | PARTIAL | Counts mostly match; router `include_router` wording imprecise (see Repository Corrections) |
| MODULE MAP | PARTIAL | Major modules exist; some responsibility/consumer claims not exhaustively re-proven |
| DEPENDENCY GRAPH | PARTIAL | Directions confirmed via imports; circular imports none verified; leakage found |
| DOMAIN BOUNDARIES | PARTIAL | Code exists for most capabilities under different names than Task 4 labels |
| AI RUNTIME | PARTIAL | Crews/YAML/API/LLM wiring verified; abstraction/tools/memory incomplete |
| ARCHITECTURE GAPS | PARTIAL | Most gaps Evidence Confirmed; GAP-010 Incorrect/Incomplete |

---

# Task 1 — SUMMARY.md number verification

| Claim in SUMMARY.md | Re-measured value | Result |
|---------------------|-------------------|--------|
| Python files excl. `.venv`/`.git` = 227 | `find … -name '*.py'` → **227** | VERIFIED |
| SQLAlchemy `class *(Base)` under `revenue_os/models` = 44 | `rg '^class \w+\(Base\)'` → **44** | VERIFIED |
| Test modules `tests/test_*.py` = 41 | `ls` → **41** | VERIFIED |
| Test functions `test_*` = 223 | ripgrep count → **223** | VERIFIED |
| Docker Compose services = 5 (`db`,`redis`,`api`,`worker`,`beat`) | `docker-compose.yml` service keys | VERIFIED |
| Included domain routers = 25 | `app.include_router(...)` lines 220–244 = **25** domain routers; plus `ui_router` at line 256 | PARTIAL — see corrections |
| Table: “Included domain routers … 25 (`include_router` list)” | Total `include_router` calls on `runner_api.app` = **26** (25 domain + UI) | PARTIAL — wording conflates domain count with full include list |
| Revenue OS v1 mounted sub-routers = 10 | `revenue_os/api/v1/__init__.py` include_router × **10** | VERIFIED |
| `runner_api_routers/*.py` files = 29 | `ls` → **29** | VERIFIED |
| `revenue_os/api/v1/*.py` files = 11 | `ls` → **11** | VERIFIED |
| Largest file `runner_api.py` = 1465 lines | `wc -l` → **1465** | VERIFIED |
| Sampled largest router/crew line counts (672/629/582/543/479/458) | `wc -l` matches listed files | VERIFIED |
| Main entry `uvicorn runner_api:app` | `Dockerfile` CMD | VERIFIED |
| Secondary app `revenue_os.main:app` | `revenue_os/main.py` defines `app = FastAPI(...)` | VERIFIED |
| Celery worker/beat entry | `docker-compose.yml` commands `celery -A revenue_os.tasks.celery_app …` | VERIFIED |
| Approximate HTTP decorators = 323 | NOT re-run to identical aggregation in this pass | NOT VERIFIED (prior Sprint A scan; not reconfirmed here) |
| Disk size 1.1G | NOT re-measured in this pass | NOT VERIFIED |
| Selected source-like files = 498 | NOT re-measured in this pass | NOT VERIFIED |

### Main entry points (verified)

| Entry | Evidence |
|-------|----------|
| `uvicorn runner_api:app` | `Dockerfile` CMD |
| `celery -A revenue_os.tasks.celery_app worker` | `docker-compose.yml` |
| `celery -A revenue_os.tasks.celery_app beat` | `docker-compose.yml` |
| `revenue_os.main:app` | `revenue_os/main.py` |
| `python -m src.main` / pipeline modules | files present under `src/` (CLI modules exist) |

---

# Task 2 — MODULE MAP validation

Do not rewrite Sprint A descriptions. Status only.

| Module (Sprint A §) | Directory present | Ownership/responsibility claim | Dependencies claim | Status |
|---------------------|-------------------|--------------------------------|---------------------|--------|
| 1. API / Runner | `runner_api.py` | FastAPI title “WorkCrew CMS OS API” present | Imports routers + revenue_os; Docker CMD matches | VERIFIED |
| 2. Runner API Routers | `runner_api_routers/` | Included via `include_router` 220–256 | Imports `utils`, `revenue_os.*`, some `src.*` confirmed | VERIFIED |
| 3. Revenue OS | `revenue_os/` | `main.py` description string present; models/services/tasks present | SQLAlchemy/config/Celery/Chroma refs present | VERIFIED |
| 4. Content / Marketing CMS (`src`) | `src/` | Crews + `src/tools/` + YAML present | CrewAI/`csv_reader`/runtime paths imports present | VERIFIED |
| 5. Authentication | `utils.py`, `revenue_os/auth.py` | API key + JWT both present | Depends on env / jose / bcrypt as coded | VERIFIED |
| 6. AI / Agents | `src/*_crew.py`, `revenue_os/agents/`, services | Multiple crews + agent modules present | LLM builders / OpenAI usage present | VERIFIED |
| 7. Sales / Prospecting / Outreach | routers + services + models | CRM/prospecting/outreach files present | SessionLocal/models imports present | VERIFIED |
| 8. Marketing | marketing router, `src/marketing_crew.py`, YAML | Present | Subprocess target `revenue_os.agents.marketing_crew` **file missing** — responsibility claim for HTTP generate path PARTIAL | PARTIAL |
| 9. Knowledge | `knowledge_base` router, content models, rag/search | Present | Chroma/RAG modules present | VERIFIED |
| 10. Customer Success | `csm` router, `customer_success/`, `csm_crew.py` | Present | Imports present | VERIFIED |
| 11. Automation / Workers / Schedulers | `automation/`, `scheduler.py`, `tasks/`, routers | Present | Redis/Celery/heartbeat evidenced | VERIFIED |
| 12. Infrastructure / Ops | Docker/CI/migrations/metrics | Present | Compose/Render/CI files present | VERIFIED |
| 13. Frontend | `frontend/` | package.json name `workcrew-crm-frontend`; pages present | Mount condition `frontend/dist` in `runner_api.py` | VERIFIED |
| 14. Shared / Platform | utils, middleware, base_crew, config, database | Present | Cross-imported | VERIFIED |
| 15. Obsidian / content vault | `obsidian_vault/`, `input/` | Present | Sync script present | VERIFIED |

---

# Task 3 — DEPENDENCY GRAPH validation

## Dependency direction (import evidence)

| Edge | Evidence | Status |
|------|----------|--------|
| `runner_api` → `runner_api_routers.*` | `include_router` imports in `runner_api.py` | VERIFIED |
| `runner_api_routers` → `revenue_os.*` | e.g. `SessionLocal`, services imports across routers | VERIFIED |
| `runner_api_routers` → `src.*` | `hermes.py` → `src.sdr_crew`; `csm.py` → `src.csm_crew`; `metrics.py` → `src.observability` | VERIFIED |
| `runner_api` → `src.*` via subprocess | `pipeline.py` runs `python -m src.tools.*` / `src.generation_crew` / `src.editor_crew` | VERIFIED |
| `src` → `revenue_os` | ripgrep of `from revenue_os` / `import revenue_os` under `src/` | NONE VERIFIED |
| `revenue_os` → `runner_api` | ripgrep under `revenue_os/` | NONE VERIFIED |
| `revenue_os` → `src` | ripgrep under `revenue_os/` | NONE VERIFIED |

## Circular imports

**NONE VERIFIED** among `runner_api` ↔ `revenue_os` ↔ `src` package imports.

## Shared modules (verified)

- `runner_api_routers.utils`
- `revenue_os.database` / `revenue_os.config`
- `src.base_crew`
- `src.tools.csv_reader` / `runtime_paths` (import sites in crews)

## Infrastructure dependencies (verified)

| Dependency | Evidence |
|------------|----------|
| Postgres | `docker-compose.yml` service `db`; `DATABASE_URL` in `revenue_os/config.py` |
| Redis | compose `redis`; Celery broker in `revenue_os/tasks/__init__.py` |
| ChromaDB | `search_service.py`, `rag_service.py`, `CHROMA_PERSIST_DIR` |
| Filesystem content roots | `input/`, `output/`, `data/` |

## Hidden coupling / domain leakage (verified)

| Finding | Evidence |
|---------|----------|
| Revenue/Hermes router imports content-pipeline crew | `runner_api_routers/hermes.py`: `from src.sdr_crew import SDRCrew` |
| CSM router imports `src.csm_crew` | `runner_api_routers/csm.py` |
| Metrics router imports `src.observability` | `runner_api_routers/metrics.py` |
| Marketing router subprocess names missing module | `runner_api_routers/marketing.py` → `revenue_os.agents.marketing_crew` (no such file; `src/marketing_crew.py` exists) |
| Duplicate HTTP handlers on `runner_api.py` overlapping routers | e.g. `@app.post("/marketing/generate")`, prospecting `@app` routes coexist with included routers |

## Layer boundaries

Strict layered boundary (API → services → models only): **NOT VERIFIED**  
Observed: routers import services/models/crews directly; `src` and `revenue_os` coupled at router layer.

---

# Task 4 — DOMAIN BOUNDARIES (named OS labels)

Sprint A used different domain names. Mapping below uses **repository evidence only** against the labels requested in Sprint A.5.

| Named domain | Status | Repository evidence |
|--------------|--------|---------------------|
| Executive OS | Partial | `revenue_os/executive/` (`kpis.py`, `insights.py`); `runner_api_routers/paperclip.py` (`/api/v1/paperclip`). No package/dir named `executive_os`. |
| Sales OS | Partial | CRM/prospecting/outreach routers + models/services + frontend Contacts/Deals pages. No package named `sales_os`. |
| Revenue OS | Implemented | Package `revenue_os/` with `main.py`, models, services, api/v1, tasks. |
| Marketing OS | Partial | `src/marketing_crew.py`, marketing YAML, `runner_api_routers/marketing.py`, `revenue_os/marketing/`, SEO router. HTTP generate targets missing module path. No package named `marketing_os`. |
| Customer Success OS | Partial | `runner_api_routers/csm.py`, `revenue_os/customer_success/`, `src/csm_crew.py`. No package named `customer_success_os`. |
| Operations OS | Partial | Pipeline ops via `runner_api_routers/pipeline.py`, `src/tools/pipeline_*`, UI `templates/pipeline.html`, heartbeat/metrics. No package named `operations_os`. |
| Knowledge OS | Partial | `/api/v1/knowledge-base`, KB models, `rag_service.py`, `search_service.py`, `obsidian_vault/`. No package named `knowledge_os`. |
| AI Platform | Partial | CrewAI crews under `src/`, `revenue_os/agents/`, `ai_service.py`, copilot, orchestration. No single package named `ai_platform`. |
| Automation Platform | Partial | `revenue_os/automation/`, Celery `revenue_os/tasks/`, heartbeat `scheduler.py`, `/api/v1/automation`, n8n integration. No package named `automation_platform`. |
| Shared Platform | Implemented | Cross-cutting `runner_api_routers/utils.py`, `middleware.py`, `revenue_os/config.py`, `database.py`, `auth.py`, `src/base_crew.py`. |

---

# Task 5 — AI Runtime (implementation presence only)

| Concern | Status | Evidence |
|---------|--------|----------|
| CrewAI | Present | `requirements.txt` / `requirements-revenue.txt`; `from crewai import Agent, Crew, LLM…` in `src/base_crew.py` |
| Crew definitions | Present | Classes: `GenerationCrew`, `EditorCrew`, `QACrew`, `MarketingCrew`, `DistributionCrew`, `ArtifactCrew`, `SDRCrew`, `CSMCrew` under `src/` |
| YAML agents | Present | `src/agents.yaml`, `agents_generation.yaml`, `agents_phase2a.yaml`, `agents_editor.yaml`, `agents_distribution.yaml`, `agents_marketing.yaml` (+ matching `tasks_*.yaml`) |
| Provider abstraction | Partial | Env-driven `_build_llm()` / `build_crew_llm()` returning `crewai.LLM`; separate `OpenAI(...)` in `ai_service.py`. No shared provider interface class spanning both. |
| LLM adapters | Partial | `crewai.LLM` adapter path; OpenAI SDK path; Gemini key in settings/MCP hub status. Anthropic client: **NOT VERIFIED** (no matches in `*.py`) |
| Tool execution | Partial | Content tools under `src/tools/` used as CLI/subprocess helpers. CrewAI `tools=` / `BaseTool` bindings in `*crew*.py`: **NOT VERIFIED** |
| Memory | Partial | Chroma persistence (`search_service.py`, `rag_service.py`). CrewAI Memory constructs: **NOT VERIFIED**. In-memory caches exist in analytics/automation/agents comments/code. |
| Persistence | Present | Filesystem (`input/`, `output/`, staging); SQLAlchemy models; Chroma dir config |
| Event flow | Partial | Automation events/workflows (`revenue_os/automation/`); n8n bridge; heartbeat jobs. End-to-end single “AI event bus” named construct: **NOT VERIFIED** |
| API entry | Present | Pipeline `/generate`,`/edit`; marketing `/marketing/generate`; `/api/v1/copilot/chat`; `/api/v1/agents/*`; `/api/v1/hermes/*`; `/api/v1/knowledge-base/ask`; `/api/v1/orchestration/*` |

---

# Task 6 — ARCHITECTURE GAPS validation

| Gap ID | Sprint A claim | Classification | Validation evidence |
|--------|----------------|----------------|---------------------|
| GAP-001 | Alembic upgrade/downgrade only `pass` | Evidence Confirmed | `migrations/versions/e8278e1169e6_full_schema.py` bodies are `pass` |
| GAP-002 | Dual FastAPI apps + overlapping `@app` routes | Evidence Confirmed | `runner_api.py` + `revenue_os/main.py`; Dockerfile uses `runner_api:app`; duplicate `@app` prospecting/marketing routes still present |
| GAP-003 | Marketing subprocess module file missing | Evidence Confirmed | Router string `revenue_os.agents.marketing_crew`; `ls revenue_os/agents/` has no `marketing_crew.py`; `src/marketing_crew.py` exists |
| GAP-004 | Celery beat without `beat_schedule` | Evidence Confirmed | compose `beat` service present; `rg beat_schedule` over repo `*.py` → no matches; `tasks/__init__.py` has no schedule map |
| GAP-005 | Auth disabled if `RUNNER_API_KEY` unset | Evidence Confirmed | `_verify_api_key` returns `None` when key empty |
| GAP-006 | Two auth systems (API key vs JWT) | Evidence Confirmed | `utils._verify_api_key` vs `revenue_os.auth.get_current_user` on v1 routers |
| GAP-007 | CrewAI version pins differ across requirements | Evidence Confirmed | `crewai>=0.80.0` vs `crewai>=1.9.0`; Dockerfile installs both requirement files |
| GAP-008 | CI installs only `requirements.txt` | Evidence Confirmed | `.github/workflows/test.yml` line `pip install -r requirements.txt` |
| GAP-009 | COVERAGE.md historical snapshot | Evidence Confirmed | Dated 2026-06-11; “140 passed”; “44%”; suite now 41 modules / 223 defs |
| GAP-010 | Empty / pass-through webhook shim | Incorrect / Evidence Incomplete | File is **300 lines** with `WebhookManager` and an `APIRouter` export; **zero** `@router.get/post/...` decorators. Comment states HTTP routes live in `runner_api_routers/integrations.py`. Not an empty file; HTTP surface on this router is empty. |
| GAP-011 | SQLite + Postgres branches in startup migrate | Evidence Confirmed | `_migrate_missing_columns` dialect branches in `runner_api.py`; `pytest_local.db` present |
| GAP-012 | Legacy `src/*.py.old` retained | Evidence Confirmed | Five `.old` files listed under `src/` |
| GAP-013 | No Anthropic client wiring | Evidence Confirmed | `rg -i anthropic\|claude` over `*.py` → no matches |

---

# Repository Corrections

Evidence-backed corrections to Sprint A documentation claims only:

1. **Router include count wording**  
   - Actual: **26** `app.include_router(...)` calls on `runner_api.app` (25 domain routers + `ui_router`).  
   - SUMMARY table text “25 (`include_router` list)” is imprecise.

2. **GAP-010 wording**  
   - `revenue_os/integrations/webhooks.py` is not empty.  
   - It exports `router = APIRouter(...)` with **no route decorators**, plus in-process `WebhookManager` implementation.  
   - Sprint A “empty shim” characterization is **Incorrect**.

3. **HTTP decorator total (323)**  
   - Not reconfirmed in Sprint A.5 → treat as **NOT VERIFIED** until re-scanned.

4. **Disk size / selected source-like file count**  
   - Not reconfirmed in Sprint A.5 → **NOT VERIFIED**.

5. **Named OS domains in Task 4**  
   - Repository does not contain packages named `executive_os`, `sales_os`, `marketing_os`, `operations_os`, etc.  
   - Capabilities exist under `revenue_os`, `src`, and `runner_api_routers` naming instead.

6. **Marketing generate path**  
   - Confirmed mismatch: HTTP path invokes `revenue_os.agents.marketing_crew`; implementation file present at `src/marketing_crew.py` only.

---

# Risks

Repository-supported only:

| Risk | Evidence |
|------|----------|
| `POST /marketing/generate` may fail with module import error | Subprocess module string absent as file under `revenue_os/agents/` |
| Schema history not encoded in Alembic DDL | Empty `upgrade()`/`downgrade()` |
| API key auth may be off in environments without `RUNNER_API_KEY` | `_verify_api_key` early `return None` |
| CI dependency set differs from Docker runtime | CI installs `requirements.txt` only; Docker installs three requirement files |
| Celery beat may run without schedule | No `beat_schedule` in repository; heartbeat scheduler is separate in-process mechanism |
| Route duplication / shadowing ambiguity | Same paths defined on both included routers and `@app` handlers in `runner_api.py` |
| Cross-domain coupling at API layer | Routers import `src` crews and `revenue_os` services directly |

---

# Readiness

**SPRINT A REQUIRES CORRECTION**

Repository evidence:

- GAP-010 classification/text does not match file contents (Incorrect).
- SUMMARY router include-list wording does not match the measured **26** `include_router` calls.
- Marketing generate module path absence is confirmed and contradicts any implication that the marketing HTTP generate entry is fully wired to an existing module file.

After those documentation corrections, quantitative backbone (227 Python files, 44 models, 41/223 tests, 5 Compose services, primary `runner_api:app` entry) remains verified and usable for Principal Architecture Review.
