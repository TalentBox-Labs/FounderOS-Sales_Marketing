# R1A — Generated / Local Artifact Cleanup (CIPHER)

**Date:** 2026-08-12  
**Scope:** R0’s ~12 generated/local artifact classes  
**Rule:** No secret values in this document

---

## Classification (re-verified)

| # | Artifact | Action | Evidence |
|---|----------|--------|----------|
| 1 | `.env.local` | **KEEP LOCAL** | Already gitignored via `.env.*`; operator secrets |
| 2 | `.env.example` | **KEEP SOURCE-CONTROLLED** | Template only |
| 3 | `.crewai_home/` (incl. `secret.key`) | **IGNORE VIA .gitignore** + KEEP LOCAL | Was missing from ignore; never commit; **not deleted** (secret recovery) |
| 4 | `.crewai_storage/` | **IGNORE VIA .gitignore** + KEEP LOCAL | Same |
| 5 | `.wrangler/` | **IGNORE VIA .gitignore** + KEEP LOCAL | Cache; keep for local deploy ops |
| 6 | `pytest_local.db` / `*.db` | **KEEP LOCAL** | Already `*.db` ignored |
| 7 | `output/qa_reports/**` (tracked) | **KEEP SOURCE-CONTROLLED** / **DEFER** | 67 tracked output files include QA evidence; not R1A delete |
| 8 | `output/website/`, `output/website-deploy/`, `output/publishing/` | **IGNORE VIA .gitignore** + KEEP LOCAL | Untracked runtime packages; **not deleted** (rollback/recovery) |
| 9 | `__pycache__/` | **KEEP LOCAL** | Already ignored |
| 10 | `.pytest_cache/` | **KEEP LOCAL** | Already ignored |
| 11 | `.venv/` | **KEEP LOCAL** | Already ignored |
| 12 | `frontend/dist/` | **IGNORE VIA .gitignore** | Also covered by `frontend/.gitignore`; root pattern added for clarity |
| — | `revenue_os/services/credentials_vault.py` | **KEEP SOURCE-CONTROLLED** | Code module, not a secret file |

---

## Physical deletions of generated artifacts

**0** — Secrets, caches, and deploy packages left on disk (KEEP LOCAL). Hygiene = prevent future VCS pollution.

---

## `.gitignore` updates (applied)

Added:

```
.crewai_home/
.crewai_storage/
.wrangler/
frontend/dist/
output/website/
output/website-deploy/
output/publishing/
```

**Pattern count:** 7  
**Did not** ignore entire `output/` (would conflict with tracked `qa_reports` / `sales` without Founder untrack decision).

---

## Deferred

| Item | Reason |
|------|--------|
| Delete `.crewai_home` from disk | Secret recovery / local tool state |
| Delete `output/website-deploy` from disk | Deploy recovery evidence |
| Untrack `output/qa_reports` | Needs Founder/ops policy (R1B+) |
| Entire `output/` ignore | DEFER — tracked content |

**Generated/Local Artifacts Removed (disk): 0**  
**Protected via ignore: 7 patterns**
