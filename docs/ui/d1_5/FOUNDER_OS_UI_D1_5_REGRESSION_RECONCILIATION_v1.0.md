# UI-D1.5 Regression Reconciliation v1.0

**STATUS: FROZEN**  
**Environment:** `SECRET_KEY=test-secret-key-for-pytest-only-32chars DATABASE_URL=sqlite:///./pytest_*.db HEARTBEAT_ENABLED=0 RUNNER_API_KEY=`

## Historical envelope (M3.5 / UI-D1)

Documented in `docs/revenue/orchestration/m3_5/REV_ORCH_M3_5_REGRESSION_RECONCILIATION_v1.0.md` and UI-D1 full run:

**9 failed; 0 errors** (sqlite env)

| Classification | Count | Identities |
|----------------|-------|------------|
| HISTORICAL_UNCHANGED | 8 | crews_unit ×3 + utilities_unit ×5 |
| PRE_EXISTING_NOT_UI_D1 | 1 | `test_mdg1_manual_demand_registration::test_jinja_shell_not_react` |

UI-D1 full regression: **1042 passed / 1051**; 9 failed; 0 errors. Cockpit 12-failure cluster from M1.1 is **eliminated** by `data['items']`.

## UI-D1.5 full regression (this sprint)

**1073 collected; 1064 passed; 9 failed; 0 errors**

| Classification | Count | Identities |
|----------------|-------|------------|
| HISTORICAL_UNCHANGED | 8 | crews_unit ×3 + utilities_unit ×5 |
| PRE_EXISTING_NOT_UI_D1 | 1 | `test_mdg1_manual_demand_registration::test_jinja_shell_not_react` |

UI-D1.5 freeze tests: 22/22. New regressions attributable to freeze: **0**.

Cockpit 12-failure cluster from M1.1 remains **eliminated** by `data['items']`.

**Regression Envelope: FULLY_RECONCILED**
