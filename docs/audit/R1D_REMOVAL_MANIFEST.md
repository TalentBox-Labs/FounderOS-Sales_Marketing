# R1D — Removal Manifest

**Date:** 2026-08-12  
**Rollback:** `git checkout` of listed paths / restore requirement lines

---

## Prior R1A (already gone — reviewed, not re-deleted)

| Path | Reason | Rollback |
|------|--------|----------|
| `src/artifact_crew.py.old` | Backup unused | git |
| `src/distribution_crew.py.old` | Backup unused | git |
| `src/editor_crew.py.old` | Backup unused | git |
| `src/generation_crew.py.old` | Backup unused | git |
| `src/marketing_crew.py.old` | Backup unused | git |
| `revenue_os/pipeline/` | Empty package | git |

---

## R1D removals

| Path / symbol | Reason | Evidence | Owner | Rollback | Tests |
|---------------|--------|----------|-------|----------|-------|
| `src/openapi_schemas.py` | Unwired OpenAPI helpers | 0 py imports | Platform | git checkout | import + full suite |
| `scripts/bootstrap_remaining_weeks.py` | One-shot scaffold complete | No runtime/CLI registration | Ops scripts | git checkout | full suite |
| `scripts/sheets_copy_mirror_values.gs` | Superseded by `reader_tab_sync.py` | Docstring in reader_tab_sync | Ops scripts | git checkout | full suite |
| `runner_api._render_orchestration_run_detail` (+ `import html`) | Superseded by Jinja `orchestration_run.html` (R1C) | 0 callers | Shared Platform | git checkout | `test_r1c_route_hygiene`, orchestration detail |
| `crewai-tools>=…` from `requirements.txt` | Unused package | 0 imports | Toolchain | restore line | import/startup |
| `asyncpg>=…` from `requirements-revenue.txt` | Unused async driver | 0 imports; sync engine | Toolchain | restore line | import/startup |

---

## Not removed (deferred)

`validation_runner.py`, `src/crew.py`, ArtifactCrew/phase2a, dual Hashnode, shadowed `@app` handlers, `redis` pin, `google-auth-httplib2` pin.
