# Founder OS ACP-3 — Tenant & Authority Attestation

## Tenant

- Every recoverable unit carries `organization_id` in WorkItem detail and log.
- Reconcile/resume require explicit org; empty org → fail closed.
- Cross-tenant recovery prohibited (queries filtered by `AgentActionLog.organization_id`).
- Contact.organization_id is ownership stamp only — not tenant-enumeration authority
  for discovering organizations (ACP-1 preserved).

## Authority

- ACP-3 never grants authority.
- Recovery calls `evaluate_authority` before any executor.
- Narrower current allowlist / kill / PROHIBITED catalog wins over historical eligibility.
- Hermes autonomous Deal create remains PROHIBITED.
- Booking/outbound remain HUMAN_REQUIRED as governed by ACP-1/ACP-2 catalog.
