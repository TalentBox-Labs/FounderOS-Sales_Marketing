# REV-ORCH M4.5 — Calendar Credential Attestation v1.0

## Resolution
`calendar_executor.resolve_calendar_connector(organization_id)`
→ `load_credentials(name, organization_id=org_id, allow_global_fallback=False)`

Connectors: `google_calendar`, then `outlook_calendar`.

## Proven
- No global fallback on the M4 booking path
- Missing tenant connector fails closed
- Payload `calendar_id` is not used as tenant authority (`_execute_book_meeting` does not pass client calendar_id)
- AI worker does not call `load_credentials`

## Contract
```
CALENDAR_CREDENTIAL_ISOLATION = TENANT_SCOPED
GLOBAL_FALLBACK = PROHIBITED_FOR_M4
CROSS_TENANT_BOOKING = BLOCKED
```
