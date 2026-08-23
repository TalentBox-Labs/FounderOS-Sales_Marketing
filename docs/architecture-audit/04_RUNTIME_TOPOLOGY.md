# 04 — Runtime Topology

Evidence from Dockerfiles, compose files, FastAPI startup hooks, scheduler, Celery, and service modules.

---

## Application startup (`runner_api:app`)

Evidence: `runner_api.py`

1. Construct `FastAPI` app (`title="WorkCrew CMS OS API"`, `version="2.0.0"`).
2. Add `CORSMiddleware` (`CORS_ALLOWED_ORIGINS`).
3. Add `StructuredLoggingMiddleware` (`runner_api_routers.middleware`).
4. `include_router` for domain routers.
5. Optionally `mount("/app", StaticFiles(...))` if `frontend/dist` exists.
6. Include `ui_router` last.
7. Call `initialize_automation()`.
8. On `@app.on_event("startup")` (present in file): DB schema create/migrate helpers, n8n bridge init, heartbeat init (imports observed around lines 344–355 in prior inspection).
9. On shutdown: stop heartbeat scheduler.

Process command (Docker):  
`uvicorn runner_api:app --host 0.0.0.0 --port ${PORT:-8000}`

---

## Application startup (`revenue_os.main:app`)

Evidence: `revenue_os/main.py`

1. FastAPI app `title="Revenue OS"`, `version="0.1.0"`.
2. CORS middleware.
3. Include `v1_router` and `webhooks_router`.
4. Startup: `Base.metadata.create_all(bind=engine)`.
5. Routes: `/health`, `/api/v1/dashboard`, `/`.

---

## API startup (HTTP)

| Surface | Host process | Evidence |
|---------|--------------|----------|
| Primary combined API | `runner_api:app` | Dockerfile, compose `api` |
| Standalone Revenue OS API | `revenue_os.main:app` | `revenue_os/main.py` |
| OpenAPI docs | FastAPI defaults `/docs`, `/redoc`, `/openapi.json` | described in `runner_api.py` FastAPI constructor text |

---

## Background workers

| Worker | Command / mechanism | Evidence |
|--------|---------------------|----------|
| Celery worker | `celery -A revenue_os.tasks.celery_app worker --loglevel=info` | `docker-compose.yml` service `worker` |
| Celery beat | `celery -A revenue_os.tasks.celery_app beat --loglevel=info` | `docker-compose.yml` service `beat` |
| Heartbeat scheduler | In-process `HeartbeatScheduler` thread/loop | `revenue_os/scheduler.py`; started from API startup when `HEARTBEAT_ENABLED` not disabled |

Celery app definition: `revenue_os/tasks/__init__.py`  
Broker/backend: `settings.REDIS_URL`  
Included task modules: `revenue_os.tasks.leads`, `outreach`, `agents`

---

## Queues

| Queue system | Evidence |
|--------------|----------|
| Redis as Celery broker/backend | `revenue_os/tasks/__init__.py`, compose `REDIS_URL` |
| Named queue topology beyond default Celery | **Repository evidence not found** |

---

## Cron jobs / schedulers

### Heartbeat jobs (`revenue_os/scheduler.py`)

Registered in `initialize_heartbeat()`:

| Job name | Default interval env | Default seconds |
|----------|----------------------|-----------------|
| `score_new_leads` | `HEARTBEAT_LEAD_SCORING_SEC` | 3600 |
| `check_deals_at_risk` | `HEARTBEAT_DEAL_RISK_SEC` | 21600 |
| `snapshot_pipeline_metrics` | `HEARTBEAT_METRICS_SNAPSHOT_SEC` | 3600 |
| `hermes_goal_check` | `HEARTBEAT_GOAL_CHECK_SEC` | 3600 |
| `sync_gmail_inbox` | `HEARTBEAT_GMAIL_SYNC_SEC` | 900 |

Disable flag: `HEARTBEAT_ENABLED` in (`0`, `false`, `False`).

### External pipeline scheduler entry

`src/tools/pipeline_orchestrator.py` docstring states it is an external scheduler entry (cron, CI).

### Celery beat

Compose defines a `beat` service; **Repository evidence not found** for a `beat_schedule` definition in the inspected Celery config block (`celery_app.conf.update` sets serializers/timezone/acks, not a schedule map in `__init__.py`).

---

## Docker services

From `docker-compose.yml`:

| Service | Image / build | Ports |
|---------|---------------|-------|
| `db` | `postgres:14` | 5432 |
| `redis` | `redis:7-alpine` | 6379 |
| `api` | build `.` | 8000 |
| `worker` | build `.` | — |
| `beat` | build `.` | — |

Volumes: `pgdata`, `chroma_data`.

Demo compose (`docker-compose.demo.yml`): same topology with demo credentials and bind mounts for chroma/output.

---

## Redis

- Compose service present.
- Used as Celery broker/backend (`REDIS_URL`).
- Settings default: `redis://localhost:6379/0` (`revenue_os/config.py`).

---

## Postgres

- Compose `POSTGRES_DB=revenue_os` (demo: `revenue_os_demo`).
- `settings.DATABASE_URL` default `postgresql://localhost:5432/revenue_os`.
- Render blueprint attaches managed DB `workcrew-crm-db`.

---

## SQLite

- Startup migration code branches on `engine.dialect.name == "sqlite"` in `runner_api.py`.
- On-disk file `pytest_local.db` observed at repository root.

---

## Vector DB

- ChromaDB declared in `requirements-revenue.txt`.
- Persist dir: `data/chroma_db` via `settings.CHROMA_PERSIST_DIR`.
- Client usage: `revenue_os/services/search_service.py` (`chromadb.PersistentClient`).
- RAG: `revenue_os/services/rag_service.py` (module docstring states retrieval uses chromadb/local embeddings).

---

## Filesystem

| Path | Runtime role |
|------|--------------|
| `input/{WEEK}/` | Canonical week content markdown |
| `output/` | QA reports, marketing outputs, pipeline summary JSON, sales presets |
| `data/runtime_config.json` | Active week / runtime flags |
| `data/week_runtime/` | Per-week profiles |
| `tracker.csv` | Content tracker rows |
| `templates/` | Jinja UI |
| `frontend/dist` | Built SPA for `/app` |
| `obsidian_vault/` | Knowledge notes (sync script) |

---

## External APIs / AI providers (runtime references)

| Provider | Evidence |
|----------|----------|
| CrewAI | Crews under `src/`; requirements |
| OpenAI | `ai_service.py` imports `openai.OpenAI` when key set |
| Ollama (via CrewAI LLM api_base) | `WORKCREW_OLLAMA_BASE_URL`, default model `ollama/llama3.1:8b` |
| Gemini | Key surfaced in MCP hub / settings |
| Anthropic / Claude as named SDK integration | **Repository evidence not found** as a first-class client module (no dedicated anthropic client file found in scan) |
| n8n | Outbound webhooks + inbound `/webhooks/n8n` |
| MCP providers | Prospecting provider status; `/api/v1/mcp/hub` in `runner_api.py` |
| Google Sheets / Gmail / Calendar | tools + integrations routers |
| Slack / WhatsApp / Hashnode / LinkedIn / Instagram / YouTube | env + integration modules |

---

## LLM configuration path (CrewAI)

Evidence: `src/base_crew.py::_build_llm`

- `WORKCREW_CREWAI_MODEL` (default `ollama/llama3.1:8b`)
- `WORKCREW_OLLAMA_BASE_URL` / `OLLAMA_BASE_URL`
- `WORKCREW_CREWAI_API_KEY`
- `WORKCREW_CREWAI_TEMPERATURE`
