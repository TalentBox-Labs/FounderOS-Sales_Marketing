# CP4 — Cockpit Source Reconciliation

**Sprint:** CP4  
**Date:** 2026-08-13  
**Parents:** UI2.5 source manifest · CP3 reconciliation — **not rewritten**

---

## Counts (unchanged)

| Metric | Value |
|--------|------:|
| Expected (UI1 widget map) | **11** |
| Verified runtime integrations | **8** |
| Unverified | **3** |

MC06 / MC06.5 **did not** add a cockpit source. CommercialOutcome is not wired into the read model.

---

## Eight verified sources

| # | Source | Panel |
|---|--------|-------|
| 1 | QualifiedDemand `AgentActionLog` | Attention, Marketing |
| 2 | CRM Contacts | Sales, Attention |
| 3 | CRM Deals | Sales, Commercial Flow |
| 4 | Editorial pending | Attention |
| 5 | Publishing queue | Attention |
| 6 | SEO readiness | Marketing/SEO |
| 7 | Technical SEO | Marketing/SEO |
| 8 | Heartbeat scheduler | Governance |

---

## Three unverified (same as CP3)

| ID | Widget | Class | Material impact? |
|----|--------|-------|------------------|
| U1 | Agent activity feed | DEFERRED | NO — governance remains truthful |
| U2 | Lead score bands (Hermes) | STALE_EXPECTATION | NO — high-score items derived from Contact |
| U3 | Commercial flow independent SoT | STALE_EXPECTATION | NO as a *source*; YES as **stale copy** (see below) |

---

## Did MC06 change cockpit availability?

**NO** as a ninth integration.  
**YES** as honesty: commercial-flow Revenue stage still says outcome is not implemented, while MC06.5 APIs exist. That is a **display lag**, not a missing 9th SoT. Do not silently change expected 11 → 8.

---

## Material decision support

**PARTIAL**

Cockpit supports: pending QD accept, high-score status, pipeline counts, SEO/editorial health, governance markers.

Cockpit does **not** support: QD reject, deal stage, CO queue, CO accept/reject, demand registration.

**Do not recommend UI3 merely to verify U1–U3.** Recommend operator-flow work only if it closes Founder action gaps (Candidate J), not source-count cosmetics.

**Cockpit Source Reconciliation: PASS**
