# CP3 — Pre-Mortem (Top 3 Candidates)

**Sprint:** CP3  
**Date:** 2026-08-13  
**Horizon:** Four sprints regret analysis

---

## 1. MC06 — CommercialOutcome v1 (recommended)

**If we choose this now and regret it four sprints later, why?**

| Risk | Assessment |
|------|------------|
| **Opportunity cost** | Delayed Marketing demand capture (Audience→Demand) and Social audience — upstream volume may stay manual |
| **Premature subsystem depth** | LOW if v1 stays event+audit stub; HIGH if scope creeps to billing/Client auto-create |
| **External dependency risk** | LOW — no OAuth/accounting in v1 |
| **Architecture debt** | LOW — follows MC04 event pattern; contract pre-defined |
| **Operational complexity** | LOW — one more human-gated emission on existing stage path |
| **Measurement weakness** | MEDIUM — outcome events without Revenue intake still leave commercial flow half-visible |
| **Founder attention cost** | LOW — no portal setup |
| **Reversibility** | HIGH — flag + audit; intake can be added later |

**Mitigation:** Strict v1 charter — emit event + audit + `commercial_outcome_emitted: true`; **no** Customer promotion, **no** billing, **no** cockpit UI3.

---

## 2. MC04.1 — QualifiedDemand Operator Completion

**If we choose this now and regret it four sprints later, why?**

| Risk | Assessment |
|------|------------|
| **Opportunity cost** | Revenue handoff still missing while polishing MC04 UX that's already operable via API |
| **Premature subsystem depth** | LOW |
| **External dependency risk** | NONE |
| **Architecture debt** | NONE |
| **Operational complexity** | LOW |
| **Measurement weakness** | Does not improve downstream metrics |
| **Founder attention cost** | LOW |
| **Reversibility** | HIGH |

**Verdict:** Safe but **low leverage** now that MC04.5 is frozen and cockpit accept works. Better as parallel polish, not primary sprint.

---

## 3. Sales A5 — Companies on Runner

**If we choose this now and regret it four sprints later, why?**

| Risk | Assessment |
|------|------------|
| **Opportunity cost** | Sales saturation confirmed — CRM entity CRUD does not move commercial outcomes |
| **Premature subsystem depth** | MEDIUM — more Sales surface before Revenue bridge |
| **External dependency risk** | NONE |
| **Architecture debt** | LOW |
| **Operational complexity** | LOW |
| **Measurement weakness** | Company records ≠ revenue |
| **Founder attention cost** | LOW |
| **Reversibility** | HIGH |

**Verdict:** Highest **Sales-only** readiness but wrong layer post-MC04 — CP2 already rejected Sales-first when cross-OS gap existed; gap has **moved downstream** to MC06.

---

## Blocked candidates (not selectable)

| Candidate | Regret if forced |
|-----------|------------------|
| Social S1 Live | OAuth/identity churn; live publish without demand capture |
| Production SEO | Domain ratification delay burns sprint; no MC06 progress |

---

## Pre-mortem conclusion

MC06 carries the best risk-adjusted cross-OS leverage **if scope stays bounded**. Primary regret vector is **not** choosing Marketing demand capture first — acceptable while manual MC04 compensates for solo Founder ops.
