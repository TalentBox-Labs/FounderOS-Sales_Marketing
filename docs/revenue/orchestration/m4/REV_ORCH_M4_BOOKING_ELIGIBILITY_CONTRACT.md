# REV-ORCH M4 — Booking Eligibility Contract

## Source: `revenue_os/services/booking_eligibility.py`

## Required Conditions (all must pass)
1. Contact belongs to resolved tenant organization
2. Contact has no stop/unsubscribe tags
3. Latest M3 `rev_orch_reply_assessment` AgentActionLog exists
4. Assessment routing indicates `booking_eligible` or `BOOKING_ELIGIBLE` or `MEETING_INTEREST`
5. No pending `book_meeting` ApprovalRequest for contact
6. No completed MEETING Activity for contact

## Prohibited Eligibility Sources
- Client payload self-declaration of BOOKING_ELIGIBLE
- AI worker output alone (must be persisted M3 assessment)
- contact_id without tenant scope
