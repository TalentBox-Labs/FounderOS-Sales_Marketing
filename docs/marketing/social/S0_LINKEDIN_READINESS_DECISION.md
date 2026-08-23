# S0 — LinkedIn Readiness Decision Packet

**Sprint:** SOCIAL S0 — LinkedIn Readiness, Auth & Publishing Boundary Audit  
**Coordinator:** Lead Engineering Coordinator  
**Date:** 2026-08-11  
**Governance:** Audit / contract only — Feature Code Changes: 0

---

## Executive Summary

Founder OS is **architecturally ready** to implement Social S1 (LinkedIn Manual Publisher) behind existing Editorial and Publishing human gates. Marketing OS **does not** yet implement a Social Engine or LinkedIn adapter (Publishing channel is a closed stub). Official LinkedIn docs verify **member** publish via `w_member_social` (Share on LinkedIn) and **organization** publish via `w_organization_social` with page admin roles. **No paid aggregator is required.** Live publish requires Founder-owned external app/OAuth/token setup. **Publishing identity (person vs org) requires a Founder decision** (or explicit CONFIGURABLE default).

**Verdict:** **CONDITIONAL GO FOR SOCIAL S1 — EXTERNAL SETUP REQUIRED**

---

## P1 Decision Context

| Item | P1 | S0 |
|------|----|----|
| Recommended engine | Social | Confirmed as next slice target |
| First slice | LinkedIn Manual Publisher | Confirmed |
| Social score | 4.22 | Context only |
| Implementation blockers | 3 | **3** (IB-01..03) — see Blocker Register |
| External setup | 3 | **3** core (ES-01..03); +1 if org (ES-04) |
| Paid tools | 0 | **0** confirmed |
| Domain dependency | NO | **NO** confirmed |
| Measurement | PARTIAL | **PARTIAL** confirmed |

---

## Current Repository Readiness

**PARTIAL** — see `S0_REPOSITORY_READINESS.md`.

- Editorial + Publishing gates: IMPLEMENTED  
- LinkedIn channel slot: PARTIAL / PLACEHOLDER (`NOT_IMPLEMENTED`)  
- Social Engine / Marketing OS LinkedIn adapter: NOT IMPLEMENTED  
- RevenueOS LinkedInPublisher: STALE / ADJACENT  

---

## Architecture Boundary

**DEFINED** — see `S0_SOCIAL_ARCHITECTURE_BOUNDARY.md`.

Compatible with Architecture v2.2: Editorial → Publishing → Social → LinkedIn Adapter → API. Publishing remains job/orchestration owner; Social owns platform adapter concerns.

---

## LinkedIn External Requirements

**PARTIAL / NOT fully ready for live calls** — see `S0_LINKEDIN_EXTERNAL_REQUIREMENTS.md`.

- Member path: SUPPORTED (`w_member_social`) — EXTERNAL VERIFIED 2026-08-11  
- Org path: SUPPORTED + REQUIRES ADMIN AUTHORITY (`w_organization_social`) — EXTERNAL VERIFIED  
- Partner/product approval latency for org Marketing APIs: EXTERNAL VERIFICATION REQUIRED  

---

## Personal vs Organization Publishing

| Dimension | Person | Organization |
|-----------|--------|--------------|
| Business | Founder voice | Brand page voice |
| API | Share on LinkedIn / member scopes | Community Management Posts + org scope |
| Auth | Member OAuth | Org scope + page roles |
| Ops | Founder account | Page admin attestation |
| S1 friction | Lower | Higher |

**Publishing Identity:** **FOUNDER DECISION REQUIRED** (recommend CONFIGURABLE adapter; S1 may start member-only).

---

## OAuth Architecture

**DEFINED** (ownership) / **PARTIAL** (implementation) — `docs/security/S0_LINKEDIN_AUTH_SECURITY.md`.

AUTHENTICATION OWNER = Founder · TOKEN OWNER = env/vault · TOKEN CONSUMER = adapter · content approval ≠ credential authority.

---

## Token / Secret Ownership

Credential Storage: **REQUIRES SETUP**. Never commit secrets; never paste into Cursor.

---

## Publishing Contract

Proposed S1: text (+ optional link), manual, human-approved, LinkedIn-only — `S0_LINKEDIN_PUBLISHING_CONTRACT.md`. Media / schedule / analytics deferred.

---

## Human Approval Boundary

| Gate | Result | Evidence |
|------|--------|----------|
| AI not editorial approver | PASS | `editorial_approval.py` FDR |
| approved ≠ auto-published | PASS | Publishing requires separate human `manual_publish` |
| Human publish command | PASS | `is_human_requester` |
| No autonomous LinkedIn in S1 | PASS (policy) | S0 scope |

---

## Measurement Boundary

**PARTIAL** — operational publish metrics OK for S1; marketing analytics deferred — `S0_MEASUREMENT_BOUNDARY.md`.

---

## Tool / Cost Assessment

**Paid Tools Required Now: 0** — official LinkedIn API only — `S0_LINKEDIN_TOOLCHAIN.md`.

---

## Blocker Register

See `S0_BLOCKER_REGISTER.md`. Counts reconciled with P1; brand-page item is identity-conditional (ES-04).

---

## External Setup Checklist (Founder — outside Cursor)

Do **not** paste secrets into chat.

1. LinkedIn Developer account  
2. LinkedIn application  
3. Enable **Share on LinkedIn** (member) and/or Community Management products as required for chosen identity  
4. Configure OAuth redirect URI(s) for the chosen auth flow  
5. Complete OAuth; place **client ID / client secret / access token** only in local env or vault  
6. If organization: confirm page admin role and org URN  
7. Optionally set person URN for member posts  

---

## S1 Test Strategy

See `S0_LINKEDIN_TEST_STRATEGY.md`. Fake provider; no live LI in unit tests.

**Sentinel (S0):** Feature/API/DB/Architecture/Frozen contract/Credentials/Paid tools changes: **0**.  
Focused: 35 passed. Full: 388 passed / 8 failed / 4 errors (historical). New regressions: **0**.

---

## Risks

| Risk | Mitigation |
|------|------------|
| Org API access friction | Prefer member for first live path or isolate behind mock until ES complete |
| Stale RevenueOS UGC client | Do not silently adopt as Marketing SoT |
| Token leak | Env/vault; redaction tests |
| Duplicate posts | Idempotency on `publishing_job_id` |
| Scope creep (media/analytics) | S1 contract freeze |

---

## S1 Proposed Scope

**LinkedIn Manual Publisher:** human-approved content only → human publish → Publishing job → Social/LinkedIn adapter → text (+ optional link); one identity type; no schedule; no media upload; no analytics ingestion; no AI autonomous publish; fake provider in tests; live calls only after external setup.

---

## GO / NO-GO Assessment

| Gate | Status |
|------|--------|
| 1 Architecture boundary clear | PASS |
| 2 Frozen Publishing compatible | PASS |
| 3 Editorial approval preserved | PASS |
| 4 Human publish preserved | PASS |
| 5 LinkedIn API path verified or mock-isolated | PASS (verified + mock until setup) |
| 6 Credential ownership defined | PASS |
| 7 No secrets committed | PASS |
| 8 Identity decided OR configurable | CONDITIONAL (decision required; configurable design OK) |
| 9 External setup enumerated | PASS |
| 10 No paid tool required | PASS |
| 11 Test strategy exists | PASS |
| 12 No production deploy in S0 | PASS |

**Classification:** **CONDITIONAL GO**

---

## Founder Decisions Required

1. **FD-01:** Publish as **PERSON**, **ORGANIZATION**, or **CONFIGURABLE** (with S1 default).  
2. *(Optional)* Accept S1 text-only (+ optional link) vs require media in first slice — recommended: defer media.

**Count:** **1** hard decision (identity); media deferral recommended default without blocking if Founder accepts.

---

## Cross-Agent Conflicts

**0** — ATLAS/HERMES/NOVA/CIPHER/LEDGER/PULSE/SENTINEL aligned on CONDITIONAL GO; org access latency marked EXTERNAL VERIFICATION REQUIRED without blocking member-path design.

---

## Artifact index

| Doc |
|-----|
| `docs/marketing/social/S0_SOCIAL_ARCHITECTURE_BOUNDARY.md` |
| `docs/marketing/social/S0_REPOSITORY_READINESS.md` |
| `docs/marketing/social/S0_LINKEDIN_PUBLISHING_CONTRACT.md` |
| `docs/security/S0_LINKEDIN_AUTH_SECURITY.md` |
| `docs/marketing/social/S0_LINKEDIN_EXTERNAL_REQUIREMENTS.md` |
| `docs/marketing/social/S0_LINKEDIN_TOOLCHAIN.md` |
| `docs/marketing/social/S0_MEASUREMENT_BOUNDARY.md` |
| `docs/marketing/social/S0_BLOCKER_REGISTER.md` |
| `docs/marketing/social/S0_LINKEDIN_TEST_STRATEGY.md` |
| `docs/marketing/social/S0_LINKEDIN_READINESS_DECISION.md` (this file) |
