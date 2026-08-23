# Founder OS UI-D2 — Live Governed Booking v1.0

**STATUS:** IMPLEMENTED
**Parent baseline:** `1d0f86c` (INT-D2 certified)
**Branch:** `ui-d2`

## Mission

Connect frozen M4/M4.5 governed meeting booking to the frozen UI-D1 Founder OS browser product without new SoTs, models, migrations, or booking authority changes.

## End-to-end flow

Meeting interest → booking eligible → view tenant-safe availability → select slot → review proposal → `ApprovalRequest(action_type=book_meeting)` → human approve/reject → M4 `CalendarExecutor` → meeting confirmation → Activity / provenance.

## Surfaces

| Surface | Role |
|---------|------|
| Contact Revenue Workspace booking panel | Primary booking UX |
| Approval Inbox | Enhanced `book_meeting` rendering |
| Command Center | Meeting approvals pending list |
| Activity / Provenance | Existing AgentActionLog labels |

## Authority

- Server `inspect_booking_eligibility` gates all booking actions
- Browser never sends `organization_id`, `requested_by`, or `decided_by` as authority
- AI proposes via M4 BookingWorker; human approves via existing ApprovalRequest executor
- Google Calendar first demo provider; Outlook availability fail-closed

## Tests

`tests/test_ui_d2_live_governed_booking.py` — 22 focused integration tests
