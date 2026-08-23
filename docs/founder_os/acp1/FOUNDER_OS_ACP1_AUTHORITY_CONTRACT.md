# Founder OS ACP-1 — Authority Contract

**STATUS:** BINDING FOR ACP-1

## Vocabulary

| Class | Meaning |
|-------|---------|
| READ | Observe only |
| PROPOSE | Draft / file `ApprovalRequest` only |
| EXECUTE_GOVERNED | Side effect only after human Approval decide (or COS-5 human INLINE) |
| HUMAN_REQUIRED | Human session required; never autonomous |
| PROHIBITED | Forbidden for autonomous/agent callers |

## Rules

1. Autonomous commercial work without explicit tenant context **fails closed**.
2. Proposal authority cannot become execution via internal helpers.
3. Hermes cannot approve Approvals; humans only (`is_human` gate).
4. No new autonomous outbound send or booking execution.
5. Hermes Deal creation is **PROHIBITED** regardless of org context.
6. `optional_tenant_mutation` paths remain human-legacy HTTP; autonomous modules must not import/call them.

## Env

- `ACP1_AUTONOMOUS_ORGANIZATION_IDS` — optional comma-separated org UUID allowlist
- `HEARTBEAT_ORGANIZATION_IDS` — alias

When set: intersect with ACTIVE `Organization`. Empty → fail closed.
When unset: all ACTIVE `Organization` rows.
Contact.organization_id never authorizes tenant activation.
