# R0 — Dependency / Toolchain Audit (BEACON)

**Date:** 2026-08-11 · **Mode:** AUDIT ONLY — nothing uninstalled

---

## Counts

| Metric | N |
|--------|--:|
| Unique Python pkgs (3 req files) | 23 |
| Unused candidates | **4** (2 high + 2 low) |
| Duplicated pins | 4 |
| Python lockfile | **0** (absent) |
| Frontend unused | 0 |
| Undeclared-but-imported | 1 (`openai` dynamic) |

---

## Unused candidates

| Package | Confidence | Evidence |
|---------|------------|----------|
| `crewai-tools` | HIGH | No imports |
| `asyncpg` | HIGH | Sync SQLAlchemy only |
| `redis` direct pin | LOW | Celery URL-only; likely transitive |
| `google-auth-httplib2` | LOW | No direct import; may be transitive |

---

## Critical toolchain issues

1. CI installs **only** `requirements.txt`; Docker installs all three.  
2. CrewAI pin conflict: `>=0.80` vs `>=1.9`.  
3. No Python lockfile.  
4. Render blueprint omits Redis/Celery present in compose.  
5. Ruff approved in governance but not shipped.  
6. `pytest` in runtime Docker image.

---

## Abandoned / stale

`bootstrap_remaining_weeks.py` (one-shot); `sheets_copy_mirror_values.gs` (superseded); `COVERAGE.md` snapshot stale; secondary `revenue_os.main` deploy-abandoned but test-kept.

**Paid tools approved (policy):** 0. Host/API usage may still incur cost when enabled (Render starter, OpenAI, etc.) — outside “dev tool install” scope.
