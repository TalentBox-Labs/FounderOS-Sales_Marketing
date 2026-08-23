# CP3 — Scoring Model & Candidate Evaluation

**Sprint:** CP3  
**Date:** 2026-08-13

---

## Weights (100%)

| Criterion | Weight |
|-----------|--------|
| Founder Leverage | 15% |
| Commercial Throughput | 20% |
| Value-Chain Unlock | 15% |
| Implementation Readiness | 15% |
| Time-to-Operable-Value | 10% |
| Reuse of Existing Capability | 10% |
| Measurement Readiness | 5% |
| Low Dependency Risk | 5% |
| Architecture Safety | 3% |
| Reversibility | 2% |

Scale: 0–5 per criterion. Weighted total /5.

---

## Candidate scores

### A — Social S1 Live (LinkedIn human-approved publisher)

| Criterion | Score | Rationale |
|-----------|------:|-----------|
| FL | 2.5 | Extends Marketing reach |
| CT | 3.0 | Audience channel only; Demand capture still missing |
| VCU | 3.0 | Partial Publishing→Audience heal |
| IR | 2.0 | IB-01..03 + ES-01..03 + FD-01 |
| TTOV | 2.0 | External setup serializes |
| Reuse | 3.0 | Publishing engine contract |
| MR | 2.0 | No live metrics path |
| LDR | 1.5 | High external dependency |
| AS | 3.0 | Boundary defined |
| Rev | 2.0 | OAuth binding hard to unwind |

**Weighted: 2.53/5** · **Executability: BLOCKED**

---

### B — Social S1 Adapter-First / Fake-First

| Criterion | Score | Rationale |
|-----------|------:|-----------|
| FL | 2.0 | Engineering-only progress |
| CT | 2.0 | No commercial activation |
| VCU | 2.0 | Does not heal value-chain break |
| IR | 3.5 | Can implement NOT_IMPLEMENTED stub |
| TTOV | 3.0 | Faster than live |
| Reuse | 3.5 | Publishing adapter pattern |
| MR | 2.0 | Fake metrics misleading if shown |
| LDR | 3.5 | No credentials |
| AS | 3.5 | Fake boundary must be honest |
| Rev | 4.0 | Easy to replace with live |

**Weighted: 2.64/5** · **Executability: CONDITIONAL**

---

### C — MC06 CommercialOutcome / Closed-Won Handoff v1

| Criterion | Score | Rationale |
|-----------|------:|-----------|
| FL | 4.5 | Next A2 cross-OS milestone post-MC04 |
| CT | 4.5 | Unblocks Revenue path on deal close |
| VCU | 4.5 | Primary cross-OS break now |
| IR | 4.0 | Contract frozen; MC04/A3 patterns |
| TTOV | 3.5 | Bounded event stub one sprint |
| Reuse | 4.5 | EventBus, audit, human gate |
| MR | 3.5 | Cockpit can surface emitted flag |
| LDR | 4.5 | No external deps in v1 |
| AS | 4.5 | Revenue isolation proven |
| Rev | 4.0 | Event-only reversible |

**Weighted: 4.27/5** · **Executability: READY**

---

### D — Sales A5 Companies on Runner (C19)

| Criterion | Score | Rationale |
|-----------|------:|-----------|
| FL | 2.5 | CRM completeness |
| CT | 2.0 | Low throughput impact |
| VCU | 2.0 | Does not heal chain break |
| IR | 5.0 | JWT API exists |
| TTOV | 4.0 | Small CRUD surface |
| Reuse | 5.0 | Runner CRM patterns |
| MR | 2.5 | Limited measurement |
| LDR | 5.0 | Isolated |
| AS | 5.0 | Sales boundary clear |
| Rev | 5.0 | Fully reversible |

**Weighted: 3.35/5** · **Executability: READY**

---

### E — Domain-Independent SEO Phase 2

| Criterion | Score | Rationale |
|-----------|------:|-----------|
| FL | 2.5 | Marketing hygiene |
| CT | 2.5 | Indirect demand support |
| VCU | 2.5 | Does not fix Audience→Demand |
| IR | 4.0 | SEO engines frozen baseline |
| TTOV | 3.5 | Incremental |
| Reuse | 4.0 | Existing seo_engine |
| MR | 3.5 | Readiness metrics exist |
| LDR | 4.0 | No domain required |
| AS | 4.0 | Frozen boundary |
| Rev | 3.5 | Incremental |

**Weighted: 3.17/5** · **Executability: READY**

---

### F — Production SEO Activation

| Criterion | Score | Rationale |
|-----------|------:|-----------|
| FL | 3.0 | High when unblocked |
| CT | 3.5 | Organic audience |
| VCU | 3.0 | Partial Audience heal |
| IR | 1.0 | FDR-N05 not ratified |
| TTOV | 1.0 | Blocked |
| Reuse | 3.0 | Engines ready |
| MR | 2.0 | Domain-dependent sampling |
| LDR | 1.0 | DNS/TLS external |
| AS | 3.0 | Contract frozen |
| Rev | 2.0 | DNS changes sticky |

**Weighted: 2.43/5** · **Executability: BLOCKED**

---

### G — Cockpit Remediation / UI3 (agent activity + score bands)

| Criterion | Score | Rationale |
|-----------|------:|-----------|
| FL | 2.0 | UX polish |
| CT | 2.0 | No throughput gain |
| VCU | 1.5 | Reconciliation PASS — not required |
| IR | 4.0 | APIs exist for U1 |
| TTOV | 4.0 | Small wiring |
| Reuse | 4.5 | Existing heartbeat API |
| MR | 2.5 | Optional visibility |
| LDR | 5.0 | Low risk |
| AS | 5.0 | Read-only |
| Rev | 5.0 | Easy revert |

**Weighted: 3.00/5** · **Executability: CONDITIONAL** (not mandated)

Phase 0: **no material defect** — include only as optional polish.

---

### H — MC04.1 QualifiedDemand Operator Completion

Scope: cockpit reject action + read-only pending queue API (reject service exists; not cockpit-exposed).

| Criterion | Score | Rationale |
|-----------|------:|-----------|
| FL | 3.0 | Operator UX completeness |
| CT | 3.0 | Faster MC04 loop |
| VCU | 2.5 | MC04 core already OPERABLE |
| IR | 4.5 | Reject path in service layer |
| TTOV | 4.5 | Small sprint |
| Reuse | 5.0 | MC04.5 frozen patterns |
| MR | 3.0 | Audit exists |
| LDR | 5.0 | No external deps |
| AS | 5.0 | Human gate preserved |
| Rev | 5.0 | Additive UI only |

**Weighted: 3.70/5** · **Executability: READY**

Note: Broader "intake automation" (web form → QD) would score ~3.85 on VCU but expands scope beyond bounded H; deferred as separate Marketing sprint.

---

## Phase 7 — Executability gate

| Candidate | Score | Executability | Selectable? |
|-----------|------:|---------------|-------------|
| **C — MC06** | **4.27** | **READY** | **YES** |
| H — MC04.1 | 3.70 | READY | YES |
| D — Sales A5 | 3.35 | READY | YES |
| E — SEO Ph2 | 3.17 | READY | YES |
| G — Cockpit | 3.00 | CONDITIONAL | YES (optional) |
| B — Social fake | 2.64 | CONDITIONAL | YES (low value) |
| A — Social live | 2.53 | BLOCKED | **NO** |
| F — Prod SEO | 2.43 | BLOCKED | **NO** |

| Metric | Winner |
|--------|--------|
| **Highest raw-value** | **C — MC06 CommercialOutcome (4.27)** |
| **Highest executable** | **C — MC06 CommercialOutcome (4.27)** |

Raw and executable **align** — MC06 is both highest value and immediately executable without Founder external setup.
