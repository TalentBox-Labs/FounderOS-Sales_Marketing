# R1C — Route Audit (NOVA)

**Date:** 2026-08-12  
**Baseline route_count (pre-fix):** 58  
**Pre-full regression:** 388/400; 8 failed; 4 errors (historical identities)

---

## Original R0 six broken-route findings (re-verified)

| # | Finding | Exists? | Registered? | Handler? | Template? | Nav? | Class | Severity | Disposition |
|---|---------|---------|-------------|----------|-----------|------|-------|----------|-------------|
| 1 | `GET /weeks/{id}/qa-report` | No | No | No | No HTML | In-page link in `week_detail.html` | **B — STALE NAVIGATION** | MEDIUM | **Remove link** (QA files under `output/qa_reports/`; no invent UI) |
| 2 | `GET /marketing/run/{slug}` | No | No | No | No | In-page View in `marketing.html` | **E — PLANNED/NOT IMPLEMENTED** | MEDIUM | **Remove View link** (do not invent detail page) |
| 3 | `POST /qa` | No | No | No | N/A | Pipeline stage radio | **E — NOT IMPLEMENTED** | MEDIUM | **Remove stage option** (capability not wired as HTTP) |
| 4 | `POST /sheet-sync` | No | No | No | N/A | Pipeline stage radio | **E — NOT IMPLEMENTED** | MEDIUM | **Remove stage option** |
| 5 | `GET /app` | No (dist absent) | Conditional mount only | StaticFiles if dist | React | Docs only | **G — FRONTEND BUILD GAP** | LOW | **DEFER** (not rebuild React in R1C) |
| 6 | `GET /marketing` → 500 | Yes | Yes (`ui.py` wins) | Yes | `marketing.html` | Sidebar | **A — BROKEN ACTIVE ROUTE** | HIGH | **Fix context** (`integration_status`, `runs`) |

---

## Associated stale navigation

| Finding | Class | Disposition |
|---------|-------|-------------|
| Sidebar `Health` → `/health` (JSON) | **D — API-ONLY** + **B — STALE NAV** | Remove from sidebar (endpoint remains) |

---

## Orphan template

| Template | Dynamic/inherit/tests? | Class | Disposition |
|----------|------------------------|-------|-------------|
| `orchestration_run.html` | Not referenced; live handler uses inline HTML; docs mention it | **C — ORPHAN** | **Reconnect** `GET /orchestration/run/{run_id}` to template (**KEEP**, not delete) |

---

## False positives

None among the six — all still present after R1A/R1B.

---

## API-only / frontend deferred

| Item | Class |
|------|-------|
| `/health` | API-ONLY — NO UI EXPECTED |
| `/app` React CRM | FRONTEND BUILD GAP — DEFERRED |
| POST `/qa`, `/sheet-sync` | NOT IMPLEMENTED as HTTP (CLI tools may exist; no fake routes) |
