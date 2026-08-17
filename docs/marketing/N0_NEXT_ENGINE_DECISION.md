# N0 — Next Marketing Engine Decision (Founder Packet)

**Sprint:** N0 — Marketing Engine Priority & Dependency Gate  
**Date:** 2026-08-10  
**Status:** RECOMMENDATION ONLY — **not authorized for implementation**  
**Governance:** Architecture / Runtime / DB / API / Production **UNCHANGED** · Code changes **0** · M-Series **FROZEN**

---

## Executive Summary

Four Marketing OS engines were scored from **repository evidence**, not roadmap hope. **SEO Engine** is the only candidate with hard dependencies already satisfied by Founder OS Website v1.0, partial runtime coverage, free first-slice path, and measurable local KPIs. **Social** and **Email** lack Marketing OS engines and force external platform/PII risk. **Campaign** should wait until distribution engines exist.

**Recommended next engine: SEO Engine** (Founder must still authorize).

---

## Repository Evidence

| Source | Role |
|--------|------|
| Website v1.0 production baseline | Live owned asset |
| `website_engine/metadata.py` | Metadata emit ≠ SEO scoring |
| Static sitemap/RSS | Search surfaces live |
| `input/*/02_SEO_Plan.md` + generation crew | SEO planning artifacts |
| `runner_api_routers/seo.py` + `revenue_os/models/seo.py` | Manual keyword/rank log |
| `publishing_engine.py` | Social/newsletter `NOT_IMPLEMENTED` |
| `social_publisher.py` / `EmailNotifier` | Legacy/adjacent — not Marketing OS engines |
| Architecture v2.2 / Marketing OS v2.2 | Destination ownership map |

Agent packs:  
[N0_ENGINE_DEPENDENCY_MATRIX.md](N0_ENGINE_DEPENDENCY_MATRIX.md) · [N0_IMPLEMENTATION_COVERAGE.md](N0_IMPLEMENTATION_COVERAGE.md) · [N0_ENGINEERING_COMPLEXITY.md](N0_ENGINEERING_COMPLEXITY.md) · [N0_SECURITY_EXTERNAL_RISK.md](N0_SECURITY_EXTERNAL_RISK.md) · [N0_TOOLCHAIN_COST_ANALYSIS.md](N0_TOOLCHAIN_COST_ANALYSIS.md) · [N0_MARKET_LEVERAGE.md](N0_MARKET_LEVERAGE.md) · [N0_MEASUREMENT_READINESS.md](N0_MEASUREMENT_READINESS.md) · [N0_PRODUCTION_DOMAIN_IDENTITY.md](../operations/N0_PRODUCTION_DOMAIN_IDENTITY.md)

---

## Candidate Engines

1. SEO Engine  
2. Social Engine  
3. Email Engine  
4. Campaign Engine  

---

## Dependency Matrix

See Atlas doc. Summary: SEO hard-deps **ready**; Social/Email/Campaign hard-deps **not ready**.

---

## Implementation Coverage

| Engine | Classification |
|--------|----------------|
| SEO | **PARTIAL** |
| Social (Marketing OS) | **NOT IMPLEMENTED** |
| Email (Marketing OS) | **NOT IMPLEMENTED** (adjacent sketches only) |
| Campaign | **NOT IMPLEMENTED** |

---

## Market Leverage

Beacon averages (1–5): SEO **4** · Social **3** · Email **4** · Campaign **3** — SEO unique in compounding the **just-shipped** website.

---

## Engineering Complexity

Nova (1–5, higher = harder): SEO **2** · Social **4** · Email **5** · Campaign **4**

---

## Security Risk

Cipher (1–5): SEO **1** · Social **5** · Email **4** · Campaign **3**

---

## Tool / Cost Risk

Ledger (1–5 cost/lock-in risk now): SEO **1** · Social **3** · Email **4** · Campaign **2**  
**Paid tools required now for SEO v0: 0**

---

## Measurement Readiness

Sentinel (1–5): SEO **3** · Social **2** · Email **2** · Campaign **1**

---

## SEO vs Social

| Lens | SEO-first | Social-first |
|------|-----------|--------------|
| Owned asset compounding | **Strong** (live site) | Weak |
| Discoverability | Search + AI-answer logs | Network feeds |
| Website leverage | Direct | Indirect referral |
| External API dependency | Optional | **Mandatory** |
| Feedback velocity | Slower | Faster |
| Founder visibility | Medium | **High** |
| Fit after M-Series | **Best** | Premature without OAuth/adapters |

**Result:** SEO-first wins on dependency readiness + owned asset + risk. Social remains next distribution candidate after SEO baseline / Brand readiness.

---

## Email Readiness

| Prerequisite | Present? |
|--------------|----------|
| Marketing subscriber model | **NO** |
| Consent model | **NO** |
| Unsubscribe handling | **NO** (docs only) |
| Delivery provider production wire | **NO** |
| Audience source SoT | **NO** (RevenueOS nurture ≠ Marketing Email) |

**Missing prerequisites:** list SoT, consent/unsubscribe, ESP, Marketing OS Email package, human send gate.

---

## Campaign Dependency

**WAIT FOR DISTRIBUTION ENGINES.**  
Campaign without Social/Email is orchestration without execution (Website already covered by Publishing/Website path).

---

## Production Domain Observation

Hostname `founderos-staging.pages.dev` is **temporarily acceptable** technical production; **custom domain recommended** (CNAME pending for `workcrew.ai` / `blog.workcrew.ai`). Creates SEO/canonical/branding ambiguity until resolved. **No DNS change in N0.**

---

## Weighted Decision Matrix

### Weighting rationale

Benefit weights emphasize **shipping something useful on assets that already exist**:

| Benefit factor | Weight | Rationale |
|----------------|-------:|-----------|
| Dependency Readiness | 0.25 | Avoid blocked engines |
| Business Leverage | 0.20 | Must matter commercially |
| Time to Value | 0.20 | Founder feedback loop |
| Owned Asset Value | 0.15 | Prefer compounding ownership |
| Automation Potential | 0.10 | Secondary |
| Measurement Readiness | 0.10 | Must falsify success |

Risk penalties (subtract):

| Risk | Weight | Rationale |
|------|-------:|-----------|
| Engineering Complexity | 0.15 | Delivery cost |
| External Platform Risk | 0.15 | Outage/suspension |
| Cost Risk | 0.10 | Free/OSS policy |

### Input scores (1–5)

| Factor | SEO | Social | Email | Campaign |
|--------|----:|-------:|------:|---------:|
| Business Leverage | 4 | 5 | 4 | 3 |
| Time to Value | 5 | 3 | 2 | 2 |
| Dependency Readiness | 5 | 2 | 1 | 1 |
| Automation Potential | 4 | 4 | 4 | 3 |
| Measurement Readiness | 3 | 2 | 2 | 1 |
| Owned Asset Value | 5 | 2 | 4 | 2 |
| Eng. Complexity (risk) | 2 | 4 | 5 | 4 |
| External Risk | 1 | 5 | 4 | 3 |
| Cost Risk | 1 | 3 | 4 | 2 |

### Benefit score

`0.20L + 0.20T + 0.25D + 0.10A + 0.10M + 0.15O`

| Engine | Benefit |
|--------|--------:|
| SEO | **4.50** |
| Social | **3.00** |
| Email | **2.65** |
| Campaign | **1.95** |

### Net score (benefit − risk penalties)

| Engine | Net |
|--------|----:|
| **SEO** | **3.95** |
| Social | **1.35** |
| Email | **0.90** |
| Campaign | **0.85** |

Terminal display scores = Benefit (1 decimal).

---

## Recommended Engine

**SEO Engine**

## Why It Wins

Live Website v1.0 + metadata/feeds + SEO plans + manual rank API give a **ready, free, low-risk** first formal Marketing OS engine that compounds owned search assets without OAuth or ESP.

## Why The Others Wait

| Engine | Wait reason |
|--------|-------------|
| Social | Adapters/OAuth unimplemented; high platform risk |
| Email | No consent/list/ESP prerequisites |
| Campaign | No multi-channel distribution engines to orchestrate |

---

## Required Prerequisites (SEO authorization)

1. Founder Accept of **SEO Engine** as next build (this packet).  
2. Keep Website/Publishing/Deploy baselines frozen.  
3. Prefer resolving branded DNS before treating `workcrew.ai` as crawl host of record (soft).  
4. Human gate for any SEO policy that mutates published content.

---

## Proposed First Implementation Slice (future — not N0)

- Formalize Marketing OS SEO package: readiness/score over approved bundles + `output/website/` HTML  
- Reports only (no auto production mutate)  
- Reuse `/api/v1/seo` manual ranks; optional later GSC read  
- Tests + baseline freeze sprint before Social

---

## Founder Decision Required

| Decision | Options |
|----------|---------|
| Next engine | **Authorize SEO Engine** / Choose Social / Choose Email / Choose Campaign / Defer |
| Domain | Accept temporary pages.dev / Prioritize custom domain cutover (ops) |
| Paid tools | Remain **0** for SEO v0 |

**N0 does not implement.**

---

## Cross-Agent Conflicts

**0**
