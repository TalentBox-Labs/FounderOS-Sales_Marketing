# A3 — Test Plan (CIPHER)

**Sprint:** SALES A3  
**Date:** 2026-08-13

| # | Scenario | Expected |
|---|----------|----------|
| 1 | Authorized human + valid stage | 200; stage/probability updated |
| 2 | Invalid stage (malformed / non-sales) | 422 |
| 3 | Unauthenticated (API key set, no Bearer) | 401 |
| 4 | Wrong API key | 401 |
| 5 | Non-human requester (`agent`, `ai`, …) | 403 |
| 6 | Nonexistent Deal | 404 |
| 7 | Malformed Deal ID | 422 |
| 8 | Same-stage repeat | 200; `changed: false` |
| 9 | Transition to `closed_won` | 200; `closed_at` set; no CommercialOutcome |
| 10 | Reopen from closed_won → discovery | 422 |
| 11 | Audit EventBus / response includes requested_by | Present |
| 12 | Existing prospecting/CRM create still works | Preserve |

File: `tests/test_a3_runner_deal_stage.py`
