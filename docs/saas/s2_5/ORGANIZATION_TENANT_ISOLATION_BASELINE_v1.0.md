# Organization / Tenant Isolation Baseline v1.0

**STATUS: FROZEN**  
**Sprint:** FOUNDER OS SaaS S2.5  
**Supersedes:** S2 implementation baseline (documents only; S1.5 identity baseline preserved)

## Canonical tenant

**Organization** — not sales `Company`, not `User`, not `Workspace`.

## Frozen contracts

### Organization
Minimal SaaS tenant boundary: id, name, slug, status, timestamps.

### Membership
User ↔ Organization with role (OWNER/ADMIN/MEMBER/VIEWER) and status (active/disabled).

### TenantContext
Server-derived: IdentityContext + organization + membership + role.  
Client org/tenant hints validated; never authoritative alone.

### Tenant resolution
Cookie `founder_os_organization` + single-membership auto-select + `/api/v1/tenant/select`.

### Query isolation (bounded slice)
Contact, Deal, AgentActionLog filtered/guarded by `organization_id`.

### Mutation isolation (bounded slice)
Founder UI proxies: operator, cockpit, MDG — `tenant_mutation_guard` wrappers before frozen domain ops.

### Audit provenance
`AgentActionLog.organization_id` stamped on QD/CO lifecycle; read filters apply.

### Non-human boundary
SERVICE/AGENT/AI cannot mutate tenant-owned state or spoof `requested_by`.

## Tenant-owned entity manifest

| Entity | Role in baseline |
|--------|------------------|
| Organization | Tenant boundary (#4 identified) |
| Contact | Scoped data (#1 of 3) |
| Deal | Scoped data (#2 of 3) |
| AgentActionLog | Scoped audit (#3 of 3) |

## Known limitations (negative scope)

- CRM API not tenant-gated (S3)
- Connector credentials global (future vault)
- Editorial/SEO/publishing reads not org-filtered
- No billing, invitations, workspace hierarchy, public signup

## Compatibility

| Baseline | Status |
|----------|--------|
| SaaS S1.5 Identity | PRESERVED (IdentityContext tenant-free) |
| UI1.1 mutation authority | PRESERVED |
| UI2.5 cockpit | PRESERVED |
| OF1.5 operator | PRESERVED |
| MDG1.5 manual demand | PRESERVED |
| MC04.5 / MC06.5 | PRESERVED (wrapped, not modified) |
| A3.5 / A4.5 | PRESERVED |

## Residual risks

See `S2_5_RESIDUAL_TENANCY_RISK_REGISTER_v1.0.md`.
