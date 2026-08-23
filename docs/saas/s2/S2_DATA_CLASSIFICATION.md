# SaaS S2 — Data Classification

| Entity | Classification | S2 action |
|--------|----------------|-----------|
| `User` | GLOBAL identity | No `organization_id` |
| `Organization` | TENANT boundary | New model |
| `OrganizationMembership` | TENANT bridge | New model |
| `Contact` | TENANT_OWNED | Nullable `organization_id` + scoped access |
| `Deal` | TENANT_OWNED | Nullable `organization_id` + scoped access |
| `AgentActionLog` | AUDIT / TENANT_OWNED | Nullable `organization_id` + scoped QD/CO |
| `Company` | USER/CRM (sales) | **Not** reused as Organization |
| `Pipeline` | SHARED_REFERENCE | Global default pipeline |
| SEO / editorial / publishing | SYSTEM / GLOBAL | Not tenant-scoped in S2 |
| Connector credentials | GLOBAL secrets | Documented future boundary |
| Configuration / static rules | GLOBAL | No org column |

**Tenant-scoped in S2:** 3 entity types (Contact, Deal, AgentActionLog)  
**Tenant-owned entities identified:** 4 (includes Organization)
