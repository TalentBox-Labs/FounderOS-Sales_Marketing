# MANUAL DEMAND AUTHORITY CONTRACT v1.0

**STATUS: FROZEN**

| Actor | Register mutation |
|-------|-------------------|
| Valid `FOUNDER_OS_OPERATOR_NAME` human | PERMITTED |
| Agent / AI / forbidden names | 503 via `_trusted_cockpit_operator` |
| Client `requested_by` / `human=true` / `approved=true` | Ignored — field absent from body |
| Direct `register_marketing_handoff(..., "agent")` | `HumanAuthorityError` (UI1.1) |
| Unauthenticated when API key set | 401 |

## Binding

```
Browser form
  → POST /api/v1/mdg/manual-demand/register  (no requested_by)
  → operator = _trusted_cockpit_operator()
  → register_marketing_handoff(db, payload, operator)
```

Browser alone never establishes trusted authority.

## MC04.5 authority preserved

Sales accept/reject remains a separate human action on OF1.5 Operator Flow.  
Registration ≠ acceptance.
