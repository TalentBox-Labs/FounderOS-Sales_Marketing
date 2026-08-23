# REV-ORCH M4.5 — Booking Idempotency Attestation v1.0

## Layers
1. Pending `ApprovalRequest` collapse: same `(action_type=book_meeting, target_id)`
2. Idempotency key: `rev-orch-m4:book:{contact_id}:{source_activity_id}`
3. Execution: completed MEETING Activity whose body contains the key → return deduplicated
4. Approval state: second approve on non-pending → 409

## Guarantee
One approved booking intent → at most one provider event + one MEETING Activity.
