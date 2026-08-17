# 14 — Router Inventory (Corrected)

Evidence date: Sprint A.6 recomputation from local repository  
`TB-FounderOS-Sales_Marketing`  
Source of registration: `runner_api.py`, `runner_api_routers/*.py`, `revenue_os/main.py`, `revenue_os/api/v1/__init__.py`, `revenue_os/integrations/webhooks.py`

---

## Corrected counts

| Metric | Corrected value | Evidence |
|--------|-----------------|----------|
| Live `app.include_router(...)` on `runner_api:app` | **26** | Lines 220–244 (25) + line 256 (`ui_router`) |
| Domain routers (excluding UI) | **25** | Lines 220–244 |
| UI router | **1** | Line 256 |
| Conditional static mounts | **1** | `app.mount("/app", …)` when `frontend/dist` exists (lines 248–252) |
| Additional `@app.(get\|post\|…)` handlers on `runner_api.py` | **25** | Decorator scan of `runner_api.py` (overlap with included routers) |
| `@router.*` decorators under `runner_api_routers/` | **245** | Aggregate count |
| `revenue_os.main` includes | **2** routers + **3** app routes | `v1_router`, `webhooks_router`; `/health`, `/api/v1/dashboard`, `/` |
| Mounted `revenue_os` v1 sub-routers | **10** | `revenue_os/api/v1/__init__.py` |
| `revenue_os/api/v1` `@router.*` decorators | **50** | Aggregate count |

**Correction vs Sprint A SUMMARY:**  
Sprint A text “25 (`include_router` list)” is replaced by: **26 live includes** = **25 domain + 1 UI**.

---

## Primary entry-point registration (`runner_api:app`)

Application construction: `runner_api.py` → `app = FastAPI(title="WorkCrew CMS OS API", version="2.0.0")`  
Docker/Render process: `uvicorn runner_api:app`

### Included routers (registration order)

| # | Symbol | Module | Prefix |
|---|--------|--------|--------|
| 1 | `pipeline_router` | `runner_api_routers/pipeline.py` | `""` |
| 2 | `orchestration_router` | `orchestration.py` | `/api/v1/orchestration` |
| 3 | `prospecting_router` | `prospecting.py` | `/api/v1/prospecting` |
| 4 | `outreach_router` | `outreach.py` | `/api/v1/outreach` |
| 5 | `marketing_router` | `marketing.py` | `""` |
| 6 | `metrics_router` | `metrics.py` | `/api/v1` |
| 7 | `hermes_router` | `hermes.py` | `/api/v1/hermes` |
| 8 | `automation_router` | `automation.py` | `/api/v1/automation` |
| 9 | `paperclip_router` | `paperclip.py` | `/api/v1/paperclip` |
| 10 | `csm_router` | `csm.py` | `/api/v1/csm` |
| 11 | `forecasting_router` | `forecasting.py` | `/api/v1/forecasting` |
| 12 | `integrations_router` | `integrations.py` | `/api/v1/integrations` |
| 13 | `reporting_router` | `reporting.py` | `/api/v1/reporting` |
| 14 | `agents_router` | `agents.py` | `/api/v1/agents` |
| 15 | `whatsapp_router` | `whatsapp.py` | `/api/v1/whatsapp` |
| 16 | `analytics_router` | `analytics.py` | `/analytics` |
| 17 | `heartbeat_router` | `heartbeat.py` | `/api/v1/heartbeat` |
| 18 | `n8n_webhooks_router` | `n8n_webhooks.py` | `/webhooks/n8n` |
| 19 | `goals_router` | `goals.py` | `/api/v1/hermes/goals` |
| 20 | `approvals_router` | `approvals.py` | `/api/v1/approvals` |
| 21 | `crm_router` | `crm.py` | `/api/v1/crm` |
| 22 | `copilot_router` | `copilot.py` | `/api/v1/copilot` |
| 23 | `seo_router` | `seo.py` | `/api/v1/seo` |
| 24 | `knowledge_base_router` | `knowledge_base.py` | `/api/v1/knowledge-base` |
| 25 | `analytics_depth_router` | `analytics_depth.py` | `/api/v1/analytics-depth` |
| 26 | `ui_router` | `ui.py` | *(no prefix)* |

### Mounted static app

| Mount path | Condition | Name |
|------------|-----------|------|
| `/app` | `frontend/dist` is a directory | `crm-frontend` |

### Duplicate `@app` handlers (same process, later in file)

`runner_api.py` also declares **25** `@app` route decorators after router inclusion, including overlapping paths such as:

- HTML: `/`, `/weeks`, `/pipeline`, `/mcp`, `/marketing`, `/sales`, `/analytics`
- Prospecting: `/api/v1/prospecting/*`
- Orchestration: `/api/v1/orchestration/*`
- Marketing: `/marketing/generate`, `/marketing/dry-run`, `/marketing/publish`
- MCP hub: `/api/v1/mcp/hub`

FastAPI keeps the first matching registered route; included routers are registered **before** these `@app` duplicates.

---

## Secondary entry-point registration (`revenue_os.main:app`)

| Registration | Prefix / path |
|--------------|---------------|
| `app.include_router(v1_router)` | `/api/v1` + sub-routers |
| `app.include_router(webhooks_router)` | `/api/v1/integrations/webhooks` (router object has **no** `@router` endpoints) |
| `GET /health` | app-level |
| `GET /api/v1/dashboard` | app-level |
| `GET /` | app-level |

### Mounted v1 sub-routers (10)

| Sub-router | Prefix under `/api/v1` |
|------------|------------------------|
| auth | `/auth` |
| agents | `/agents` |
| command_center | `/command-center` |
| contacts | `/contacts` |
| companies | `/companies` |
| deals | `/deals` |
| outreach | `/outreach` |
| social | `/social` |
| orchestration | `/orchestration` |
| prospecting | `/prospecting` |

---

## Webhook-related HTTP surface (cross-reference GAP-010)

| Surface | Prefix / paths | Registered on |
|---------|----------------|---------------|
| Integrations webhook CRUD | `/api/v1/integrations/webhooks/subscribe`, `/subscriptions`, `/subscriptions/{id}` | `runner_api` via `integrations_router` |
| n8n inbound | `/webhooks/n8n/catalog`, `/webhooks/n8n/{event_name}` | `runner_api` via `n8n_webhooks_router` |
| `revenue_os.integrations.webhooks.router` | prefix `/api/v1/integrations/webhooks` | `revenue_os.main` only; **zero** route decorators on that router object |

---

## Non-router files in `runner_api_routers/`

| File | Role |
|------|------|
| `__init__.py` | Package |
| `utils.py` | Shared helpers / auth dependency |
| `middleware.py` | `StructuredLoggingMiddleware` |

Total `runner_api_routers/*.py` files: **29** (26 router modules + 3 support files).
