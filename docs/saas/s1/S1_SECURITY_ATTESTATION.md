# SaaS S1 — Security Attestation

**Sprint:** FOUNDER OS SaaS S1  
**Date:** 2026-08-14

## Controls

| Control | Status |
|---------|--------|
| Password hashing (bcrypt) | PASS |
| httpOnly identity cookie | PASS |
| SameSite=Lax | PASS |
| Secure flag (opt-in) | PASS |
| Token expiry (`exp`) | PASS |
| Invalid token rejection | PASS |
| Logout cookie clear + `jti` denylist | PASS |
| Brute-force 429 | PASS (in-process) |
| Open redirect on `next` | BLOCKED |
| Secrets in HTML | NONE (login template attested) |
| Hardcoded production passwords | NONE |
| Public signup on runner_api | ABSENT |
| API key as HUMAN | BLOCKED |
| Agent/AI HUMAN_ONLY | BLOCKED |
| Client `requested_by` on Founder proxies | IGNORED / server-bound |
| CSRF (forms) | SameSite=Lax MVP — not a full CSRF token suite |
| Multi-worker logout denylist | LIMITATION (in-process) |

## Threats explicitly out of S1

Full IAM, OAuth, org invitations, tenant isolation, WAF productization.

## Frozen HUMAN_ONLY

UI1.1 `require_human_mutation_authority` **preserved**. S1 feeds it a trusted name from IdentityContext on wrapped routes.
