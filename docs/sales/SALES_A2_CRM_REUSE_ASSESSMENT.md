# SALES A2 — CRM Reuse Assessment

**Sprint:** SALES A2  
**Date:** 2026-08-13  
**Frozen disposition:** **RETAIN_AND_REFACTOR_LATER** (unchanged)

---

## Reusable assets (evidence)

| Asset | Reusable? | Notes |
|-------|-----------|-------|
| Screens (Contacts, Deals, DealDetail, Dashboard, …) | YES | 17 pages in `frontend/src/pages` |
| API client assumptions | YES | Targets runner `/api/v1/crm/*` |
| Domain assumptions | PARTIAL | Contact/Deal aligned; expects stage updates missing on runner |
| Interaction patterns | YES | List/detail/kanban patterns |
| Mount path `/app` | NO for A3 | Frozen unmounted |

---

## First implementation slice (A3) UI need

| Option | Applies to A3 Deal Stage Update? |
|--------|----------------------------------|
| **A. requires no CRM UI work** | **YES — selected** |
| B. reuse CRM component without refactor | No — would require mount |
| C. eventually requires CRM refactor | Later (A4+) after stage API exists |

A3 is **API-first** on `runner_api_routers/crm.py` (+ tests). Optional tiny Jinja affordance on `/sales` is **excluded** from A3 to keep scope S.

---

## Conditions before SPA reuse

1. Runner stage mutation API live with human requester gate  
2. Explicit refactor/mount sprint (not A3)  
3. Disposition still RETAIN_AND_REFACTOR_LATER until ADR changes it  

**CRM UI Required for A3: NO**
