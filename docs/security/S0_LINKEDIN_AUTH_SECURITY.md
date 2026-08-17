# S0 — LinkedIn Auth & Security

**Sprint:** SOCIAL S0  
**Agent:** CIPHER  
**Date:** 2026-08-11  
**Rule:** Never paste secrets into Cursor/chat/docs/logs/fixtures.

---

## 1. Ownership model (proposed)

| Role | Owner |
|------|-------|
| AUTHENTICATION OWNER | Founder / operator (creates LinkedIn app; completes OAuth) |
| TOKEN OWNER | Founder OS secret store (env / vault) — **not** git |
| TOKEN CONSUMER | LinkedIn Adapter (runtime read-only) |
| ROTATION OWNER | Founder / operator + documented runbook |
| REVOCATION PROCESS | LinkedIn app revoke + delete env/vault entry + disable channel |

Editorial content approval **does not** grant credential access.

---

## 2. Repository evidence

| Item | Status | Class |
|------|--------|-------|
| `.env.example` `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PERSON_URN` | Template only | REPO VERIFIED |
| Marketing OS OAuth callback routes | Absent | REPO VERIFIED / NOT IMPLEMENTED |
| RevenueOS credentials vault | Generic encrypted connector vault | REPO VERIFIED / PARTIAL |
| Secrets in docs/tests committed | None found for live LI tokens | REPO VERIFIED |

**Credential Storage readiness:** **REQUIRES SETUP** (convention exists; Marketing OS binding + OAuth flow not implemented).

---

## 3. Expected OAuth architecture (EXTERNAL VERIFIED + ASSUMPTION)

Sources (retrieved 2026-08-11):

- [Share on LinkedIn](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin)  
- [Posts API permissions](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api?view=li-lms-2026-07)  
- [OAuth 2.0 authentication guide](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authentication) *(linked from Share docs)*

| Topic | Finding | Class |
|-------|---------|-------|
| Member post scope | `w_member_social` via Share on LinkedIn product | EXTERNAL VERIFIED |
| Org post scope | `w_organization_social` + page roles (ADMINISTRATOR / CONTENT_ADMIN / DIRECT_SPONSORED_CONTENT_POSTER) | EXTERNAL VERIFIED |
| Member read social | `r_member_social` **restricted / approved users only** | EXTERNAL VERIFIED |
| OAuth | OAuth 2.0 authorization for members | EXTERNAL VERIFIED |
| Token refresh details for S1 | Not fully re-specified in this sprint beyond OAuth guide | EXTERNAL VERIFICATION REQUIRED for refresh token persistence design |
| Client secret storage | Must be env/vault only | ASSUMPTION (standard) + governance |

---

## 4. Forbidden placements

Never store tokens/secrets in: git, source, docs, logs, audit JSON (raw), test fixtures, frontend HTML.

Audit may store: `token_present=true/false`, last-4 hash optional, never raw token.

---

## 5. S1 secure procedure (Founder-facing, no secret paste)

1. Create LinkedIn Developer App outside Cursor.  
2. Enable required product(s).  
3. Complete OAuth locally / secure machine.  
4. Place access token (and client credentials if needed) in **local `.env` / vault** — never commit.  
5. Confirm `.gitignore` covers `.env`.  
6. Rotate on leak suspicion; revoke in LinkedIn portal.

---

## 6. OAuth Architecture status

**DEFINED** at ownership/policy level; **PARTIAL** at Marketing OS implementation (no OAuth routes yet).
