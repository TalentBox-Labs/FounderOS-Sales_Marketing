# SALES A1 — Architecture Decision Record

**Sprint:** SALES A1 — Sales OS Architecture, Domain Reconciliation & Cross-OS Boundary Definition  
**Date:** 2026-08-13  
**Coordinator:** Lead Engineering Coordinator  
**Cross-Agent Conflicts:** **0**

---

## Executive summary

SALES A1 resolves A0 structural conflicts through **governance and contracts only**. Sales OS destination architecture is defined; domain model conflicts are resolved conceptually; Marketing and Revenue boundaries are contract-defined; agent authority is matrix-defined; CRM UI disposition is decided; 14/14 integrations classified; 2/2 test failures classified. **All 12 LIVE capabilities preserved.** No code, runtime, DB, or integration changes.

**Verdict: READY FOR SALES A1.5**

---

## A0 reconciliation

| A0 finding | A1 resolution |
|------------|---------------|
| Sales OS PARTIAL | Acknowledged — target architecture defined; migration mapped |
| Domain CONFLICTED | **RESOLVED** (conceptual) |
| Sales↔Marketing PARTIAL | **DEFINED** |
| Sales↔Revenue CONFLICTED | **DEFINED** |
| Agent governance PARTIAL | **DEFINED** |
| CRM UI UNMOUNTED | **RETAIN_AND_REFACTOR_LATER** |
| 28 capabilities | 12 LIVE preserved; gaps in migration map |

---

## Key decisions

1. **Revenue OS** = CRM entity SoT; **Sales OS** = prospecting, outreach ops, qualification workflow, pipeline ops.  
2. **Lead** / **Opportunity** / **Account** = documented aliases — not new tables in A1.  
3. **Marketing → Sales:** `QualifiedDemand` contract (not implemented).  
4. **Sales → Revenue:** `CommercialOutcome` contract (not implemented).  
5. **CRM UI:** retain source; refactor before mount.  
6. **ADR-004** accepted; Architecture v2.2 remains FROZEN (additive links only).

---

## Completion gates

| Gate | Status |
|------|--------|
| Sales Domain Model RESOLVED | ✅ |
| Sales↔Marketing DEFINED | ✅ |
| Sales↔Revenue DEFINED | ✅ |
| Agent Governance DEFINED | ✅ |
| CRM UI DECIDED | ✅ |
| 14/14 integrations classified | ✅ |
| 2/2 test failures classified | ✅ |
| 12/12 live capabilities preserved | ✅ |
| New regressions 0 | ✅ |
| Feature code changes 0 | ✅ |
| Runtime changes 0 | ✅ |
| DB migrations 0 | ✅ |
| Integrations activated 0 | ✅ |
| Cross-agent conflicts 0 | ✅ |

---

## Deliverable index

| Document |
|----------|
| [SALES_OS_ARCHITECTURE.md](SALES_OS_ARCHITECTURE.md) |
| [SALES_DOMAIN_MODEL.md](SALES_DOMAIN_MODEL.md) |
| [SALES_MARKETING_CONTRACT.md](SALES_MARKETING_CONTRACT.md) |
| [SALES_REVENUE_CONTRACT.md](SALES_REVENUE_CONTRACT.md) |
| [SALES_AGENT_AUTHORITY_MATRIX.md](SALES_AGENT_AUTHORITY_MATRIX.md) |
| [SALES_INTEGRATION_DISPOSITION.md](SALES_INTEGRATION_DISPOSITION.md) |
| [SALES_CRM_UI_DECISION.md](SALES_CRM_UI_DECISION.md) |
| [SALES_A1_TEST_CLASSIFICATION.md](SALES_A1_TEST_CLASSIFICATION.md) |
| [SALES_A1_MIGRATION_MAP.md](SALES_A1_MIGRATION_MAP.md) |
| [../architecture/Architecture_ADR_004.md](../architecture/Architecture_ADR_004.md) |

Prior A0 pack: `SALES_A0_*.md`

---

## Recommended next sprint

**SALES A1.5 — SALES OS ARCHITECTURE BASELINE FREEZE**

Do **not** execute automatically. Founder review of ADR-004 and Sales contracts required before implementation sprints.

---

## Workstream independence

Marketing OS (Social FD-01 → S0.1 → S1) continues independently. Sales A1 does not modify Marketing frozen contracts.
