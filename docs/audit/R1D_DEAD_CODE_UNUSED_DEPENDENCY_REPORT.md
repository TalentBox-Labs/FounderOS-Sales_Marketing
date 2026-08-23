# R1D — Dead Code & Unused Dependency Report

**Date:** 2026-08-12  
**Coordinator:** Lead Engineering Coordinator  
**Agents:** FORGE · BEACON · SENTINEL · ATLAS  
**Cross-Agent Conflicts:** 0

---

## Scope

Only dead-code candidates and unused dependencies. No moves, legacy consolidation, frontend CRM build, or route work.

---

## Pre-R1D Baseline

397/409; 8 failed; 4 errors; Runtime PASS; historical identities recorded.

---

## Dead Code Candidates Reviewed

**15/15** (re-baselined set in `R1D_DEAD_CODE_AUDIT.md`)

| Result | N |
|--------|--:|
| Confirmed dead | 10 |
| Removed this sprint | 4 |
| Already removed R1A | 6 |
| Deferred | 5 |
| False positives | 0 |

---

## Confirmed Dead Code / Removals

See manifest. R1D deleted: `openapi_schemas.py`, `bootstrap_remaining_weeks.py`, `sheets_copy_mirror_values.gs`, `_render_orchestration_run_detail`.

---

## False Positives

**0**

---

## Deferred Candidates

validation_runner · crew helpers · ArtifactCrew · dual Hashnode · shadowed `@app` handlers

---

## Dependencies Reviewed

**4/4** · Confirmed unused **2** · Removed **2** (`crewai-tools`, `asyncpg`) · Deferred **2** (`redis` pin, `google-auth-httplib2`)

---

## Files Removed (this sprint)

**3** files (+ 1 symbol in `runner_api.py`)

## Symbols Removed

**1** (`_render_orchestration_run_detail`; also unused `import html`)

## Dependency Manifest Changes

`requirements.txt`, `requirements-revenue.txt`

---

## Tests

| Suite | Result |
|-------|--------|
| Focused engines + R1C routes | **113 passed** |
| Full | **397/409; 8 failed; 4 errors** |
| Historical identities | **UNCHANGED** |
| New regressions | **0** |

## Runtime

**PASS** (`/`, `/marketing`, `/publishing`, `/seo` 200; `/app` 503 optional)

## Frozen Contracts / Architecture / Behavior

**UNCHANGED** / **PASS** / **UNCHANGED**

## Rollback

**READY** — git restore paths in `R1D_REMOVAL_MANIFEST.md`

---

## Remaining Technical Debt

Artifact/Generation merge · Hashnode consolidation · `@app` dedupe · validation_runner retire · crew.py QA path · optional redis pin cleanup · React CRM dist (non-blocking)

## Recommended R1E Scope

**R1E — LEGACY & MIGRATION REMNANT CONSOLIDATION**

---

## Verdict

**R1D DEAD CODE & UNUSED DEPENDENCY CLEANUP COMPLETE — READY FOR R1E**
