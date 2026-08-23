# REV-ORCH M4 — Execution-Time Revalidation

## Function: `revalidate_booking_execution()` + `_execute_book_meeting()`

At calendar side-effect time, revalidate:
- Contact tenant ownership
- Suppression/stop tags
- Booking eligibility state (no duplicate meeting)
- Selected slot not in past
- Idempotency key consistency

Principle: **T1 authorization ≠ T2 calendar execution authorization**
