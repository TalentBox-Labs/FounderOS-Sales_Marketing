# Founder OS ACP-1 — Tenant Attestation

| Invariant | Evidence |
|-----------|----------|
| Autonomous work requires explicit tenant | `resolve_autonomous_organization_ids`; jobs fail closed when empty |
| Contact rows do not activate tenants | Enumeration uses allowlist ∩ ACTIVE Organization or ACTIVE Organization only |
| No global commercial Contact query | `job_score_new_leads` / follow-up scan / Hermes score filter by `organization_id` |
| No global commercial Deal query | `get_deals_at_risk(..., organization_id=)` from heartbeat/Hermes |
| Tenant/entity mismatch fails closed | `assert_contact_org` before score/proposal; mismatch → blocked log |
| Gmail match scoped | `Contact.organization_id.in_(org_uuids)` |
| Cross-tenant isolation | ACP-1 test: score allowlist Org A leaves Org B unscored |

## Limitation (documented)

`Goal` rows have no `organization_id`. ACP-1 injects authorized org into Hermes steps at check time rather than adding a Goal migration. HTTP `/hermes/goals/{id}/check` without org now fail-closes commercial steps (no global queries).
