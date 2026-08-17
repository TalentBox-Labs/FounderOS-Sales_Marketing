# R0 — Code Health (FORGE)

**Date:** 2026-08-11 · **Mode:** AUDIT ONLY

---

## Executive

| Class | Count |
|-------|------:|
| HIGH confidence REMOVE | 6 paths (5× `*.py.old` + empty `revenue_os/pipeline/`) |
| MEDIUM consolidate / quarantine | 9 |
| Orphaned routers | 0 |
| Broken-but-wired agents | 2 (`SDRCrew`, `CSMCrew`) |

---

## KEEP — ACTIVE (major)

`runner_api.py` + routers; `publishing_engine`; `editorial_approval`; `website_engine`; `website_deployment`; `seo_engine` (+ technical); Content Studio routers; pipeline crews; `revenue_os` services/models/tasks; Celery app.

---

## REMOVE CANDIDATES

| ID | Path | Evidence | Refs | Dynamic risk | Runtime risk | Action | Confidence |
|----|------|----------|------|--------------|--------------|--------|------------|
| RC-01a..e | `src/{artifact,distribution,editor,generation,marketing}_crew.py.old` | Backups beside live crews; 0 imports | 0 | None | None | REMOVE in R1A | **HIGH** |
| RC-02 | `revenue_os/pipeline/` (empty `__init__.py`) | 0 `revenue_os.pipeline` refs | 0 | Low | None | REMOVE package | **HIGH** |
| RC-03 | `src/openapi_schemas.py` | 0 code imports; docs only | 0 code | Low | Low | Wire or delete later | MEDIUM |
| RC-04 | `src/tools/validation_runner.py` | 5-line alias | 0 imports | Med (CLI) | Low | KEEP until docs updated | MEDIUM |
| RC-05 | `src/crew.py` `run_qa_agent` | Legacy vs `QACrew` | Helpers still used | Med | High if whole file deleted | Partial deprecate | MEDIUM |
| RC-06 | `ArtifactCrew` + phase2a YAML | Parallel GenerationCrew | Tests/CLI | Med | Med | MERGE then retire | MEDIUM |
| RC-07 | `scripts/bootstrap_remaining_weeks.py` | One-off scaffold | Low | Low | None | ARCHIVE | MEDIUM |
| RC-08 | Dual Hashnode clients | `hashnode_publish` vs `social_publisher` | Both live | High | High | CONSOLIDATE later | MEDIUM |
| RC-09 | Duplicate `@app` HTML/API in `runner_api.py` | Shadowed by routers | N/A | N/A | Med if wrong delete | Deduplicate after tests | MEDIUM |

---

## Dead / incomplete (KEEP — still referenced)

| Item | Class |
|------|-------|
| Publishing social adapters `NOT_IMPLEMENTED` | KEEP (contract) |
| Website adapter `PLACEHOLDER` | STALE wire gap |
| Orchestration synthetic agent execute | KEEP stub |
| `SDRCrew` / `CSMCrew` BaseCrew init mismatch | FIX candidate — wired |

---

## Dynamic import warning

Validators and crews loaded via subprocess `-m` maps (`pipeline_runner`, `validate_staged`, routers). **Never REMOVE on static import count alone.**

---

## Recommended R1 sequence

1. Delete `*.py.old` + empty pipeline package.  
2. Route-ownership tests → remove shadowed `@app` handlers.  
3. Fix or feature-flag SDR/CSM crews.  
4. Plan Artifact→Generation and Hashnode consolidation (separate sprints).
