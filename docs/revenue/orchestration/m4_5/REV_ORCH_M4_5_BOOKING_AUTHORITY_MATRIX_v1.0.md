# REV-ORCH M4.5 — Booking Authority Matrix v1.0

| Action | BookingWorker | Eligibility Policy | Human | CalendarExecutor |
|--------|--------------|-------------------|-------|------------------|
| Establish booking eligibility | PROHIBITED | ALLOWED | — | — |
| Read availability | PROHIBITED | — | — | ALLOWED (tenant-scoped) |
| Propose slots / title | ALLOWED | — | — | — |
| Select final slot | PROHIBITED | — | ALLOWED | — |
| Approve booking | PROHIBITED | PROHIBITED | ALLOWED | — |
| Revalidate provider slot | PROHIBITED | — | — | REQUIRED |
| Create calendar event | PROHIBITED | PROHIBITED | Via approval | ALLOWED |
| Mutate Contact.status | PROHIBITED | PROHIBITED | A4 only | PROHIBITED |
| Mutate Deal.stage | PROHIBITED | PROHIBITED | A3 only | PROHIBITED |
| Select credentials | PROHIBITED | PROHIBITED | — | Server-resolved |

AI Authority: PROPOSAL_ONLY
Human Booking Authority: REQUIRED (`ApprovalRequest.action_type=book_meeting`)
