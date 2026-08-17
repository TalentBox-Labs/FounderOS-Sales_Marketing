# P1 — Marketing OS Priority Decision Packet

**Sprint:** P1 — Marketing OS Priority Review (Post SEO Baseline)  
**Date:** 2026-08-11  
**Governance:** Code Changes **0** · Architecture **UNCHANGED** · M-Series / SEO Readiness v1.0 / Technical SEO v1.0 **UNCHANGED** · Production **UNCHANGED** · Domain **UNCHANGED** · Paid Tools Approved **0**

Supporting analyses: `P1_ENGINE_DEPENDENCY_MATRIX.md`, `P1_IMPLEMENTATION_COVERAGE.md`, `P1_MARKET_LEVERAGE.md`, `P1_ENGINEERING_COMPLEXITY.md`, `P1_SECURITY_PLATFORM_RISK.md`, `P1_COST_TOOLCHAIN_ANALYSIS.md`, `P1_MEASUREMENT_READINESS.md`.

---

## Executive Summary

After SEO Readiness v1.0 and Technical SEO v1.0 freeze, the highest next-step business leverage with the lowest dependency risk is **Social Engine**, starting with a **LinkedIn-only manual publisher** behind Editorial + Publishing.

Email lacks marketing list/consent SoT. Campaign is **PREMATURE** (insufficient real channels). SEO Phase 2 high-value work is **DOMAIN BLOCKED**.

**Recommended next engine: SOCIAL ENGINE**  
**Score margin vs #2 (SEO Phase 2): 1.28** — no founder tie-break required.

---

## Current Frozen Baselines

| Baseline | Status |
|----------|--------|
| Architecture v2.2 | FROZEN |
| M-Series | COMPLETE |
| Founder OS Website v1.0 | PRODUCTION BASELINE FROZEN |
| SEO Readiness Engine v1.0 | FROZEN |
| Technical SEO Engine v1.0 | FROZEN (10 families / 72 rules; robots PARTIAL accepted) |
| Production SEO activation | BLOCKED PENDING FUTURE DOMAIN |
| Future production domain | NOT YET RATIFIED |

---

## Candidate Comparison

| Candidate | Dep readiness | Coverage | Business horizon | Eng complexity | Security | Measurement | Domain effect |
|-----------|---------------|----------|------------------|----------------|----------|-------------|----------------|
| Social | READY (bounded) | NOT IMPLEMENTED + stubs PARTIAL | IMMEDIATE | Medium | Medium–High (OAuth) | PARTIAL | Low |
| Email | NOT READY | NOT IMPLEMENTED | MEDIUM | Highest | Highest (compliance) | NOT READY | Medium |
| Campaign | PREMATURE | NOT IMPLEMENTED | LONG-TERM | High | High (launch) | NOT READY | Low |
| SEO Phase 2 | DOMAIN BLOCKED | Phase 1 frozen; Phase 2 empty | LONG-TERM | Lower locally | Medium | DOMAIN BLOCKED | **Critical** |

---

## Dependency Evidence

See Atlas matrix.

- **Social:** Editorial + Publishing **IMPLEMENTED**; LinkedIn/Twitter/Instagram adapters **NOT_IMPLEMENTED**; Campaign/Email **not required** for LinkedIn S0.  
- **Email:** No subscriber/consent/unsubscribe/suppression; CRM contacts unsafe as SoT.  
- **Campaign:** Only website is a real owned path; Publishing social/email stubs fail → **PREMATURE**.  
- **SEO Phase 2:** GSC / indexing activation / organic KPIs **DOMAIN BLOCKED**.

---

## Implementation Evidence

See Hermes coverage.

- No Marketing OS `social_engine` / `email_engine` / `campaign_engine` packages.  
- Publishing channel registry stubs must not be counted as Social/Email completion.  
- RevenueOS `social_publisher` / SMTP nurture = **STALE/ADJACENT**.  
- SEO Phase 1 packages are **FROZEN** and complete for local analysis.

---

## Business Leverage

See Scout. Social converts frozen content pipeline (Content Studio → Editorial → Publishing → Website) into **external distribution** immediately. Email owns audience later. Campaign multiplies missing channels. SEO Phase 2 compounds after domain.

---

## Engineering Complexity

See Nova. Social S0 is medium (OAuth + adapter). Email is highest (DB + compliance + ESP). Campaign orchestration without channels wastes effort. SEO Phase 2 local work is easy but low leverage pre-domain.

---

## Security / Platform Risk

See Cipher. Email compliance risk dominates. Social OAuth/platform policy is manageable with human gates. Campaign accidental multi-channel launch risk is unacceptable without real adapters + launch gate. SEO activation remains blocked by design.

---

## Tool / Cost Risk

See Ledger. **Paid tools required now for Social LinkedIn S0: 0** (official LinkedIn API). Email production likely needs paid ESP later (not approved). SEO Phase 2 prefers free GSC after domain — no Ahrefs-class tools.

---

## Measurement Readiness

| Candidate | Status |
|-----------|--------|
| Social | PARTIAL |
| Email | NOT READY |
| Campaign | NOT READY |
| SEO Phase 2 | DOMAIN BLOCKED |

---

## Weighted Matrix

### Weights (fixed; not tuned to force a winner)

| Dimension | Weight |
|-----------|--------|
| Business Leverage | 20% |
| Time to Value | 15% |
| Dependency Readiness | 15% |
| Implementation Coverage | 10% |
| Automation Potential | 10% |
| Measurement Readiness | 10% |
| Revenue Proximity | 10% |
| Free-Tool Viability | 10% |

### Dimension scores (1–5)

| Dimension | Social | Email | Campaign | SEO Phase 2 |
|-----------|--------|-------|----------|-------------|
| Business Leverage | 5 | 4 | 3 | 3 |
| Time to Value | 4 | 2 | 1 | 2 |
| Dependency Readiness | 4 | 2 | 1 | 2 |
| Implementation Coverage | 3 | 2 | 1 | 4 |
| Automation Potential | 4 | 4 | 5 | 3 |
| Measurement Readiness | 3 | 2 | 1 | 1 |
| Revenue Proximity | 4 | 5 | 4 | 3 |
| Free-Tool Viability | 5 | 2 | 4 | 4 |
| **Weighted base** | **4.10** | **2.90** | **2.40** | **2.70** |

### Risk modifiers

Penalty = `0.12 × (score − 3)` per risk dimension (engineering complexity, platform risk, compliance risk); higher risk lowers total.

| Risk (1–5 high) | Social | Email | Campaign | SEO Phase 2 |
|-----------------|--------|-------|----------|-------------|
| Engineering complexity | 3 | 4 | 4 | 2 |
| External platform risk | 3 | 3 | 4 | 3 |
| Compliance risk | 2 | 5 | 4 | 2 |
| **Adjusted total** | **4.22** | **2.54** | **2.04** | **2.94** |

### Ranking

| Rank | Engine | Score |
|------|--------|-------|
| 1 | **Social Engine** | **4.22** |
| 2 | SEO Phase 2 | 2.94 |
| 3 | Email Engine | 2.54 |
| 4 | Campaign Engine | 2.04 |

**Margin #1 vs #2:** **1.28** (> 0.25) → no tie-break.

---

## Recommended Engine

**SOCIAL ENGINE**

---

## Why It Wins

Approved content already flows through Editorial and Publishing; Website is live; Social is the missing **distribution** surface. A LinkedIn-only manual slice reuses frozen Publishing contracts, needs **0** paid tools, is not domain-blocked, and produces immediate amplification without Campaign or Email.

---

## Why Others Wait

### Why Email waits
No marketing subscriber/consent/unsubscribe/suppression SoT; CRM contacts are unsafe; delivery is toy SMTP / unpaid ESP decision. Foundation work dominates before first responsible send.

### Why Campaign waits
**PREMATURE:** Publishing social/email adapters are `NOT_IMPLEMENTED`; website-only orchestration is already Publishing/Website territory. Campaign without real multi-channel destinations is premature centralization.

### Why SEO Phase 2 waits
Readiness + Technical SEO v1.0 already deliver local analysis. High-value Phase 2 (GSC, indexing activation, organic KPIs) is **DOMAIN BLOCKED** until Founder domain ratification. Marginal local SEO work is low leverage vs Social.

### Why Social still has setup (not “zero blockers”)
Marketing OS LinkedIn adapter, LinkedIn Developer App/OAuth vaulting, and brand-page publish permission attestation remain **external/engineering prerequisites** — not Campaign/Email/domain blockers.

---

## First Implementation Slice

**Name:** Social Engine S0 — LinkedIn Manual Publisher  

**Scope:**

1. Marketing OS LinkedIn channel adapter owned by Social Engine  
2. Wire Publishing `linkedin` adapter from `NOT_IMPLEMENTED` → real adapter result  
3. Preserve Editorial approval + human `manual_publish` gates  
4. Vaulted token/credential binding (no hardcoded secrets)  
5. Focused tests: stub removed, failure modes, no auto-schedule  

**Out of scope:** Twitter/IG/Facebook, Campaign Engine, Email, scheduler/Celery, paid aggregators, analytics dashboards, SEO changes.

**Blast radius:** Low — single channel; human-gated; no DB schema required for minimal slice if token config is env/vault.

---

## Required External Setup

1. LinkedIn Developer Application  
2. OAuth / access token (or equivalent) stored in vault/env — not committed  
3. Brand/organization page publish permission attested  

**Count: 3**

---

## Human Approval Boundary

- Editorial approval remains mandatory before publish job creation  
- Publishing `manual_publish` remains human-requested  
- No autonomous social posting in S0  
- No Campaign auto-launch  

---

## Risks

| Risk | Mitigation |
|------|------------|
| Dual path with RevenueOS `social_publisher` | Explicit Marketing OS ownership; do not silently call legacy as SoT |
| LinkedIn API/policy changes | Official API; narrow S0; human gate |
| Token leakage | Vault/env only; rotate |
| Scope creep to multi-network | Freeze S0 LinkedIn-only |

---

## Implementation Blockers (pre-S0)

1. LinkedIn app + OAuth not configured for Marketing OS  
2. Marketing OS LinkedIn adapter not implemented  
3. Brand page permission not attested  

**Count: 3** (all solvable without Campaign/Email/domain)

---

## Founder Decision

**Approve Social Engine as next Marketing OS engine**, with first slice **LinkedIn Manual Publisher (S0)**.

Optional later (separate decisions): Email foundation after consent model; SEO Phase 2 after domain ratification; Campaign after ≥1 additional live distribution channel.

**Production SEO activation:** remains **BLOCKED PENDING DOMAIN**.

---

## Verdict

**READY FOR FOUNDER PRIORITY DECISION**
