# 05 — API Surface

Evidence: FastAPI route decorators and router prefixes in the local repository.  
Approximate decorated route count across scanned files: **323** (includes duplicate definitions in `runner_api.py` and routers).

---

## Authentication / authorization / middleware (shared)

| Mechanism | Evidence |
|-----------|----------|
| Runner API key | `HTTPBearer` + `Depends(_verify_api_key)` in `runner_api_routers/utils.py`; env `RUNNER_API_KEY`; if unset, verify returns `None` (auth disabled) |
| Revenue OS JWT | `revenue_os/auth.py` `get_current_user`; applied as router dependencies in `revenue_os/api/v1/__init__.py` for non-auth routes |
| n8n inbound | `runner_api_routers/n8n_webhooks.py` `_verify_n8n_auth` |
| CORS | `CORSMiddleware` on both apps |
| Structured logging middleware | `StructuredLoggingMiddleware` on `runner_api` |
| Validation | Pydantic `BaseModel` request bodies on many routes; FastAPI path/query validation |
| Versioning | Many routes under `/api/v1/...`; marketing/pipeline also use unprefixed paths; analytics router uses `/analytics` |

---

## Primary app: `runner_api:app`

### Included routers (`runner_api.py`)

| Router module | Prefix | Auth pattern |
|---------------|--------|--------------|
| `pipeline` | `` (empty) | `_verify_api_key` |
| `orchestration` | `/api/v1/orchestration` | `_verify_api_key` |
| `prospecting` | `/api/v1/prospecting` | `_verify_api_key` |
| `outreach` | `/api/v1/outreach` | `_verify_api_key` |
| `marketing` | `` (empty) | `_verify_api_key` |
| `metrics` | `/api/v1` | mixed / health endpoints |
| `hermes` | `/api/v1/hermes` | `_verify_api_key` |
| `automation` | `/api/v1/automation` | `_verify_api_key` |
| `paperclip` | `/api/v1/paperclip` | `_verify_api_key` |
| `csm` | `/api/v1/csm` | `_verify_api_key` |
| `forecasting` | `/api/v1/forecasting` | `_verify_api_key` |
| `integrations` | `/api/v1/integrations` | `_verify_api_key` |
| `reporting` | `/api/v1/reporting` | `_verify_api_key` |
| `agents` | `/api/v1/agents` | `_verify_api_key` |
| `whatsapp` | `/api/v1/whatsapp` | `_verify_api_key` |
| `analytics` | `/analytics` | `_verify_api_key` |
| `heartbeat` | `/api/v1/heartbeat` | `_verify_api_key` |
| `n8n_webhooks` | `/webhooks/n8n` | n8n auth dependency |
| `goals` | `/api/v1/hermes/goals` | `_verify_api_key` |
| `approvals` | `/api/v1/approvals` | `_verify_api_key` |
| `crm` | `/api/v1/crm` | `_verify_api_key` |
| `copilot` | `/api/v1/copilot` | `_verify_api_key` |
| `seo` | `/api/v1/seo` | `_verify_api_key` |
| `knowledge_base` | `/api/v1/knowledge-base` | `_verify_api_key` |
| `analytics_depth` | `/api/v1/analytics-depth` | `_verify_api_key` |
| `ui` | (none) | HTML pages; health endpoints |

Static mount: `/app` → `frontend/dist` when directory exists.

---

### Pipeline (`runner_api_routers/pipeline.py`)

| Method | Path |
|--------|------|
| POST | `/run` |
| POST | `/validate` |
| POST | `/generate` |
| POST | `/edit` |
| POST | `/switch-week` |
| POST | `/go-live` |
| POST | `/run-pipeline` |

Request model: `WeekRequest` (`week`, `topic`, `url` optional fields).

---

### Marketing (`runner_api_routers/marketing.py`)

| Method | Path |
|--------|------|
| POST | `/marketing/generate` |
| POST | `/marketing/dry-run` |
| POST | `/marketing/publish` |

---

### UI / health (`runner_api_routers/ui.py`)

| Method | Path | Response |
|--------|------|----------|
| GET | `/` | HTML |
| GET | `/weeks` | HTML |
| GET | `/weeks/{week_id}` | HTML |
| GET | `/weeks/{week_id}/file/{filename:path}` | HTML |
| GET | `/pipeline` | HTML |
| GET | `/mcp` | HTML |
| GET | `/marketing` | HTML |
| GET | `/sales` | HTML |
| GET | `/analytics` | HTML |
| GET | `/health` | JSON |
| GET | `/health/debug` | JSON |
| GET | `/api/v1/health` | JSON |

---

### Prospecting (`/api/v1/prospecting`)

| Method | Path |
|--------|------|
| GET | `/providers` |
| POST | `/plan` |
| POST | `/execute` |
| GET | `/presets` |
| POST | `/presets/save` |
| POST | `/import` |

---

### Outreach (`/api/v1/outreach`)

| Method | Path |
|--------|------|
| GET | `/sequences` |
| POST | `/sequences` |
| GET | `/sequences/{seq_id}` |
| PATCH | `/sequences/{seq_id}` |
| POST | `/sequences/{seq_id}/steps` |
| POST | `/sequences/{seq_id}/enroll` |
| POST | `/generate-email` |

---

### Orchestration (`/api/v1/orchestration`)

| Method | Path |
|--------|------|
| GET | `/backends` |
| GET | `/logs` |
| POST | `/plan` |
| POST | `/run` |

---

### CRM (`/api/v1/crm`)

| Method | Path |
|--------|------|
| GET | `/contacts` |
| GET | `/contacts/{contact_id}` |
| POST | `/contacts` |
| POST | `/contacts/{contact_id}/enrich` |
| GET | `/deals` |
| GET | `/deals/{deal_id}` |
| POST | `/deals` |
| GET | `/pipeline` |
| GET | `/activities` |
| POST | `/activities` |
| POST | `/activities/{activity_id}/complete` |
| GET | `/followups` |

---

### Hermes (`/api/v1/hermes`)

| Method | Path |
|--------|------|
| POST | `/score-contacts` |
| GET | `/lead-scores` |
| GET | `/score-distribution` |
| POST | `/qualify-contacts` |
| GET | `/pipeline-health` |
| GET | `/pipeline-forecast` |
| GET | `/deals-at-risk` |
| GET | `/revenue-summary` |
| POST | `/sdr-outreach` |

Goals sub-router prefix `/api/v1/hermes/goals`: POST ``, GET ``, GET `/{goal_id}`, POST `/{goal_id}/check|pause|resume`.

---

### Agents (`/api/v1/agents`)

Endpoints include registry CRUD/messaging, tasks, decisions, workflows, safeguards, monitor/audit/performance/health, and sales helpers:

- POST `/sales/{contact_id}/research`
- POST `/sales/{contact_id}/cold-email`
- POST `/sales/{contact_id}/linkedin-opener`
- POST `/sales/{contact_id}/sequence`
- POST `/sales/{contact_id}/handle-reply`

(Full decorator list: 28 routes in `agents.py`.)

---

### Automation (`/api/v1/automation`)

Workflows CRUD/toggle/presets/executions; events history; action/event types; health (15 routes).

---

### Integrations (`/api/v1/integrations`)

Connectors, email, webhooks, Slack, Google/Outlook calendar, Gmail OAuth/sync, health (23 routes).

---

### Analytics (`/analytics`)

Metrics, data-points, dashboards, reports, aggregate, compare-periods, trends, forecast, anomalies, health (19 routes).

---

### Analytics depth (`/api/v1/analytics-depth`)

`/attribution`, `/ltv`, `/cac`, `/spend` (+ POST/DELETE), `/agent-productivity`.

---

### Metrics / system health (`/api/v1`)

| Method | Path |
|--------|------|
| GET | `/metrics` |
| GET | `/metrics/prometheus` |
| GET | `/system/health` |
| GET | `/system/health/{component}` |
| GET | `/crew/executions` |
| GET | `/crew/summary` |
| GET | `/trace/info` |
| POST | `/metrics/reset` |
| GET | `/status/summary` |

---

### Other runner routers (summary)

| Prefix | Notable paths |
|--------|---------------|
| `/api/v1/paperclip` | dashboard, kpis, insights, recommendations, health-score, forecast-accuracy, strategic-summary |
| `/api/v1/csm` | accounts health/at-risk/expansion, recommendations, review, health |
| `/api/v1/forecasting` | churn, revenue-forecast, deal-win-probability, expansion, scenarios, model-performance, health |
| `/api/v1/reporting` | templates, generate, schedules, publish, deliveries, health |
| `/api/v1/whatsapp` | configure, contacts, templates, messages, broadcasts, communities, content, health |
| `/api/v1/seo` | keywords CRUD/checks, summary |
| `/api/v1/knowledge-base` | bases, articles, search, ask |
| `/api/v1/copilot` | POST `/chat` |
| `/api/v1/approvals` | list/create/approve/reject |
| `/api/v1/heartbeat` | status, runs, run/{job_name}, activity |
| `/webhooks/n8n` | GET `/catalog`, POST `/{event_name}` |

---

### Duplicate handlers still defined on `runner_api.py`

`runner_api.py` also declares overlapping HTML and API routes (examples from decorator scan):

- GET `/`, `/weeks`, `/weeks/{week_id}`, `/pipeline`, `/mcp`, `/marketing`, `/sales`, `/analytics`
- GET `/api/v1/mcp/hub`
- Prospecting and orchestration endpoints
- POST `/marketing/generate|dry-run|publish`
- GET `/api/v1/analytics`

Exact precedence depends on FastAPI registration order (routers included before some `@app` handlers; UI router last).

---

## Standalone app: `revenue_os.main:app`

### Mounted routers

`v1_router` prefix `/api/v1` includes:

| Sub-router | Prefix | Auth |
|------------|--------|------|
| auth | `/auth` | public register/login; `/me` uses token |
| agents | `/agents` | JWT |
| command_center | `/command-center` | JWT |
| contacts | `/contacts` | JWT |
| companies | `/companies` | JWT |
| deals | `/deals` | JWT |
| outreach | `/outreach` | JWT |
| social | `/social` | JWT |
| orchestration | `/orchestration` | JWT |
| prospecting | `/prospecting` | JWT |

Plus `webhooks_router` from `revenue_os.integrations.webhooks`.

### App-level routes

| Method | Path |
|--------|------|
| GET | `/health` |
| GET | `/api/v1/dashboard` |
| GET | `/` |

### Auth routes (`/api/v1/auth`)

| Method | Path | Response model (declared) |
|--------|------|---------------------------|
| POST | `/register` | `TokenResponse` |
| POST | `/login` | `TokenResponse` |
| GET | `/me` | `UserResponse` |

### Sample domain routes (Revenue OS v1)

- Companies: GET/POST ``, GET/PUT/DELETE `/{company_id}`
- Contacts: GET/POST ``, GET `/search`, GET/PUT/DELETE `/{contact_id}`
- Deals: pipelines CRUD-ish + deals CRUD + forecast/health
- Outreach: sequences, activities, generate-email
- Agents: score-lead, outreach-sequence, match-candidate, screen-resume
- Social: posts/content CRUD + publish
- Prospecting: providers, plan
- Orchestration: backends, plan, run, logs

---

## Controllers

Repository uses FastAPI route functions on `APIRouter` instances.  
**Repository evidence not found** for a separate MVC “controller” layer naming convention beyond routers + services.

---

## Response models

- Many runner routes return `dict[str, Any]`.
- Revenue OS v1 uses Pydantic response models (e.g. `ContactResponse`, `DealResponse`, `TokenResponse`) declared beside those routers.
- OpenAPI tag metadata and schema helpers also exist in `src/openapi_schemas.py` (presence evidenced by file).
