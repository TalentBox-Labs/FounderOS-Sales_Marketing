# R1C.1 — Remaining Runtime Blocker Diagnosis (NOVA)

**Date:** 2026-08-12  
**Sprint:** R1C.1  
**Mode:** Evidence from code + runtime (not summary counts alone)

---

## Blocker ID

**R1C-RB-01**

---

## Trace

| Layer | Finding |
|-------|---------|
| Route | `GET /app` (and `/app/*`) |
| Handler | Conditional `StaticFiles` mount in `runner_api.py` **only if** `frontend/dist` is a directory |
| Template/frontend | React SPA source under `frontend/src`; **dist ABSENT** locally |
| Runtime dependency | Built Vite output `frontend/dist` |
| Failure mode | Pre-R1C.1: generic **404**; no mount registered |

---

## Capture

| Field | Value |
|-------|-------|
| Affected path | `/app` |
| Affected module | Shared Platform UI — React CRM (optional) |
| Affected UI | WorkCrew CRM SPA (`frontend/`) |
| Observed (pre) | HTTP 404, no mount |
| Expected (design) | Mount CRM **iff** dist exists; else Jinja shell is active UI |
| Reproduction | Start `runner_api:app` without `frontend/dist`; `GET /app` |
| Blocks startup? | **NO** |
| Blocks one UI surface only? | **YES** (CRM SPA only) |
| API-only? | No — SPA when built |
| Frontend-only? | **YES** |
| Production-relevant? | Docker multi-stage **builds** dist (`Dockerfile`); local/dev often omits it |
| Jinja nav link to `/app`? | **NONE** (`templates/` grep empty) |

---

## Classification

**B — FRONTEND BUILD GAP**  
also **G — OPTIONAL / NON-BLOCKING CAPABILITY** for active Founder OS Jinja runtime

**Frontend taxonomy:** **OPTIONAL FRONTEND** / **FUTURE FRONTEND** relative to Marketing OS Jinja shell (source present; dist optional for active ops UI)

---

## Answers to mission questions

1. Remaining blocker = unmounted React CRM at `/app` when `frontend/dist` missing  
2. **YES** — same as R1C “Frontend Build Gaps Deferred: 1”  
3. Not an active broken Jinja/API route for required product surfaces  
4. Not a missing runtime service (API/DB)  
5. **YES** — missing build artifact (`frontend/dist`)  
6. Not a misconfigured env secret for Jinja shell  
7. Not a frozen Marketing OS engine contract issue  
8. In-repo; build is local/Docker optional for CRM  
9. Does **not** prevent Runtime: PASS for the **active** Jinja Founder OS UI  
10. Building CRM now is out of R1C.1 scope; clarifying optional status **is** safe  

---

## Ownership

| Role | Owner |
|------|-------|
| Mount gate | Shared Platform (`runner_api.py`) |
| SPA source | Revenue/CRM frontend (`frontend/`) |
| Active ops UI | Marketing OS Jinja shell (`runner_api_routers/ui.py`) |
