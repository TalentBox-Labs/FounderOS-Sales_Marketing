# UI-D2 Booking Authority Attestation

## Preserved

- ApprovalRequest `book_meeting` executor unchanged
- TenantContext from session only
- Human identity from server on approve/reject
- BookingWorker proposal-only; no self-approve
- M4.5 provider slot revalidation at execution

## Browser prohibited

- `decided_by` in approval POST body
- `organization_id` as authority override in propose body
- Direct calendar create routes
- Client `booking_eligible=true` flags

## UX language

- "Suggested time", "Approval required", "Approve booking"
- "AI proposes · you approve"
