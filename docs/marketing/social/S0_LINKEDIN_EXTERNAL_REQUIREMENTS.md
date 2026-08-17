# S0 — LinkedIn External Requirements

**Sprint:** SOCIAL S0  
**Date:** 2026-08-11  
**Retrieval date for Microsoft Learn:** 2026-08-11

---

## Official sources consulted

| Source | URL | Status |
|--------|-----|--------|
| Share on LinkedIn | https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin | EXTERNAL VERIFIED |
| Posts API (Community Management) | https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2026-07 | EXTERNAL VERIFIED |
| Authentication (linked) | LinkedIn OAuth 2.0 docs via Share on LinkedIn | EXTERNAL VERIFIED (reference) |

---

## 1. Developer account / application

| Requirement | Status | Class |
|-------------|--------|-------|
| LinkedIn Developer account | Required to create apps | EXTERNAL VERIFIED (developer portal prerequisite — standard for Share on LinkedIn) |
| LinkedIn application | Required; add products | EXTERNAL VERIFIED |
| “Share on LinkedIn” product | Enables `w_member_social` | EXTERNAL VERIFIED |
| Redirect URI configuration | Required for OAuth authorization code flow | EXTERNAL VERIFIED (OAuth pattern) |

---

## 2. Publishing as person (member)

| Aspect | Finding | Class |
|--------|---------|-------|
| Capability | Create posts on behalf of authenticated member | EXTERNAL VERIFIED |
| Scope | `w_member_social` | EXTERNAL VERIFIED |
| Product path | Share on LinkedIn (self-serve) | EXTERNAL VERIFIED |
| Access timing | Product add → scope available for member share (self-serve path) | EXTERNAL VERIFIED (Share docs) |
| Classification | **SUPPORTED** (member share) | EXTERNAL VERIFIED |

Share docs still document `POST https://api.linkedin.com/v2/ugcPosts` for consumer share. Posts API docs state marketing Posts API replaces ugcPosts for that surface — **S1 must pick one verified surface and pin version headers**.

---

## 3. Publishing as organization (company page)

| Aspect | Finding | Class |
|--------|---------|-------|
| Scope | `w_organization_social` | EXTERNAL VERIFIED |
| Page roles required | ADMINISTRATOR, DIRECT_SPONSORED_CONTENT_POSTER, or CONTENT_ADMIN | EXTERNAL VERIFIED |
| Classification | **SUPPORTED** with **REQUIRES ADMIN AUTHORITY** | EXTERNAL VERIFIED |
| Community Management / partner product access | Marketing Posts API lives under Community Management docs | EXTERNAL VERIFIED |
| Whether partner program approval is always required before first org write | Not fully settled from consulted pages alone for every app tier | **EXTERNAL VERIFICATION REQUIRED** |
| Classification nuance | Higher friction than member Share-on-LinkedIn | ASSUMPTION / EXTERNAL VERIFICATION REQUIRED for approval latency |

---

## 4. Permissions summary

| Scope / permission | Person | Org | Notes |
|--------------------|--------|-----|-------|
| `w_member_social` | Required | N/A for org author | Member create |
| `w_organization_social` | N/A | Required | Org create |
| `r_member_social` | Restricted | — | Read member posts — **not required for basic publish** |
| Page admin roles | — | Required | EXTERNAL VERIFIED |

**Do not assume person and org use identical permissions.** REPO + EXTERNAL VERIFIED.

---

## 5. API access after app creation

| Path | Immediate? | Class |
|------|------------|-------|
| Member share via Share on LinkedIn product | Self-serve product enablement documented | EXTERNAL VERIFIED |
| Org / Community Management Posts API | May require additional product/partner access | EXTERNAL VERIFICATION REQUIRED for exact gate |

---

## 6. Rate limits (member Share docs)

| Limit | Value | Class |
|-------|-------|-------|
| Per member per day | 150 | EXTERNAL VERIFIED (Share on LinkedIn) |
| Per app per day | 100,000 | EXTERNAL VERIFIED (Share on LinkedIn) |

---

## 7. Identity recommendation

**FOUNDER LINKEDIN IDENTITY DECISION REQUIRED**

- **Member path:** lower setup friction for S1 Manual Publisher.  
- **Organization path:** stronger brand voice; requires page admin + `w_organization_social` (+ possible product access gates).

S1 design should keep **identity configurable**; first runtime identity can be member-only if Founder chooses.
