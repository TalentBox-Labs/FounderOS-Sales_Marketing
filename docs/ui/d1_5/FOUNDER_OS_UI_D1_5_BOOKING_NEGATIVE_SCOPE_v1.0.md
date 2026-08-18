# UI-D1.5 Booking Negative Scope v1.0

**STATUS: FROZEN**  
**CROSS_STREAM_DEPENDENCY: M4 booking contract required**

UI-D1.5 predates M4 integration. Do not assume M4/M4.5 exists in this worktree.

## Visible (allowed)

| Signal | Source | UI |
|--------|--------|----|
| Meeting interest | M3/M3.5 reply routing `meeting_interest` | Badge |
| Booking eligible | M3/M3.5 `booking_eligible` / `BOOKING_ELIGIBLE` | Badge + “booking workflow pending” |

## NOT_IMPLEMENTED in UI-D1

- Availability
- Slot selection
- Calendar booking
- Meeting creation
- Calendar integration setup
- `book_meeting` ApprovalRequest executor UI

No fake availability calendars. No “Book a meeting” primary action.

## Future M4 integration points (document only)

1. Eligibility (already displayed)
2. Availability
3. Slot selection
4. Proposal
5. ApprovalRequest `book_meeting`
6. Confirmation

Do not implement these in UI-D1.5.
