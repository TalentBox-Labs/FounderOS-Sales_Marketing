# R1D — Dead Code Audit (FORGE)

**Date:** 2026-08-12  
**Post:** R1A–R1C.1 tree

## Re-baselined candidate set (15)

| # | Path / symbol | Classification | Action | Confidence |
|---|---------------|----------------|--------|------------|
| 1–5 | `src/*_crew.py.old` (5) | A CONFIRMED DEAD | Already removed R1A | HIGH |
| 6 | `revenue_os/pipeline/` | A CONFIRMED DEAD | Already removed R1A | HIGH |
| 7 | `src/openapi_schemas.py` | A CONFIRMED DEAD | **Removed R1D** | HIGH |
| 8 | `runner_api._render_orchestration_run_detail` | A CONFIRMED DEAD | **Removed R1D** | HIGH |
| 9 | `scripts/bootstrap_remaining_weeks.py` | A CONFIRMED DEAD (one-shot) | **Removed R1D** | HIGH |
| 10 | `scripts/sheets_copy_mirror_values.gs` | A CONFIRMED DEAD (superseded by `reader_tab_sync`) | **Removed R1D** | HIGH |
| 11 | `src/tools/validation_runner.py` | F / CLI transitional | **DEFER** | — |
| 12 | `src/crew.py` | G / C helpers + tests | **DEFER** | — |
| 13 | `ArtifactCrew` + phase2a YAML | H DUPLICATE + tests | **DEFER** | — |
| 14 | Dual Hashnode clients | H DUPLICATE both live | **DEFER** | — |
| 15 | Shadowed `@app` HTML/API in `runner_api.py` | G STALE BUT REFERENCED | **DEFER** | — |

**False positives:** 0 among the 15 (stubs/NOT_IMPLEMENTED engines were never in this 15).

**Confirmed dead:** 10 · **Removed this sprint:** 4 · **Prior R1A:** 6 · **Deferred:** 5
