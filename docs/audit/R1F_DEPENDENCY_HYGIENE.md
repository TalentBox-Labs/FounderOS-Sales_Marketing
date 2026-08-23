# R1F — Dependency Hygiene (BEACON)

**Sprint:** R1F  
**Date:** 2026-08-13  
**Mode:** MEASUREMENT ONLY — no dependency removal

---

## Manifests Inspected

| Artifact | Present | Notes |
|----------|---------|-------|
| `requirements.txt` | Yes | Primary API/runtime |
| `requirements-revenue.txt` | Yes | Revenue/Celery path |
| `pyproject.toml` | **No** | Still absent |
| Root `package.json` | **No** | — |
| `frontend/package.json` | Yes | Optional CRM |
| `Dockerfile` / `docker-compose.yml` / `docker-compose.demo.yml` | Yes | Redis service wired |
| Lockfiles | **No** | Pin drift risk unchanged vs R0 |

---

## Removals Already Applied (prior)

| Package | Manifest | Status |
|---------|----------|--------|
| `crewai-tools` | `requirements.txt` | **Removed** (R1D); still absent |
| `asyncpg` | `requirements-revenue.txt` | **Removed** (R1D); still absent |

---

## Remaining Candidates

| Package | Evidence | Class |
|---------|----------|-------|
| `google-auth-httplib2` | Only appears as install-hint string in `google_sheets_verify.py`; no `import google_auth_httplib2` | **UNUSED candidate** (deferred R1D) |
| `redis` (explicit pin) | Celery uses `REDIS_URL`; compose runs Redis; `celery[redis]` also present — explicit pin may be redundant | **OPTIONAL / DUPLICATE pin** — not safely unused |
| Frontend npm tree | Optional; `frontend/dist` absent by design | **OPTIONAL future** |

---

## Dev / Runtime Separation

- Demo compose still carries intentional demo credentials (R1B NEW-02 deferred LOW).
- CI vs Docker lock parity remains a toolchain debt (R0); not blocking Social Engine design.

---

## Score Inputs

| Metric | R0 | Current |
|--------|---:|--------:|
| Unused deps (candidates) | 4 | **2** remaining candidates (`google-auth-httplib2` + redis pin redundancy) |
| Confirmed removed | 0 | 2 |
| Lockfile | Absent | Absent |

**Dependency Hygiene Score: 68/100** (R0: 55; Δ +13)

Rationale: two unused packages gone; Redis/Celery stack is real; remaining uncertainty is pin redundancy + no lockfile — medium debt, not runtime-blocking.
