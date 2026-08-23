# S0 — LinkedIn Test Strategy (Future S1)

**Sprint:** SOCIAL S0  
**Date:** 2026-08-11  
**Rule:** No live LinkedIn API calls in unit tests.

---

## Mock / fake provider

| Component | Strategy |
|-----------|----------|
| `FakeLinkedInPublisher` | Returns success with synthetic `external_post_id` |
| `RejectingLinkedInPublisher` | Provider 400/403 |
| `TimeoutLinkedInPublisher` | Raises timeout |
| `RateLimitedLinkedInPublisher` | 429 normalized |
| Credential probes | Missing / invalid env → fail closed without network |

Inject via Publishing CHANNEL_ADAPTERS or Social Engine factory — **tests only**.

---

## Required cases

| Case | Expect |
|------|--------|
| Unapproved content | Blocked before / at job create |
| AI requester | Blocked |
| Human approved + human publish | Adapter invoked |
| Missing credentials | Safe fail; no token leak |
| Invalid credentials | Safe fail; redacted error |
| Provider timeout | Job failed / retryable per policy |
| Provider rejection | Normalized error + audit |
| Rate-limit | Normalized; no tight loop |
| Duplicate publish | Idempotent on `publishing_job_id` |
| Retry behavior | Matches Publishing retry + adapter rules |
| Audit creation | Job events recorded |
| Secret redaction | No raw token in logs/audit |
| Unsupported channel | Rejected |
| Payload validation | Empty text / bad URN rejected |
| `approved != auto-published` | Explicit test — approval alone does not call adapter |

---

## Integration / manual (Founder machine only)

Live LinkedIn smoke **outside CI**, after ES-01..03, never commit tokens.

---

## Existing baseline (S0)

`tests/test_publishing_engine.py` + `tests/test_editorial_approval.py`: **35 passed** (2026-08-11).  
Full suite: **388 passed; 8 failed; 4 errors** — historical identities (crews_unit, utilities_unit, orchestration_api, prospecting_ui). **New regressions: 0** (docs-only sprint).
