# R1F — Security Hygiene Re-Audit (CIPHER)

**Sprint:** R1F  
**Date:** 2026-08-13  
**Mode:** MEASUREMENT ONLY — values not disclosed

---

## Controls Verified

| Control | Evidence | Status |
|---------|----------|--------|
| `.env` / `.env.*` ignored | `.gitignore` lines; `.env.local` ignored | PASS |
| `.env.example` allowed | `!.env.example`; placeholders only | PASS |
| CrewAI / Wrangler locals ignored | `.crewai_home/`, `.crewai_storage/`, `.wrangler/` | PASS |
| `frontend/dist`, website output ignored | patterns present | PASS |
| `*.log`, staging runtime ignored | R1B patterns | PASS |
| Compose `SECRET_KEY` | `${SECRET_KEY:?…}` required — no `change-me` default | PASS |
| Tracked secret files | `git ls-files` — no `.env`; `credentials_vault.py` is **code**, not a secret store dump | PASS |
| Public deployment exclusions | R1B attestation stands (no re-deploy this sprint) | PASS |

---

## Findings Remaining

| ID | Item | Severity | Class |
|----|------|----------|-------|
| NEW-02 | `docker-compose.demo.yml` demo passwords | LOW | **DEFERRED** intentional demo |

**Confirmed active secrets in VCS: 0**  
**Critical: 0 · High: 0**

**Security Findings Remaining (actionable unresolved): 1** (demo-compose LOW deferred only)

If counted strictly as “blocking security findings”: **0**.

---

## Score

| | R0 | Current | Δ |
|--|---:|--------:|--:|
| Security Hygiene | 68 | **90** | **+22** |

Rationale: R0’s seven actionable hygiene gaps closed via ignore + compose/env template hardening; only intentional demo-compose LOW remains.

**Security-blocking issues: 0**
