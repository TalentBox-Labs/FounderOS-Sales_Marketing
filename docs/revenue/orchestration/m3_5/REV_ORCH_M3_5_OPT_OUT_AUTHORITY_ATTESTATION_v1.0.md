# REV-ORCH M3.5 — OPT_OUT Authority Attestation v1.0

## Status: FROZEN

## Mutation Boundary

### Who Performs the Mutation
The deterministic policy code in `run_inbound_reply_handling()` (revenue_orchestration_service.py),
NOT the ReplyAnalysisWorker.

### Call Chain
```
AI classifies → OPT_OUT
route_reply_assessment() → {apply_opt_out_tag: True}
run_inbound_reply_handling() checks routing["apply_opt_out_tag"]
→ contact.tags = merge_opt_out_tag(contact.tags)
→ db.commit()
```

### Exactly What Changes
- Field: `Contact.tags`
- Token added: `"unsubscribed"` (constant `OPT_OUT_TAG` in reply_routing.py)
- Function: `merge_opt_out_tag()` — idempotent, only adds the fixed token

### What Cannot Change
- Contact.status: NOT mutated
- Contact.email: NOT mutated
- Contact.first_name/last_name: NOT mutated
- Any other Contact field: NOT mutated
- Deal: NOT mutated
- QualifiedDemand: NOT affected

### AI Cannot Supply Arbitrary Values
The AI classification output is normalized to a fixed enum. The tag value is a hardcoded
constant ("unsubscribed"), not derived from AI output. No AI-supplied string reaches
`Contact.tags`.

## Properties

| Property | Status |
|----------|--------|
| Policy-bound | YES (only via OPT_OUT classification) |
| Tenant-scoped | YES (contact validated via get_contact_for_tenant) |
| Idempotent | YES (merge_opt_out_tag is set-based) |
| Auditable | YES (AgentActionLog records routing decision) |
| Reversible by automation | NO (no automated un-suppress path) |
| Arbitrary field injection | BLOCKED (fixed constant only) |

## Follow-Up Impact

`evaluate_follow_up_eligibility()` checks `_contact_stop_tags()` which includes
"unsubscribed" in `_STOP_TAGS`. Result: `FOLLOWUP_STOPPED`.

## Contract

```
OPT_OUT_MUTATION = POLICY_BOUND_TAG_ONLY
OPT_OUT_SCOPE = TENANT_ISOLATED
OPT_OUT_FIELD = Contact.tags ("unsubscribed" token only)
AI_ARBITRARY_MUTATION = PROHIBITED
```
