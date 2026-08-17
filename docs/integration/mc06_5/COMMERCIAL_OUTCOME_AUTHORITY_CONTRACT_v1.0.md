# COMMERCIAL OUTCOME AUTHORITY CONTRACT v1.0

**STATUS: FROZEN**  
**Baseline:** Founder OS CommercialOutcome Baseline v1.0  
**Date:** 2026-08-13  
**Parents:** A3.5 authority · UI1.1 `mutation_authority` · MC04.5 human gate — **UNCHANGED**

---

## Frozen matrix

| Actor | Sales handoff | Revenue accept | Revenue reject |
|-------|---------------|----------------|----------------|
| Authorized human | Permitted | Permitted | Permitted |
| Agent | Prohibited | Prohibited | Prohibited |
| AI | Prohibited | Prohibited | Prohibited |
| Spoofed human (`ai`, `agent`, `bot`, `automation`, `system`, `ai:` / `agent:` / `bot:`) | Prohibited | Prohibited | Prohibited |

A3.5 `closed_won` does **not** authorize Revenue mutation.

---

## Enforcement (frozen layers)

1. Router: `is_human_approver` → HTTP 403  
2. Service: `require_human_mutation_authority` → `HumanAuthorityError` (API 403)

Direct service/domain bypass of the human gate is **prohibited** (UI1.1 pattern).  
`requested_by` is validated, not trusted as a role claim.

---

## Do not expand

No agent-assisted accept. No cockpit mutation. No JWT ungated CommercialOutcome path in this baseline.
