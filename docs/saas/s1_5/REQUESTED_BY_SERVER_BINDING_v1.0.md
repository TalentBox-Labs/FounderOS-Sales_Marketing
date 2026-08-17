# REQUESTED_BY SERVER BINDING v1.0

**STATUS: FROZEN**  
**Sprint:** FOUNDER OS SaaS S1.5

## Rule

```
client-supplied requested_by  ≠  trusted authority
server IdentityContext        =  trusted actor
```

## Wrapper pattern (frozen)

```
resolve_trusted_human()
        ↓
_trusted_cockpit_operator()
        ↓
frozen domain service(..., requested_by=operator)
```

Priority:

1. Session HUMAN `display_name` from IdentityContext
2. Legacy `FOUNDER_OS_OPERATOR_NAME` (DEPRECATE_LATER)
3. Else HTTP 503

`RUNNER_API_KEY` never satisfies this path.

## Wrapped Founder proxies

| Surface | Notes |
|---------|-------|
| Cockpit POSTs (2) | No `requested_by` on body models |
| Operator POSTs (8) | `_trusted_cockpit_operator()` call sites preserved for OF1.5 freeze |
| MDG POST | Client `requested_by` not on body; server binds operator |

## Unchanged frozen JSON APIs

`crm.py` / `qualified_demand.py` / `commercial_outcome.py` may still accept client `requested_by` for A3.5 / A4.5 / MC04.5 / MC06.5 compatibility. UI1.1 rejects agent/AI names at the service layer. S1.5 does **not** rewrite those schemas.
