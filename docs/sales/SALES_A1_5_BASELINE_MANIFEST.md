# SALES A1.5 — Baseline Manifest

**Baseline:** SALES OS ARCHITECTURE v1.0  
**Status:** FROZEN  
**Sprint:** SALES A1.5  
**Date:** 2026-08-13  
**ADR:** [Architecture_ADR_005.md](../architecture/Architecture_ADR_005.md)

Hashing: This repository uses SHA-256 checksums selectively (e.g. deployment packages). **No new hashing mechanism** introduced for A1.5. Authority is path + STATUS:FROZEN + ADR-005.

---

## Frozen artifact list (authoritative)

| # | Path | Role |
|---|------|------|
| 1 | `docs/sales/SALES_OS_ARCHITECTURE_BASELINE_v1.0.md` | Architecture baseline |
| 2 | `docs/sales/SALES_DOMAIN_MODEL_CONTRACT_v1.0.md` | Domain model contract |
| 3 | `docs/sales/SALES_MARKETING_BOUNDARY_CONTRACT_v1.0.md` | Marketing ↔ Sales |
| 4 | `docs/sales/SALES_REVENUE_BOUNDARY_CONTRACT_v1.0.md` | Sales ↔ Revenue |
| 5 | `docs/sales/SALES_AGENT_AUTHORITY_CONTRACT_v1.0.md` | Agent authority |
| 6 | `docs/sales/SALES_INTEGRATION_DISPOSITION_v1.0.md` | Integration freeze |
| 7 | `docs/sales/CRM_UI_DISPOSITION_v1.0.md` | CRM UI disposition |
| 8 | `docs/sales/SALES_A1_5_KNOWN_TEST_EXCEPTIONS.md` | Known test exceptions |
| 9 | `docs/sales/SALES_A1_5_BASELINE_MANIFEST.md` | This manifest |
| 10 | `docs/architecture/Architecture_ADR_005.md` | Freeze ADR |

## Binding A1 sources (frozen by reference)

| Path | Role |
|------|------|
| `docs/sales/SALES_OS_ARCHITECTURE.md` | Canonical architecture prose |
| `docs/sales/SALES_DOMAIN_MODEL.md` | Domain reconciliation |
| `docs/sales/SALES_MARKETING_CONTRACT.md` | QualifiedDemand contract |
| `docs/sales/SALES_REVENUE_CONTRACT.md` | CommercialOutcome contract |
| `docs/sales/SALES_AGENT_AUTHORITY_MATRIX.md` | Full authority matrix |
| `docs/sales/SALES_INTEGRATION_DISPOSITION.md` | I01–I14 detail |
| `docs/sales/SALES_CRM_UI_DECISION.md` | UI decision rationale |
| `docs/sales/SALES_A1_MIGRATION_MAP.md` | Migration dispositions |
| `docs/architecture/Architecture_ADR_004.md` | Sales boundary ADR |

## Parent freezes (must not break)

| Baseline | Status |
|----------|--------|
| Architecture v2.2 | FROZEN |
| Marketing OS engines / Publishing / Website / SEO baselines | FROZEN |
| Toolchain Baseline v1.0 | FROZEN |
| Platform Agent Registry v1.0 | FROZEN |

---

## Verification snapshot (A1.5)

| Metric | Value |
|--------|-------|
| Focused tests | 15/17 |
| Known exceptions | 2 |
| Full regression | 397/409; 8 failed; 4 errors |
| Historical failures | UNCHANGED |
| New regressions | 0 |
| Feature / runtime / DB / integrations activated | 0 |
| Cross-agent conflicts | 0 |

---

## Change control

Any change to frozen Sales architecture, domain model, Marketing/Sales ownership, Sales/Revenue ownership, agent authority, integration disposition, or CRM UI disposition requires an explicit ADR and approved sprint. Implementation may target contracts; it may not silently reinterpret them.

**SALES OS ARCHITECTURE BASELINE v1.0 FROZEN**
