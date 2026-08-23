# CP3 — Execution Roadmap

**Sprint:** CP3  
**Date:** 2026-08-13  
**Horizon:** Next implementation sprint only (+ one secondary action)

---

## NOW

**MC06 — Commercial Outcome v1 (bounded event + audit stub)**

| Deliverable | Scope |
|-------------|-------|
| Event schema | Align with `SALES_REVENUE_CONTRACT.md` §3 |
| Emission trigger | Human-gated on A3.5 CLOSED_WON / CLOSED_LOST |
| Idempotency | `outcome_id` dedupe |
| Audit | EventBus + AgentActionLog |
| API response | `commercial_outcome_emitted: true` when emitted |
| Explicit exclusions | No Revenue intake, no billing, no Client auto-create, no schema migration (unless audit-only ADR) |

**Entry criteria:** MC04.5 FROZEN ✓ · A3.5 FROZEN ✓ · UI2.5 VALID ✓  
**Exit criteria:** Closed-won emits auditable CommercialOutcome once; duplicate emission blocked; Revenue isolation attestation

---

## NEXT

**MC04.1 — QualifiedDemand operator completion**

- Expose reject action in cockpit (service exists; UI1.1 blocked reject in UI2 scope)
- Read-only pending queue API if not already externalized
- No intake automation / web form in this slice

---

## PARKED

| Workstream | Why parked |
|------------|------------|
| Sales A5 Companies on runner | Sales saturation |
| Domain-independent SEO Phase 2 | Lower leverage vs cross-OS |
| Cockpit U1 agent activity | Reconciliation PASS — optional |
| Social S1 fake-first | Low commercial throughput |
| Marketing demand capture (web form) | Separate Marketing sprint; manual MC04 compensates |

---

## BLOCKED

| Workstream | Blocker |
|------------|---------|
| Social S1 live LinkedIn | FD-01 + ES-01..03 |
| Production SEO activation | FDR-N05 domain ratification |

---

## EXTERNAL / FOUNDER ACTION

| ID | Action | Unblocks |
|----|--------|----------|
| **FDR-N05** | Ratify production website domain | Production SEO activation |
| **FD-01** | Choose Person vs Organization LinkedIn identity | Social S1 live |
| **ES-01..03** | LinkedIn Developer app, products, token storage | Social live publish |
| **ES-04** | Org page admin (if Organization chosen) | Org publishing path |

None required for MC06.

---

## Sequence after MC06 (reference only — not committed)

1. Revenue intake v1 (Customer/Client promotion on outcome consume)  
2. Marketing demand capture (Audience→Demand)  
3. MC04.1 polish or parallel  
4. Social S1 (after FD-01 + ES)  
5. Production SEO (after FDR-N05)

Do not treat as sprint commitments.
