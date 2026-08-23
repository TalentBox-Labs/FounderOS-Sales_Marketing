# CP2 — Pre-Mortem (Top Three Candidates)

**Sprint:** CP2  
**Date:** 2026-08-13

---

## 1. Candidate C — QualifiedDemand MC04

**Regret scenario (4 sprints later):** We built intake before Marketing could emit real demand; MC04 sits idle with manual test events only.

| Risk | Mitigation |
|------|------------|
| Opportunity cost vs Sales polish | Bounded v1: manual Marketing qualification → emit + Sales accept |
| Hidden dependency on web forms | v1 does NOT require production form — operator-triggered emit OK |
| Architecture debt (shared SoT) | Contract frozen — enforce event-only handoff in sprint scope |
| Measurement failure | Track accept/reject/idempotency from day one |
| Premature if Audience→Demand still MISSING | Pair v1 emitter with minimal Marketing qualification record (not full form engine) |

---

## 2. Candidate A — Companies on runner (A5)

**Regret scenario:** CRM has Companies API but commercial throughput unchanged — still manually creating contacts with no demand pipeline.

| Risk | Mitigation |
|------|------------|
| Sales saturation | CP2 Sales audit: isolated Sales slice no longer highest leverage |
| Opportunity cost | Defer A5 until cross-OS bridge or CRM mount sprint |
| Hidden value | Useful before CRM SPA mount — but mount still RETAIN_AND_REFACTOR |

---

## 3. Candidate E — CommercialOutcome stub

**Regret scenario:** Closed-won emits events but no deals close because upstream demand never arrives.

| Risk | Mitigation |
|------|------------|
| Downstream optimization | Sequence after demand ingress (MC04) |
| Revenue not yet bottleneck | Classify EMERGING_DEPENDENCY not CRITICAL |
| Architecture creep into finance | Keep stub: event + audit only, no invoice |

---

## Pre-mortem verdict

Lowest regret for **Founder OS value chain** if MC04 v1 includes bounded Marketing emitter. Highest regret for another Sales-only slice (A) without upstream fix.
