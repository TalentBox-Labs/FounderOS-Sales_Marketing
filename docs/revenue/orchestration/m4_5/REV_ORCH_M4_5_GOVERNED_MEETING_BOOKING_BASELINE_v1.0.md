# REV-ORCH M4.5 — Governed Meeting Booking Baseline v1.0

## Status: FROZEN

## Parent Baseline
- Commit: `1e446ac` (M3.5 freeze)
- Branch: `rev-orch-m4`

## Canonical Flow (frozen)

```
M3 BOOKING_ELIGIBLE (AgentActionLog rev_orch_reply_assessment)
→ evaluate_booking_eligibility() [deterministic]
→ get_tenant_availability() [tenant-scoped]
→ run_booking_worker() [SPECIALIZED_AI_WORKER, proposal only]
→ request_approval(action_type=book_meeting)
→ human approve via session TenantContext
→ revalidate_booking_execution()
→ revalidate_provider_slot() [provider busy overlap]
→ create_tenant_calendar_event()
→ Activity(MEETING) + MeetingActivity + AgentActionLog
```

## Canonical Authority
- Orchestrator: `WorkflowOrchestrator.execute_revenue_workflow(REV_ORCH_M4_WORKFLOW_KEY)`
- Workflow key: `rev_orch_booking_to_meeting`
- Eligibility cannot be payload-forged
- Credentials: `load_credentials(..., allow_global_fallback=False)`

## Freeze Tests
`tests/test_rev_orch_m4_5_governed_meeting_booking_baseline_freeze.py`
