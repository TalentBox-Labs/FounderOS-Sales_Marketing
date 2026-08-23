# REV-ORCH M2.5 — Regression Reconciliation v1.0

**STATUS: FROZEN**  
**Environment:** `SECRET_KEY=test-secret-key-for-pytest-only-32chars DATABASE_URL=sqlite:///./pytest_*.db HEARTBEAT_ENABLED=0 RUNNER_API_KEY=`

## Historical envelope (from M1.5 / M2)

**20 failed; 0 errors**

| Category | Count | Identities |
|----------|-------|------------|
| HISTORICAL_MATCH | 8 | `test_crews_unit.py` ×3 + `test_utilities_unit.py` ×5 |
| PRE_EXISTING_NOT_PREVIOUSLY_RUN | 12 | cockpit `templates/cockpit.html:53` TypeError (`org_membership`) |
| FIXED (env) | 4 | prior orchestration/prospecting errors — pass with sqlite DATABASE_URL |

M2.5 adds freeze tests + docs only.

**Full regression (M2.5):** 975/995 passed; 20 failed; 0 errors  
(M2 was 939/959; +36 freeze tests)

New regressions: 0. Failure identities unchanged.

## Suites

- M2.5 freeze: 36/36
- M2 focused: 21/21
- M1.5 freeze: 22/22 unchanged
- M1.1: 5/5; M1: 10/10
