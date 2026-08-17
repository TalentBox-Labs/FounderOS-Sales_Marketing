# A3 — Adversarial Validation

**Sprint:** SALES A3  
**Date:** 2026-08-13  
**Evidence:** `tests/test_a3_runner_deal_stage.py` (15 passed)

| Attack / probe | Result | Evidence |
|----------------|--------|----------|
| Agent requester (`agent`) | **BLOCKED** 403 | `test_runner_stage_rejects_agent_requester` |
| AI-prefixed requester (`ai:copilot`) | **BLOCKED** 403 | `test_runner_stage_rejects_ai_prefix` |
| Missing auth with API key set | **BLOCKED** 401 | `test_runner_stage_unauthenticated_when_key_set` |
| Malformed / wrong Bearer | **BLOCKED** 401 | `test_runner_stage_wrong_api_key` |
| Invalid stage name | **BLOCKED** 422 | `test_runner_stage_malformed_stage` |
| Recruitment stage via enum | **BLOCKED** ValueError / not accepted as sales | `test_apply_deal_stage_update_rejects_recruitment_stage` |
| Repeated same-stage | **SAFE** 200 `changed:false` | `test_runner_stage_same_stage` |
| closed_won | **OK** fields only; `commercial_outcome_emitted:false` | `test_runner_stage_closed_won_no_commercial_outcome` |
| Reopen closed deal | **BLOCKED** 422 | `test_runner_stage_rejects_reopen_via_api` |
| Nonexistent Deal | **BLOCKED** 404 | `test_runner_stage_not_found` |
| Malformed Deal ID | **BLOCKED** 422 | `test_runner_stage_malformed_deal_id` |
| Direct runner API (no UI) | **Expected path** — API-first; human + key still required | design |
| Audit without EventBus | Event publish attempted; failure logged, response still returns | create pattern parity |
| Missing `requested_by` | **BLOCKED** 422 Pydantic | Field required |

**Agent Mutation Blocked: PASS**  
**Closed-Won Boundary: PASS** (no CommercialOutcome)
