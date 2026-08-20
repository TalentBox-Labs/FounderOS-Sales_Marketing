# Founder OS COS-2 Authority Attestation

COS-2 did not change ApprovalRequest executors, WorkflowOrchestrator, calendar create, or outbound send.

| Control | Status |
|---------|--------|
| Marketing handoff | Still `register_marketing_handoff` + human `requested_by` |
| Sales intake | Still Operator `accept_qualified_demand` / `reject_qualified_demand` |
| Client `requested_by` on Operator | Unchanged — trusted operator |
| `JSON.stringify({})` on founder approvals | Preserved |
| Advisory next action on person workspace | Unchanged |
| Contact.status from marketing slice | Not written (handoff-only; accept creates LEAD via MC04 only) |
| Deal.stage from marketing slice | Not written |
| Booking propose/approve/execute | Unchanged (UI-D2 / M4) |
| Outreach send | Unchanged |
| Qualification vs decision | UI labels system recommended separately from needs your decision |

Handoff is **not** labeled as AI work. Activity marks QD handoff as system recommended and accept/reject as human decided.
