# P1 — Cost / Toolchain Analysis

**Sprint:** P1  
**Agent:** LEDGER  
**Policy:** NO paid tools unless separately approved · **Paid Tools Approved: 0**

---

## Social

| Item | Status |
|------|--------|
| Existing | Publishing stubs; legacy env LinkedIn token docs |
| Free path | Official LinkedIn API (developer app) |
| Aggregators (Buffer/Hootsuite) | Avoid for S0 — lock-in + cost |
| Paid required now | **0** |
| Limits | LinkedIn API rate/product limits |
| Lock-in | Platform account; prefer first-party adapter |

---

## Email

| Item | Status |
|------|--------|
| Existing | Toy SMTP `EmailNotifier` |
| Free/open-source | Self-hosted SMTP (poor deliverability) |
| Likely production | Paid ESP (SendGrid/Postmark/etc.) — **not approved** |
| Paid required for responsible production | Likely later; **0 approved now** |
| Lock-in | ESP + DNS auth (SPF/DKIM) |

---

## Campaign

| Item | Status |
|------|--------|
| Existing | None |
| Free path | Orchestrate owned engines only |
| Paid | Not inherent; risk is premature build cost |
| Paid required now | **0** |

---

## SEO Phase 2

| Item | Status |
|------|--------|
| Existing | Local SEO engines (frozen) — $0 |
| Free future | Google Search Console API |
| Paid SEO SaaS | Explicitly not required for baseline; not approved |
| Blocked | Domain / property verification |

---

## Gate

**Paid Tools Required Now for recommended path (Social LinkedIn S0): 0**
