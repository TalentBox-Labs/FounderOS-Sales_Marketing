# R0 — Proposed Repository Structure (MINIMAL)

**Date:** 2026-08-11 · **Mode:** PROPOSAL ONLY — no moves executed

Prefer **minimal cleanup** over cosmetic restructuring. Do **not** invent speculative folders.

---

## CURRENT → PROPOSED

```
CURRENT (keep as-is for engines)
  src/ tools engines + crews
  runner_api.py + runner_api_routers/
  revenue_os/
  templates/ + tests/ + docs/ + input/ + migrations/

PROPOSED deltas only:
  1. Delete src/*.py.old                          → gone (git history retains)
  2. Delete empty revenue_os/pipeline/            → gone
  3. Strengthen .gitignore                        → ignore .crewai_*, .wrangler/, output/*, frontend/dist
  4. Deduplicate shadowed @app handlers           → runner_api.py slim (after tests)
  5. Add docs/README.md + marketing/operations INDEX  → navigation (R1E)
  6. Quarantine root Phase docs via index label   → no move required initially
  7. CMS sibling trees                            → ARCHIVE outside repo (Founder)
```

**No** proposed merge of `revenue_os/` into `src/`.  
**No** proposed rename of Marketing OS engines.  
**No** deletion of `docs/migration/**` or freeze packs.

---

## Candidate changes (detail)

| Change | Reason | Benefit | Risk | Dependencies | Rollback | Confidence |
|--------|--------|---------|------|--------------|----------|------------|
| Remove `*.py.old` | Unused backups | Less noise | None | None | git checkout | HIGH |
| Remove empty `revenue_os/pipeline/` | Empty package | Clarity | None | Confirm rg | git checkout | HIGH |
| gitignore generated locals | Prevent secret/cache commits | Security hygiene | May hide needed ops files if over-broad | Founder OK on `output/` policy | revert gitignore | HIGH |
| Remove shadowed `@app` HTML | Dead handlers | Maintainability | Medium if first-match assumptions wrong | Route ownership tests | revert commit | MEDIUM |
| Docs indexes | Navigation chaos | Operator clarity | Low | LEDGER index list | delete indexes | HIGH |
| Archive CMS siblings | Migration complete? | Disk/clarity | High if parity incomplete | Founder decision | restore zip | NEEDS FOUNDER |
| Fix `/marketing` context | Runtime 500 | UX | Low | Small UI fix sprint | revert | HIGH (fix, not structure) |
| Consolidate ArtifactCrew | Duplicate generation | Less drift | Med (tests) | Test migration | revert | MEDIUM |

---

## Explicit non-proposals

- Do not relocate `docs/security/` Social auth into marketing without index first.  
- Do not delete Hashnode/sheet tools without Founder channel decision.  
- Do not flatten `docs/marketing/` sprint history.
