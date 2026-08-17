# R1E — Governance & Historical Evidence Audit (LEDGER)

**Date:** 2026-08-12  
**Rule:** Prefer KEEP WITH SUPERSEDED POINTER over deletion.

---

## Protected corpora (MUST RETAIN)

| Corpus | Class |
|--------|-------|
| `docs/architecture/**` ADRs + v2.x | KEEP — GOVERNANCE |
| `docs/architecture-audit/**` | KEEP — GOVERNANCE / BASELINE |
| `docs/migration/**` | KEEP — MIGRATION EVIDENCE |
| `docs/governance/**` FDR/toolchain/registry | KEEP — GOVERNANCE |
| `docs/operations/**` M6 recovery / runbooks | KEEP — ROLLBACK / RECOVERY |
| `docs/runtime-verification/**`, `runtime-certification/**` | KEEP — GOVERNANCE |
| `docs/audit/R0*`–`R1D*` | KEEP — AUDIT EVIDENCE |
| `docs/marketing/**` freezes / S0–P1 | KEEP — GOVERNANCE (engine history) |
| `docs/security/S0_LINKEDIN_*` | KEEP — GOVERNANCE |

**Items deleted this sprint:** **0**

---

## Supersession hygiene (non-destructive)

| Topic | Current tip | Older nodes |
|-------|-------------|-------------|
| Architecture | v2.2 + ADR-003 | v2.0 / v2.1 |
| Next Marketing engine | P1 → Social | Post-M / N0 SEO advice |
| SEO | S1.5 + S2.5 freezes | S0 models |
| Website prod | M7.5 baseline | M1–M7 evidence |

**Action:** Navigation consolidated via `docs/audit/R1E_LEGACY_NAV_INDEX.md` (pointers only). **No file moves. No history erased.**

---

## Duplicate docs

Near-duplicate M4 Hermes/Sentinel pairs remain **KEEP — HISTORICAL** (citation risk if deleted). Consolidation = index pointers, not merge-delete.

---

## Root Phase narratives (14)

Class: **KEEP — GOVERNANCE/HISTORICAL** + **ARCHIVE candidate** for a future Founder-approved quarantine. **Not moved in R1E.**
