# 02 — Module Map

Evidence: directory layout, imports, and entry points in the local repository.

---

## 1. API / Runner (WorkCrew CMS OS API)

| Field | Evidence |
|-------|----------|
| **Purpose** | Combined FastAPI application titled "WorkCrew CMS OS API" |
| **Primary responsibility** | HTTP API, Jinja UI pages, mount of React CRM, startup of automation/heartbeat |
| **Entry point** | `runner_api.py` → `app = FastAPI(...)`; Docker CMD `uvicorn runner_api:app` |
| **Dependencies** | `runner_api_routers.*`, `revenue_os.*`, `src.*` (via subprocess / imports), Jinja2 templates, optional `frontend/dist` |
| **Consumers** | Docker `api` service, Render web service, tests (`TestClient`), browser UI |
| **Major files** | `runner_api.py`, `runner_api_routers/*.py`, `templates/*.html` |

---

## 2. Runner API Routers

| Field | Evidence |
|-------|----------|
| **Purpose** | Domain-specific FastAPI routers included by `runner_api.py` |
| **Primary responsibility** | Route handlers for pipeline, CRM, marketing, sales, observability, integrations |
| **Entry point** | Included via `app.include_router(...)` in `runner_api.py` lines 220–256 |
| **Dependencies** | `runner_api_routers.utils`, `revenue_os.database`, `revenue_os.services.*`, some `src.*` |
| **Consumers** | `runner_api:app` |
| **Major files** | `pipeline.py`, `ui.py`, `crm.py`, `prospecting.py`, `outreach.py`, `marketing.py`, `orchestration.py`, `hermes.py`, `agents.py`, `integrations.py`, `analytics.py`, `metrics.py`, `middleware.py`, `utils.py`, plus others listed in inventory |

---

## 3. Revenue OS

| Field | Evidence |
|-------|----------|
| **Purpose** | Package described in `revenue_os/main.py` as "AI-first Revenue Operating System" |
| **Primary responsibility** | ORM models, services, JWT auth API, integrations, scheduler, Celery tasks, forecasting, CSM, automation |
| **Entry point** | `revenue_os/main.py` (`app`); also imported by `runner_api.py` |
| **Dependencies** | SQLAlchemy, Redis/Celery (declared), ChromaDB, OpenAI client usage in services, CrewAI (requirements) |
| **Consumers** | `runner_api` routers; standalone `revenue_os.main` app; Celery worker/beat |
| **Major files** | `config.py`, `database.py`, `auth.py`, `scheduler.py`, `models/`, `services/`, `api/v1/`, `tasks/`, `integrations/`, `agents/`, `automation/`, `customer_success/`, `forecasting/`, `executive/`, `analytics/`, `reporting/`, `marketing/` |

---

## 4. Content / Marketing CMS (`src`)

| Field | Evidence |
|-------|----------|
| **Purpose** | Content pipeline crews, validators, tracker tools |
| **Primary responsibility** | CrewAI crews, YAML agent/task configs, filesystem validators, pipeline runners |
| **Entry point** | `src/main.py`; module CLIs (`src.generation_crew`, `src.editor_crew`, `src.tools.*`) |
| **Dependencies** | CrewAI, pandas, YAML, `data/runtime_config.json`, `tracker.csv`, `input/`, `output/` |
| **Consumers** | Pipeline HTTP routes (subprocess), QA/marketing flows, scripts, tests |
| **Major files** | `base_crew.py`, `generation_crew.py`, `editor_crew.py`, `qa_crew.py`, `marketing_crew.py`, `distribution_crew.py`, `artifact_crew.py`, `sdr_crew.py`, `csm_crew.py`, `crew.py`, `crew_contract.py`, `tools/*`, `agents*.yaml`, `tasks*.yaml` |

---

## 5. Authentication

| Field | Evidence |
|-------|----------|
| **Purpose** | Two auth mechanisms present |
| **Primary responsibility** | (A) API key Bearer for runner routes; (B) JWT user auth for `revenue_os.api.v1` |
| **Entry point** | `runner_api_routers/utils.py::_verify_api_key`; `revenue_os/auth.py` |
| **Dependencies** | `RUNNER_API_KEY` env; `SECRET_KEY`, bcrypt, python-jose |
| **Consumers** | Nearly all `runner_api_routers` endpoints; `revenue_os` v1 routers via `Depends(get_current_user)` |
| **Major files** | `runner_api_routers/utils.py`, `revenue_os/auth.py`, `revenue_os/models/user.py`, `revenue_os/api/v1/auth.py` |

---

## 6. AI / Agents

| Field | Evidence |
|-------|----------|
| **Purpose** | Multi-agent content and sales AI |
| **Primary responsibility** | CrewAI crews under `src/`; agent registry/execution under `revenue_os/agents/`; LLM chat helpers under `revenue_os/services/ai_service.py`, `copilot.py`, `sales_agents.py` |
| **Entry point** | Crew CLIs; HTTP routes under `/api/v1/agents`, `/api/v1/copilot`, `/api/v1/hermes`, pipeline generate/edit |
| **Dependencies** | CrewAI LLM env vars; OpenAI SDK when `OPENAI_API_KEY` set; YAML configs |
| **Consumers** | Pipeline, marketing, Hermes, outreach generate-email, knowledge-base ask |
| **Major files** | Crew modules listed above; `revenue_os/agents/*.py`; `revenue_os/services/ai_service.py`; `rag_service.py`; `search_service.py` |

---

## 7. Sales / Prospecting / Outreach

| Field | Evidence |
|-------|----------|
| **Purpose** | CRM contacts/deals, prospecting plans, outreach sequences |
| **Primary responsibility** | HTTP CRM/prospecting/outreach + services |
| **Entry point** | `runner_api_routers/crm.py`, `prospecting.py`, `outreach.py`; also `revenue_os/api/v1/{contacts,deals,outreach,prospecting}.py` |
| **Dependencies** | SQLAlchemy models `Contact`, `Deal`, `OutreachSequence`, etc.; `lead_prospecting_service` |
| **Consumers** | CRM UI pages, React frontend pages (`Contacts.jsx`, `Deals.jsx`), API clients |
| **Major files** | Routers above; `revenue_os/services/lead_prospecting_service.py`, `outreach_service.py`, `contact_service.py`, `deal_service.py` |

---

## 8. Marketing (multi-channel)

| Field | Evidence |
|-------|----------|
| **Purpose** | Marketing content generation and social publish |
| **Primary responsibility** | `/marketing/*` routes; `src/marketing_crew.py`; `revenue_os/integrations/social_publisher.py`; SEO keyword API |
| **Entry point** | `runner_api_routers/marketing.py`, `seo.py`; UI `/marketing` |
| **Dependencies** | CrewAI marketing YAML; social tokens in env; Hashnode tools under `src/tools/hashnode_publish.py` |
| **Consumers** | Marketing UI template; API callers |
| **Major files** | `src/marketing_crew.py`, `src/agents_marketing.yaml`, `src/tasks_marketing.yaml`, `runner_api_routers/marketing.py`, `revenue_os/marketing/*`, `revenue_os/integrations/social_publisher.py` |

---

## 9. Knowledge

| Field | Evidence |
|-------|----------|
| **Purpose** | Knowledge bases / articles / ask |
| **Primary responsibility** | CRUD + search/ask endpoints |
| **Entry point** | `runner_api_routers/knowledge_base.py` prefix `/api/v1/knowledge-base` |
| **Dependencies** | Models `KnowledgeBase`, `KnowledgeBaseArticle`; RAG/search services |
| **Consumers** | Frontend `KnowledgeBase.jsx` |
| **Major files** | `knowledge_base.py` router; `revenue_os/models/content.py`; `rag_service.py`; `search_service.py` |

---

## 10. Customer Success

| Field | Evidence |
|-------|----------|
| **Purpose** | Account health and recommendations |
| **Primary responsibility** | `/api/v1/csm/*` endpoints |
| **Entry point** | `runner_api_routers/csm.py` |
| **Dependencies** | `revenue_os/customer_success/*` |
| **Consumers** | API / frontend `Customers.jsx` |
| **Major files** | `csm.py`; `revenue_os/customer_success/account_health.py`, `recommendations.py`; `src/csm_crew.py` |

---

## 11. Automation / Workers / Schedulers

| Field | Evidence |
|-------|----------|
| **Purpose** | Workflows, heartbeat jobs, Celery tasks |
| **Primary responsibility** | Event/workflow automation; recurring heartbeat; Redis-backed Celery |
| **Entry point** | `initialize_automation()` in `runner_api.py`; `initialize_heartbeat()` on startup; Celery app `revenue_os.tasks.celery_app` |
| **Dependencies** | Redis URL; DB session; n8n bridge optional |
| **Consumers** | Docker `worker`/`beat`; `/api/v1/automation`, `/api/v1/heartbeat` |
| **Major files** | `revenue_os/automation/*`, `revenue_os/scheduler.py`, `revenue_os/tasks/*`, `runner_api_routers/automation.py`, `heartbeat.py`, `n8n_webhooks.py` |

---

## 12. Infrastructure / Ops

| Field | Evidence |
|-------|----------|
| **Purpose** | Deploy, observe, migrate |
| **Primary responsibility** | Docker/Render/CI; metrics/health; Alembic; scripts |
| **Entry point** | Compose/Dockerfile/CI; `/api/v1/system/health*`, `/metrics*` |
| **Dependencies** | Postgres, Redis volumes; curl healthcheck |
| **Consumers** | Operators, CI |
| **Major files** | `Dockerfile`, `docker-compose*.yml`, `render.yaml`, `.github/workflows/test.yml`, `migrations/`, `runner_api_routers/metrics.py`, `src/observability.py`, `scripts/*` |

---

## 13. Frontend (React CRM)

| Field | Evidence |
|-------|----------|
| **Purpose** | SPA named `workcrew-crm-frontend` |
| **Primary responsibility** | Browser CRM UI mounted at `/app` when `frontend/dist` exists |
| **Entry point** | `frontend/src/main.jsx`, `App.jsx` |
| **Dependencies** | axios, react-router-dom; API base via `frontend/src/api.js` |
| **Consumers** | End users via `/app` |
| **Major files** | `frontend/src/pages/*.jsx`, `components/*.jsx` |

---

## 14. Shared / Platform utilities

| Field | Evidence |
|-------|----------|
| **Purpose** | Cross-cutting helpers |
| **Primary responsibility** | Auth verify, subprocess runners, logging middleware, CSV/runtime path helpers, base crew |
| **Entry point** | Imported widely |
| **Dependencies** | stdlib + FastAPI security |
| **Consumers** | Routers, crews, tools |
| **Major files** | `runner_api_routers/utils.py`, `middleware.py`, `src/base_crew.py`, `src/tools/runtime_paths.py`, `csv_reader.py`, `revenue_os/config.py`, `database.py` |

---

## 15. Knowledge content / Obsidian

| Field | Evidence |
|-------|----------|
| **Purpose** | Human-editable vault and week content |
| **Primary responsibility** | Store markdown weeks, SEO notes, brand voice, QA notes |
| **Entry point** | Filesystem; `scripts/sync_obsidian_vault.py` |
| **Dependencies** | None (content) |
| **Consumers** | Operators; content pipeline reads `input/` primarily |
| **Major files** | `obsidian_vault/**`, `input/**` |
