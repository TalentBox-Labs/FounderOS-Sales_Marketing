# COMMERCIAL OUTCOME OWNERSHIP CONTRACT v1.0

**STATUS: FROZEN**  
**Baseline:** Founder OS CommercialOutcome Baseline v1.0  
**Date:** 2026-08-13  
**Parent:** A1.5 Sales ↔ Revenue Boundary Contract v1.0 — **UNCHANGED**

---

## Frozen invariant

| Phase | Owner | Object |
|-------|-------|--------|
| Before handoff | Sales (ops) | `Deal.stage` via A3.5 |
| After handoff register, before accept | Sales request / Revenue pending | `AgentActionLog` handoff row only |
| After acceptance | Revenue | CommercialOutcome representation (`commercial_outcome_accepted` row) |
| After rejection | Revenue (audit) | Reject row only; no outcome representation |

---

## Canonical Deal

| Rule | Frozen meaning |
|------|----------------|
| Entity SoT | Revenue `Deal` model (`revenue_os/models/deal.py`) — **A1.5 PRESERVED** |
| Stage operations | Sales via A3.5 — **UNCHANGED** |
| MC06 Deal writes | **PROHIBITED** |
| Ownership transfer of Deal | **DOES NOT OCCUR** |

MC06 does not make Sales the owner of Revenue financial state.  
MC06 does not make Revenue the writer of `Deal.stage`.

“Sales owns Deal before handoff” means Sales owns the **close/handoff action** and **stage operations**. It does **not** rewrite A1.5 entity SoT.

---

## Shared SoT

**PROHIBITED.**

- No shared writable CommercialOutcome table
- Handoff payload is immutable after register
- Accept does not copy Deal into a second Deal store
- Reject does not alter Deal

---

## State protection

| Side | Frozen rule |
|------|-------------|
| Sales / Deal | Accept/reject/handoff must not assign `Deal.stage`, `value`, `closed_at`, or `probability` |
| Revenue finance | No Client, Project, BillingRecord, invoice, or recognized-revenue write |
| MC04.5 | Accept still `commercial_outcome_emitted: false`; no Deal auto-create |
