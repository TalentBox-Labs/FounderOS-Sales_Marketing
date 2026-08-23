# M1.1 Legacy Agent Containment

**Sprint:** REV-ORCH M1.1  
**Date:** 2026-08-17

---

## Scope

`runner_api_routers/agents.py` — 5 live sales-agent routes under `/api/v1/agents/sales/{contact_id}/*`

## Pre-M1.1 Risk

- Routes used `sales_agents._load_contact(db, contact_id)` — ID-only, no tenant scope
- Cross-tenant contact access possible if caller knew UUID

## Containment Applied

1. All 5 sales routes now require `require_tenant_context(http_request)` → 403 without session
2. `sales_agents` functions require `organization_id: str` keyword arg
3. `_load_contact` uses `get_contact_for_tenant` when `organization_id` supplied
4. Approval payloads include `organization_id` for tenant-bound outbound validation

## Routes Audited

| Route | Mutates CRM | Sends | Approves | Overlaps M1 |
|-------|-------------|-------|----------|-------------|
| `POST …/research` | Activity NOTE | NO | NO | Partial (research only) |
| `POST …/cold-email` | Activity NOTE | NO (ApprovalRequest) | NO | YES — legacy path |
| `POST …/linkedin-opener` | Activity NOTE | NO (ApprovalRequest) | NO | Partial |
| `POST …/sequence` | OutreachSequence | NO | NO | NO |
| `POST …/handle-reply` | Activity NOTE | NO (ApprovalRequest) | NO | NO |

## M1 Canonical Path Isolation

Canonical M1: `POST /api/v1/revenue/contacts/{id}/research-to-outreach`  
Legacy sales routes remain for backward compatibility but are **tenant-scoped** and **not** used by M1.

## Residual

Legacy routes still duplicate capability surface with M1 (cold-email). Deprecation marker deferred to M2 — not in M1.1 scope.

## Verdict

**Legacy ID-Only Contact Risk: MITIGATED**  
**Cross-Tenant via sales routes: BLOCKED** (403 without tenant; contact not found cross-tenant)
