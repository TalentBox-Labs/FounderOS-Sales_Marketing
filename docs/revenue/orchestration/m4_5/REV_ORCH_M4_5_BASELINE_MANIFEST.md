# REV-ORCH M4.5 — Baseline Manifest

## Freeze identity
- Sprint: REV-ORCH M4.5
- Version: v1.0
- Parent: `1e446ac`
- Branch: `rev-orch-m4`

## Canonical files
- `revenue_os/agents/orchestration.py` — M4 workflow registration
- `revenue_os/services/booking_eligibility.py` — deterministic eligibility + execution revalidation
- `revenue_os/services/calendar_executor.py` — tenant credentials, availability, provider slot revalidation, create
- `revenue_os/services/revenue_workers.py` — `run_booking_worker`
- `revenue_os/services/revenue_orchestration_service.py` — M4 orchestration
- `revenue_os/services/approvals.py` — `_execute_book_meeting`
- `runner_api_routers/revenue_orchestration.py` — eligibility/availability/propose routes
- `revenue_os/integrations/calendar.py` — Google `has_busy_overlap` (M4.5 containment)

## Freeze tests
`tests/test_rev_orch_m4_5_governed_meeting_booking_baseline_freeze.py`

## Explicit non-goals
Booking feature expansion, Outlook availability implementation, UI, new SoTs, new integrations.
