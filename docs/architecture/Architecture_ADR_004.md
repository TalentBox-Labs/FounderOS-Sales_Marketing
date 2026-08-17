# Architecture ADR-004 — Sales OS Domain & Cross-OS Boundaries

**ADR ID:** Architecture_ADR_004  
**Status:** Accepted (governance)  
**Sprint:** SALES A1 — Sales OS Architecture & Domain Boundary  
**Date:** 2026-08-13  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`

**Decision type:** Sales OS destination clarification and cross-OS contract definition  
**Implementation changes in this ADR:** **NONE**

Related:

- [Architecture_v2.2.md](Architecture_v2.2.md) (FROZEN — additive cross-links only)
- [Platform_vs_OS_Boundaries.md](Platform_vs_OS_Boundaries.md)
- [../sales/SALES_OS_ARCHITECTURE.md](../sales/SALES_OS_ARCHITECTURE.md)
- [../sales/SALES_REVENUE_CONTRACT.md](../sales/SALES_REVENUE_CONTRACT.md)
- [../sales/SALES_MARKETING_CONTRACT.md](../sales/SALES_MARKETING_CONTRACT.md)

---

## Context

SALES A0 established that Sales capability is **PARTIAL**, domain model **CONFLICTED**, and Sales↔Revenue boundary **CONFLICTED** in documentation vs co-located `revenue_os/` implementation. Twelve LIVE Sales capabilities must be preserved. Marketing OS architecture remains FROZEN (v2.2 / ADR-003).

Migration and capability matrix documents sometimes attribute CRM to Sales OS while Architecture v2.0 law attributes **CRM entities** to Revenue OS. A1 must reconcile without runtime migration.

---

## Decision

1. **Adopt** the Sales OS responsibility model in `docs/sales/SALES_OS_ARCHITECTURE.md` as canonical destination language for Sales A1 onward.
2. **Ratify** entity system-of-record ownership:
   - **Revenue OS** owns persisted CRM entities: `Company`, `Contact`, `Deal`, `Pipeline`, `Activity`, and related approval/forecast records.
   - **Sales OS** owns prospecting, outreach **operations**, SDR workflows, qualification **policy/workflow**, pipeline **operations**, and sales engagement orchestration **consuming** Revenue entities.
3. **Ratify** conceptual aliases (not separate tables in target model):
   - **Lead** → early-lifecycle `Contact` (+ `ContactStatus` / events).
   - **Opportunity** → `Deal` in sales-process language.
   - **Account** (CSM) → `Company` in customer-success language.
4. **Adopt** cross-OS contracts:
   - Marketing → Sales: `SALES_MARKETING_CONTRACT.md` (event/intake; no shared persistence coupling).
   - Sales → Revenue: `SALES_REVENUE_CONTRACT.md` (closed-won commercial event intake; Revenue does not duplicate CRM).
5. **Adopt** Sales Agent Authority Matrix (`SALES_AGENT_AUTHORITY_MATRIX.md`) as governance SoT for human vs agent actions.
6. **CRM UI disposition:** **RETAIN_AND_REFACTOR_LATER** (`SALES_CRM_UI_DECISION.md`) — do not mount during A1.
7. **Preserve** all 12 LIVE capabilities listed in A0; no deletion, rename, move, or behavioral change in A1.
8. **No Architecture version bump** beyond additive ADR-004 and Sales pack cross-links. Architecture v2.2 remains FROZEN.

---

## Compatibility impact

| Domain | Impact |
|--------|--------|
| Marketing OS frozen engines | **None** — contracts are forward-looking |
| Revenue OS runtime | **None** — co-location accepted as legacy |
| Shared / AI / Automation platforms | **None** — consumption rules clarified |
| Existing APIs | **Unchanged** |

---

## Migration impact

All structural alignment deferred to future sprints per `SALES_A1_MIGRATION_MAP.md`. A1 is documentation and contract only.

---

## Consequences

- Future Sales implementation sprints must map changes to Sales vs Revenue ownership before code moves.
- Dual API stacks (`runner_api` CRM vs `revenue_os.main` JWT) remain **ACCEPTED_LEGACY** until a migration sprint.
- A1.5 baseline freeze recommended after Founder review of Sales pack.
