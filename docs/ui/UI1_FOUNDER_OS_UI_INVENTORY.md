# UI1 — Founder OS UI Inventory

**Sprint:** UI1  
**Date:** 2026-08-13  
**Mode:** Audit only — no runtime changes

---

## Frontend frameworks

| Stack | Path | Role |
|-------|------|------|
| **Jinja2 + vanilla JS** | `templates/`, `runner_api_routers/ui.py` | **Canonical primary shell** (live locally) |
| **React 18 + Vite** | `frontend/` | CRM SPA — **UNMOUNTED** at `/app` without `frontend/dist` |
| FastAPI docs | `/docs`, `/redoc` | **LIVE_INTERNAL** |

**Entry point:** `uvicorn runner_api:app` → `runner_api.py`

---

## Classification summary

| Class | Count | Notes |
|-------|------:|-------|
| **LIVE_MOUNTED** | **21** | 20 Jinja routes + orchestration run page |
| **LIVE_INTERNAL** | **3+** | Swagger/ReDoc, Vite dev :5173 |
| **UNMOUNTED** | **1** | React CRM `/app` (503 when dist absent) |
| **PARTIAL** | **4** | Jinja vs React overlap (sales, analytics, marketing, CRM) |
| **API_ONLY** | **30+** | `runner_api_routers/*` JSON domains |
| **DEAD** | **13+** | 9 shadowed handlers, 3 deferred nav, legacy static |

---

## LIVE_MOUNTED surfaces (Jinja)

| Route | Template |
|-------|----------|
| `/` | `dashboard.html` |
| `/weeks`, `/weeks/{id}`, `/weeks/{id}/file/{name}` | weeks/detail/file |
| `/content-studio/*` | content studio (3) |
| `/editorial/*` | editorial (3) |
| `/publishing/*` | publishing (2) |
| `/pipeline` | `pipeline.html` |
| `/mcp` | `mcp.html` |
| `/marketing` | `marketing.html` |
| `/sales` | `sales.html` (prospecting) |
| `/analytics` | `analytics.html` |
| `/seo`, `/seo/technical`, `/seo/{slug}` | SEO (3) |
| `/orchestration/run/{id}` | `orchestration_run.html` |

**Layout/nav:** `templates/base.html` — sidebar "WorkCrew CMS OS"

---

## UNMOUNTED — React CRM (`frontend/`)

| Item | Evidence |
|------|----------|
| Mount condition | `frontend/dist` exists (`runner_api.py:253-285`) |
| Local state | **503 JSON** `not_built` — `tests/test_r1c_route_hygiene.py` |
| Docker | Built in Dockerfile → **LIVE_MOUNTED** in container |
| Routes | 16 hash routes in `App.jsx` (Dashboard, Contacts, Deals, Approvals, …) |

**Why unmounted locally:** `frontend/dist` not built; frozen disposition **RETAIN_AND_REFACTOR_LATER** (CRM UI).

---

## API_ONLY (no dedicated HTML)

Key domains: `/api/v1/crm`, `/api/v1/hermes`, `/api/v1/seo`, `/api/v1/editorial`, `/api/v1/publishing`, `/api/v1/qualified-demand` (MC04), `/api/v1/approvals`, `/api/v1/heartbeat`, `/api/v1/prospecting`, etc.

Jinja pages **consume** some APIs (SEO, editorial, sales prospecting); React SPA intended consumer when mounted.

---

## DEAD / dormant

| Item | Evidence |
|------|----------|
| Shadowed `@app.get` in `runner_api.py` | Registered after `ui_router` — never reached |
| `/qa`, `/publish`, `/settings` nav | Commented DEFERRED in `base.html` |
| `revenue_os/static/index.html` | Separate `revenue_os/main.py` app — not primary |
| `/weeks/{id}/qa-report` | No route (404 test) |

---

## Canonical frontend shell

**Jinja2 Founder OS shell** via `runner_api_routers/ui.py` + `templates/base.html`.

Unified Founder OS UI: **PARTIAL** (dual stack; CRM unmounted locally).
