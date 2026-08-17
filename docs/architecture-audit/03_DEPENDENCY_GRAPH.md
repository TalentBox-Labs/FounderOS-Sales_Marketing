# 03 — Dependency Graph

Direction of dependency only. Evidence from import statements and compose/requirements files.

---

## Module dependency direction

```
frontend (React)
    → HTTP → runner_api:app

runner_api.py
    → runner_api_routers.*
    → revenue_os.* (database, services, scheduler, integrations, automation)
    → templates/
    → frontend/dist (optional StaticFiles mount)
    → subprocess → src.* modules (pipeline_orchestrator, pipeline_runner, generation_crew, editor_crew, runtime_apply, go_live_helpers)
    → subprocess → revenue_os.agents.marketing_crew  (invoked by marketing router; see gaps)

runner_api_routers.*
    → runner_api_routers.utils / middleware
    → revenue_os.database / models / services / agents / analytics / forecasting / reporting / integrations / scheduler
    → src.sdr_crew (hermes router import)

revenue_os.main
    → revenue_os.api.v1.*
    → revenue_os.database / models / auth / services / integrations.webhooks

revenue_os.services.*
    → revenue_os.models.*
    → revenue_os.database
    → revenue_os.config
    → external SDKs (openai, chromadb, httpx) when configured

revenue_os.tasks (Celery)
    → revenue_os.config (REDIS_URL)
    → task modules: leads, outreach, agents

src.crews (generation, editor, qa, marketing, …)
    → src.base_crew → crewai
    → src.tools.csv_reader / runtime_paths / staging_overlay
    → YAML under src/
    → filesystem input/ output/ data/

src.tools.*
    → data/runtime_config.json, tracker.csv, input/, output/
    → optional Google / Hashnode clients
```

---

## Shared libraries (in-repo)

| Shared unit | Imported by |
|-------------|-------------|
| `runner_api_routers.utils` | Most runner routers |
| `revenue_os.database.SessionLocal` / `get_db` | Routers + services |
| `revenue_os.config.settings` | Services, tasks, auth |
| `src.base_crew.BaseCrew` | All crew classes |
| `src.tools.csv_reader.get_active_content` | Multiple crews |
| `src.tools.runtime_paths` | Pipeline tools / crews |

---

## Cross-module imports (examples with evidence)

| From | To | File evidence |
|------|----|---------------|
| `runner_api_routers.hermes` | `src.sdr_crew.SDRCrew` | `runner_api_routers/hermes.py` |
| `runner_api_routers.orchestration` | `revenue_os.services.go_to_market_orchestrator` | `orchestration.py` |
| `runner_api_routers.prospecting` | `revenue_os` models/services | `prospecting.py` |
| `src.generation_crew` | `src.crew` (`BASE_DIR`, helpers) | `generation_crew.py` |
| `runner_api` | `revenue_os.scheduler` | startup/shutdown in `runner_api.py` |

---

## Circular dependencies

Repository evidence of import cycles between top-level packages (`runner_api` ↔ `revenue_os` ↔ `src`):

**Repository evidence not found** for a closed import cycle among these packages.

Notes observed without claiming a cycle:
- `runner_api` imports `revenue_os` and launches `src` via **subprocess** (not import) for several pipeline steps.
- `revenue_os` does not show `import runner_api` in searched Python files.

---

## Infrastructure dependencies

| Dependency | Evidence |
|------------|----------|
| PostgreSQL 14 | `docker-compose.yml` service `db`; `DATABASE_URL` in config/compose |
| Redis 7 | `docker-compose.yml` service `redis`; Celery broker/backend |
| SQLite | `runner_api.py` contains SQLite dialect handling in `_migrate_missing_columns`; file `pytest_local.db` present on disk |
| ChromaDB | `requirements-revenue.txt`; `revenue_os/config.py` `CHROMA_PERSIST_DIR`; `revenue_os/services/search_service.py`, `rag_service.py` |
| Filesystem volumes | `input/`, `output/`, `data/`, compose volume `chroma_data` / demo bind mounts |

---

## Third-party services (configured via env / code references)

| Service | Evidence location |
|---------|-------------------|
| OpenAI | `OPENAI_API_KEY`, `revenue_os/services/ai_service.py` |
| Gemini | `GEMINI_API_KEY` in `.env.example` / MCP hub settings |
| Ollama / CrewAI LLM | `WORKCREW_CREWAI_MODEL`, `WORKCREW_OLLAMA_BASE_URL` |
| n8n | `N8N_WEBHOOK_BASE_URL`, `revenue_os/integrations/n8n.py`, `/webhooks/n8n` |
| Slack | `SLACK_*`, `integrations/slack.py` |
| Google Sheets | `WORKCREW_GOOGLE_*`, `src/tools/sheet_sync.py` etc. |
| Gmail | Gmail sync routes / heartbeat job |
| Hashnode | `HASHNODE_*`, `hashnode_publish.py` |
| LinkedIn / Instagram / YouTube | `.env.example` publishing vars |
| Apollo MCP / LinkedIn Sales Nav MCP / scraper | prospecting env + MCP hub |
| Hermes / OpenClaw agent URLs | `.env.example` |
| Stripe | `STRIPE_API_KEY` in settings |
| WhatsApp | `WHATSAPP_*`, whatsapp router/integrations |
| Render managed Postgres | `render.yaml` |

---

## Third-party Python packages (declared)

See `requirements.txt`, `requirements-api.txt`, `requirements-revenue.txt`, and `frontend/package.json` in `01_REPOSITORY_INVENTORY.md`.
