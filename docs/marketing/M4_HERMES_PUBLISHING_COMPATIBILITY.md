# M4 Hermes — Publishing Engine Compatibility (Deployment Boundary)

**Agent:** Hermes — Publishing Engine  
**Sprint:** M4 (analysis only)  
**Date:** 2026-08-10  
**Owned file:** this document only  
**Code / API / DB / runtime / git changes:** **NONE**

**Sources verified:**

| Source | Role |
|--------|------|
| `src/tools/publishing_engine.py` | SoT — website adapter + orchestration |
| [M1_5_PUBLISHING_BASELINE.md](M1_5_PUBLISHING_BASELINE.md) | Frozen Publishing v1.0 ownership |
| [Publishing_Channel_Interface.md](Publishing_Channel_Interface.md) | Frozen channel / PLACEHOLDER contract |
| [Architecture_v2.2.md](../architecture/Architecture_v2.2.md) | Current Marketing OS split |
| [Marketing_OS_v2.2.md](../architecture/Marketing_OS_v2.2.md) | Engine missions / I/O |
| [Architecture_v2.1.md](../architecture/Architecture_v2.1.md) | Publishing ≠ Website (ADR-002 lineage) |
| [M3_5_M4_DEPLOYMENT_READINESS.md](M3_5_M4_DEPLOYMENT_READINESS.md) | Deploy ownership for M4 (Website Engine) |

---

## 1. Question under test

Does the Publishing Engine remain **orchestration-only** with respect to **deployment** — i.e. no deployment logic, no hosting assumptions, website channel still a **PLACEHOLDER** relative to Website Engine ownership, and deploy must **not** enter Publishing Engine?

---

## 2. Evidence — website adapter (`publishing_engine.py`)

### Module contract (header)

Publishing Engine Phase 1 is declared **orchestration ONLY**: jobs, queue, channel selection, state machine, audit, manual publish. Explicitly does **not** perform website render, social APIs, email delivery, campaigns, scheduling, or AI publishing.

### Ownership map in code

| Channel | `CHANNEL_OWNERS` | Adapter mode (`list_channels`) |
|---------|------------------|--------------------------------|
| `website` | **Website Engine** | `placeholder` |
| `linkedin` / `twitter` / `instagram` | Social Engine | `not_implemented` |
| `newsletter` | Email Engine | `not_implemented` |

### `_adapter_website` behavior (verified)

Returns:

- `ok: true`
- `status: "PLACEHOLDER"`
- `owner_engine: "Website Engine"`
- `website_engine_invoked: false`
- `rendering_performed: false`
- Message: orchestration recorded only — **no Markdown/HTML/SEO/deploy**

Job records set `orchestration_only: true` and `website_engine: false`.

### Deploy / hosting scan

Within Publishing SoT (`publishing_engine.py` and publishing router surface), the only deploy-related language is **negative** (adapter message: no deploy). No hosting provider names, no sync/upload/CDN/cache-invalidation APIs, no filesystem publish to a docroot, no CI/deploy hooks.

---

## 3. Evidence — M1.5 Publishing baseline (frozen)

[M1_5_PUBLISHING_BASELINE.md](M1_5_PUBLISHING_BASELINE.md) freezes:

**Publishing owns:** jobs, queue, state machine, channel registry, audit, manual publish.

**Publishing does NOT own (verified at freeze):** Website Engine product logic, rendering, SEO, WordPress/Ghost, external APIs, scheduling, Celery/n8n, AI publishing — and explicitly **Website deployment**.

Website adapter at freeze: **PLACEHOLDER only**. Compatible with Architecture v2.1 orchestration boundary at **100%**.

Channel interface freeze ([Publishing_Channel_Interface.md](Publishing_Channel_Interface.md)):

- Website PLACEHOLDER must not render, deploy, invalidate cache, or call Website Engine.
- `published` on website channel means **orchestration recorded**, not site live.
- Replacing PLACEHOLDER with Website Engine invocation is an **M2+** change; Publishing must still only orchestrate.

---

## 4. Evidence — Architecture v2.2 Publishing / Website split

[Architecture_v2.2.md](../architecture/Architecture_v2.2.md):

- Boundary law: **Publishing orchestration ≠ Website render**; Website ≠ Social/Email/Campaign.
- Publishing Engine status: shipped orchestration; future = channel adapters invoke engines; **no render**.
- Website Engine status: shipped Core + Static Provider; **Deploy mode decision (M4)**; CMS adapters later.

[Marketing_OS_v2.2.md](../architecture/Marketing_OS_v2.2.md):

| Engine | Owns | Does not own |
|--------|------|--------------|
| Publishing Engine | Jobs, queue, channels, orchestration | Website render, SEO scoring, social APIs |
| Website Engine | Canonical site render/publish/static/**deploy hooks** | Campaign, social |

Publishing future status: wire website channel to Website Engine; **keep orchestration-only**.  
Website future status: M4 deployment-mode decision; deploy transport via Shared/Automation — **not Publishing**.

Lineage ([Architecture_v2.1.md](../architecture/Architecture_v2.1.md)): publication orchestration → Publishing; canonical website (render, URLs, metadata, **site deploy**) → Website Engine.

---

## 5. Confirmations (M4 checklist)

| Claim | Result | Notes |
|-------|--------|-------|
| No deployment logic in Publishing | **CONFIRMED** | Adapter PLACEHOLDER; no deploy hooks in Publishing SoT |
| No hosting assumptions in Publishing | **CONFIRMED** | No provider/host/CDN/docroot coupling |
| Website channel is PLACEHOLDER vs Website Engine ownership | **CONFIRMED** | Owner = Website Engine; adapter still `PLACEHOLDER` / `website_engine_invoked: false` |
| Deploy must not enter Publishing Engine | **CONFIRMED** | v2.1/v2.2 + M1.5 + M3.5/M4 readiness assign deploy hooks to Website Engine; transport to Automation; secrets to Shared Platform |

**Note (non-regression):** Website Engine Core/Static (M2–M3.5) may exist and write `output/website/`, but Publishing’s website adapter has **not** absorbed render or deploy. That separation is correct and required. Wiring (if/when) must remain an orchestration call into Website Engine — never deploy implementation inside Publishing.

---

## 6. Compatibility verdict

# **PASS**

Publishing Engine remains orchestration-only regarding deployment. M4 deploy-mode work belongs under **Website Engine** (hooks) + **Automation Platform** (transport) + **Shared Platform** (secrets). It must **not** be implemented inside Publishing Engine.

---

## 7. Constraints for M5 (Publishing-facing)

Hard constraints derived from this PASS. M5 (and any deploy-mode implementation) must honor:

1. **Deploy stays out of Publishing** — No rsync, git push, object upload, container roll, CDN purge, DNS/TLS, or host credentials in `publishing_engine.py` / publishing routers/UI.
2. **Website Engine owns deploy hooks** — Any public-reachability / deploy-mode decision implements hooks under Website Engine, not as Publishing business logic.
3. **Publishing may only orchestrate** — If the website channel advances beyond PLACEHOLDER, Publishing may: validate editorial gate, create/track jobs, invoke a Website Engine API/adapter, record `adapter_result` + audit. It must not perform render, static write, or deploy itself.
4. **No hosting assumptions in Publishing contracts** — Channel registry, job schema, and API must remain host-agnostic (no Netlify/Vercel/Cloudflare/etc. as Publishing fields or required paths).
5. **Human gates preserved** — Production publish remains human-requested + editorially approved; deploy must not bypass Editorial/Publishing gates (auto-deploy on approval forbidden).
6. **Semantics of `published`** — Until Website Engine is truly invoked (and later until deploy succeeds under Website/Automation ownership), do not redefine Publishing `published` to mean “live on public host” without an explicit baseline/ADR bump.
7. **Baseline discipline** — Changing website adapter from PLACEHOLDER → Website Engine invocation requires a Publishing baseline bump (e.g. v1.1) and governance note; silent edits to frozen M1.5 contracts are forbidden.
8. **Ownership map frozen for M5 planning** — Jobs/queue/channels/audit = Publishing; `output/website/` + deploy hooks = Website Engine; deploy transport = Automation; secrets = Shared Platform.

---

## 8. Impact of this analysis

| Dimension | Impact |
|-----------|--------|
| Architecture | **NONE** (certification only) |
| Runtime / API / DB / code / git | **NONE** |

**Hermes M4 deliverable complete.**
