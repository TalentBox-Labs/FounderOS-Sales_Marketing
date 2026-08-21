# Founder OS ACP-3 — Effect Recovery & Idempotency Attestation

## ACP-1 effect modes preserved

| Mode | Recovery |
|------|----------|
| AUTONOMOUS (governed) | May retry if RETRYABLE + gates + fresh authority |
| HUMAN_REQUIRED | Remains waiting; approval evidence required; resume does **not** auto-send |
| PROHIBITED | Remains blocked; never retryable into execution |

## External effects (no blind replay)

Kinds treated as ambiguous when RUNNING without success provenance:

- `outbound_send` / `follow_up_send`
- `booking_execute`

Unless an existing idempotency contract **proves** completion, classify
`AMBIGUOUS_EFFECT` for human review.

## Replay-safe examples

- **Lead score:** domain `Contact.lead_score > 0` (same org) proves completion.
- **Follow-up propose:** presence of related ApprovalRequest may prove proposal filed.
- **Duplicate orchestrate tick:** `_already_succeeded(idempotency_key)` short-circuits.

## Claimed guarantee

at-least-once discovery + idempotent effect execution — **not** distributed exactly-once.
