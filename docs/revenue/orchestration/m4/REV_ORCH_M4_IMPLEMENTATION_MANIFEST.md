# REV-ORCH M4 — Implementation Manifest

## Parent: `1e446ac` (M3.5 freeze)

## New Files
- `revenue_os/services/booking_eligibility.py`
- `revenue_os/services/calendar_executor.py`
- `tests/test_rev_orch_m4_governed_meeting_booking.py`
- `docs/revenue/orchestration/m4/*`

## Modified Files
- `revenue_os/services/revenue_workers.py` — WORKER_BOOKING, run_booking_worker
- `revenue_os/services/revenue_orchestration_service.py` — M4 orchestration functions
- `revenue_os/services/approvals.py` — _execute_book_meeting executor
- `revenue_os/agents/orchestration.py` — M4 workflow registration
- `runner_api_routers/revenue_orchestration.py` — M4 API routes

## Reused (No New SoT)
- Activity + MeetingActivity (meeting record)
- ApprovalRequest (human gate)
- AgentActionLog (audit)
- credentials_vault (tenant calendar credentials)
- GoogleCalendarClient / OutlookCalendarClient (connectors)

## Tests: 17/17 M4 focused; 122/122 rev-orch frozen suites
