# Founder OS COS-5 Tenant Attestation

**STATUS:** BINDING

## Fail closed

Missing / invalid `organization_id`:

- Command snapshot `state=unavailable`
- `attach_command_actions(..., organization_id=None)` → `[]`
- No inline action enumeration

## Inline action tenant enforcement

| Action | Enforcement (existing) |
|--------|------------------------|
| QD accept/reject | `require_tenant_mutation` + `scoped_demand_handoff` |
| Approval approve/reject | `require_tenant_context` + `get_approval_for_tenant` |

## Exclusions

optional_tenant Operator mutations are never INLINE_GOVERNED.

## Company

No Company queries in COS-5 composition.
