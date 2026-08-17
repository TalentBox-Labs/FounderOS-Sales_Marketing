# R0 — Documentation Governance Audit (LEDGER)

**Date:** 2026-08-11 · **Corpus:** 284 markdown files under `docs/` · **Mode:** AUDIT ONLY

---

## Verdict

Debt is **navigation + supersession hygiene**, not over-retention. Historical freezes/ADRs/recovery **must retain**.

| Class | Approx |
|-------|-------:|
| HISTORICAL — RETAIN | ~175 |
| CANONICAL CURRENT | ~55 |
| SUPERSEDED — RETAIN WITH POINTER | ~20 |
| STALE | ~22 |
| DUPLICATE | ~8 |
| REMOVE CANDIDATE | ~4 |

**Indexes present under `docs/`:** 0 README/INDEX files → **navigation chaos**.

---

## Folder rollup

| Folder | MD | Dominant | Index priority |
|--------|---:|----------|----------------|
| marketing/ | 99 | HISTORICAL + CURRENT | **Critical** |
| migration/ | 50 | HISTORICAL | Medium |
| operations/ | 44 | HISTORICAL + CURRENT | High |
| governance/ | 27 | MIXED + STALE next-sprint | High |
| architecture-audit/ | 17 | HISTORICAL | Low–Med |
| architecture/ | 15 | CANONICAL + SUPERSEDED | Medium |
| runtime-* | 15 | HISTORICAL | Medium |
| root loose Phase docs | 14 | STALE | Quarantine |
| security / editorial / implementation | 3 | CURRENT/HISTORICAL | Cross-link |
| audit/ | (this pack) | NEW | Ledger home |

---

## Canonical tips (living SoT)

Architecture **v2.2** · Marketing OS **v2.2** · Publishing/Website/Static/Deploy freezes · SEO Readiness + Technical **v1.0** · Website Prod Baseline · Toolchain Baseline · Platform Agent Registry · P1 → Social · Social S0 decision packet · FDR-N05 domain **OPEN**

---

## Explicit non-delete

ADRs, `*BASELINE*`, `*FREEZE*`, architecture-audit, runtime verification/certification, M6 recovery ops, migration packs, ratified FDR.

---

## Soft REMOVE CANDIDATE (later)

Confirmed near-duplicate M4 Hermes/Sentinel twins **after** citation check; root Phase narratives only after Founder confirms supersession.

---

## Index recommendation

Add `docs/README.md` + `docs/marketing/INDEX.md` + `docs/operations/INDEX.md` + `docs/governance/INDEX.md` **before** any doc moves in R1E.
