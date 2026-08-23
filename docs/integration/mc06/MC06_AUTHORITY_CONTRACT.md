# MC06 — Authority Contract

**Sprint:** FOUNDER OS MC06  
**Date:** 2026-08-13  
**Follows:** A3.5 / UI1.1 / MC04 human-gate stack

| Actor | Handoff | Accept | Reject |
|-------|---------|--------|--------|
| Authorized human | Permitted | Permitted | Permitted |
| Agent | Prohibited | Prohibited | Prohibited |
| AI | Prohibited | Prohibited | Prohibited |
| Spoofed human metadata (`ai`, `agent`, `bot`, `automation`, `ai:`…) | Prohibited | Prohibited | Prohibited |

## Enforcement layers

1. Router: `is_human_approver` → HTTP 403  
2. Service: `require_human_mutation_authority` → `HumanAuthorityError` (403 at API)

Client-supplied `requested_by` is validated, not trusted as a role claim.

A3.5 closed_won does **not** authorize Revenue mutation. A separate human must register and a separate (or same) human must accept.
