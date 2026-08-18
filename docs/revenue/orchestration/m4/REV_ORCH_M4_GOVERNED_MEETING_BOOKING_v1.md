# REV-ORCH M4 — Governed Meeting Booking v1

## Status: OPERABLE

## Parent Baseline
- Commit: `1e446ac` (M3.5 freeze)
- Branch: `rev-orch-m4`

## Canonical Flow

```
M3 BOOKING_ELIGIBLE (AgentActionLog routing)
→ evaluate_booking_eligibility() [deterministic]
→ get_tenant_availability() [tenant-scoped calendar read]
→ run_booking_worker() [SPECIALIZED_AI_WORKER, proposal only]
→ request_approval(action_type=book_meeting)
→ human approve/reject
→ _execute_book_meeting() [deterministic calendar executor]
→ Activity(MEETING) + MeetingActivity + AgentActionLog
```

## Entry Points
- `GET /api/v1/revenue/contacts/{id}/booking/eligibility`
- `GET /api/v1/revenue/contacts/{id}/booking/availability`
- `POST /api/v1/revenue/contacts/{id}/booking/propose`
- `WorkflowOrchestrator.execute_revenue_workflow(REV_ORCH_M4_WORKFLOW_KEY)`

## Non-Goals (Preserved)
- No autonomous booking agent
- No Contact.status mutation from booking
- No Deal.stage mutation from booking
- No new persistent SoT
- No UI implementation (see REV_ORCH_M4_UI_REQUIREMENTS.md)
