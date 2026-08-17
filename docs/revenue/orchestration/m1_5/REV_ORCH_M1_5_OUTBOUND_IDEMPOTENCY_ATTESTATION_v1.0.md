# REV-ORCH M1.5 — Outbound / Idempotency Attestation v1.0

**STATUS: FROZEN**

## Outbound Path

1. M1 workflow files `ApprovalRequest` (status=pending)
2. Human approve via session tenant
3. `decide()` → `_execute_send_outreach_email`
4. `_validate_outbound_payload` (tenant + contact)
5. `n8n.trigger_workflow("send-email", payload)` — **executor only**
6. Outbound `Activity` on success

## Gates

| State | n8n invoked |
|-------|-------------|
| pending | NO |
| rejected | NO |
| approved (first) | YES (once) |
| approved (replay) | NO (409) |

## Idempotency

- Payload `idempotency_key`: `rev-orch-m1:{workflow_run_id}:send`
- `execution_result.executed` + `handed_to_n8n` skips re-execute

## n8n Authority

n8n is **EXECUTOR_ONLY** — not orchestrator, not tenant authority, not approval authority.
