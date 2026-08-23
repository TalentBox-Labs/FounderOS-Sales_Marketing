# SALES A0 — UI Audit (BEACON)

**Sprint:** SALES A0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY — no UI implementation

---

## Verdict

Sales appears in the Founder OS Jinja shell as **prospecting ops** (`/sales`). Full CRM screens live in an optional React SPA that is **UNMOUNTED** when `frontend/dist` is absent.

**Existing CRM UI: UNMOUNTED**

---

## Live shell routes (Jinja)

| Route | Sales relevance | Status |
|-------|-----------------|--------|
| `/sales` | Prospecting / SDR operator UI | **LIVE** (200) |
| `/pipeline` | Content week pipeline | **LIVE** — **not** deal CRM |
| `/analytics` | Analytics | LIVE (shared) |
| `/app` | React CRM | **503** `not_built` locally |
| Nav link to `/app` | — | **Absent** in `base.html` |

Nav (`templates/base.html`) includes `/sales`, `/pipeline`, `/analytics` — not `/app`.

---

## React CRM (`frontend/`)

| Item | Finding |
|------|---------|
| Package | `workcrew-crm-frontend` (React 18 + Vite 5) |
| Pages | Dashboard, Contacts, ContactDetail, Deals, DealDetail, Customers, Marketing, Analytics, Goals, Approvals, Automation, Agents, KnowledgeBase, Integrations, Activity, Copilot, Login |
| Dist | **Absent** |
| Mount | `runner_api.py` StaticFiles `/app` iff dist exists |
| Docker | Builds frontend → dist present in image path |
| Gap | SPA cannot advance deal stages via runner CRM (no PATCH) |

---

## Capability presentation

| Capability | How operator sees it today |
|------------|----------------------------|
| Prospecting | Jinja `/sales` |
| Contacts/Deals CRM | SPA only (unmounted) or raw API |
| Companies | API-only (no shell page) |
| Forecasting | API-only |
| Approvals / Goals | SPA pages when built; APIs live |
| Content pipeline | Jinja `/pipeline` (Marketing) |

---

## Dead / API-only UI notes

- No UI_ONLY Sales capability without a backing API found.  
- Deal kanban in SPA is display-oriented relative to runner API limits.  
- Dual JWT UI path via `revenue_os.main` static is PLACEHOLDER when not built.

---

## Classification summary (UI)

| Surface | Class |
|---------|-------|
| `/sales` | LIVE |
| `/app` CRM | PARTIAL / UNMOUNTED |
| Companies screens | NOT_IMPLEMENTED in shell |
| Deal stage board (writable) | NOT_IMPLEMENTED on runner path |
