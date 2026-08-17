# REV-ORCH M3 — Booking Negative Scope

M3 MUST NOT:

- query calendars
- book meetings
- send invites
- select availability
- mutate Deal.stage from meeting interest

M3 MAY set `routing.booking_eligible = true` and `recommended_next_action = BOOKING_ELIGIBLE`.

Booking is M4.
