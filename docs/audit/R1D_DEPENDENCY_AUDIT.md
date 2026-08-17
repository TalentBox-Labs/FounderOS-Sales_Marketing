# R1D — Dependency Audit (BEACON)

**Date:** 2026-08-12

## R0 unused candidates (4) re-verified

| Package | Manifest | Classification | Action | Evidence |
|---------|----------|----------------|--------|----------|
| `crewai-tools` | `requirements.txt` | **UNUSED — SAFE TO REMOVE** | **Removed** | 0 `crewai_tools` imports; pip Required-by empty |
| `asyncpg` | `requirements-revenue.txt` | **UNUSED — SAFE TO REMOVE** | **Removed** | Sync SQLAlchemy + `psycopg2` only; 0 imports |
| `redis` (direct pin) | `requirements-revenue.txt` | USED — DEPLOYMENT (transitive via `celery[redis]`) | **DEFER** pin keep | No app `import redis`; Celery broker needs redis package |
| `google-auth-httplib2` | `requirements.txt` | USED — RUNTIME (transitive) | **DEFER** pin keep | Required-by `google-api-python-client` |

**Reviewed:** 4/4 · **Confirmed unused:** 2 · **Removed:** 2 · **Deferred:** 2

No version upgrades. No replacements.
