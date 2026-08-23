# M4 — Atlas Architecture Validation

**Status:** ANALYSIS ONLY — governance / architecture decision validation  
**Sprint:** M4 (Website deployment-mode decision)  
**Role:** Agent Atlas — Architecture  
**Date:** 2026-08-10  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
**Owned file:** this document only  
**Code / API / DB / runtime / git changes:** **NONE**

**Authoritative architecture:** [Architecture_v2.2.md](../architecture/Architecture_v2.2.md), [Marketing_OS_v2.2.md](../architecture/Marketing_OS_v2.2.md)  
**Frozen baselines:** [M2_5_WEBSITE_ENGINE_BASELINE.md](M2_5_WEBSITE_ENGINE_BASELINE.md) (Website Engine Core v1.0), [M3_5_STATIC_PROVIDER_BASELINE.md](M3_5_STATIC_PROVIDER_BASELINE.md) (Static Website Provider v1.0)  
**Prior readiness:** [M3_5_M4_DEPLOYMENT_READINESS.md](M3_5_M4_DEPLOYMENT_READINESS.md), [M2_5_WEBSITE_PROVIDER_READINESS.md](M2_5_WEBSITE_PROVIDER_READINESS.md)

---

## 1. Mission

Validate that any M4 deployment-mode decision (and subsequent M5 deploy-hook work) respects Architecture v2.2 and frozen Website Engine baselines:

1. Website Engine owns website publish + future deploy hooks (destination ownership).
2. Deploy strategy must not place hosting inside Publishing Engine.
3. Deploy must not expand frozen Website Engine Core / Static Provider contracts without a new baseline.
4. Deployment remains outside Website Engine Core (Core = content / render / provider; Deploy = separate M5 layer / hooks).
5. Future extensibility remains open (static first; CMS adapters later).

---

## 2. Evidence base

| Source | Binding statement for M4 |
|--------|--------------------------|
| Architecture v2.2 §6 | Website Engine **SHIPPED** (Core + Static Provider); future = **Deploy mode decision (M4)**; **CMS adapters later** |
| Marketing OS v2.2 §4.3 | Publishing Engine = orchestration only; does **not** own website render |
| Marketing OS v2.2 §4.4 | Website Engine owns content model, slug/URL, metadata, render, sitemap/RSS, provider adapters (static shipped), **future CMS/deploy hooks** |
| Marketing OS v2.2 §5 | Destination flow: Publishing orchestrates → Website Engine is the website channel destination |
| Platform_vs_OS_Boundaries | Website render / slug / deploy / site publish → **Website Engine**; Automation may execute deploy transport; SEO must not own site deploy |
| M2.5 Core baseline | Core v1.0 **does not** own deploy / cache invalidation; WordPress/Ghost not in Core; interfaces frozen — changes require new baseline |
| M3.5 Static baseline | Static Provider v1.0 = filesystem write only; **no** deploy / CDN / network; `external_http=False`; CMS adapters not registered |
| M3.5 freeze summary | M4 = **deployment-mode decision**; hooks under Website Engine; **not** Publishing Engine work |
| M3.5 / M4 deployment readiness | Candidate modes A–C (static public); D optional; E CMS deferred; deploy hook owner = Website Engine; no paid vendor chosen |

---

## 3. Layer model (binding for M4 → M5)

```text
Publishing Engine          →  orchestration / jobs / channel routing / audit
        ↓ (channel invoke, future bridge)
Website Engine Core v1.0   →  content model, slug/URL, metadata, render, feeds, publish result
        ↓
Static Provider v1.0       →  local artifact write under output/website/ (no host, no network)
        ↓
M5 Deploy layer / hooks    →  package public subset + sync/serve/upload via Website Engine hooks
        ↓                         Automation Platform = transport only
Host / edge (A/B/C/D)      →  dumb static serving; secrets in Shared Platform
        ⋯ later ⋯
CMS adapters (E)           →  future WebsiteProvider implementations (WP/Ghost); not first path
```

| Layer | In frozen Core / Static? | Owner |
|-------|--------------------------|-------|
| Content / render / provider publish | **YES** (M2.5 / M3.5) | Website Engine |
| Deploy / hosting / CDN / TLS / DNS | **NO** | Website Engine **hooks** (M5); Automation transport; Shared secrets |
| Publish job state machine | **NO** (never Website) | Publishing Engine |
| CMS runtime / DB | **NO** | Future provider adapters only |

**Verdict on layering:** Deployment is correctly modeled as **outside Website Engine Core**. M4 decides mode; M5 implements hooks without absorbing hosting into Core contracts or into Publishing.

---

## 4. Constraint checks

### 4.1 Website Engine owns website publish + future deploy hooks — PASS

| Claim | Evidence |
|-------|----------|
| Site publish destination | Marketing OS v2.2 §4.4; Architecture v2.2 engine table |
| Deploy hooks destination | Marketing OS v2.2 “future CMS/deploy hooks”; Platform_vs_OS_Boundaries deploy → Website Engine |
| M4 role | Architecture v2.2: “Deploy mode decision (M4)” — decision, not Core expansion |

No document assigns website hosting ownership to Publishing, SEO, Social, or Campaign.

### 4.2 Deploy strategy must not put hosting inside Publishing Engine — PASS

| Publishing owns | Publishing must not own |
|-----------------|-------------------------|
| Jobs, queue, channel selection, state machine, audit, human production-publish gate | Docroot, static serve, CDN, TLS, DNS, deploy CLI, image registry, CMS host |

M3.5 / M4 readiness and M3.5 freeze summary explicitly: M4 is **not** Publishing Engine work. Channel bridge (`publish_from_job`) remains Website Engine–side; orchestration stays Publishing-side.

### 4.3 Deploy must not expand frozen Core / Static contracts without new baseline — PASS (constraint affirmed)

Frozen surfaces that M4/M5 must **not** silently mutate:

| Baseline | Frozen scope (do not expand in-place) |
|----------|----------------------------------------|
| Website Engine Core v1.0 | Content model, `WebsiteProvider` protocol fields, slug/URL, metadata, render, feeds, `WebsitePublishResult` / channel shape, public `__all__` |
| Static Website Provider v1.0 | Registration (`static`/`stub`), input/output artifact set, path safety, idempotency, `external_http=False`, error/rollback boundary |

**Rule (from M2.5 / M3.5 freeze texts):** changes require a **new baseline version** (e.g. Core v1.1 / Static v1.1) and governance note — not silent edits.

M4 decision documents and M5 deploy hooks must be additive layers (new modules / hook interfaces / packaging), not redefinition of Core request/result fields unless a new baseline is opened.

### 4.4 Deployment remains outside Website Engine Core — PASS

| Concern | Core / Static today | Deploy (M5) |
|---------|---------------------|-------------|
| Markdown → HTML, slug, metadata, feeds | Implemented & frozen | Consumes artifacts only |
| Write `output/website/` | Static Provider v1.0 | May package/filter that tree |
| Public serve / sync / upload | Explicitly out of scope | Hook interface + Automation transport |
| Cache invalidation | Not in Core | Website Engine ownership; implement with deploy layer |
| `external_http` | Always `false` for static success path | Deploy transport may use network **outside** Static Provider publish path |

Static Provider success messages and baselines remain “no external HTTP, no deploy.” Deploy is a **separate** step after local publication, not an inlined mutation of `StaticWebsiteProvider.publish`.

### 4.5 Future extensibility (CMS later, static first) — PASS

| Path | Status | Constraint |
|------|--------|------------|
| Static first | **Chosen & shipped** (M2.5 recommendation → M3/M3.5 freeze) | First public reachability uses static artifacts |
| Modes A/B/C (+ optional D) | M4 decision candidates | Provider-agnostic; no paid vendor lock-in required by architecture |
| Mode E (WordPress / Ghost) | **Deferred** | Later `WebsiteProvider` adapters; same protocol; must not force Core rewrite if adapters consume `WebsitePublicationRequest` |
| Registry | `static`, `stub` only today | CMS names remain unregistered until explicit adapter sprint |

Provider-neutral protocol (`WebsiteProvider`) already supports later CMS adapters without moving ownership to Publishing Engine.

---

## 5. Provider independence

| Check | Result | Notes |
|-------|--------|-------|
| Core contracts provider-neutral | **PASS** | `WebsiteProvider` + request/result shapes; engine resolves via registry |
| Static is one adapter, not the only forever destination | **PASS** | Stub retained; CMS deferred behind same protocol |
| Host/vendor not baked into Core | **PASS** | No Netlify/Vercel/Cloudflare/AWS required in frozen contracts |
| Deploy mode choice (A–D) does not require CMS | **PASS** | Public-static modes consume filesystem artifacts |
| Publishing remains channel-agnostic orchestrator | **PASS** | Does not embed host or CMS credentials |

**Provider Independence: PASS**

---

## 6. Architecture compliance matrix (v2.2)

| Rule | M4 decision posture | Status |
|------|---------------------|--------|
| Website Engine owns website publish destination | Affirmed | **PASS** |
| Website Engine owns future deploy hooks | Affirmed; implement in M5, not Core freeze rewrite | **PASS** |
| Publishing = orchestration only | Hosting / deploy must not land in Publishing | **PASS** |
| Editorial ≠ publish; human production gate retained | Deploy must not bypass Editorial/Publishing gates | **PASS** |
| Core v1.0 / Static v1.0 frozen | No silent interface expansion | **PASS** |
| Deploy outside Core | Separate M5 layer/hooks | **PASS** |
| Static first; CMS later | E deferred; A–C primary | **PASS** |
| Platforms: Automation = transport; Shared = secrets | Deploy credentials / job runners not OS business logic | **PASS** |
| SEO Engine ≠ site deploy | Unchanged | **PASS** |

**Architecture: PASS**

---

## 7. Key constraints for M5

M5 (deploy hooks / public reachability implementation) **must**:

1. **Keep deploy under Website Engine ownership** — hooks, packaging, cache-invalidation intent live in Website Engine (or clearly Website-owned deploy package), not in Publishing Engine.
2. **Keep Publishing orchestration-only** — Publishing may later invoke Website Engine; it must not own docroots, host APIs, or TLS/DNS.
3. **Treat Deploy as a layer after Static publish** — do not fold host sync into `StaticWebsiteProvider.publish` in a way that redefines Static Provider v1.0 without a new baseline; prefer post-publish hook(s) that consume `output/website/` (or a public subset).
4. **Do not expand Core v1.0 / Static v1.0 in place** — new hook interfaces, packaging helpers, or result fields require an explicit new baseline (v1.1+) if they change frozen public contracts / `__all__` / provider result semantics.
5. **Preserve `external_http=False` on Static Provider publish path** — network deploy belongs to the deploy hook / Automation transport, not the frozen static adapter’s publish contract.
6. **Stay host-agnostic at the architecture seam** — implement a minimal deploy-hook interface compatible with modes A/B/C (and optional D); do not hard-require a single paid vendor in Core.
7. **Keep CMS (E) future-only** — WordPress/Ghost remain later adapters behind `WebsiteProvider`; first public path stays static.
8. **Respect human gates** — production deploy must not bypass Editorial approval + Publishing production-publish requirements (Architecture v2.2 mandatory human gates).
9. **Secrets & transport** — deploy credentials → Shared Platform; rsync/CI/container roll → Automation Platform (no business decisions in platforms).
10. **Public-subset packaging** — exclude or block operator files (`metadata.json`, `source.md`) from public serve unless explicitly decided; do not redefine local artifact layout without baseline governance.
11. **Canonical URL alignment** — chosen host/DNS must match embedded `canonical_url`; URL policy remains Website Engine Core ownership.
12. **Reversibility** — switching host mode (A↔B↔C) or adding CMS later must not require relocating website ownership out of Website Engine.

M5 **must not**:

- Move hosting into Publishing Engine.
- Treat Website Engine Core freeze as a license to silently widen provider/request/result contracts.
- Make CMS the first public path or register WP/Ghost as required for M5 static reachability.
- Put SEO scoring or Campaign/Social logic into deploy hooks.

---

## 8. Explicit non-decisions (this validation)

This Atlas document does **not**:

- Choose mode A vs B vs C (or D).
- Select a paid hosting vendor.
- Authorize implementation of deploy hooks (M5 scope).
- Open Core v1.1 / Static v1.1.
- Wire Publishing `_adapter_website` to Website Engine (separate coordinated bridge).

---

## 9. Attestation

| Item | Value |
|------|-------|
| Validation file | `docs/marketing/M4_ATLAS_ARCHITECTURE_VALIDATION.md` |
| Architecture reference | v2.2 FROZEN |
| Core baseline | Website Engine Core v1.0 FROZEN (M2.5) |
| Provider baseline | Static Website Provider v1.0 FROZEN (M3.5) |
| Application code reviewed for change | N/A — analysis only; no code writes |
| Boundary violations found in destination model | **0** |

---

## FINAL

```text
Architecture: PASS
Provider Independence: PASS

Key constraints for M5:
1. Deploy hooks owned by Website Engine; transport via Automation; secrets via Shared Platform.
2. Publishing Engine remains orchestration-only — no hosting/docroot ownership.
3. Deploy is a separate M5 layer after Static publish — outside Core v1.0 / Static v1.0 freezes.
4. Do not expand frozen Core/Static contracts without a new baseline (v1.1+).
5. Keep Static Provider publish path free of deploy/network (`external_http=False`); hooks are post-publish.
6. Static-first public path; CMS adapters (WP/Ghost) remain future WebsiteProvider work.
7. Host-agnostic hook seam (A/B/C, optional D); no paid-vendor lock-in in architecture.
8. Preserve human production-publish gates; public-subset packaging; canonical URL ↔ DNS alignment.
```
