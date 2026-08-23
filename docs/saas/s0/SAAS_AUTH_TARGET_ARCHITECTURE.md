# SaaS S0 — Auth Target Architecture

**Sprint:** SaaS S0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY — no vendor purchase required for MVP

## Current suitability

**Insufficient for SaaS.** Shared API key + env operator + unused JWT User stack.

## Target (recommended)

| Capability | Priority |
|------------|----------|
| Signup / login / logout | **REQUIRED_FOR_MVP** |
| Session or httpOnly token for Jinja + API | **REQUIRED_FOR_MVP** |
| Email verification | REQUIRED_LATER |
| Password reset | REQUIRED_FOR_MVP (basic) |
| Organization create on signup | **REQUIRED_FOR_MVP** (with tenancy) — after Identity S1 may stub single-org |
| Invites + membership | REQUIRED_FOR_MVP (minimal) |
| Role assignment (OWNER/ADMIN/MEMBER/VIEWER) | REQUIRED_FOR_MVP |
| API keys per org (machine) | REQUIRED_LATER |
| OAuth SSO | OPTIONAL |
| MFA | OPTIONAL / REQUIRED_LATER |

## Architecture preference

```
Browser (Jinja)
  → Session cookie (httpOnly)
  → Auth middleware binds User + Organization membership
  → Tenant Context
  → Frozen domain services (unchanged semantics)
```

Do **not** trust client `requested_by`.  
Do **not** select a paid IdP unless justified after MVP; start with first-party email/password on primary `runner_api`.

Reuse secondary `User` model carefully or replace with membership-aware identity — decide in SaaS S1 design without breaking freezes.
