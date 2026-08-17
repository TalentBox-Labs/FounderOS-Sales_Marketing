# SaaS S0 — Current Architecture

**Sprint:** SaaS S0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY

## Current product model

**HOSTED_SINGLE_USER / HYBRID** — single-instance FastAPI Founder OS with strong local mode.  
**Not** multi-tenant SaaS.

## Authoritative map

| Component | Evidence | Role |
|-----------|----------|------|
| Primary entry | `runner_api.py` → `uvicorn runner_api:app` | Production process |
| Secondary entry | `revenue_os/main.py` | JWT User API — **not** Docker/Render entry |
| UI | Jinja2 `templates/` + `runner_api_routers/ui.py` | Canonical Founder OS shell |
| SPA | `frontend/` mounted at `/app` only if `frontend/dist` exists | Dormant CRM; not Founder OS shell |
| APIs | `runner_api_routers/*` | Domain + cockpit + operator + MDG |
| DB | SQLAlchemy `DATABASE_URL` | Postgres (compose/Render) or SQLite local |
| FS SoT | `tracker.csv`, `output/` | Content / editorial / publishing / website |
| Workers | Celery worker/beat in compose; in-process heartbeat | PARTIAL on Render (no Redis in `render.yaml`) |
| Public website | `output/website/` → Cloudflare Pages | **SEPARATE** from Founder OS app |
| Auth (primary) | Shared `RUNNER_API_KEY` | Instance-global |
| Operator identity | `FOUNDER_OS_OPERATOR_NAME` | Instance-global trusted human |
| Secrets | Env + vault PK=`connector_name` | Instance-global |

## Public website vs Founder OS application

| Surface | Host |
|---------|------|
| Public website | Cloudflare Pages (static) |
| Founder OS application | uvicorn / Docker / Render |

**SAME_APPLICATION: NO — SEPARATE_APPLICATIONS**

## Implication for SaaS

HTTP + Docker ≠ multi-tenant SaaS. One deployment ≈ one founder’s world until Organization isolation exists.
