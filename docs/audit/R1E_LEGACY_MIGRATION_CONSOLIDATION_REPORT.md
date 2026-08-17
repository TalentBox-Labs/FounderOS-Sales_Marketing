# R1E — Legacy & Migration Consolidation Report

**Date:** 2026-08-12  
**Coordinator:** Lead Engineering Coordinator  
**Agents:** SCOUT · LEDGER · ATLAS · FORGE · SENTINEL  
**Cross-Agent Conflicts:** 0

---

## Scope

Re-audit R0’s **28** legacy/migration remnants. Consolidation-first. No governance/history deletion. No reference-repo deletion.

---

## R1D Reconciliation

See `R1E_R1D_RECONCILIATION.md`.

**Reconciled: YES** — Confirmed(10)=R1A(6)+R1D(4); Deferred(5) disjoint; Removed(4)+Deferred(5)=9 was a **REPORTING ERROR** (omitted R1A + mixed categories).

---

## Legacy Items Reviewed

**28/28** — `R1E_LEGACY_INVENTORY.md`

## Active Compatibility Items

**12** (branding contracts, WORKCREW_* env, Hashnode optional, Sheets mirror, publishing stubs, stub provider, n8n, site_origin denylist, etc.)

## Governance/Historical Items Retained

**8+** (architecture-audit, comments, vault notes, Phase docs, non-findings)

## Migration Evidence

**5+** themes / full `docs/migration/**` retained

## Archive Candidates

**3** (sibling CMS×2, root Phase docs) — **not moved**

## Archived Items

**0**

## Consolidated Items

**1** — `R1E_LEGACY_NAV_INDEX.md` (pointers only)

## Removed Items

**0**

## Deferred Items

**9** Founder-decision themes (brand, domain, Hashnode SoT, CMS archive timing, infra rename, shadowed handlers, …)

---

## workcrew.ai References

| Kind | Disposition |
|------|-------------|
| Denylist in `site_origin` | KEEP — ACTIVE (safety) |
| marketing_crew / OpenAPI / go_live / hashnode strings | DEFER — FOUNDER (stale emitters) |
| `input/**` FM | KEEP — MIGRATION/CONTENT |
| Docs historical | KEEP |

**Active runtime emitter surfaces remaining: 4** (excluding denylist + content FM bulk)

## Hashnode/Old Provider Runtime Remnants

**3** (CLI tool, RevenueOS publisher, marketing status) — KEEP ACTIVE / FD

## CMS/Sheets Runtime Remnants

**1** active mirror family (`sheet_sync*`) — KEEP (not SoT)

## Reference Repository Decision

**FOUNDER DECISION REQUIRED** (KEEP until Founder authorizes ARCHIVE outside canonical repo)

---

## Tests / Runtime / Regression

| Check | Result |
|-------|--------|
| Pre/post full | 397/409; 8 failed; 4 errors |
| Historical identities | UNCHANGED |
| New regressions | 0 |
| Runtime | PASS |
| Focused engines | PASS (same suite as baseline) |
| Architecture | PASS |
| Frozen contracts | UNCHANGED |
| Behavior | UNCHANGED |
| Rollback | READY (delete nav index only) |

---

## Remaining Legacy Debt

1. Brand rename WorkCrew → Founder OS  
2. Domain / `workcrew.ai` emitter cleanup after FDR-N05  
3. Hashnode vs Website Engine SoT  
4. Archive sibling CMS trees  
5. Shadowed `@app` handler dedupe  
6. Optional root Phase doc quarantine  

## Recommended Next Sprint

**R1F — REPOSITORY HYGIENE RE-AUDIT**

---

## Verdict

**R1E LEGACY & MIGRATION CONSOLIDATION COMPLETE — READY FOR R1F**
