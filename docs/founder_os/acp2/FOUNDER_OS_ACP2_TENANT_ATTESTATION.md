# Founder OS ACP-2 — Tenant Attestation

| Invariant | Evidence |
|-----------|----------|
| Missing org fails closed | `evaluate_authority` → BLOCKED `missing_tenant` |
| Non-allowlisted org fails closed | Intersects ACP-1 `resolve_autonomous_organization_ids` |
| Cross-tenant child blocked | `delegate_child` copies parent org only |
| Contact does not activate tenant | ACP-1 enumeration unchanged; ACP-2 test |
| Scheduler commercial work org-scoped | `job_score_new_leads` / follow-up via `orchestrate(..., organization_id=)` |
