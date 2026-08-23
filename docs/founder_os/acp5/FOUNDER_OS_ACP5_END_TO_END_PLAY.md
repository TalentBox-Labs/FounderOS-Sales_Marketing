# Founder OS ACP-5 — End-to-End Play (Follow-Up)

**Baseline:** `founder-os-acp4-v1.0` @ `954af7b34590a45991dd098afb21235dfef71fd2`
**Primary play:** Follow-up propose → founder/approval review → decide → governed send → provenance → Command refresh

## Sequence

| Step | Actor | Component | Mode | Mutates external effect? |
|------|-------|-----------|------|--------------------------|
| 1 Discover eligible | heartbeat / ACP-5 loop | `scan_eligible_follow_ups` | READ | No |
| 2 Claim + propose | heartbeat | `orchestrate_claimed(WORK_FOLLOW_UP_PROPOSE)` | AUTONOMOUS | No (draft + ApprovalRequest only) |
| 3 Compose draft | followup worker | `run_follow_up_proposal_scheduled` | AUTONOMOUS propose | No |
| 4 File approval | approvals | `request_approval(send_outreach_email)` | Creates pending ApprovalRequest | No |
| 5 Surface attention | Command | `compose_commercial_decision_items` + `agent_orchestration` | INLINE/INFO | No |
| 6 Human decide | founder | `POST …/approvals/{id}/approve\|reject` → `decide` | INLINE_GOVERNED / HUMAN_REQUIRED | Only on approve |
| 7 Execute send | approval executor | `_execute_send_outreach_email` | EXECUTE_GOVERNED | Yes (n8n handoff) |
| 8 Provenance | ACP-2/3 | AgentActionLog + approval.execution_result | — | — |
| 9 Refresh | Command | rebuild snapshot | — | No |

## Work identity

- Kind: `follow_up_propose` then send via approval action `send_outreach_email`
- Idempotency: eligibility `idempotency_key` in approval payload (existing M2 key)
- Logical key on propose: cadence step (scheduler already uses `logical_key=str(cadence_step)`)

## Success / failure / recovery

| Case | Behavior |
|------|----------|
| Proposal filed, not decided | WAITING_HUMAN / pending ApprovalRequest; Command `requires_founder` |
| Rejected | No executor; approval rejected provenance |
| Approved, executor fails | `execution_result.executed=False`; retryable/exhausted via ACP-3 classes if applicable |
| Approved, executor succeeds | executed + activity/provenance; leave pending queue |
| Ambiguous external | ACP-3 AMBIGUOUS; no blind replay |
| Tenant deactivated while waiting | Fail closed on decide/fence |
| Authority/kill/pause while waiting | Fail closed; no send |
| Concurrent approve | ACP-4 ≤1 executor invocation |

## Booking secondary play (if included)

Same shape with `_run_booking_proposal` → `request_approval(action_type="book_meeting")` → HUMAN_REQUIRED execute via existing booking executor. **No silent calendar write.**

## Research-to-outreach

**DEFER from v1.** Requires ad-hoc research/draft path; not required to close the primary follow-up operating loop.
