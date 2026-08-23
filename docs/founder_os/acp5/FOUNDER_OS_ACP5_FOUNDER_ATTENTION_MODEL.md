# Founder OS ACP-5 — Founder Attention Model

**Baseline:** `founder-os-acp4-v1.0` @ `954af7b34590a45991dd098afb21235dfef71fd2`

## Principle

Attention is **deterministic** and org-scoped. No new opaque AI priority score.

Reuse COS-3/5 bands where present:

- `requires_founder`
- `ready`
- `completed`
- `informational`

Plus ACP orchestration buckets from `compose_orchestration_summary`.

## Reason codes (v1)

Prefer stable machine codes aligned to existing escalation/failure reasons:

| Code | Meaning | Primary source |
|------|---------|----------------|
| `approval_required` | Pending ApprovalRequest needs decide | decision_items kind=approval |
| `follow_up_ready` | Follow-up signal / NAVIGATE or pending propose | follow_up_signals / approvals |
| `booking_review_ready` | Booking ApprovalRequest pending | pending approval book_meeting |
| `awaiting_human` | ACP-2 WAITING_HUMAN work | agent_orchestration.awaiting_human |
| `execution_failed` | Failed / executor error | agent_orchestration.failed |
| `retryable` | ACP-3 retryable | reconcile / orchestration |
| `retry_exhausted` | Exhausted | agent_orchestration.exhausted |
| `ambiguous_effect` | Ambiguous external | agent_orchestration.ambiguous_effect |
| `authority_blocked` | Fence/blocked/prohibited | blocked / fence_rejected |
| `tenant_blocked` | Missing/inactive/not allowlisted | fence / empty compose |
| `claim_suppressed` | Duplicate worker claim unavailable | claim_rejected |
| `agent_succeeded` | Recent autonomous success | succeeded_recently |
| `pause_active` / `kill_active` | Runtime gates | orchestration.pause / kill |

Do not invent revenue/confidence scores.

## Command questions (must be answerable)

| Question | V1 answer surface |
|----------|-------------------|
| What are the agents doing? | `agent_orchestration` buckets + counts + pause/kill |
| What requires me? | `decision_items` with `requires_founder` (approvals, QD) |
| What happened? | succeeded_recently + completed decision items + approval execution_result |
| What happens next? | remaining requires_founder / ready / retryable / ambiguous |

## Before vs after follow-up decide

| Phase | Attention |
|-------|-----------|
| After propose | `approval_required` + `awaiting_human` |
| After reject | approval leaves pending; informational/completed note |
| After approve success | `agent_succeeded` / completed activity; approval gone from pending |
| After approve fail | `execution_failed` / retryable |
| Ambiguous | `ambiguous_effect` — founder review, no auto-replay |

## Non-goals

- Generic observability dashboard
- Parallel attention SoT
- Replacing COS decision_items
