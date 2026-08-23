# S0 — Blocker Register (Social / LinkedIn)

**Sprint:** SOCIAL S0  
**Date:** 2026-08-11  
**P1 claimed:** Implementation Blockers: 3 · External Setup Required: 3

---

## Reconciliation method

Locate P1 decision language, map each claim to repo/external evidence, then recount with unique IDs. Do not rubber-stamp “3”.

**P1 source:** `docs/marketing/P1_MARKETING_OS_PRIORITY_DECISION.md` (and related P1 packets) — Social blockers: LinkedIn app+OAuth not configured; Marketing OS LinkedIn adapter missing; brand page permission not attested. External: Developer App; OAuth/token vaulting; brand/org page permission.

---

## Register

| ID | Type | Description | Evidence | Owner | Resolution | Blocks S1? | Status |
|----|------|-------------|----------|-------|------------|------------|--------|
| IB-01 | Implementation | Marketing OS LinkedIn adapter not implemented (Publishing returns `NOT_IMPLEMENTED`) | `publishing_engine.py` CHANNEL_ADAPTERS | Eng / Social | Implement in S1 behind gates | YES (is the S1 work) | OPEN — expected |
| IB-02 | Implementation | Social Engine package / channel abstraction absent | No `src/tools/social_engine/` | Eng / Social | Introduce thin Social module in S1 | YES (is the S1 work) | OPEN — expected |
| IB-03 | Implementation | Marketing OS OAuth callback / token bind not implemented | No LI OAuth routes in Marketing OS; only `.env.example` keys | Eng / Security | S1 may start with operator-supplied token in env **or** minimal OAuth; design in Cipher doc | CONDITIONAL | OPEN |
| ES-01 | External | LinkedIn Developer account + application | Learn Share on LinkedIn | Founder | Create outside Cursor | YES for live publish | OPEN |
| ES-02 | External | Enable Share on LinkedIn (and/or Community Management products as needed) + OAuth | Learn docs 2026-08-11 | Founder | Portal configuration | YES for live publish | OPEN |
| ES-03 | External | Store access token / client secret in env or vault (never git/chat) | `.env.example`; vault adjacent | Founder + Ops | Secure config | YES for live publish | OPEN |
| ES-04 | External | If org identity: page admin role + `w_organization_social` (+ possible product access) | Posts API permissions | Founder | Page admin attestation | YES **if** org chosen | OPEN / CONDITIONAL |
| FD-01 | Founder decision | Person vs Organization publishing identity | External + business | Founder | Decide or keep CONFIGURABLE with S1 default | Soft-blocks identity choice; not architecture | OPEN |
| ST-01 | Stale risk | RevenueOS `LinkedInPublisher` UGC path vs Marketing OS SoT | `revenue_os/integrations/social_publisher.py` | Eng | Do not silently reuse as Marketing SoT | No if ignored | OPEN (governance) |

---

## Corrected counts (S0)

| Category | P1 said | S0 corrected | Why |
|----------|---------|--------------|-----|
| Implementation blockers | 3 | **3** (IB-01..03) | Aligned; IB-03 is OAuth/bind missing (code), not “brand page” |
| External setup | 3 | **3 core** (ES-01..03); **+1 conditional** (ES-04) if org | P1’s “brand page permission” is identity-conditional → ES-04 |
| Founder decisions | (implicit) | **1** (FD-01) | Explicit identity decision |

**Note:** IB-01/IB-02 are “blockers” only in the sense that S1 must implement them — they do **not** make S0 a NO-GO; they **are** S1 scope. True **pre-S1 external** blockers for live LinkedIn are ES-01..03 (+ ES-04 if org).

**S0 Implementation Blockers (precluding unblocked live publish without work):** treat **IB-01..03 + ES-01..03** as the readiness gap; for terminal count use:

- **Implementation Blockers: 3** (IB-01..03)  
- **External Setup Items: 3** (ES-01..03) with ES-04 conditional  
- Or expanded external **4** if Founder chooses Organization.

Terminal output uses: Implementation Blockers **3**, External Setup Items **3** (member path) / note org adds ES-04.
