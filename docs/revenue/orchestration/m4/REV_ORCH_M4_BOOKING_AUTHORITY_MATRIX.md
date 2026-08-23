# REV-ORCH M4 — Booking Authority Matrix

| Action | BookingWorker | BookingEligibilityPolicy | Human | CalendarExecutor |
|--------|--------------|------------------------|-------|------------------|
| Determine booking eligibility | PROHIBITED | ALLOWED | — | — |
| Read calendar availability | PROHIBITED | — | — | ALLOWED (tenant-scoped) |
| Propose candidate slots | ALLOWED | — | — | — |
| Select final slot | PROHIBITED | — | ALLOWED | — |
| Approve booking | PROHIBITED | PROHIBITED | ALLOWED | — |
| Create calendar event | PROHIBITED | PROHIBITED | Via approval | ALLOWED |
| Mutate Contact.status | PROHIBITED | PROHIBITED | ALLOWED (A4) | PROHIBITED |
| Mutate Deal.stage | PROHIBITED | PROHIBITED | ALLOWED (A3) | PROHIBITED |
| Select credentials | PROHIBITED | PROHIBITED | — | PROHIBITED (server-resolved) |
