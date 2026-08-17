# Architecture Audit — SUMMARY

Evidence package location: `docs/architecture-audit/`  
Source: local repository `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing` only.

---

## Repository size

| Metric | Value |
|--------|-------|
| Disk (`du -sh` at audit time) | 1.1G |
| Python files (excl. `.venv`/`.git`) | 227 |
| Selected source-like files | 498 |
| Largest Python file by lines | `runner_api.py` (1465) |

---

## Major modules

1. `runner_api` + `runner_api_routers` (combined WorkCrew CMS OS API)
2. `revenue_os` (models, services, JWT API, workers, integrations)
3. `src` (CrewAI crews + content pipeline tools)
4. `frontend` (React CRM SPA)
5. `templates` (Jinja ops UI)
6. `input` / `output` / `data` (content & runtime filesystem)
7. `tests`, `scripts`, `migrations`, `docs`, `obsidian_vault`

---

## Technology stack

- Python 3.11+ (Docker 3.11-slim; CI 3.11–3.13)
- FastAPI + Uvicorn + Jinja2
- SQLAlchemy + Alembic + Postgres (SQLite paths also present)
- Redis + Celery
- React 18 + Vite
- pytest
- Docker Compose / Render blueprint

---

## AI stack

- CrewAI (`src` crews, YAML agents/tasks)
- LLM env: `WORKCREW_CREWAI_*`, Ollama base URL defaults
- OpenAI SDK usage in `revenue_os/services/ai_service.py` (when keyed)
- Gemini API key surfaced in settings/MCP hub
- ChromaDB + RAG/search services
- Agent orchestration under `revenue_os/agents` and GTM orchestrator
- Anthropic first-class client: Repository evidence not found

---

## Database stack

- SQLAlchemy DeclarativeBase models: **44** `Base` subclasses under `revenue_os/models`
- Postgres 14 via Docker; `DATABASE_URL` in settings
- Alembic present; single revision with empty `upgrade()`/`downgrade()`
- Startup `create_all` + additive column patches
- Chroma persistence under `data/chroma_db` (config default)

---

## API stack

- Primary process: `uvicorn runner_api:app`
- Secondary app module: `revenue_os.main:app`
- Runner routers included: **25** domain routers (+ utils/middleware/__init__)
- Revenue OS v1 sub-routers: **10** under `revenue_os/api/v1`
- Approximate decorated HTTP handlers scanned: **323** (includes overlaps/duplicates)
- Auth: Bearer API key (`RUNNER_API_KEY`) and JWT (`revenue_os.auth`)

---

## Number of domains

Logical domains documented in `07_DOMAIN_BOUNDARIES.md`: **12**

(Content Pipeline, Marketing, Revenue/CRM/Sales, Hermes, Agents/Orchestration, Automation/Heartbeat, CSM, Knowledge/Copilot, Analytics/Reporting/Forecasting/Executive, Integrations/Messaging, Platform/Auth/Observability, Frontend UX)

---

## Number of services

Docker Compose services (canonical `docker-compose.yml`): **5**  
(`db`, `redis`, `api`, `worker`, `beat`)

Renderable web+DB blueprint services: **1** web + **1** database (`render.yaml`)

---

## Number of routers

| Surface | Count |
|---------|-------|
| `runner_api_routers/*.py` files | 29 (includes `__init__`, `utils`, `middleware`) |
| Included domain routers on `runner_api` | 25 (`include_router` list) |
| `revenue_os/api/v1/*.py` files | 11 (includes `__init__`) |
| Mounted v1 sub-routers | 10 |

---

## Number of models

SQLAlchemy `class *(Base)` under `revenue_os/models`: **44**

---

## Number of tests

| Metric | Count |
|--------|-------|
| Test modules | 41 |
| Test functions (`test_*`) | 223 |

---

## Largest modules (by line count, sampled)

| File | Lines |
|------|------:|
| `runner_api.py` | 1465 |
| `runner_api_routers/analytics.py` | 672 |
| `runner_api_routers/integrations.py` | 629 |
| `runner_api_routers/crm.py` | 582 |
| `runner_api_routers/agents.py` | 543 |
| `src/generation_crew.py` | 479 |
| `src/observability.py` | 458 |

---

## Potential evidence gaps

- Fresh coverage run not executed for this package (only `COVERAGE.md` snapshot).
- Full line-by-line inventory of every Pydantic response model field not enumerated.
- Complete route list inside `revenue_os/integrations/webhooks.py` not fully expanded beyond import usage.
- Runtime behavior of missing `revenue_os.agents.marketing_crew` module not executed (file absence recorded in gaps).
- No GitHub remote inspection (per instructions).

---

## Package index

| File |
|------|
| `01_REPOSITORY_INVENTORY.md` |
| `02_MODULE_MAP.md` |
| `03_DEPENDENCY_GRAPH.md` |
| `04_RUNTIME_TOPOLOGY.md` |
| `05_API_SURFACE.md` |
| `06_DATABASE_MODEL.md` |
| `07_DOMAIN_BOUNDARIES.md` |
| `08_AI_RUNTIME.md` |
| `09_MARKETING_OS.md` |
| `10_REVENUE_OS.md` |
| `11_SHARED_PLATFORM.md` |
| `12_TESTING.md` |
| `13_ARCHITECTURE_GAPS.md` |
| `SUMMARY.md` |
