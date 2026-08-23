# S0-R — Blocker Register Revalidation (HERMES)

**Sprint:** SOCIAL S0-R — LinkedIn Readiness Revalidation  
**Date:** 2026-08-13  
**Canonical prior register:** `docs/marketing/social/S0_BLOCKER_REGISTER.md`  
**Mode:** REVALIDATION ONLY — no LinkedIn implementation

---

## Method

Re-checked each S0 blocker against **current** repository/configuration evidence. Documentation alone is insufficient for READY.

---

## Implementation blockers

### IB-01 — Marketing OS LinkedIn adapter not implemented

| Field | Value |
|-------|--------|
| **Original issue** | Publishing `linkedin` channel returns `NOT_IMPLEMENTED` |
| **Current evidence** | `src/tools/publishing_engine.py`: `ADAPTERS[CHANNEL_LINKEDIN] = _adapter_not_implemented(...)`; adapter returns `status: NOT_IMPLEMENTED`, `external_api_called: False`. No Marketing OS LinkedIn adapter module. |
| **Current status** | **OPEN** (unchanged) — **MISSING** implementation |
| **Owner** | Eng / Social |
| **Blocks S1?** | **YES** — this **is** core S1 work (does not make S0-R a NO-GO by itself) |

### IB-02 — Social Engine package / channel abstraction absent

| Field | Value |
|-------|--------|
| **Original issue** | No `src/tools/social_engine/` |
| **Current evidence** | `ls src/tools/social_engine` → absent. `CHANNEL_OWNERS[linkedin] = "Social Engine"` remains a ownership label only. |
| **Current status** | **OPEN** (unchanged) — **MISSING** |
| **Owner** | Eng / Social |
| **Blocks S1?** | **YES** — S1 must introduce thin Social module |

### IB-03 — Marketing OS OAuth callback / token bind not implemented

| Field | Value |
|-------|--------|
| **Original issue** | No LinkedIn OAuth routes; only `.env.example` key names |
| **Current evidence** | No OAuth LinkedIn routes under Marketing OS routers. `.env.example` still documents `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PERSON_URN` (comments). No `LINKEDIN_CLIENT_*` binding routes. Security ownership model remains in `docs/security/S0_LINKEDIN_AUTH_SECURITY.md` (design only). |
| **Current status** | **OPEN** (unchanged) — **PARTIAL** design / **MISSING** code |
| **Owner** | Eng / Security |
| **Blocks S1?** | **CONDITIONAL** — S1 may start with operator-supplied token in env **or** minimal OAuth; still unresolved |

---

## External setup items

### ES-01 — LinkedIn Developer account + application

| Field | Value |
|-------|--------|
| **Original issue** | App must exist in LinkedIn Developer Portal |
| **Current evidence** | No repo artifact proves app existence. Local `.env.local` has **0** non-placeholder `LINKEDIN_*` keys (only Cloudflare keys present). Process env has **0** `LINKEDIN_*` keys. Portal state **NOT VERIFIED**. |
| **Current status** | **OPEN** — **MISSING** (local) / **NOT VERIFIED** (portal) |
| **Owner** | Founder |
| **Blocks S1?** | **YES for live publish**; does not block S1 **code** behind fakes |

### ES-02 — Enable Share on LinkedIn (+ products) + OAuth

| Field | Value |
|-------|--------|
| **Original issue** | Product enablement + OAuth for chosen identity |
| **Current evidence** | Official Share on LinkedIn docs still require `w_member_social` via Share on LinkedIn product (re-fetched 2026-08-13). No local proof products enabled or OAuth completed. |
| **Current status** | **OPEN** — **MISSING** / **NOT VERIFIED** |
| **Owner** | Founder |
| **Blocks S1?** | **YES for live publish** |

### ES-03 — Store access token / client secret in env or vault

| Field | Value |
|-------|--------|
| **Original issue** | Secrets only in env/vault; never git |
| **Current evidence** | `.gitignore` still ignores `.env` / `.env.*`. `.env.example` placeholders only. No LinkedIn secrets tracked. Local `.env.local` has **no** LinkedIn token values set. Vault binding for Marketing OS Social still not implemented. |
| **Current status** | **OPEN** — convention **PARTIAL**; live values **MISSING** → **REQUIRES SETUP** |
| **Owner** | Founder + Ops |
| **Blocks S1?** | **YES for live publish** |

### ES-04 — Org page admin + `w_organization_social` (conditional)

| Field | Value |
|-------|--------|
| **Original issue** | Required only if Organization identity chosen |
| **Current evidence** | Identity still **not ratified** (FD-01). Org path not attested. |
| **Current status** | **OPEN / CONDITIONAL** — **NOT VERIFIED** |
| **Owner** | Founder |
| **Blocks S1?** | **YES if org chosen**; N/A until FD-01 |

---

## Founder / governance

### FD-01 — Person vs Organization publishing identity

| Field | Value |
|-------|--------|
| **Original issue** | Founder must choose PERSON / ORGANIZATION / CONFIGURABLE |
| **Current evidence** | Searched `docs/governance` and social packs: **no ratified decision** since S0. No new FDR for LinkedIn identity. |
| **Current status** | **OPEN** — **FOUNDER LINKEDIN IDENTITY DECISION REQUIRED** |
| **Owner** | Founder |
| **Blocks S1?** | Soft-blocks identity wiring; full GO gate requires RATIFIED or CONFIGURABLE |

### ST-01 — RevenueOS `LinkedInPublisher` stale vs Marketing SoT

| Field | Value |
|-------|--------|
| **Original issue** | Do not silently reuse RevenueOS UGC path as Marketing SoT |
| **Current evidence** | `revenue_os/integrations/social_publisher.py` `LinkedInPublisher` still present; Marketing OS still does not call it for Publishing channel. |
| **Current status** | **OPEN** (governance) — **ACTIVE** adjacent / **STALE** for Marketing SoT |
| **Owner** | Eng |
| **Blocks S1?** | **NO** if ignored and Marketing adapter built fresh |

---

## Disposition summary

| ID | Status | Resolved in S0-R? |
|----|--------|-------------------|
| IB-01 | OPEN | **No** |
| IB-02 | OPEN | **No** |
| IB-03 | OPEN | **No** |
| ES-01 | OPEN | **No** |
| ES-02 | OPEN | **No** |
| ES-03 | OPEN | **No** |
| ES-04 | OPEN / CONDITIONAL | **No** |
| FD-01 | OPEN | **No** |
| ST-01 | OPEN (governance) | **No** |

**Previous Implementation Blockers: 3**  
**Resolved Implementation Blockers: 0**  
**Implementation Blockers Remaining: 3**

**Previous External Setup Items: 3**  
**External Setup Items Remaining: 3** (+ ES-04 conditional)

**Net change since Social S0:** R1A–R1F cleanup improved platform hygiene; **did not** resolve Social/LinkedIn blockers.
