# Architecture ADR-005 — Sales OS Architecture Baseline v1.0 Freeze

**ADR ID:** Architecture_ADR_005  
**Status:** Accepted  
**Sprint:** SALES A1.5 — Sales OS Architecture Baseline Freeze  
**Date:** 2026-08-13  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`

**Decision type:** Governance freeze  
**Implementation changes in this ADR:** **NONE**

Supersedes for Sales baseline authority: none (additive freeze of ADR-004 decisions).  
Parent: Architecture v2.2 FROZEN; ADR-004 Accepted.

Related:

- [SALES_OS_ARCHITECTURE_BASELINE_v1.0.md](../sales/SALES_OS_ARCHITECTURE_BASELINE_v1.0.md)  
- [SALES_A1_5_BASELINE_MANIFEST.md](../sales/SALES_A1_5_BASELINE_MANIFEST.md)  
- [Architecture_ADR_004.md](Architecture_ADR_004.md)  

---

## Context

SALES A1 defined canonical Sales OS architecture, domain model, Marketing/Revenue contracts, agent authority, integration disposition, and CRM UI disposition with zero runtime impact. A1.5 freezes that package as **Sales OS Architecture Baseline v1.0** so later Sales A2+ / Marketing / Revenue / agent work cannot silently redefine ownership.

---

## Decision

1. **Freeze** Sales OS Architecture Baseline **v1.0** as documented in the A1.5 manifest.  
2. **Bind** implementation agents to implement *against* frozen contracts — not reinterpret them.  
3. **Preserve** 12 LIVE Sales capabilities; no deletions or behavioral changes in A1.5.  
4. **Retain** CRM UI disposition **RETAIN_AND_REFACTOR_LATER** (unmounted).  
5. **Freeze** integration classifications: Retain Core 4 / Optional 6 / Deferred 3 / Retired 1.  
6. **Register** two known focused-test exceptions (ENVIRONMENT_DEPENDENCY) — not new regressions.  
7. **Require** explicit ADR + approved sprint to amend any frozen Sales contract after A1.5.  
8. **Do not** bump Architecture v2.2 version; additive Sales baseline only.

---

## Compatibility impact

| Area | Impact |
|------|--------|
| Runtime / DB / APIs | None |
| Marketing OS | None |
| Revenue OS implementation | None |
| Architecture v2.2 | Unchanged |

---

## Consequences

- Recommended next: **SALES A2 — Sales OS Implementation Priority Review** (planning only until started).  
- Unfreeze path: new ADR + Founder-approved sprint naming which contract versions change.

---

## Verification

Focused 15/17 with 2 known exceptions matching A1; full regression historical failures UNCHANGED; new regressions 0; cross-agent conflicts 0.
