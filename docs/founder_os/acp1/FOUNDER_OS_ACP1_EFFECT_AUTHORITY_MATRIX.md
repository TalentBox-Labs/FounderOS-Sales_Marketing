# Founder OS ACP-1 — Effect Authority Matrix

| Effect | Class | Autonomous? | Gate |
|--------|-------|-------------|------|
| QD accept/reject | HUMAN_REQUIRED | NO | COS-5 INLINE / Operator require_tenant |
| Approval approve/reject | HUMAN_REQUIRED | NO | `decide` + human identity |
| Deal stage / Contact status / CO | HUMAN_REQUIRED | NO (PROHIBITED_FOR_AGENT) | optional_tenant human HTTP only |
| Follow-up generation | PROPOSE | YES (org-scoped) | ApprovalRequest |
| Follow-up / outbound send | EXECUTE_GOVERNED | NO | Approval executor → n8n |
| Booking proposal | PROPOSE | YES via rev-orch HTTP | ApprovalRequest |
| Booking execution | EXECUTE_GOVERNED | NO | Approval executor |
| Lead score write | org-scoped mutate | YES if tenant resolved | Heartbeat/Hermes with org |
| Hermes create Deal | PROHIBITED | NO | Always blocked + provenance |
| Gmail inbound Activity | org-scoped | YES if tenant resolved | Match only in-org contacts |
| Metrics snapshot | org-scoped READ aggregate | YES if tenant resolved | Per-org dimension |

## Escalation closed

| Path | Result |
|------|--------|
| Hermes → create_deal_from_contact | Blocked (no call) |
| Heartbeat → global Contact score | Removed |
| EventBus SEND_EMAIL stub | Unchanged (not real send; not widened) |
| Celery send_email_task | Unwired; not enabled |
