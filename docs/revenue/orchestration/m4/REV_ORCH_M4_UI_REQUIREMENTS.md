# REV-ORCH M4 — UI Requirements (for UI-D1)

## CROSS_STREAM_DEPENDENCY: UI implementation belongs to UI-D1

M4 exposes minimum API contract only. UI-D1 should implement:

### Screens / Actions
1. **Booking eligibility badge** on contact detail when M3 assessment is BOOKING_ELIGIBLE
2. **Availability picker** calling `GET .../booking/availability`
3. **Slot selection** with timezone display (UTC baseline)
4. **Propose booking** → `POST .../booking/propose` with optional `selected_slot`
5. **Approval queue item** for `book_meeting` action type (reuse existing approvals UI)
6. **Meeting confirmation** showing Activity(MEETING) after approval

### Must NOT
- Bypass ApprovalRequest human gate
- Call calendar executor directly
- Pass organization_id as authority override
