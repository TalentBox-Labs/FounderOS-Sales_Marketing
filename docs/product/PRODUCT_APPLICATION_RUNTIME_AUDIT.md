# Product Application Runtime Audit

**Sprint:** MDG0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY

## What Founder OS is today

A **single-instance, founder-operated web application** with strong local mode:

- Process: `uvicorn runner_api:app` (`Dockerfile`, `render.yaml`)
- Framework: FastAPI
- UI: Jinja2 SSR (`templates/`, `runner_api_routers/ui.py`)
- Optional SPA: React 18 + Vite CRM under `/app` **only if** `frontend/dist` exists (currently unmounted → 503)
- Secondary app: `revenue_os.main:app` (JWT User API) — **not** the production entry
- Data: Postgres (compose/hosted) or SQLite local; filesystem `tracker.csv` / `output/` for content OS
- Workers: Celery worker + beat (compose); in-process heartbeat
- Public website: **separate** static tree `output/website/` → Deployment Adapter → Cloudflare Pages

## Classification

**HYBRID** (single-tenant hosted web app + local-first mode + separate static public site)

Not LOCAL_ONLY (Docker/Render exist).  
Not DESKTOP.  
Not MULTI_TENANT_SAAS.

| Trait | Present |
|-------|---------|
| Application server | YES — uvicorn |
| Server-rendered UI | YES — Jinja |
| SPA components | DORMANT — CRM `/app` |
| Static site components | YES — Website Engine (separate deploy) |
| APIs | YES — `/api/v1/*` |
| Background workers | YES — Celery |
| Databases | YES — SQLAlchemy |
| Filesystem dependencies | YES — content/publishing/SEO artifacts |
| Docker | YES |
| Cloudflare | YES — **static website only** |
| Reverse proxy | Documented (nginx/Caddy); platform TLS on Render |

## Implication

HTTP routes do not make this multi-tenant SaaS. One deployment ≈ one founder’s operating world.
