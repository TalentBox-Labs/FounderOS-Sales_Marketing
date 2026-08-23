# R0 — UI / Route / Template Audit (NOVA)

**Date:** 2026-08-11 · **Mode:** AUDIT ONLY

---

## Counts

| Metric | N |
|--------|--:|
| Templates | 21 |
| Live Jinja routes (`ui.py`) | 18 HTML + health JSON |
| Shadowed duplicate `@app` HTML handlers | 9 |
| Orphan templates | **1** (`orchestration_run.html`) |
| Dead nav (active) | **1** (`/health` → JSON) |
| Broken in-page targets | **5** |
| React `/app` | NOT LIVE (`frontend/dist` absent) |
| Root `static/` | ABSENT |

---

## Registration

Primary: `uvicorn runner_api:app` → domain routers → conditional `/app` mount → `ui_router` → later shadowed `@app.get` HTML duplicates.

Secondary: `revenue_os.main:app` + `revenue_os/static/index.html`.

---

## Nav vs live

All sidebar links OK except **Health → `/health` (JSON)**. Deferred commented: `/qa`, `/publish`, `/settings`.

---

## Broken in-page targets

1. `GET /weeks/{id}/qa-report`  
2. `GET /marketing/run/{slug}`  
3. `POST /qa` (pipeline UI)  
4. `POST /sheet-sync` (pipeline UI)  
5. `GET /app` (dist absent)

**Plus runtime:** `GET /marketing` returns **500** (`integration_status` undefined) — template/context bug.

---

## Orphan / duplicate

| Item | Class |
|------|-------|
| `orchestration_run.html` | ORPHAN (inline HTML used instead) |
| `ui.py` vs `runner_api.py` page handlers | DUPLICATE HANDLERS |
| `/weeks` vs Content Studio | DUPLICATE UX |
| Jinja vs React CRM pages | DUPLICATE SURFACES (React off) |

---

## CMS naming (STALE branding)

`WorkCrew CMS OS` / `CMS OS` in API title, `base.html`, most page titles. SEO pages partially use Founder OS.

---

## API-only domains

CRM, Approvals, Automation, Agents, Copilot, KB, Integrations, Goals, Hermes, CSM, Forecasting, Outreach, Prospecting, Paperclip, WhatsApp, Heartbeat, Reporting, Metrics, n8n webhooks — no dedicated Jinja shell pages.
