# Founder OS — UI Surface Verification

**Status:** AUDIT COMPLETE (read-only)  
**Date:** 2026-08-09  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
**Method:** Code/route/template inspection only — **no inference from Architecture v2.1 destination docs**  
**Code changes in this audit:** **0**

---

## Separation (mandatory)

| Surface | What it is (verified) |
|---------|------------------------|
| **A. Internal Founder OS application UI** | Jinja2 ops shell (`templates/base.html` + `runner_api_routers/ui.py` / duplicate `runner_api.py` HTML handlers) + optional React CRM SPA under `/app` **when** `frontend/dist` exists |
| **B. Public Website Engine** | **No application code / routes found.** Only a prepare-only checklist doc exists. **Not a live UI.** |

This audit does **not** treat Architecture v2.1 Website Engine as implemented.

---

## 1. Application UI entry point

| Item | Evidence |
|------|----------|
| Process entry | `uvicorn runner_api:app` (documented in `runner_api.py` header) |
| FastAPI app | `runner_api:app` |
| Primary HTML shell | Jinja templates extending `templates/base.html` |
| UI router | `runner_api_routers/ui.py` included last via `app.include_router(ui_router)` |
| Duplicate handlers | `runner_api.py` also defines `@app.get` HTML for `/`, `/weeks`, `/pipeline`, `/marketing`, `/sales`, `/mcp`, `/analytics`, etc. (legacy co-location) |

**Canonical UI Entry (internal app):** `/` → dashboard (`dashboard.html` via `ui.py` `page_dashboard`, branded “WorkCrew CMS OS”).

---

## 2. Root / dashboard route

| Route | Handler | Template | Classification |
|-------|---------|----------|----------------|
| `GET /` | `ui.page_dashboard` (+ duplicate `runner_api.page_dashboard`) | `dashboard.html` extends `base.html` | **UI LIVE** |

---

## 3. Live HTML / UI routes (verified in code)

### A1 — Jinja routes in `runner_api_routers/ui.py`

| Route | Template / response |
|-------|---------------------|
| `GET /` | `dashboard.html` |
| `GET /weeks` | `weeks.html` |
| `GET /weeks/{week_id}` | `week_detail.html` |
| `GET /weeks/{week_id}/file/{filename}` | `file_view.html` |
| `GET /content-studio` | `content_studio.html` |
| `GET /content-studio/kanban` | `content_studio_kanban.html` |
| `GET /content-studio/{content_id}` | `content_studio_detail.html` |
| `GET /editorial` | `editorial_pending.html` |
| `GET /editorial/pending` | `editorial_pending.html` |
| `GET /editorial/{content_id}` | `editorial_detail.html` |
| `GET /publishing` | `publishing_queue.html` |
| `GET /publishing/{job_id}` | `publishing_detail.html` |
| `GET /pipeline` | `pipeline.html` |
| `GET /mcp` | `mcp.html` |
| `GET /marketing` | `marketing.html` |
| `GET /sales` | `sales.html` |
| `GET /analytics` | `analytics.html` |
| `GET /health` | **JSON** `{"status":"ok",…}` — not HTML |
| `GET /health/debug` | JSON |
| `GET /api/v1/health` | JSON |

### A2 — Additional HTML on `runner_api.py` (not only via `ui.py`)

| Route | Notes |
|-------|-------|
| `GET /orchestration/run/{run_id}` | HTMLResponse (inline render helper); template `orchestration_run.html` exists in tree |
| Duplicate `@app.get` for `/`, `/weeks`, `/pipeline`, `/mcp`, `/marketing`, `/sales`, `/analytics`, week/file views | Coexists with `ui_router` |

### A3 — React CRM SPA (`frontend/`)

| Item | Status |
|------|--------|
| Source routes | `frontend/src/App.jsx` HashRouter: Dashboard, Copilot, Contacts, Deals, Customers, Marketing, Analytics, Goals, Approvals, Automation, Agents, Knowledge Base, Integrations, Activity, Login |
| Mount point | `app.mount("/app", StaticFiles(...))` **only if** `frontend/dist` exists |
| `frontend/dist` present in repo (audit time) | **NO** |
| Runtime `/app` UI | **NOT LIVE** unless operator builds dist |

### B — Public Website Engine

| Item | Status |
|------|--------|
| Public site routes / render UI | **NONE in code** |
| Classification | **NO UI** |

---

## 4. Navigation structure (Jinja shell)

**Source:** `templates/base.html` sidebar (“WorkCrew / CMS OS”).

### Overview

| Label | `href` | Route exists? |
|-------|--------|---------------|
| Dashboard | `/` | YES |
| Analytics | `/analytics` | YES (HTML) |
| Content Calendar | `/weeks` | YES |
| Content Studio | `/content-studio` | YES |
| Studio Kanban | `/content-studio/kanban` | YES |
| Editorial Approval | `/editorial` | YES |
| Publishing | `/publishing` | YES |

### Pipeline

| Label | `href` | Route exists? |
|-------|--------|---------------|
| Run Pipeline | `/pipeline` | YES |
| QA Reports | `/qa` | **NO HTML route found** |
| Go-Live | `/publish` | **NO HTML route found** (legacy go-live is API/CLI; Publishing UI is `/publishing`) |
| Marketing | `/marketing` | YES |
| Sales | `/sales` | YES |

### System

| Label | `href` | Route exists? |
|-------|--------|---------------|
| MCP Hub | `/mcp` | YES |
| Settings | `/settings` | **NO HTML route found** |
| Health | `/health` | YES but **JSON**, not shell page |

**React CRM nav** (`frontend/src/App.jsx`): separate “WorkCrew CRM” navbar — **not** the Jinja `base.html` shell; not mounted without `frontend/dist`.

---

## 5. Templates / components used

### Jinja templates (`templates/`)

`base.html`, `dashboard.html`, `weeks.html`, `week_detail.html`, `file_view.html`, `content_studio.html`, `content_studio_detail.html`, `content_studio_kanban.html`, `editorial_pending.html`, `editorial_detail.html`, `publishing_queue.html`, `publishing_detail.html`, `pipeline.html`, `marketing.html`, `sales.html`, `analytics.html`, `mcp.html`, `orchestration_run.html`

### React components / pages (`frontend/src/`)

Pages listed in §3 A3; shared `components/Charts.jsx`, `Timeline.jsx`; auth via `api.js`.

### Public Website Engine templates

**None found.**

---

## 6–8. Domain classification (code-verified)

Legend: **UI LIVE** · **PARTIAL UI** · **API ONLY** · **NO UI** · **NOT VERIFIED**

### A. Internal Founder OS application UI

| Domain / surface | Classification | Evidence |
|------------------|----------------|----------|
| Dashboard / Overview | **UI LIVE** | `GET /` + `dashboard.html` |
| Content Calendar (`/weeks`) | **UI LIVE** | weeks + week detail + file view |
| Content Studio | **UI LIVE** | list/detail + API `/api/v1/content-studio` |
| Content Studio Kanban | **UI LIVE** | `/content-studio/kanban` in shell nav |
| Editorial Engine | **UI LIVE** | `/editorial*` + `/api/v1/editorial` |
| Publishing Engine (orchestration) | **UI LIVE** | `/publishing*` + `/api/v1/publishing` |
| Pipeline runner | **UI LIVE** | `/pipeline` |
| Marketing agent page | **UI LIVE** | `/marketing` (ops generate UI; not full Marketing OS engines) |
| Sales prospecting page | **UI LIVE** | `/sales` |
| Analytics (Jinja page) | **PARTIAL UI** | HTML page exists; deep analytics also under `/analytics` API router |
| MCP Hub | **UI LIVE** | `/mcp` |
| Orchestration run detail | **PARTIAL UI** | `/orchestration/run/{run_id}` HTML; not in sidebar |
| QA Reports (`/qa` nav) | **NO UI** | Nav link only; no route |
| Go-Live (`/publish` nav) | **NO UI** | Nav link only; `POST /go-live` API exists elsewhere |
| Settings (`/settings` nav) | **NO UI** | Nav link only |
| Health | **API ONLY** (as “page”) | JSON liveness; nav points here |
| CRM (React) | **PARTIAL UI** | Source complete; **`/app` not mounted** without `frontend/dist` |
| Revenue approvals / automation / agents / KB / copilot / integrations / goals / activity | **API ONLY** (or CRM-only if dist built) | Routers under `/api/v1/...`; CRM pages not live without dist |
| Prospecting / Outreach | **PARTIAL UI** | Sales Jinja page + APIs; not full Sales OS shell |
| SEO | **API ONLY** | `runner_api_routers/seo.py` |
| CSM | **API ONLY** | `/api/v1/csm` |
| Forecasting | **API ONLY** | `/api/v1/forecasting` |
| Hermes / Paperclip / WhatsApp / Heartbeat / n8n webhooks | **API ONLY** | routers present |
| Reporting | **API ONLY** | includes `POST /api/v1/reporting/.../publish` — not Go-Live UI |

### B. Public Website Engine

| Domain | Classification | Evidence |
|--------|----------------|----------|
| Website Engine (public site) | **NO UI** | No engine module/routes; checklist doc only |
| Website rendering / public pages | **NO UI** | Not present in runtime app |

### Architecture-named engines without UI (current code)

| Domain | Classification |
|--------|----------------|
| Campaign Engine | **NO UI** |
| GEO Engine | **NO UI** |
| AEO Engine | **NO UI** |
| Social Engine | **NO UI** |
| Email Engine | **NO UI** |
| Brand Engine | **NO UI** |
| Executive OS | **NO UI** |
| Knowledge OS (product UI) | **NO UI** / CRM source-only **PARTIAL** if counting unbuilt SPA |
| Customer Success OS | **API ONLY** (CSM) |
| Operations OS | **NOT VERIFIED** as distinct UI |

---

## 9. Single canonical Founder OS shell / navigation?

| Question | Verdict |
|----------|---------|
| One primary ops shell? | **PARTIAL** — Jinja `base.html` is the live ops shell for content/marketing/sales pages |
| Fully unified across all domains? | **NO** — React CRM is a second shell (unmounted without dist); many APIs have no shell entry; sidebar has dead links (`/qa`, `/publish`, `/settings`) |
| Public Website Engine shell? | **NO** — does not exist |

**Unified Founder OS Shell:** **PARTIAL**

---

## 10. Content Studio, Kanban, Editorial, Publishing accessible from that shell?

| Surface | In `base.html` nav? | Route live? |
|---------|---------------------|-------------|
| Content Studio | YES → `/content-studio` | YES |
| Studio Kanban | YES → `/content-studio/kanban` | YES |
| Editorial Approval | YES → `/editorial` | YES |
| Publishing | YES → `/publishing` | YES |

**Answer:** **YES** — all four are linked from the Jinja shell and have live HTML routes.

---

## Counts (for summary)

Counted as **Live UI Domains** (Jinja pages with working routes, excluding JSON health and dead nav):

1. Dashboard  
2. Content Calendar  
3. Content Studio  
4. Studio Kanban  
5. Editorial  
6. Publishing  
7. Pipeline  
8. Marketing (agent page)  
9. Sales (prospecting page)  
10. Analytics (Jinja)  
11. MCP Hub  
(+ Orchestration run detail as partial, not counted in “live domains” primary list)

**Live UI Domains:** **11** (primary Jinja surfaces above)

**API-only Domains (representative):** CRM/Approvals/Automation/Agents/Copilot/KB/SEO/CSM/Forecasting/Hermes/Integrations/WhatsApp/Heartbeat/Paperclip/Reporting/n8n — **≥15** (router surfaces without live shell pages when CRM dist absent)

**No-UI Domains (representative):** Website Engine, Campaign, GEO, AEO, Social, Email, Brand, Executive OS, QA page, Settings page, Go-Live page — **≥11**

Exact taxonomy is multi-axis (Architecture OS vs routers); counts above are audit-oriented, not Architecture v2.1 inventory.

---

## Impact

| Dimension | Value |
|-----------|-------|
| Code changes | **0** |
| Runtime changes | **0** |
| Redesign / implementation | **None** |

---

## Final audit block

```
FOUNDER OS UI AUDIT COMPLETE

Canonical UI Entry:
/

Unified Founder OS Shell:
PARTIAL

Live UI Domains:
11

API-only Domains:
15

No-UI Domains:
11

Code Changes:
0
```
