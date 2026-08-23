# MC04 — Test Plan (CIPHER)

**Sprint:** FOUNDER OS MC04  
**Date:** 2026-08-13

| # | Case | Test |
|---|------|------|
| 1 | Valid accept | `test_runner_handoff_and_accept_flow` |
| 2 | Canonical Contact | `test_accept_creates_canonical_contact` |
| 3 | Duplicate handoff | `test_handoff_idempotent` |
| 4 | Idempotent accept | `test_accept_idempotent` |
| 5 | Invalid payload | `test_runner_rejects_invalid_payload` |
| 6 | Missing handoff | `test_accept_without_handoff_rejected` |
| 7 | Malformed demand_id | invalid payload test |
| 8 | Unauthorized agent handoff | `test_runner_rejects_agent_handoff` |
| 9 | Agent intake blocked | `test_runner_rejects_agent_intake` |
| 10 | Marketing unchanged | handoff creates no Contact |
| 11 | No pre-accept mutation | accept requires handoff |
| 12 | No auto status | status `lead` on create |
| 13 | No Deal | `deal_created: false` |
| 14 | Revenue untouched | no deal/commercial outcome |
| 15 | Provenance | notes contain demand_id |
| 16 | Accept audit | ACTION_ACCEPTED log |
| 17 | Reject audit | `test_reject_creates_audit` |
| 18 | Retry safe | idempotent tests |
| 19–20 | A4/A3 frozen | separate regression suites |

Suite: `tests/test_mc04_qualified_demand.py` — **12/12**
