# REV-ORCH M4.5 — Legacy Booking Reconciliation v1.0

| Path | Classification | Bypass |
|------|----------------|--------|
| `WorkflowOrchestrator` M4 workflow | CANONICAL | N/A |
| `run_booking_to_meeting` / `evaluate_booking_eligibility` | SUBORDINATE | Called only via orchestrator/API |
| `runner_api_routers/integrations.py` calendar event routes | LEGACY_CONTAINED | API-key admin configure/create; not eligibility-gated; not canonical M4 |
| n8n `meeting.booked` webhook | LEGACY_CONTAINED | Logs recommendation only; no Contact.status mutation |
| `go_to_market_orchestrator` booking_n8n | LEGACY_CONTAINED | Separate GTM path |

Legacy paths audited: 4
Unsafe reachable: 0
Unknown: 0
Canonical booking authority bypass: NOT_REACHABLE
