# R0 — Security / Generated Artifacts (CIPHER)

**Date:** 2026-08-11 · **Mode:** AUDIT ONLY  
**Rule:** Secret values not reproduced in this document.

---

## Findings (no values)

| ID | Item | Class | Notes |
|----|------|-------|-------|
| SEC-01 | `.env.local` present locally | LOCAL ONLY | Covered by `.gitignore` `.env.*` |
| SEC-02 | `.env.example` tracked | SOURCE CONTROLLED | Templates only — OK |
| SEC-03 | `.crewai_home/.../secret.key` untracked | LOCAL ONLY / REMOVE CANDIDATE from VCS | **Must never commit**; gitignore gap |
| SEC-04 | `.crewai_storage/.crewai_user.json` | LOCAL ONLY | gitignore gap |
| SEC-05 | `.wrangler/cache` | BUILD/RUNTIME LOCAL | gitignore gap |
| SEC-06 | `pytest_local.db` / `*.db` | RUNTIME OUTPUT | `*.db` gitignored |
| SEC-07 | `output/` website + deploy packages | RUNTIME OUTPUT / BACKUP | Partially untracked; should stay LOCAL ONLY |
| SEC-08 | `__pycache__`, `.pytest_cache`, `.venv` | LOCAL ONLY | Mostly ignored |
| SEC-09 | Credentials vault module | SOURCE CONTROLLED | Encryption code OK; secrets in DB/env only |
| SEC-10 | Untracked deploy snapshots under `output/website-deploy/` | RUNTIME OUTPUT | Do not commit |

**Security Findings count (actionable hygiene):** **7** (SEC-01 context + SEC-03..08 gaps/artifacts; not confirmed leaked secrets in git history in this pass).

---

## `.gitignore` adequacy

| Pattern | Status |
|---------|--------|
| `.env` / `.env.*` | Present |
| `__pycache__`, `.venv`, `.pytest_cache` | Present |
| `*.db`, `htmlcov` | Present |
| `.crewai_home/`, `.crewai_storage/` | **MISSING** |
| `.wrangler/` | **MISSING** |
| `output/` | **MISSING** (selective ignore recommended) |
| `frontend/dist/` | **MISSING** (build output) |

---

## Classification

| Artifact type | Disposition |
|---------------|-------------|
| Source code / freeze docs | SOURCE CONTROLLED |
| `.env.example` | SOURCE CONTROLLED |
| Real env/tokens/keys | LOCAL ONLY |
| Website deploy packages / snapshots | RUNTIME OUTPUT / BACKUP — LOCAL |
| CrewAI home / wrangler cache | LOCAL ONLY |
| `frontend/dist` | BUILD OUTPUT — LOCAL |

**Never paste secrets into Cursor/chat.**
