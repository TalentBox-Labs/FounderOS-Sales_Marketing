# Founder OS — Internal UI Shell Hardening Plan

**Status:** EVIDENCE-BACKED PLAN + MINIMAL SAFE FIX  
**Date:** 2026-08-09  
**Agent:** B — Internal UI Shell Hardening  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
**Prior audit:** [`FOUNDER_OS_UI_SURFACE.md`](./FOUNDER_OS_UI_SURFACE.md)  
**Method:** Code/route/template inspection; no redesign; no Architecture v2.1 destination inference  

---

## Mission constraints (applied)

| Rule | Application |
|------|-------------|
| Do NOT redesign UI | No layout/visual/IA redesign |
| Repair only if all gates pass | Clear broken nav · no API/business contract change · no architecture impact · no Agent A collision · trivial rollback |
| Owned files | **Must create** this plan; **optional** `templates/base.html` only |
| Do NOT touch | `src/tools/website_engine/**`, `src/tools/publishing_engine.py`, `tests/test_website_engine.py`, `docs/marketing/M2_*`, `runner_api_routers/publishing.py`, editorial*, content_studio* |
| Prefer NOT touch | `runner_api_routers/ui.py` (document instead) |

---

## Classification legend

| Code | Meaning |
|------|---------|
| **A** | BROKEN LIVE NAVIGATION — sidebar/shell link to non-existent HTML route |
| **B** | STALE LINK — in-page or secondary link to missing route/page |
| **C** | API-ONLY CAPABILITY — router/API exists; no shell page |
| **D** | PLANNED DOMAIN — named in product/architecture; no live UI in code |
| **E** | FRONTEND BUILD/DEPLOYMENT GAP — source exists; runtime mount missing |
| **F** | NOT VERIFIED |

---

## 1. Verdict

| Dimension | Value |
|-----------|-------|
| **Internal Shell** | **PARTIAL** |
| Immediate Safe Fixes applied | **1** (`templates/base.html` dead nav removal) |
| Deferred UI Gaps documented | **8** |
| Application code changes | **1** |
| Plan doc | This file |

**Why PARTIAL (not BROKEN):** Canonical Jinja shell at `/` is live; Content Studio / Kanban / Editorial / Publishing / Pipeline / Marketing / Sales / Analytics / MCP / Weeks all have live HTML routes and (post-fix) working sidebar entries. Failures are confined to dead/stale links, JSON-as-“page” Health, unmounted CRM SPA, and API-only Revenue surfaces.

**Why not HEALTHY:** Pre-fix sidebar contained three dead HTML destinations; CRM `/app` unmounted without `frontend/dist`; Sales/Revenue/CRM experiences are split and incomplete vs product naming.

---

## 2. Evidence inventory

### 2.1 Dead sidebar destinations (pre-fix)

| Nav label | `href` | HTML route in `ui.py` / `runner_api.py`? | Class | Decision |
|-----------|--------|------------------------------------------|-------|----------|
| QA Reports | `/qa` | **NO** `GET /qa` | **A** | Remove; comment deferred — do not invent QA page |
| Go-Live | `/publish` | **NO** `GET /publish` (Publishing UI is `GET /publishing`) | **A** | Remove; comment — use `/publishing`; legacy `POST /go-live` is API-only |
| Settings | `/settings` | **NO** `GET /settings` | **A** | Remove; comment deferred — do not invent settings page |

**Evidence:**

- Sidebar source: `templates/base.html` (Pipeline + System sections).
- Live HTML routes in `runner_api_routers/ui.py`: `/`, `/weeks*`, `/content-studio*`, `/editorial*`, `/publishing*`, `/pipeline`, `/mcp`, `/marketing`, `/sales`, `/analytics`, plus JSON `/health*`.
- Grep for `@router.get("/qa"|"/publish"|"/settings")` / `@app.get(...)` equivalents: **no matches**.
- Publishing Engine UI: `GET /publishing`, `GET /publishing/{job_id}` in `ui.py` (already linked under Overview → Publishing).
- Legacy go-live: `POST /go-live` in `runner_api_routers/pipeline.py` — **C API-ONLY**, not a page.

### 2.2 Nav coverage of live Jinja domains

| Live domain | Route | In `base.html` nav? | Class if gap |
|-------------|-------|---------------------|--------------|
| Dashboard | `/` | YES | — |
| Analytics | `/analytics` | YES | — |
| Content Calendar | `/weeks` | YES | — |
| Content Studio | `/content-studio` | YES | — |
| Studio Kanban | `/content-studio/kanban` | YES | — |
| Editorial Approval | `/editorial` | YES | — |
| Publishing Engine | `/publishing` | YES | — |
| Pipeline | `/pipeline` | YES | — |
| Marketing agent page | `/marketing` | YES | — |
| Sales prospecting page | `/sales` | YES | — |
| MCP Hub | `/mcp` | YES | — |
| Orchestration run detail | `/orchestration/run/{run_id}` | NO (reachable from marketing/orchestration flows) | **C**/partial — document only |
| Health | `/health` | YES | **C** — returns JSON, not shell HTML |

**Post-fix:** All primary live domains remain linked; dead `/qa`, `/publish`, `/settings` removed.

### 2.3 React CRM `/app` vs `frontend/dist`

| Item | Evidence | Class |
|------|----------|-------|
| SPA source | `frontend/src/App.jsx` HashRouter: Dashboard, Copilot, Contacts, Deals, Customers, Marketing, Analytics, Goals, Approvals, Automation, Agents, Knowledge Base, Integrations, Activity, Login | Source present |
| Mount gate | `runner_api.py` L252–259: `app.mount("/app", …)` **only if** `frontend/dist` is a directory | Conditional |
| `frontend/dist` at audit | **ABSENT** (`DIST_ABSENT`) | **E** |
| Jinja shell link to `/app` | **None** in `templates/` | Shell does not advertise CRM |

**Runtime:** CRM UI **NOT LIVE** until operator builds/deploys `frontend/dist`. Not a one-line shell fix; build/deploy concern.

### 2.4 Sales / Revenue / CRM experiences

| Surface | Runtime | Class | Notes |
|---------|---------|-------|-------|
| Jinja Sales (`/sales` + `sales.html`) | **LIVE** | Live ops page (prospecting/outreach helpers) | Not full Revenue OS / CRM shell |
| React CRM pages | **NOT LIVE** without dist | **E** | Separate shell (“WorkCrew CRM”) |
| Approvals / Automation / Agents / Copilot / KB / Goals / Integrations / Activity | API routers under `/api/v1/...` + CRM pages | **C** (+ **E** for SPA) | No Jinja nav entries |
| Forecasting / CSM / SEO | API routers | **C** | No shell pages |
| Website Engine public UI | None in app code | **D** | Out of Agent B scope; Agent A territory |

**Broken experience characterization:** Not “Sales HTML 404” — `/sales` renders. Gap is **product completeness**: Revenue/CRM deep UX lives in unmounted SPA + APIs; Jinja Sales is prospecting-ops only.

### 2.5 `base.html` ↔ `ui.py` consistency

| Check | Result |
|-------|--------|
| `active_page` values set in `ui.py` | `dashboard`, `weeks`, `week_detail`, `file_view`, `content_studio`, `content_studio_kanban`, `editorial`, `publishing`, `pipeline`, `mcp`, `marketing`, `sales`, `analytics` |
| Sidebar `active_page` expectations | Matches live pages above; pre-fix also referenced `qa`, `publish`, `settings` with **no** corresponding `ui.py` handlers |
| Duplicate HTML handlers | `runner_api.py` still defines `@app.get` for `/`, `/weeks`, `/pipeline`, `/mcp`, `/marketing`, `/sales`, `/analytics`, etc. alongside `ui_router` | Document only — not a dead-nav fix; avoid `ui.py` edits |

### 2.6 Related stale links (document only — not Agent B optional fix scope)

| Location | Link / call | Exists? | Class | Action |
|----------|-------------|---------|-------|--------|
| `templates/week_detail.html` | `GET /weeks/{week_id}/qa-report` | **NO** route | **B** | Deferred; do not invent QA page |
| `templates/pipeline.html` `STAGE_ENDPOINTS` | `POST /qa`, `POST /sheet-sync` | **NO** matching posts in `pipeline.py` (has `/run`, `/validate`, `/generate`, `/edit`, `/go-live`, …) | **B** | Deferred; API/page invention out of scope |
| `templates/week_detail.html` | `POST /go-live` | YES (`pipeline.py`) | OK (API) | Keep |

---

## 3. Safe-fix gate evaluation

### Applied: remove dead sidebar links in `templates/base.html`

| Gate | Pass? |
|------|-------|
| Clearly broken existing navigation | **YES** — `/qa`, `/publish`, `/settings` had no HTML routes |
| No API/business contract change | **YES** — template-only; no router/API edits |
| No architecture impact | **YES** — no new pages/modules |
| No collision with Agent A files | **YES** — does not touch publishing engine, website engine, M2 docs, publishing router, editorial/content_studio code |
| Trivial rollback | **YES** — restore three `<a>` blocks |

**Implementation choice:**

- **`/qa`:** removed + Jinja comment (deferred; no QA page invented).
- **`/publish` (Go-Live):** removed + comment pointing operators to Overview → **Publishing** (`/publishing`) and noting `POST /go-live` remains API-only. Did **not** retarget label “Go-Live” to `/publishing` (would duplicate Overview → Publishing and mislabel Publishing Engine as Go-Live).
- **`/settings`:** removed + deferred comment (no settings page invented).
- **Health:** left as-is (live JSON probe; not a missing route).

### Not applied (document only)

| Candidate | Why not safe-fix now |
|-----------|------------------------|
| Build/commit `frontend/dist` or always-mount `/app` | **E** — deploy/build policy; architecture/runtime surface change |
| Add Jinja CRM/Revenue nav to `/app` | Requires dist; redesign/IA; may collide with dual-shell story |
| Wire `/weeks/.../qa-report` or invent `/qa` HTML | Invents QA UI; may touch editorial/content paths |
| Fix `pipeline.html` `STAGE_ENDPOINTS` `/qa` `/sheet-sync` | API contract territory; not optional owned file |
| Deduplicate `runner_api.py` vs `ui.py` HTML handlers | Prefer not touch `ui.py`; larger refactor |
| Convert `/health` nav to a shell page | Invents settings-like ops page; out of scope |

---

## 4. Hardening plan (smallest sequence)

### Phase 0 — Done (this sprint)

1. Document shell state (this file + prior audit).
2. Remove dead sidebar links `/qa`, `/publish`, `/settings` from `templates/base.html` with deferred comments.

### Phase 1 — Deferred (no code in Agent B)

| ID | Gap | Class | Owner hint | Notes |
|----|-----|-------|------------|-------|
| D1 | React CRM not mounted | **E** | Frontend/deploy | Build `frontend/dist`; verify `/app` mount log |
| D2 | Revenue deep UX only via CRM/API | **C**+**E** | Revenue/CRM | Do not invent Jinja clones |
| D3 | `week_detail` QA report button | **B** | Editorial/UI hygiene | Point to existing file view or remove; no new QA route without decision |
| D4 | Pipeline stage POST `/qa`, `/sheet-sync` | **B** | Pipeline API | Align UI endpoints to live posts or disable stage options |
| D5 | Health nav → JSON | **C** | Ops UX (optional) | Accept as probe or later thin HTML wrapper |
| D6 | Dual HTML handler co-location (`runner_api.py` + `ui.py`) | Consistency debt | Platform | Consolidate carefully; not a nav hotfix |
| D7 | Settings page | **D** | Platform | Explicit product decision before any UI |
| D8 | Dedicated QA Reports page / Go-Live UI | **D** | Editorial / Publishing | Publishing Engine UI already at `/publishing`; go-live stays API/CLI unless product decides otherwise |

### Phase 2 — Explicit non-goals

- No Website Engine UI work (Agent A).
- No Publishing Engine / editorial / content_studio backend changes.
- No redesign of `base.html` visual system.
- No inventing Settings / QA / Go-Live pages to “fill” nav.

---

## 5. Rollback

```bash
# Revert only the shell nav fix
git checkout -- templates/base.html
```

Plan doc may remain as audit artifact.

---

## 6. Files changed

| File | Change |
|------|--------|
| `docs/governance/FOUNDER_OS_UI_HARDENING_PLAN.md` | **Created** (this plan) |
| `templates/base.html` | Removed dead nav links `/qa`, `/publish`, `/settings`; deferred comments |

**Not changed:** `runner_api_routers/ui.py`, Agent A surfaces, APIs, React source.

---

## 7. Final response block

```
Internal Shell: PARTIAL
Immediate Safe Fixes: 1
Deferred UI Gaps: 8
Code Changes: 1
Files changed:
- docs/governance/FOUNDER_OS_UI_HARDENING_PLAN.md
- templates/base.html
```
