# Integration Audit Provenance Contract v1.0

## n8n inbound

- Actor: `"n8n"` (service)
- `stamp_agent_action_log_organization` when org binding resolves
- Payload secrets redacted via `_redact_payload`

## Prohibited in audit

- Raw API keys, tokens, passwords in `detail`

## Cross-tenant audit

**BLOCKED** — org stamp on tenant-bound mutations; cockpit/operator audit scoping preserved from S2.5.

## No second audit SoT

Reuses `AgentActionLog` + `log_agent_action`.
