# CP1 — Founder OS Priority Decision

**Sprint:** CP1  
**Date:** 2026-08-13  
**Mode:** Decision only  
**Frozen Contract Changes:** 0  
**Cross-Agent Conflicts:** 0

Weights: FV 25% · CR 20% · IR 20% · CL 15% · EE 10% · MR 5% · RR 5%

---

## Candidate scores (0–5 dims → weighted /5)

### Candidate A — Marketing Social S1 (LinkedIn manual publisher)

| Dim | Score | Evidence |
|-----|------:|----------|
| FV | 4 | External demand / brand channel; S0-R CONDITIONAL GO |
| CR | 4 | LinkedIn professional network leverage |
| IR | 3 | Architecture PASS; IB is S1 work; live blocked ES; FD-01 open |
| CL | 3 | Marketing-primary; Publishing/Editorial ready |
| EE | 3 | Medium adapter + Social package |
| MR | 2 | Measurement PARTIAL |
| RR | 3 | Human publish gates; OAuth risk if live |

**Weighted = 0.25×4 + 0.20×4 + 0.20×3 + 0.15×3 + 0.10×3 + 0.05×2 + 0.05×3 = 3.40**

**Blocker classification:** **FOUNDER_DECISION** (FD-01) + **EXTERNAL** (ES-01..03 for live). Engineering start behind fakes: **SOFT**. No architecture **HARD** stop.

### Candidate B — Sales LeadScorer / Contact.status human gate

| Dim | Score | Evidence |
|-----|------:|----------|
| FV | 4 | Closes A1.5 authority debt; safer CRM |
| CR | 2 | Indirect (data integrity) |
| IR | 5 | COMPLETE_EXISTING; local; A3.5 sequence |
| CL | 2 | Sales/Revenue Contact field |
| EE | 5 | Small gate around existing scorer |
| MR | 3 | Auditable status changes |
| RR | 5 | Reduces autonomous mutation risk |

**Weighted = 0.25×4 + 0.20×2 + 0.20×5 + 0.15×2 + 0.10×5 + 0.05×3 + 0.05×5 = 3.60**

**Blocker classification:** **NONE**

### Candidate C — Marketing→Sales QualifiedDemand (MC04/C27)

| Dim | Score | Evidence |
|-----|------:|----------|
| FV | 5 | Heals primary value-chain break |
| CR | 4 | Demand → pipeline visibility |
| IR | 2 | BUILD_NEW; no Marketing emitter; WEB_FORM unused |
| CL | 5 | Explicit cross-OS contract |
| EE | 2 | Intake + emitter coordination |
| MR | 3 | Contract fields support metrics |
| RR | 3 | PII intake; policy needed |

**Weighted = 0.25×5 + 0.20×4 + 0.20×2 + 0.15×5 + 0.10×2 + 0.05×3 + 0.05×3 = 3.70**

**Blocker classification:** **SOFT** (engineering + Marketing coordination). Priority **rose** post-A3; still not cleanest immediate slice.

---

## Decision rule application

| Metric | Winner |
|--------|--------|
| Highest raw score | **C — 3.70** |
| Highest executable (blocker NONE) | **B — 3.60** |
| A vs Founder/external | A does **not** outscore B/C on raw; still report FD-01/ES as unlock path for Marketing lane |

**Selected next implementation sprint: Candidate B**

Rationale: After A3.5, Sales pipeline ops are frozen; the next **fully executable** Founder-value slice is the known LeadScorer human gate (COMPLETE_EXISTING, no credentials, no frozen-contract edits). MC04 is strategically hottest on the value chain but is BUILD_NEW with Marketing dependency. Social S1 remains CONDITIONAL — Founder FD-01 + external setup unlock live publish; do not silently skip that reporting.

---

## Recommended actions

| Lane | Action |
|------|--------|
| **NOW** | **SALES A4 — LEADSCORER / CONTACT.STATUS HUMAN GATE** |
| **NEXT (parallel Founder)** | FD-01 + LinkedIn ES-01..03 |
| **PARKED** | Social S1 engineering until Founder prioritizes Marketing lane post-FD-01 **or** explicitly accepts fake-first S1 without identity ratification |
| **BLOCKED (live LI)** | Live LinkedIn publish until ES complete |
| **DECISION REQUIRED** | FD-01 (1) |

---

## Architecture protection

Marketing / SEO / Sales A1.5 / Sales A3.5 / Sales↔Marketing / Sales↔Revenue / Agent authority: **UNCHANGED** by CP1.
