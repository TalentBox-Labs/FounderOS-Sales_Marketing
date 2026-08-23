# SaaS S1 — requested_by Compatibility

**Sprint:** FOUNDER OS SaaS S1

## Rule

```
client requested_by  ≠  trusted identity
server IdentityContext  =  trusted actor
```

## Founder UI proxies (wrapped)

These paths **do not** accept client `requested_by`. They call `_trusted_cockpit_operator()`, which now resolves:

1. Session HUMAN `display_name`
2. Else `FOUNDER_OS_OPERATOR_NAME` (legacy, DEPRECATE_LATER)
3. Else HTTP 503

Covered:

- `POST /api/v1/cockpit/actions/*` (exactly two frozen mutations)
- `POST /api/v1/operator/actions/*` (exactly eight frozen mutations)
- `POST /api/v1/mdg/manual-demand/register`

OF1.5 freeze still asserts `src.count("_trusted_cockpit_operator()") == 8`. Call sites were **not** renamed.

## Frozen domain JSON APIs (not rewritten)

`runner_api_routers/crm.py`, `qualified_demand.py`, `commercial_outcome.py` still accept `requested_by` in the request body for A3.5 / A4.5 / MC04.5 / MC06.5 compatibility.

S1 does **not** change those frozen request schemas. UI1.1 still rejects agent/AI names at the service layer.

Future S2 may wrap those routers the same way without editing domain contracts.

## Spoofing blocked on wrapped paths

Extra JSON field `requested_by` on MDG/cockpit/operator bodies is ignored (not in the Pydantic model). The operator recorded on the frozen handoff is the session (or env) human.
