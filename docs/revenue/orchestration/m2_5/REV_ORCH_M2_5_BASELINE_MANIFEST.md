# REV-ORCH M2.5 — Baseline Manifest

**STATUS: FROZEN**  
**Parent commit:** `b0004a4`  
**M2_5_PARENT_HEAD:** `b0004a4`  
**Branch:** `rev-orch-m2`  
**Baseline version:** v1.0

## Canonical M2 files

| File | Role |
|------|------|
| `runner_api_routers/revenue_orchestration.py` | Canonical API (propose + eligibility) |
| `revenue_os/agents/orchestration.py` | WorkflowOrchestrator M2 registration |
| `revenue_os/services/follow_up_eligibility.py` | Deterministic eligibility / cadence / stop / reply |
| `revenue_os/services/revenue_workers.py` | `run_followup_worker` |
| `revenue_os/services/revenue_orchestration_service.py` | Subordinate proposal implementation |
| `revenue_os/services/approvals.py` | ApprovalRequest + send-time revalidation + n8n executor |
| `revenue_os/services/activity_log.py` | AgentActionLog |
| `revenue_os/scheduler.py` | `job_scan_follow_up_eligibility` |
| `runner_api_routers/n8n_webhooks.py` | `email.replied` → EMAIL_REPLY Activity |
| `runner_api_routers/approvals.py` | Human approve/reject |

## Freeze pointers

| Concern | Implementation |
|---------|----------------|
| Scheduler | `HeartbeatScheduler.job_scan_follow_up_eligibility` |
| Eligibility | `evaluate_follow_up_eligibility` |
| FollowUpWorker | `revenue_workers.run_followup_worker` |
| Reply signal | inbound Activity EMAIL / EMAIL_REPLY / LINKEDIN_MESSAGE; n8n `email.replied` |
| Approval | existing ApprovalRequest `send_outreach_email` |
| Outbound | `_execute_send_outreach_email` → `n8n.trigger_workflow("send-email")` |
| Audit | AgentActionLog + outbound Activity |

## Freeze tests

`tests/test_rev_orch_m2_5_governed_followup_baseline_freeze.py`

## Legacy follow-up

`sales_agents.build_followup_sequence` = LEGACY_CONTAINED (no send; tenant-scoped). Canonical engine remains M2.

## Known historical failures

8 crews/utilities + 12 cockpit.html:53. New regressions expected: 0.

## Change budget (M2.5)

Feature code: 0. Runtime: 0. Migrations: 0. New SoTs: 0. Credentials: 0. Frozen M1.5/M2 contract changes: 0.

Allowed: freeze tests + freeze docs only.

## Explicit non-goals

M3 booking, objection automation, cadence expansion, autonomous agents, new follow-up SoT, second scheduler, second approval store, n8n-as-orchestrator, UI redesign.
