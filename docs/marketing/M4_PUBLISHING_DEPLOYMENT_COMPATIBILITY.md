# M4 — Publishing ↔ Deployment Compatibility (Hermes)

**Agent:** Hermes — Publishing Engine  
**Sprint:** M4 (analysis only)  
**Date:** 2026-08-10  
**Owned file:** this document only  
**Code / API / DB / runtime / git changes:** **NONE**

**Sources verified:**

| Source | Role |
|--------|------|
| `src/tools/publishing_engine.py` | SoT — queue, audit, adapter_result, website PLACEHOLDER |
| [M1_5_PUBLISHING_BASELINE.md](M1_5_PUBLISHING_BASELINE.md) | Frozen Publishing v1.0 ownership |
| [Publishing_State_Machine.md](Publishing_State_Machine.md) | Queue membership + transitions |
| [Publishing_Audit_Schema.md](Publishing_Audit_Schema.md) | Append-only audit contract |
| [Publishing_Channel_Interface.md](Publishing_Channel_Interface.md) | Adapter result contract |
| [Publishing_API_Contract.md](Publishing_API_Contract.md) | Job object / `adapter_result` |
| [Architecture_v2.2.md](../architecture/Architecture_v2.2.md) | Publishing ≠ Website; deploy under Website (M4) |
| [Marketing_OS_v2.2.md](../architecture/Marketing_OS_v2.2.md) | Engine owns / does-not-own |

---

## 1. Question under test

1. Does Publishing **only orchestrate** the website channel (trigger Website Engine when wired) and **never own deployment**?
2. Are Publishing **queue**, **audit**, **publish result** (`adapter_result`), and **rollback** surfaces compatible with a **future deploy adapter owned by Website Engine**?

---

## 2. Ownership confirmation

### Architecture (v2.2)

- Boundary law: **Publishing orchestration ≠ Website render**; Website ≠ Social/Email/Campaign.
- Publishing: shipped orchestration; future = channel adapters **invoke engines**; **no render**.
- Website Engine: shipped Core + Static Provider; **Deploy mode decision (M4)**; deploy hooks owned by Website Engine (transport via Automation; secrets via Shared Platform).

### M1.5 baseline (frozen)

Publishing owns: jobs, queue, state machine, channel registry, audit, manual publish.  
Publishing does **NOT** own: website rendering, SEO, **website deployment**, social APIs, campaigns, scheduling, Celery/n8n, AI publishing.

### Code SoT (`publishing_engine.py`)

| Fact | Evidence |
|------|----------|
| Orchestration-only module contract | Header: jobs/queue/channel/state/audit/manual publish; does not render/deploy |
| Website channel owner | `CHANNEL_OWNERS[website] = "Website Engine"` |
| Website adapter mode | `list_channels` → `adapter: "placeholder"` |
| `_adapter_website` | `status: "PLACEHOLDER"`; `website_engine_invoked: false`; `rendering_performed: false`; message denies Markdown/HTML/SEO/**deploy** |
| Job flags | `orchestration_only: true`; `website_engine: false` |
| Deploy/hosting logic in Publishing | **Absent** (only negative language in PLACEHOLDER message) |

**Current vs target wire:**

| Mode | Behavior |
|------|----------|
| **Today (M1 / M1.5)** | Website adapter does **not** call Website Engine; records orchestration only |
| **Target (post-wire)** | Publishing may **invoke** Website Engine via channel adapter only; Website Engine owns render + **deploy hooks**; Publishing still never implements deploy |

**Confirmed:** Publishing triggers Website Engine **only as orchestration** (when wired). Publishing **never owns deployment**.

---

## 3. Surface compatibility with future Website Engine deploy adapter

Assumed future shape (Website Engine side): a deploy adapter/hook that packages/serves or syncs `output/website/` (or public subset), returns a structured result, and retains prior artifact for rollback — **owned by Website Engine**, not Publishing.

### 3.1 Queue — **COMPATIBLE**

| Publishing surface | Behavior | Deploy-adapter fit |
|--------------------|----------|--------------------|
| Queue states | `publish_pending`, `publishing`, `failed`, `retry` | Deploy runs inside adapter call while job is `publishing`; success → `published`, failure → `failed` |
| Terminal | `published`, `cancelled` | Deploy outcome does not require new queue states |
| Membership | `list_queue` filters on orchestration states | Host/provider-agnostic; no deploy-specific queue |

**Constraint:** Do **not** add deploy-provider states (`deploying`, `live`, `rolled_back`) into Publishing’s frozen state machine without a Publishing baseline bump. Deploy phases stay inside Website Engine / `adapter_result`.

### 3.2 Audit — **COMPATIBLE**

| Publishing surface | Behavior | Deploy-adapter fit |
|--------------------|----------|--------------------|
| Storage | Append-only `output/publishing/audit.jsonl` | Deploy outcomes recorded as orchestration `state_change` (and optional additive keys later) |
| Required fields | `bundle_id`, `channel`, `requested_by`, `utc_timestamp`, `state`, `retry_count`, `errors` | Unchanged by Website Engine deploy |
| Events (v1.0) | `job_created`, `state_change` | Sufficient to trail publish/fail/retry; deploy detail belongs in job `adapter_result` / notes |

**Constraint:** Audit must remain orchestration forensic trail. No deploy credentials, host tokens, or provider-private payloads in Publishing audit. Website Engine may keep its own deploy/ops audit under Website ownership.

### 3.3 Publish result (`adapter_result`) — **COMPATIBLE**

Frozen adapter contract (`adapter(job) -> dict`):

| Required | Role for future deploy adapter |
|----------|--------------------------------|
| `ok` | Drives `published` vs `failed` |
| `status` | Extend beyond `PLACEHOLDER` (e.g. engine/deploy status codes) via baseline bump when replacing PLACEHOLDER |
| `channel` / `owner_engine` | Remain `website` / `Website Engine` |
| `message` | Human summary; may mention deploy outcome without Publishing owning deploy |

Job stores last payload in `adapter_result` (opaque to Publishing beyond `ok`). Additive fields from Website Engine (e.g. `deploy_ref`, `artifact_hash`, `rollback_ref`, `website_engine_invoked: true`) are **compatible** as long as required fields remain and Publishing does not interpret host-specific logic.

**Constraint:** Replacing PLACEHOLDER with real Website Engine invocation (render and/or deploy-hook call) requires a Publishing baseline bump (e.g. v1.1). Until then `website_engine_invoked` stays `false` per channel freeze.

### 3.4 Rollback — **COMPATIBLE (with ownership constraint)**

| Layer | Current | Required ownership |
|-------|---------|-------------------|
| Publishing | No rollback command/state; `retry` re-runs manual publish; cannot cancel `published` | Orchestration only — may later **trigger** a Website Engine rollback/re-publish action via adapter, recording `adapter_result` |
| Website Engine deploy adapter (future) | Not implemented | **Owns** artifact snapshot retention + re-point / restore (per M3.5 readiness) |
| Automation / Shared | N/A | Transport execution / secrets — not Publishing |

Publishing `retry` ≠ site rollback. Site rollback must not be implemented inside `publishing_engine.py`. Compatibility holds if rollback is a Website Engine deploy-adapter capability; Publishing optionally orchestrates a human-gated job that invokes that adapter and audits the orchestration outcome.

**Constraint:** Do not invent Publishing `rolled_back` as a deploy-live semantic without ADR + baseline bump. Do not allow auto-rollback or auto-deploy on Editorial Approval.

---

## 4. Compatibility matrix

| Surface | Compatible with Website Engine–owned deploy adapter? | Verdict |
|---------|------------------------------------------------------|---------|
| Ownership (orchestrate only; no deploy in Publishing) | YES | **PASS** |
| Queue | YES | **PASS** |
| Audit | YES | **PASS** |
| Publish result (`adapter_result`) | YES | **PASS** |
| Rollback | YES — if owned by Website Engine; Publishing records orchestration only | **PASS** |

---

## 5. Final verdict

# **COMPATIBILITY: PASS**

Publishing Engine remains **orchestration-only**. It may trigger Website Engine for the `website` channel; it **must not** own deployment, hosting, CDN, or rollback transport. Queue, audit, and `adapter_result` are already shaped for a future Website Engine deploy adapter. Rollback is compatible only as a **Website Engine–owned** adapter concern (Publishing may orchestrate invocation later under a baseline bump).

---

## 6. Constraints (binding for wire-up / M5+)

1. **Deploy never enters Publishing** — No rsync, git push, object upload, container roll, CDN purge, DNS/TLS, or host credentials in Publishing SoT/routers/UI.
2. **Website Engine owns deploy adapter/hooks** — Public reachability, artifact packaging, cache invalidation, and rollback restore live under Website Engine (+ Automation transport, Shared secrets).
3. **Publishing may only orchestrate** — Validate editorial gate → create/track job → invoke Website Engine adapter → store `adapter_result` + append audit. No render, no static write, no deploy.
4. **Queue stays orchestration states** — Do not encode provider deploy phases as Publishing states without a new Publishing baseline.
5. **Audit stays append-only orchestration trail** — No secrets; tolerate additive keys later; required v1.0 fields preserved.
6. **`adapter_result` is the seam** — Deploy refs / rollback refs are Website Engine fields inside the adapter payload; Publishing treats `ok` for transitions.
7. **`published` semantics** — v1.0 `published` on website = adapter `ok` (today: orchestration recorded). Do not redefine as “live on public host” without explicit baseline/ADR when deploy is truly wired.
8. **Human gates preserved** — Manual publish + editorial approval required; no auto-publish / auto-deploy on Editorial Approval; no AI publish.
9. **PLACEHOLDER → Website Engine wire = baseline bump** — Silent edits to frozen M1.5 channel/API contracts forbidden.
10. **Rollback ≠ Publishing retry** — `retry` re-orchestrates publish; site rollback is Website Engine deploy-adapter responsibility.

---

## 7. Impact of this analysis

| Dimension | Impact |
|-----------|--------|
| Architecture | **NONE** (certification only) |
| Runtime / API / DB / code / git | **NONE** |

**Hermes M4 deliverable complete.**
