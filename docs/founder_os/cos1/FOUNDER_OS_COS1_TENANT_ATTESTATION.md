# Founder OS COS-1 Tenant Attestation

| Rule | COS-1 |
|------|-------|
| Organization is tenant | Unchanged |
| Company is not tenant | Unchanged; company **name** shown from Contact.company relationship |
| Person workspace | `get_contact_for_tenant` |
| People list | operator flow org filter + org-scoped Contact lookup for names |
| Home / activity / approvals | existing organization_id filters |
| Unscoped Company/Deal enumeration UI | Not added |
| Client org cookie spoof | Person workspace remains isolated (same class as UI-D1.5). Demand list cookie vs membership is **pre-existing S2 behavior**, not expanded; COS-1 did not add a client org switcher. |

No TenantContext redesign.
