# Founder OS ACP-1 — Authority Attestation

| Invariant | Evidence |
|-----------|----------|
| Hermes Deal create prohibited | `action_create_deals_for_qualified` always blocked; test asserts zero Deal delta |
| Agent cannot approve | `decide` rejects non-human `TenantContext` |
| COS-5 INLINE preserved | QD/Approval still INLINE_GOVERNED; no optional_tenant inline |
| optional_tenant not used by autonomous modules | Static assert: scheduler/hermes/boundary lack `optional_tenant_mutation` |
| No new send/book | Static assert + no EXECUTOR wiring from heartbeat |
| Propose ≠ Execute | Hermes ACTION_REGISTRY has no send/book/approve |
| create_deal stamp ≠ eligibility | Stamp from Contact.organization_id; Hermes still PROHIBITED |

## Residual

Operator/CRM `optional_tenant_mutation` remains for human HTTP (S2.5/S3.5 freezes). Not agent-callable via ACP-1 surfaces.
