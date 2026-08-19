# UI-D2 Booking Surface Contract

## UI states (presentation only)

| `ui_state` | Meaning |
|------------|---------|
| `NOT_ELIGIBLE` | Server reports no booking eligibility |
| `BOOKING_ELIGIBLE` | Eligible + Google connector; availability actionable |
| `APPROVAL_PENDING` | Pending `book_meeting` ApprovalRequest |
| `BOOKED` | Completed meeting Activity exists |
| `CONNECTOR_UNAVAILABLE` | Outlook-only tenant; fail-closed |
| `NO_CONNECTOR` | No tenant calendar credentials |
| `ERROR` | Orchestration/read error |

Source: `founder_ui_read_model._build_booking_panel()` composing M4 `inspect_booking_eligibility` + `resolve_calendar_connector`.

## Contact workspace panel

- View availability → `GET /api/v1/revenue/contacts/{id}/booking/availability`
- Select slot (client state only; not authority)
- Submit for approval → `POST /api/v1/revenue/contacts/{id}/booking/propose` with `{ selected_slot: { start, end } }`
- Never calls calendar create directly
