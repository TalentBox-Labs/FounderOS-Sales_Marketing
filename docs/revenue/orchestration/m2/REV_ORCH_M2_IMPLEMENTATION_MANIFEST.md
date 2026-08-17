# REV-ORCH M2 — Implementation Manifest

**Parent baseline:** `b0004a4`

## New files

| File | Purpose |
|------|---------|
| `revenue_os/services/follow_up_eligibility.py` | Deterministic eligibility |
| `tests/test_rev_orch_m2_governed_followup.py` | M2 security + lifecycle tests |
| `docs/revenue/orchestration/m2/*` | M2 documentation (8 artifacts) |

## Modified files

| File | Change |
|------|--------|
| `revenue_os/services/revenue_workers.py` | `FollowUpWorker` |
| `revenue_os/services/revenue_orchestration_service.py` | M2 workflow implementation |
| `revenue_os/services/ai_service.py` | `generate_follow_up_email` |
| `revenue_os/services/approvals.py` | Stale revalidation + follow-up Activity subject |
| `revenue_os/agents/orchestration.py` | M2 workflow registration; dynamic step result |
| `runner_api_routers/revenue_orchestration.py` | Eligibility + propose routes |
| `runner_api_routers/n8n_webhooks.py` | Record inbound EMAIL_REPLY Activity |
| `revenue_os/scheduler.py` | `job_scan_follow_up_eligibility` |

## Change budget

| Item | Count |
|------|-------|
| New persistent SoTs | 0 |
| New database models | 0 |
| Migrations | 0 |
| New external integrations | 0 |
| Credentials added | 0 |
| Frozen M1.5 contract changes | 0 |

## Reused (not duplicated)

- `followups.py` — dashboard aggregation (unchanged)
- `ApprovalRequest` — human gate SoT
- `Activity` — outbound/inbound timeline
- `AgentActionLog` — audit trail
- M1 outbound executor path via n8n
