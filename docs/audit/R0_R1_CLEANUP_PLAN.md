# R0 → R1 Cleanup Plan

**Date:** 2026-08-11 · **Prerequisite:** Founder review of R0 packet  
**Rule:** Small reversible slices; no blind mass delete

---

## R1A — Generated / local artifact hygiene

| Field | Content |
|-------|---------|
| Files | `.gitignore` updates; ensure `.crewai_*`, `.wrangler/`, `frontend/dist/`, selective `output/` ignored; delete `src/*.py.old`; delete empty `revenue_os/pipeline/` |
| Behavior impact | None expected |
| Tests | Full suite + focused engines |
| Rollback | `git revert` |
| Approval | Coordinator; Founder if `output/` ignore policy ambiguous |

---

## R1B — Dead / shadowed code

| Field | Content |
|-------|---------|
| Files | Shadowed `@app` HTML/API duplicates in `runner_api.py`; optional orphan `orchestration_run.html` decision; `openapi_schemas` wire-or-delete |
| Behavior impact | None if first-match already uses `ui_router` |
| Tests | UI route ownership tests; smoke all nav paths; `/marketing` fix if bundled |
| Rollback | revert |
| Approval | Eng lead |

---

## R1C — Stale routes / templates

| Field | Content |
|-------|---------|
| Files | Fix `/marketing` `integration_status`; fix or remove dead POST `/qa`, `/sheet-sync`, qa-report, marketing/run links; Health nav → JSON or HTML |
| Behavior impact | UX fixes |
| Tests | UI smoke + template render tests |
| Rollback | revert |
| Approval | Eng lead |

---

## R1D — Legacy migration remnants (non-destructive first)

| Field | Content |
|-------|---------|
| Files | Branding rename plan only OR Founder archive of CMS siblings; **no** Hashnode delete without FD |
| Behavior impact | Branding/docs only if rename |
| Tests | Health string tests if rename |
| Rollback | revert / restore archive |
| Approval | **Founder required** for archive + brand |

---

## R1E — Documentation consolidation

| Field | Content |
|-------|---------|
| Files | Add `docs/README.md`, `docs/marketing/INDEX.md`, `docs/operations/INDEX.md`, `docs/governance/INDEX.md`; fix stale “current/next” banners; mark M4 duplicates |
| Behavior impact | None (docs) |
| Tests | None / link check optional |
| Rollback | delete indexes |
| Approval | Ledger / Coordinator |

---

## Out of R1 (separate sprints)

- Publishing → Website adapter wire  
- Social S1 LinkedIn Manual Publisher  
- ArtifactCrew merge  
- Hashnode retirement  
- CI/Docker/requirements lockfile alignment (may be R1F if Founder wants toolchain)

---

## Global gates

- Architecture / frozen contracts: **UNCHANGED**  
- No production deploy as cleanup side-effect  
- No secret commits  
- Each slice: one PR, reversible
