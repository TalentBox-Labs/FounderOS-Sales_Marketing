# CRM UI Disposition v1.0

**STATUS: FROZEN**  
**VERSION: v1.0**  
**Sprint:** SALES A1.5  
**Date:** 2026-08-13  
**Source:** [SALES_CRM_UI_DECISION.md](SALES_CRM_UI_DECISION.md) (A1)

---

## Frozen disposition

**CRM UI Disposition: RETAIN_AND_REFACTOR_LATER**

---

## Current state (verified A1.5)

| Check | Evidence |
|-------|----------|
| Source preserved | `frontend/` present (`workcrew-crm-frontend`) |
| Dist | **Absent** (`frontend/dist` not present) |
| Mount | Conditional; local → `GET /app` **503** `not_built` |
| Jinja Sales entry | `/sales` LIVE — not replaced |
| Nav to `/app` | Not in `base.html` |

A1.5 did **not** mount, refactor, or delete the CRM UI.

---

## Known incompatibilities (frozen notes)

1. Runner CRM lacks deal **stage update** — SPA kanban non-writable on primary path.  
2. Dual JWT stack exists but SPA targets runner `/api/v1/crm/*`.  
3. Domain aliases (Lead/Opportunity) not reflected as separate SPA entities — uses Contact/Deal.  
4. Mounting without refactor would expose PARTIAL CRM as if complete.

---

## Canonical domain-model dependencies

Before mount/refactor, SPA must align with:

- [SALES_DOMAIN_MODEL_CONTRACT_v1.0.md](SALES_DOMAIN_MODEL_CONTRACT_v1.0.md)  
- [SALES_REVENUE_BOUNDARY_CONTRACT_v1.0.md](SALES_REVENUE_BOUNDARY_CONTRACT_v1.0.md)  
- [SALES_AGENT_AUTHORITY_CONTRACT_v1.0.md](SALES_AGENT_AUTHORITY_CONTRACT_v1.0.md)  

---

## Conditions required before future mounting/refactoring

1. Approved implementation sprint (post A1.5; typically after A2 priority review).  
2. Runner (or Sales facade) stage-mutation API with human accountability.  
3. Explicit decision on nav link in Founder shell.  
4. Build `frontend/dist` in controlled ops/Docker — not silent local-only mount.  
5. No reinterpretation of RETAIN_AND_REFACTOR_LATER without ADR.

---

## Prohibited in A1.5 / without unfreeze

- Mount `/app`  
- Refactor SPA  
- Delete `frontend/`  
- Rebuild as greenfield without ADR  
