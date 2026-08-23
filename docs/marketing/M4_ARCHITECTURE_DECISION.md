# M4 — Architecture Decision: Deployment Boundaries

**Status:** DECIDED (architecture / governance only)  
**Sprint:** M4  
**Role:** Agent Atlas — Architecture  
**Date:** 2026-08-10  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
**Owned file:** this document only  
**Code / API / DB / runtime / deploy / git changes:** **NONE**

**Authoritative architecture:** [Architecture_v2.2.md](../architecture/Architecture_v2.2.md), [Marketing_OS_v2.2.md](../architecture/Marketing_OS_v2.2.md), [Platform_vs_OS_Boundaries.md](../architecture/Platform_vs_OS_Boundaries.md)  
**Frozen baselines:** Website Engine Core v1.0 (M2.5), Static Website Provider v1.0 (M3.5)  
**Prior Atlas validation:** [M4_ATLAS_ARCHITECTURE_VALIDATION.md](M4_ATLAS_ARCHITECTURE_VALIDATION.md)  
**M4 mode decision (peer):** [M4_DEPLOYMENT_DECISION.md](M4_DEPLOYMENT_DECISION.md)  
**M3.5 readiness:** [M3_5_M4_DEPLOYMENT_READINESS.md](M3_5_M4_DEPLOYMENT_READINESS.md), [M3_5_FREEZE_SUMMARY.md](M3_5_FREEZE_SUMMARY.md)

---

## 1. Decision

**Deployment remains outside Website Engine Core.**

Canonical chain (binding):

```text
Website Engine Core  →  Deployment Adapter  →  Hosting Platform
```

| Layer | Role | Inside Core? |
|-------|------|--------------|
| **Website Engine Core** | Content model, slug/URL, metadata, render, feeds, provider publish (`output/website/`) | **YES** (frozen v1.0) |
| **Deployment Adapter** | Package public subset; sync/upload/serve-intent hooks; host-agnostic deploy interface | **NO** — outside Core |
| **Hosting Platform** | Dumb static edge / docroot / TLS / DNS / optional CDN | **NO** — infrastructure, not OS Core |

**Hard rule:** Website Engine Core must **never** depend directly on a hosting platform (Netlify, Vercel, Cloudflare, AWS, nginx host APIs, etc.). Hosting is reached only through a Deployment Adapter owned as an extensibility surface under Website Engine, not as a Core contract.

---

## 2. Boundary statement

```text
Website Engine Core publishes local site artifacts; Deployment Adapter (outside Core) talks to Hosting Platforms; Core never imports or couples to a host.
```

---

## 3. Layer model (full Marketing OS context)

```text
Editorial Engine                 →  human approve (≠ publish, ≠ deploy)
        ↓
Publishing Engine                →  orchestration only (jobs / queue / channel / audit)
        ↓  (future channel invoke)
Website Engine Core v1.0         →  render + metadata + feeds + provider resolution
        ↓
Static Provider v1.0             →  filesystem write under output/website/ (no network, no host)
        ↓
Deployment Adapter (M5+)         →  OUTSIDE Core — host-agnostic hooks / packaging
        ↓
Hosting Platform (A/B/C/D…)      →  serve / edge / TLS / DNS (dumb relative to Marketing OS)
        ⋯ later ⋯
CMS WebsiteProvider (E)          →  alternate provider adapters; still not “host inside Core”
```

This matches Architecture v2.2 (Website Engine owns site + future deploy hooks; Publishing = orchestration) and Marketing OS v2.2 §4.4 (provider adapters shipped; CMS/deploy hooks future).

---

## 4. Ownership

| Concern | Owner | Not owner |
|---------|-------|-----------|
| Canonical website content / render / slug / metadata / feeds | **Website Engine Core** | Publishing, SEO, Social, Campaign |
| Local static publication (`output/website/`) | **Static Provider** (Website Engine adapter) | Hosting platforms |
| Deploy hooks / public-subset packaging / cache-invalidation **intent** | **Website Engine** (Deployment Adapter layer — outside Core freeze) | Publishing Engine |
| Deploy **transport** (rsync job, CI push, container roll) | **Automation Platform** | Website Engine Core business contracts |
| Deploy secrets, TLS material, host credentials | **Shared Platform** | Core / Static Provider / Publishing |
| Docroot, CDN, DNS, TLS termination, paid host APIs | **Hosting Platform / ops** | Core; Publishing |
| Publish job state machine | **Publishing Engine** | Website Engine |
| SEO scoring | **SEO Engine** | Site deploy |

Per [Platform_vs_OS_Boundaries.md](../architecture/Platform_vs_OS_Boundaries.md): website render / slug / deploy / site publish → Website Engine; Automation may execute deploy transport; SEO must not own site deploy.

---

## 5. Responsibilities

### 5.1 Website Engine Core (frozen — do not expand in place)

- Own business decisions for the Founder website surface.
- Resolve `WebsiteProvider` via registry; emit channel-compatible publish results.
- Remain **provider-independent**: no host vendor types in Core request/result contracts.
- **Must not:** call hosting APIs, embed CDN/TLS/DNS logic, or require a paid host to succeed at local publish.

### 5.2 Static Provider v1.0 (frozen)

- Write local artifacts only (`external_http=False`).
- Explicit non-goals (M3.5): deploy, CDN, cache invalidation, CMS network publish.
- Success path remains “no external HTTP, no deploy.”

### 5.3 Deployment Adapter (outside Core — M5+)

- Consume Core/Static outputs (or a filtered public subset).
- Expose a **host-agnostic** hook seam (sync / git publish / upload / image package — mode-dependent).
- Translate Website Engine deploy intent into host-specific operations **behind** the adapter boundary.
- May use network; that network belongs to the adapter/Automation path, **not** to Static Provider publish.
- **Must not:** redefine Core v1.0 / Static v1.0 contracts without a new baseline (v1.1+).

### 5.4 Hosting Platform

- Serve static files (or later accept CMS payload via a separate provider adapter).
- Provide TLS/DNS/edge as infrastructure.
- Remain swappable (self-host ↔ git-host ↔ managed static) without rewriting Website Engine Core.

### 5.5 Publishing Engine

- Orchestrate jobs and channels only.
- **Must not** own docroots, deploy CLIs, host credentials, or hosting SDKs.

---

## 6. Provider independence

| Rule | Status |
|------|--------|
| Core contracts stay host-agnostic | **PASS** |
| Static Provider is one publication adapter, not the forever public host | **PASS** |
| Deployment Adapter isolates host vendors from Core | **PASS** |
| Switching hosting modes must not force Core rewrite | **PASS** |
| Future CMS (WordPress/Ghost) = later `WebsiteProvider`s, not Core hosting embeds | **PASS** |
| No paid vendor required by architecture for first public static path | **PASS** |

**Provider Independence: PASS**

---

## 7. Future extensibility

```text
Now (frozen):
  Core → Static Provider → output/website/

Next (M5+):
  Core → Static Provider → Deployment Adapter → Hosting (static self-host primary; git secondary)

Later:
  Core → WebsiteProvider (WP/Ghost/…)  [and/or]  Deployment Adapter → other hosts
```

| Extension | How it stays legal |
|-----------|--------------------|
| New host (A↔B↔C, optional D) | New or swapped **Deployment Adapter** implementation; Core unchanged |
| New CMS | New **WebsiteProvider** registration; same Core protocol; not a Core host dependency |
| Automation | Transport only; no business decisions in Automation Platform |
| Core/Static contract growth | Requires **new baseline version** + governance — not silent freeze edits |

Reversibility: changing hosts or adding CMS later must **not** relocate website ownership out of Website Engine or move hosting into Publishing.

---

## 8. Compliance checks (Architecture v2.2)

| Check | Result |
|-------|--------|
| Deploy outside Website Engine Core | **PASS** |
| Website Engine owns future deploy hooks (adapter layer) | **PASS** |
| Website Engine Core never depends directly on hosting platform | **PASS** |
| Publishing remains orchestration-only | **PASS** |
| Static first; CMS deferred | **PASS** |
| Core v1.0 / Static v1.0 not silently expanded | **PASS** |
| Automation = transport; Shared = secrets | **PASS** |
| Human production-publish gates retained (deploy does not bypass) | **PASS** |
| Boundary violations in destination model | **0** |

---

## 9. Explicit non-decisions (this document)

This Atlas architecture decision does **not**:

- Implement deploy hooks or choose a paid vendor SKU.
- Open Core v1.1 / Static v1.1.
- Wire Publishing `_adapter_website` to Website Engine (separate bridge).
- Authorize WordPress/Ghost as the first public path.

Mode selection among public-static candidates is recorded in [M4_DEPLOYMENT_DECISION.md](M4_DEPLOYMENT_DECISION.md); this file freezes the **boundary law** those modes must obey.

---

## 10. Attestation

| Item | Value |
|------|-------|
| Decision file | `docs/marketing/M4_ARCHITECTURE_DECISION.md` |
| Architecture | v2.2 FROZEN |
| Core baseline | Website Engine Core v1.0 FROZEN |
| Provider baseline | Static Website Provider v1.0 FROZEN |
| Application / deploy actions | **NONE** |

---

## FINAL

```text
Architecture: PASS

Boundary: Website Engine Core → Deployment Adapter → Hosting Platform; Core never depends directly on a host.
```
