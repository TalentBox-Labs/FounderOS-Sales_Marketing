# UI-D1 Cross-Stream Dependencies

## M4 — Governed Meeting Booking

**CROSS_STREAM_DEPENDENCY: M4 booking contract required**

UI-D1 displays:

- Meeting interest detected
- Booking eligible
- "Booking workflow pending"

UI-D1 does **not** implement:

- Availability / slot selection
- Calendar booking
- Meeting creation
- Calendar integration setup

## No other cross-stream dependencies

All surfaced capabilities use frozen M1/M2/M3/M3.5 APIs on ui-d1 baseline.
