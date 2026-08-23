# UI-D1.5 Navigation Contract v1.0

**STATUS: FROZEN**

## Primary nav (Founder)

Rendered from `templates/base.html`:

- Command Center → `/command`
- Demand & Contacts → `/demand`
- Approvals → `/pending-approvals`
- Activity → `/activity`
- Revenue Workflow → `/operator`

Contact workspace is reached from Demand (`/contacts/{id}`), not a duplicate nav item.

## Secondary (Content Ops)

Collapsed `<details>`: Dashboard, legacy Executive Cockpit, Analytics, Content Calendar, Content Studio, Editorial, Publishing, SEO, Pipeline, Marketing, Sales, MCP Hub.

## Product language (primary flow)

Allowed: Command Center, Demand, Contacts, Approvals, Activity, Revenue Workflow, Meeting interest, Booking eligible, Recommended (advisory only).

Forbidden in primary product copy: SoT, MC04.5, M3.5, TenantContext, AgentActionLog.

## Shell chrome

- Organization name when server tenant resolves (`data-testid="founder-org-name"`)
- No client org switcher (cookie is server-validated membership only)
- Mobile sidebar toggle
- Sign out when human session present
