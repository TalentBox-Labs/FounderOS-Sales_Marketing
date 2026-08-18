# REV-ORCH M3.5 — Reply Authority Matrix v1.0

## Status: FROZEN

| Action | ReplyAnalysisWorker | Deterministic Routing | Human Operator |
|--------|--------------------|-----------------------|----------------|
| Classify reply intent | ALLOWED | — | — |
| Recommend qualification | ALLOWED | ALLOWED | — |
| Mutate Contact.status | PROHIBITED | PROHIBITED | ALLOWED |
| Mutate Deal.stage | PROHIBITED | PROHIBITED | ALLOWED |
| Accept QualifiedDemand | PROHIBITED | PROHIBITED | ALLOWED |
| Apply OPT_OUT tag | PROHIBITED | ALLOWED (policy-bound) | ALLOWED |
| Send outbound | PROHIBITED | PROHIBITED | Via ApprovalRequest |
| Book meeting | PROHIBITED | PROHIBITED | Future M4 |
| Select tenant | PROHIBITED | PROHIBITED | N/A |
| Select credentials | PROHIBITED | PROHIBITED | N/A |

## OPT_OUT Mutation Boundary

The `apply_opt_out_tag` action is executed by deterministic routing policy code
(`run_inbound_reply_handling` in `revenue_orchestration_service.py`), NOT by the AI worker.

- Only field mutated: `Contact.tags` (adds "unsubscribed" token)
- AI cannot supply arbitrary tag values
- Mutation is idempotent (`merge_opt_out_tag`)
- Mutation is tenant-scoped (contact already validated via `get_contact_for_tenant`)
- No other Contact fields are modified

## Routing Output Guarantees (all classifications)

Every routing result includes these frozen-false guarantees:
- `contact_status_changed: False`
- `deal_stage_changed: False`
- `qualified_demand_accepted: False`
- `booking_created: False`
- `outbound_sent: False`
