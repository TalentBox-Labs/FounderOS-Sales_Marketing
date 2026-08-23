# S0 — LinkedIn Publishing Contract (Proposed S1)

**Sprint:** SOCIAL S0  
**Agent:** NOVA  
**Status:** CONTRACT ONLY — no production code  
**Date:** 2026-08-11

---

## 1. Scope pressure-test

| Capability | S1 | Reason |
|------------|----|--------|
| LinkedIn only | CORE | P1 decision |
| Manual human publish | CORE | Frozen Publishing model |
| Editorially approved content only | CORE | FDR-003 |
| Text-only post | CORE | Lowest complexity |
| Text + article/URL link | CORE optional | Share-on-LinkedIn supports ARTICLE; useful for Website deep links |
| Image/video upload | **DEFERRED** | Extra asset register/upload steps |
| Scheduling | **DEFERRED** | Not in Publishing frozen schedule |
| Analytics ingestion | **DEFERRED** | Not required to publish |
| Multi-identity simultaneous | **DEFERRED** | One identity type in S1 |
| Autonomous AI publish | **REJECTED** | Governance |

---

## 2. Conceptual interface

```text
LinkedInPublisher.publish(request) -> LinkedInPublishResult
```

### Proposed request fields

| Field | Core S1? | Notes |
|-------|----------|-------|
| `content_id` | YES | Bundle id |
| `publishing_job_id` | YES | Idempotency / audit |
| `channel` | YES | Must be `linkedin` |
| `requested_by` | YES | Human identity (already gated upstream) |
| `text` / body | YES | Post commentary |
| `author_urn` | YES | `urn:li:person:` or `urn:li:organization:` |
| `visibility` | YES | Default PUBLIC |
| `article_url` | OPTIONAL | If text+link |
| `idempotency_key` | YES | Prefer `publishing_job_id` |
| `media` | DEFERRED | |

### Proposed result

| Field | Required |
|-------|----------|
| `ok` | YES |
| `status` | YES (`published` / `failed` / `rejected`) |
| `external_post_id` | WHEN SUCCESS |
| `external_url` | IF AVAILABLE |
| `provider` | `linkedin` |
| `provider_status_code` | WHEN KNOWN |
| `error_code` / `error_message` | WHEN FAIL (redacted) |
| `timestamp` | YES |
| `attempt` | YES |

---

## 3. Idempotency & retry

| Rule | Proposal |
|------|----------|
| Idempotency | One successful LinkedIn create per `publishing_job_id` |
| Safe retry | Only if prior attempt left no `external_post_id` |
| Unsafe retry | Blind re-POST after unknown timeout → requires provider lookup or Founder-safe “mark failed / new job” policy |
| Publishing Engine retry | Existing `retry` → `manual_publish` path; adapter must be retry-aware |

**Class:** ASSUMPTION until S1 implements lookup strategy — document as CONDITIONAL.

---

## 4. Upstream invariants (must remain)

1. Unapproved content → cannot create publish job  
2. Non-human requester → rejected  
3. `approved` ≠ auto-published  
4. Adapter invoked only from Publishing `manual_publish`

---

## 5. Provider surface (external — see External Requirements)

Prefer targeting current LinkedIn **Posts API** / Share surfaces with verified scopes; legacy RevenueOS uses `/v2/ugcPosts` (**STALE reference** — migrate carefully in S1).
