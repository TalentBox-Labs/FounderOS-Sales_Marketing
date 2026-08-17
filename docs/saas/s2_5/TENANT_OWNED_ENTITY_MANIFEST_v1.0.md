# Tenant-Owned Entity Manifest v1.0

**Reconciles S2:** 4 identified / 3 scoped

## Reconciliation statement

S2 reported **4 tenant-owned entities identified** and **3 tenant-scoped entities implemented**.

| # | Entity | Classification | S2 scope |
|---|--------|----------------|----------|
| 1 | **Organization** | TENANT_BOUNDARY (A*) | Created; IS the tenant — not org_id-filtered |
| 2 | **Contact** | TENANT_SCOPED_AND_GUARDED (A) | `organization_id` + scoped mutations/reads |
| 3 | **Deal** | TENANT_SCOPED_AND_GUARDED (A) | `organization_id` + scoped mutations/reads |
| 4 | **AgentActionLog** | TENANT_SCOPED_AND_GUARDED (A) | `organization_id` + QD/CO scoping + audit filter |

\*Organization is tenant-owned infrastructure, not a data row scoped by `organization_id`. It is the **fourth entity** in the inventory but not counted among the **three data entities** that received org_id columns and query guards.

## Explicit fourth entity

**Organization** — the canonical tenant boundary model (`revenue_os/models/organization.py`).

Without Organization there is no tenant; Contact/Deal/AgentActionLog reference it via `organization_id`.

## Not tenant-owned (explicit)

| Entity | Classification |
|--------|----------------|
| `User` | GLOBAL identity |
| `OrganizationMembership` | TENANT bridge (not business data) |
| `Company` | CRM sales entity — NOT Organization |
| `Pipeline` | SHARED_REFERENCE |
| `ConnectorCredentialRecord` | GLOBAL secrets |
| SEO / editorial / publishing | GLOBAL_BY_DESIGN |

## Per-entity contract

### Contact
- Persistence: `contacts.organization_id` (nullable, backfilled)
- Read isolation: cockpit/operator read models filter by org
- Mutation isolation: `scoped_contact()`
- Audit: status changes via frozen A4.5

### Deal
- Persistence: `deals.organization_id` (nullable, backfilled)
- Read isolation: operator read model filter
- Mutation isolation: `scoped_deal()`, `assign_new_deal_org()`
- Audit: stage changes via frozen A3.5

### AgentActionLog
- Persistence: `agent_action_log.organization_id`
- Read isolation: QD/CO pending lists filtered by org
- Mutation isolation: handoff lookup by org + target_id
- Audit: stamp on register/accept/reject/handoff

### Organization
- Persistence: `organizations` table
- S3 ownership: billing/subscription (deferred)

## Deferred tenant-owned entities

**NONE** among the four identified. Residual unscoped surfaces (CRM API) operate on Contact/Deal but are **ungated routes**, not missing entity classification.
