# S0 — Social Architecture Boundary

**Sprint:** SOCIAL S0  
**Agent:** ATLAS  
**Status:** AUDIT ONLY — no implementation  
**Architecture:** v2.2 FROZEN  
**Date:** 2026-08-11

---

## 1. Target flow (proposed S1)

```
Content Studio
    ↓
Editorial Engine          (human approve ≠ publish)
    ↓
Publishing Engine         (job + channel + human manual_publish)
    ↓
Social Engine             (channel abstraction + payload map)
    ↓
LinkedIn Adapter          (API request / response normalize)
    ↓
LinkedIn API              (external)
```

**Evidence class:** ASSUMPTION for Social Engine / Adapter packages (not present).  
**REPO VERIFIED:** Content Studio, Editorial, Publishing exist; LinkedIn Publishing adapter returns `NOT_IMPLEMENTED`.

---

## 2. Responsibility matrix

| Engine | Owns | Must NOT |
|--------|------|----------|
| **Editorial** | Decision state, human approve/reject/request-changes, phase promote, editorial audit | Call LinkedIn; store OAuth; authorize publish |
| **Publishing** | Job lifecycle, channel selection, queue/state, retry/cancel, dispatch to adapter, publishing audit | Own LinkedIn token secrets as business SoT; bypass Editorial |
| **Social Engine** *(proposed)* | Social channel abstraction, platform validation, payload mapping, adapter invocation, normalize provider status | Replace Publishing job state machine; editorial approval |
| **LinkedIn Adapter** *(proposed)* | LinkedIn request construction, HTTP to LinkedIn, URN mapping, error normalization | Decide human approval; mutate Editorial |

---

## 3. Repository verification (Publishing)

| Claim | Evidence | Class |
|-------|----------|-------|
| Channel `linkedin` registered | `src/tools/publishing_engine.py` `CHANNEL_LINKEDIN` | REPO VERIFIED |
| Owner = Social Engine | `CHANNEL_OWNERS[linkedin] = "Social Engine"` | REPO VERIFIED |
| Adapter stub | `_adapter_not_implemented` → `NOT_IMPLEMENTED` | REPO VERIFIED |
| Job flags | `social_engine: False`, `campaign_engine: False` | REPO VERIFIED |
| Editorial prerequisite | `validate_publish_readiness` / `has_editorial_approval` | REPO VERIFIED |
| Human requester gate | `is_human_requester` on create/publish/retry/cancel | REPO VERIFIED |
| Manual publish only | `manual_publish` — no Celery schedule in Publishing | REPO VERIFIED |
| FDR-003 editorial ≠ publish | `editorial_approval.py` docstring | REPO VERIFIED |

---

## 4. Architecture v2.2 fit

Marketing OS names Social Engine as destination adapter owner; Publishing owns orchestration. **COMPATIBLE** with proposed boundary.

**No Social Engine package exists** under `src/tools/` → Social Engine Boundary: **DEFINED (contract) / NOT IMPLEMENTED (code)**.

---

## 5. Explicit S1 non-goals

- Autonomous publish  
- Scheduling  
- Multi-network  
- Campaign Engine  
- Media upload (deferred unless Founder requires)  
- Analytics ingestion as launch blocker  

---

## 6. Dual-path warning

`revenue_os/integrations/social_publisher.py` is **STALE/ADJACENT** — must not become Marketing OS SoT without explicit migration ADR.
