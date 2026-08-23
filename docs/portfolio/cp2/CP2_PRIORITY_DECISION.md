# CP2 — Priority Decision

**Sprint:** CP2 — Founder OS Cross-OS Priority Checkpoint  
**Date:** 2026-08-13  
**Mode:** Decision only — no implementation

---

## Candidate scores (weighted /5)

| ID | Candidate | Score | Executability |
|----|-----------|------:|---------------|
| **C** | Marketing→Sales QualifiedDemand (MC04) | **3.70** | CONDITIONAL |
| **A** | Sales A5 — Companies on runner (C19) | **3.60** | READY |
| **E** | CommercialOutcome / closed-won stub (MC06) | **3.55** | READY |
| **D1** | Domain-independent SEO (incremental) | **3.30** | READY |
| **B1** | Social S1 live LinkedIn | **2.95** | BLOCKED |
| **B2** | Social S1 fake-first | **2.65** | CONDITIONAL |
| **D2** | Production SEO activation | **1.45** | BLOCKED |

Weights: FL 15% · CV 15% · VCU 15% · IR 15% · TTOV 10% · Reuse 10% · MR 5% · LDR 5% · AS 5% · Rev 5%

---

## Rankings

| Metric | Winner |
|--------|--------|
| **Highest raw-value** | **C — QualifiedDemand (3.70)** |
| **Highest executable (no soft deps)** | **A — Companies runner (3.60)** |
| **Second executable Revenue-adjacent** | **E — CommercialOutcome (3.55)** |

Raw and executable differ: C wins on value-chain unlock; A wins on Sales-only readiness. **CP2 selects C** because post-A4.5 Sales internal ops are saturated and Founder OS must heal the cross-OS break.

---

## Special audits

### QualifiedDemand (MC04)

| Check | Result |
|-------|--------|
| Marketing qualification source | Bounded v1 possible (operator/manual emit) |
| Handoff object/event | Contract frozen — payload defined |
| Sales acceptance boundary | Intake accept/reject + idempotency specified |
| Sales Contact intake path | Runner CRM create LIVE |
| Duplicate handling | Merge policy in contract |
| No shared SoT | Event-only — enforce in implementation |
| Auditability | Accept/reject + `SalesDemandRejected` |
| Human gate | HUMAN_ONLY intake acceptance |

**Classification: READY_WITH_SOFT_DEPENDENCY**  
(Soft = bounded Marketing emitter scope in same sprint; not external credentials)

### Sales saturation

| Question | Answer |
|----------|--------|
| Can Sales receive, qualify, and progress demand? | **PARTIAL** — human-gated qualification (A4.5) and deal stage (A3.5) OPERABLE; automated intake MISSING |
| Would another isolated Sales capability increase throughput without upstream? | **NO** |

**Sales Saturation: YES** (for Sales-only slices; cross-OS still PARTIAL)

### Social

| Dimension | State |
|-----------|-------|
| Engineering readiness | **CONDITIONAL** (B2 BUILD_NEW possible) |
| Live publishing readiness | **BLOCKED** (FD-01 + ES-01..03) |

Fake-first B2 moves technical work forward without commercial activation — **low leverage now** vs MC04.

### Revenue

**EMERGING_DEPENDENCY** — A3.5/A4.5 unblocked MC06 sequencing, but demand ingress (MC04) is upstream bottleneck. Not CRITICAL_BOTTLENECK yet.

---

## Value chain

| Finding | Transition |
|---------|------------|
| **First material break** | **Audience → Demand** (no demand capture) |
| **Highest-leverage horizontal bridge** | **Qualification → Sales Contact** (`QualifiedDemand` MC04) |

Healing MC04 does not fully fix Audience→Demand but enables the primary cross-OS ingress once Marketing emits qualified demand (including bounded manual/operator v1).

---

## Recommended next sprint

**FOUNDER OS MC04 — QUALIFIED DEMAND HANDOFF v1**

Bounded scope:
- Marketing emitter (operator/manual qualification → `QualifiedDemand` event)
- Sales intake (accept/reject/idempotency → canonical Contact create via existing SoT)
- Audit trail; no shared tables; no CRM direct writes from Marketing
- No production domain, LinkedIn OAuth, external CRM, DB migration

---

## Secondary next action

**Founder: FD-01 LinkedIn identity + ES-01..03** (unblocks Social S1 live when Marketing lane prioritized)

---

## Parked workstreams

| Workstream | Until |
|------------|-------|
| Social S1 live (B1) | FD-01 + ES complete |
| Social S1 fake-first (B2) | Explicit Marketing lane priority after MC04 or parallel if capacity |
| Sales A5 Companies | After MC04 or CRM mount prep |
| Production SEO (D2) | FDR-N05 domain decision |
| CRM SPA mount | RETAIN_AND_REFACTOR_LATER sprint |
| Outreach n8n live | External n8n setup |

---

## Why non-selected candidates lost

| Candidate | Reason |
|-----------|--------|
| **A** Companies | Highest executable Sales slice but **Sales saturation YES** — no throughput gain without upstream demand |
| **E** CommercialOutcome | Second chain break; premature before demand ingress |
| **D1** SEO | Ready but does not heal commercial value chain |
| **B1** Social live | BLOCKED — Founder + external setup |
| **B2** Social fake | Low commercial value while activation blocked |
| **D2** SEO production | BLOCKED — domain pending |

---

## Change control

| Item | Count |
|------|------:|
| Feature code changes | 0 |
| Runtime changes | 0 |
| Frozen contract changes | 0 |

**Architecture: PASS** · **Cross-Agent Conflicts: 0**
