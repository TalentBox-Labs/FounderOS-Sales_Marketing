# SaaS S0 — Data Isolation Matrix

**Sprint:** SaaS S0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY

`tenant_id` present today: **NO** on domain entities.  
Queries tenant-scoped today: **NO**.

| Entity | Class today | Future SaaS class | Tenant key | Writes scoped | Leakage risk |
|--------|-------------|-------------------|------------|---------------|--------------|
| Contact | GLOBAL | TENANT_OWNED | absent | no | CRITICAL |
| Company | GLOBAL (unique domain) | TENANT_OWNED | absent | no | CRITICAL |
| Deal | GLOBAL | TENANT_OWNED | absent | no | CRITICAL |
| Pipeline | GLOBAL | TENANT_OWNED | absent | no | HIGH |
| AgentActionLog | GLOBAL | TENANT_OWNED (AUDIT) | absent | no | CRITICAL |
| QualifiedDemand (audit) | GLOBAL audit | TENANT_OWNED | absent | no | CRITICAL |
| CommercialOutcome (audit) | GLOBAL audit | TENANT_OWNED | absent | no | CRITICAL |
| User | GLOBAL | USER_OWNED + membership | absent | n/a | HIGH |
| ConnectorCredentialRecord | GLOBAL | TENANT_OWNED | absent | no | CRITICAL |
| SEOKeyword / RankCheck | GLOBAL | TENANT_OWNED | absent | no | HIGH |
| KnowledgeBase / ContentLibrary | GLOBAL | TENANT_OWNED | absent | no | HIGH |
| ApprovalRequest | GLOBAL | TENANT_OWNED | absent | no | HIGH |
| Editorial decisions (FS) | SYSTEM/INSTANCE FS | TENANT_OWNED or SYSTEM | n/a | n/a | HIGH |
| Website `output/website/` | INSTANCE FS | SHARED_REFERENCE / TENANT | n/a | n/a | MEDIUM |
| Platform config / env | SYSTEM_OWNED | SYSTEM_OWNED | n/a | n/a | — |

**Tenant-Owned Entities Identified (future):** Contact, Company, Deal, Pipeline, AgentActionLog, vault credentials, SEO/content/approval rows, most goals/agents records.  
**Tenant-Scoped Entities Today:** **0**
