# REV-ORCH M4.5 — Execution Authority Revalidation v1.0

Immediately before calendar side effect, `_execute_book_meeting` +
`revalidate_booking_execution` + `revalidate_provider_slot` re-check:

- Contact tenant ownership (`get_contact_for_tenant`)
- Suppression / stop tags
- Latest M3 meeting-interest assessment still valid
- Duplicate completed meeting
- Approval already executed (idempotency key)
- Selected slot timezone-aware and not in the past
- Tenant calendar connector still bound (`allow_global_fallback=False`)
- Provider busy overlap (Google) or fail-closed (Outlook)

T1 proposal authorization does not authorize T3 event creation.
