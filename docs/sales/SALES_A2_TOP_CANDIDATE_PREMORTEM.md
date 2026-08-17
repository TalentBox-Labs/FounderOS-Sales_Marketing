# SALES A2 — Top Candidate Premortem

**Sprint:** SALES A2  
**Date:** 2026-08-13  
**Candidates:** #1 Runner Deal Stage Update (4.85) · #2 QualifiedDemand (3.38) · #3 Outreach send (3.33)

---

## #1 — Runner Deal Stage Update

| Question | Answer |
|----------|--------|
| Why wrong? | Founder may rarely use deals today; prospecting-only workflow might suffice short-term |
| Dependency invalidate? | If primary path were forced to JWT-only app — but runner is Founder SoT gateway |
| Existing make unnecessary? | JWT `PUT /api/v1/deals/{id}` — unused by shell/SPA; does not remove runner gap |
| Boundary pressure? | Must not claim Deal entity ownership; mutate Revenue SoT via Sales ops + human gate |
| External block? | None for core slice; optional n8n stage webhook already in JWT path — **exclude** from A3 |
| Operational risk? | Incorrect stage / closed_won without CommercialOutcome — mitigate with HUMAN_ONLY + audit |
| 80% smaller slice? | PATCH stage only (no probability auto) — possible but `advance_deal_stage` already maps probability; reuse it |
| UI immediately? | **No** |
| Premature CRM complexity? | Low if API-only; high if bundling SPA mount |

**Strongest argument against:** Ship governance (LeadScorer gate) first for safety.  
**Counter:** Gate is valuable but does not unblock pipeline; A3 stage + A4 gate is better sequence.

---

## #2 — Marketing→Sales QualifiedDemand

| Question | Answer |
|----------|--------|
| Why wrong? | Manual capture already works; Marketing engines frozen — emitter not trivial |
| Dependency? | Requires Marketing OS change or Shared webhook — cross-stream |
| Unnecessary? | Manual Contact create (C03) substitutes |
| Boundary? | Safe if contract-only; pressure if Sales writes Marketing tables |
| External? | Possibly form hosting / Turnstile later |
| Risk? | Duplicate Contacts / consent |
| Smaller slice? | Intake stub without Marketing emitter — low value |
| UI? | Not required first |
| CRM complexity? | Medium (idempotency/merge) |

**Strongest against:** Cross-OS coordination cost without completing in-Sales pipeline ops first.

---

## #3 — Outreach send (n8n completion)

| Question | Answer |
|----------|--------|
| Why wrong? | Approvals already LIVE; gap is ops config not missing Sales code |
| Dependency? | **n8n external setup** — fails External Independence |
| Unnecessary? | Manual email outside OS |
| Boundary? | Approvals correctly Revenue queue |
| External block? | Yes — I04 |
| Risk? | Accidental bulk send if gates weak |
| Smaller? | Document runbook only — not A3 feature |
| UI? | SPA approvals when mounted |
| Complexity? | Integration ops, not Sales domain slice |

**Strongest against:** A2 prefers local slice; activating n8n is ops, not architecture-priority feature.

---

## Conclusion

Premortems do not overturn score order. **#1 remains A3.**
