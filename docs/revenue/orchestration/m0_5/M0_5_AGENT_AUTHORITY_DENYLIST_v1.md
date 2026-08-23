# M0.5 Agent Authority Denylist v1.0

**Sprint:** REV-ORCH M0.5  
**Date:** 2026-08-17  
**Status:** FROZEN

---

## Freeze

Unless an existing frozen Founder OS contract **explicitly** permits the action, **SPECIALIZED AI WORKERS MUST NOT:**

1. Select `organization_id`
2. Override TenantContext
3. Fabricate IdentityContext
4. Fabricate `requested_by`
5. Select connector credentials
6. Retrieve another tenant’s credentials
7. Directly send email
8. Directly send LinkedIn message
9. Directly send DM
10. Directly mutate `Contact.status`
11. Directly mutate `Deal.stage`
12. Accept or reject QualifiedDemand
13. Accept or reject CommercialOutcome
14. Approve their own ApprovalRequest
15. Impersonate a human approver
16. Bypass domain validation
17. Bypass audit
18. Execute arbitrary tools / general LLM tool calling
19. Create alternative business SoTs
20. Chain actions across two organizations
21. Treat GLOBAL_BY_DESIGN env credentials as per-tenant agent authority
22. Treat NULL `organization_id` GLOBAL_BY_DESIGN credentials as generic agent authority (S4.5)

---

## Existing frozen contracts that already encode parts of this list

| Item | Contract |
|------|----------|
| Contact.status | A4.5 + `require_human_mutation_authority` |
| Deal.stage | A3.5 |
| QualifiedDemand accept/reject | MC04.5 |
| CommercialOutcome accept/reject | MC06.5 |
| Tenant selection | S2.5 / S3.5 server-derived TenantContext |
| requested_by spoof | S1.5 |
| Connector credential selection | S4.5 |
| Human-only approval | FDR-002 / `is_human_approver` |
| General tool calling | M0 `PROHIBITED_FOR_M1` |

This denylist does **not** modify those contracts. It binds specialized workers to them.

---

## Enforcement expectation for M1

| Deny | Enforcement locus |
|------|-------------------|
| Tenant/identity | Server-derived context; ignore worker-supplied IDs |
| Send | Only `approvals.EXECUTORS` after human `decide(approve=True)` |
| CRM privileged mutate | Domain services + HUMAN_ONLY |
| Tool calling | Do not add `tools=` to AIService |
| Credentials | `load_credentials(org, allow_global_fallback=False)` never called by worker |

---

*End of M0.5 Agent Authority Denylist v1.0*
