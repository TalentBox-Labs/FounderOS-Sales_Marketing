# REV-ORCH M3 — Reply Idempotency Contract

Key: `EmailActivity.message_id`

- Explicit `payload.message_id` or `provider_message_id`, else `rev-orch-m3:{sha256(contact_id:body)[:32]}`.
- Duplicate webhook: no second Activity, no second lead_score boost, no second `rev_orch_reply_assessment` log (cached by message_id).
- Reuses existing EmailActivity table — no new SoT.
