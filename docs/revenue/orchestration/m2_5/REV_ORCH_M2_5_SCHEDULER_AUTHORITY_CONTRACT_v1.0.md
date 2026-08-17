# REV-ORCH M2.5 — Scheduler Authority Contract v1.0

**STATUS: FROZEN**  
**SCHEDULER_AUTHORITY = INFRASTRUCTURE_ONLY**

## Allowed

- Scan contacts with persisted `organization_id` (`scan_eligible_follow_ups`)
- Reconstruct tenant from current `Contact.organization_id`
- Call `run_follow_up_proposal_scheduled` (eligibility → proposal → ApprovalRequest)
- Write `AgentActionLog` (`followup_proposal_scheduled`)

## Prohibited

- Approve follow-up
- Call n8n / `trigger_workflow`
- Call `decide()`
- Select tenant from client input
- Select connector credentials
- Mutate `Contact.status` or `Deal.stage`
- Bypass eligibility or reply-stop
- Inherit stale human authority

## Implementation

`HeartbeatScheduler.job_scan_follow_up_eligibility`  
Env: `HEARTBEAT_FOLLOWUP_SCAN_SEC` (default 3600)

Source inspection: job body contains `run_follow_up_proposal_scheduled` and does not contain `trigger_workflow` or `decide(`.
