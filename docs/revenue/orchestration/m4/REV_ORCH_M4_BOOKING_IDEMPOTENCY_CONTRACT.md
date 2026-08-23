# REV-ORCH M4 — Booking Idempotency Contract

## Layers
1. **ApprovalRequest dedup**: pending `book_meeting` + same target_id collapsed
2. **Idempotency key**: `rev-orch-m4:book:{contact_id}:{source_activity_id}`
3. **Execution dedup**: `_execute_book_meeting` checks Activity.body for existing idempotency_key
4. **Approval state**: second approve on non-pending returns 409

## Guarantee
One approved booking intent → at most one calendar event + one MEETING Activity.
