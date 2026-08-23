# Founder OS ACP-2 — Idempotency & Retry Attestation

## Idempotency

Key: `acp2:{work_kind}:{org}:{target}:{logical_key}` (deterministic).

Prior `acp2_work_succeeded` with same key → SUCCEEDED `{deduplicated: true}` without re-running executor.

## Retry

| Failure class | Behavior |
|---------------|----------|
| Transient | RETRYABLE until `max_attempts` → EXHAUSTED |
| HUMAN_REQUIRED | No retry into execution |
| PROHIBITED | No retry into execution |
| Tenant/authority | BLOCKED (no mutate) |

Default `max_attempts = 3`.
