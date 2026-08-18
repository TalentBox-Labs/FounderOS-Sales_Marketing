# REV-ORCH M4 — Legacy Booking Reconciliation

| Path | Classification | Bypass Risk |
|------|---------------|-------------|
| M4 WorkflowOrchestrator → run_booking_to_meeting | CANONICAL_M4 | N/A |
| runner_api_routers/integrations.py calendar events | LEGACY_CONTAINED | Direct API, no M4 eligibility; admin/API-key gated |
| n8n meeting.booked webhook | LEGACY_CONTAINED | Logs only, no Contact.status mutation |
| go_to_market_orchestrator booking_n8n | LEGACY_CONTAINED | Separate GTM path, not rev-orch M4 |
| sales_agents appointment logic | LEGACY_CONTAINED / NONE | No direct calendar create found |

Legacy paths audited: 4
Unsafe reachable: 0
