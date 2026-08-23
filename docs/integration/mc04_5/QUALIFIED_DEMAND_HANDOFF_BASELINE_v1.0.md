# FOUNDER OS QUALIFIED DEMAND HANDOFF BASELINE v1.0

**STATUS: FROZEN**  
**Date:** 2026-08-13  
**Implementation sprint:** FOUNDER OS MC04 (BUILD_NEW)

**Parents (UNCHANGED):**
- Sales OS Architecture Baseline v1.0 (A1.5)
- Sales A3.5 Runner Deal Stage Update v1.0
- Sales A4.5 LeadScorer / Contact.status v1.0
- Sales↔Marketing Boundary Contract v1.0

---

## Frozen flow

```
Marketing operator → POST /api/v1/marketing/qualified-demand/handoff
                 → audit (no CRM write)

Sales operator   → POST /api/v1/sales/intake/demand/accept|reject
                 → Contact create/merge OR reject audit
                 → provenance on Contact.notes (accept only)
```

---

## Frozen interfaces

| Method | Path |
|--------|------|
| POST | `/api/v1/marketing/qualified-demand/handoff` |
| POST | `/api/v1/sales/intake/demand/accept` |
| POST | `/api/v1/sales/intake/demand/reject` |

---

## Frozen behavioral guarantees (20 principles)

All MC04.5 non-negotiable principles **VERIFIED** — see `QUALIFIED_DEMAND_HANDOFF_CONTRACT_v1.0.md`.

---

## Frozen implementation SoT

| File |
|------|
| `revenue_os/services/qualified_demand_service.py` |
| `runner_api_routers/qualified_demand.py` |

---

## Frozen tests

| File | Result |
|------|--------|
| `tests/test_mc04_qualified_demand.py` | 12/12 |

---

## Prohibited without architecture review

- Shared Marketing/Sales SoT tables
- Marketing direct CRM writes
- Autonomous intake accept
- Auto Contact.status promotion on accept
- Auto Deal/Opportunity creation
- CommercialOutcome on accept
- DB schema migration for handoff v1

---

## Supersession

New ADR + approved sprint required.
