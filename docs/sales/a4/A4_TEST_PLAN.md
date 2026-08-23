# A4 — Test Plan (CIPHER)

**Sprint:** SALES A4  
**Date:** 2026-08-13

## Required cases → test mapping

| # | Case | Test |
|---|------|------|
| 1 | Score generated | `test_score_contact_does_not_mutate_status`, `test_runner_score_without_mutation` |
| 2 | Score without mutation | `test_high_score_does_not_auto_qualify_via_score_endpoint` |
| 3 | Human valid status change | `test_runner_status_valid_human_change` |
| 4 | Unauthenticated rejected | `test_runner_status_unauthenticated_when_key_set` |
| 5 | Unauthorized human | Covered by agent/AI rejection tests |
| 6 | AI requester rejected | `test_runner_status_rejects_ai_prefix` |
| 7 | Agent requester rejected | `test_runner_status_rejects_agent_requester` |
| 8 | Nonexistent contact | `test_runner_status_not_found` |
| 9 | Malformed contact ID | `test_runner_status_malformed_contact_id` |
| 10 | Invalid status | `test_runner_status_invalid_status` |
| 11 | Same-status noop | `test_runner_status_same_status` |
| 12 | Audit evidence | EventBus assertions in human change + score tests |
| 13 | Marketing not mutated | No Marketing imports in A4 code path |
| 14 | Revenue deal state not mutated | Status-only on Contact |
| 15 | No external integrations | No enrichment/API calls in A4 endpoints |
| 16 | Frozen contracts unchanged | Architecture audit Phase 5 |

Implementation: `tests/test_a4_runner_contact_status.py`
