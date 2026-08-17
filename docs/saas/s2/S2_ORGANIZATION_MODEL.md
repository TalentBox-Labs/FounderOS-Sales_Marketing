# SaaS S2 — Organization Model

**Status:** IMPLEMENTED (S2)  
**Canonical tenant boundary:** `Organization` (separate from sales `Company`)

## Model

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `name` | string | Display name |
| `slug` | string | Unique stable identifier |
| `status` | enum | `active` \| `suspended` |
| `created_at` / `updated_at` | datetime | Audit timestamps |

**Module:** `revenue_os/models/organization.py`

## Explicit non-scope (S2)

No billing, subscription, workspace hierarchy, seats, entitlements, or CRM semantics on Organization.

## Bootstrap

`revenue_os/services/tenant_bootstrap.py` creates one default organization for active users without membership (idempotent). Existing tenant-owned rows with null `organization_id` are backfilled on startup.
