# SaaS S0 — SaaS S1 Recommendation

**Sprint:** SaaS S0  
**Date:** 2026-08-13  
**Mode:** RECOMMENDATION ONLY — do not implement in S0

## Recommended SaaS S1

**Identity Foundation on primary `runner_api`**

### Implementation type

**BUILD_NEW** (session/user binding on primary app)  
+ **CONNECT_EXISTING** (reuse human gates / frozen APIs / Jinja shell)

### Why this slice first

1. Auth is the blocking SaaS gap (shared API key + env operator).
2. Tenancy without identity creates org_id with no trustworthy actor.
3. Smallest independently testable advance toward multi-tenant SaaS.
4. Preserves all `*.5` freezes via outer context later.
5. MDG1.5 already attested wrap-friendly identity evolution.

### In scope (proposed for future S1)

- First-party login/logout on primary app (or bind JWT User into runner carefully)
- httpOnly session for Jinja + API
- Eliminate client `requested_by` as authority on new paths
- Map authenticated human → mutation `actor` for cockpit/operator/MDG
- Tests: spoof blocked, session required, freeze suites green

### Out of scope for S1

- Organization / workspace schema
- `organization_id` backfill
- Public MDG2 forms
- CRM SPA remount
- Lovable production FE
- Paid IdP
- Rate limiting productization (unless needed for auth endpoints)

## MDG2 Status: PARKED

Reason: public inbound security MISSING; trusted manual path already FROZEN (MDG1.5). Resume after Identity Foundation + abuse controls design.

## Next after S1 (not authorized now)

SaaS S2 — Organization model + tenant context middleware + scoped query wrappers.
