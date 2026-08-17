# M1.5 — Publishing Engine Baseline Freeze

**Baseline name:** Publishing Engine **v1.0**  
**Status:** **FROZEN**  
**Sprint:** M1.5  
**Date:** 2026-08-09  
**Architecture:** v2.1 (ADR-002) — authoritative  
**Implementation report:** [M1_PUBLISHING_ENGINE_REPORT.md](M1_PUBLISHING_ENGINE_REPORT.md)

**Nature:** Governance certification only.  
**Code / API / DB / runtime / git changes in M1.5:** **NONE**

---

## Companion freeze docs

| Document | Freeze target |
|----------|---------------|
| [Publishing_State_Machine.md](Publishing_State_Machine.md) | States + valid/invalid transitions |
| [Publishing_API_Contract.md](Publishing_API_Contract.md) | REST contracts |
| [Publishing_Channel_Interface.md](Publishing_Channel_Interface.md) | Channel registry + adapter interface |
| [Publishing_Audit_Schema.md](Publishing_Audit_Schema.md) | Audit required fields |
| [Website_Engine_Implementation_Checklist.md](Website_Engine_Implementation_Checklist.md) | M2 prepare-only checklist |

---

## 1. Verification — ownership

| Publishing Engine owns | Verified |
|------------------------|----------|
| Publish jobs | YES — `output/publishing/jobs/` |
| Publish queue | YES — `list_queue` / GET `/jobs` |
| State machine | YES — see State Machine doc |
| Channel registry | YES — five registered channels |
| Audit | YES — `output/publishing/audit.jsonl` |
| Manual publish command | YES — POST `/{id}/publish` |

| Untouched / absent | Verified |
|--------------------|----------|
| Website Engine | YES — no website engine module; website adapter PLACEHOLDER only |
| Social Engine | YES — adapters `NOT_IMPLEMENTED` |
| Campaign Engine | YES — no campaign logic |
| SEO logic | YES — none in Publishing Engine |
| Rendering | YES — `rendering_performed: false` |
| WordPress / Ghost | YES — none |
| External API integrations | YES — `external_api_called: false` |
| Scheduling | YES — none |
| Celery / n8n | YES — not used by Publishing Engine |
| AI publishing | YES — human requester gate |

---

## 2. Permissions (frozen)

| Rule | Status |
|------|--------|
| Editorial approval required to create job | FROZEN / VERIFIED |
| Human requester required | FROZEN / VERIFIED |
| No AI authorization | FROZEN / VERIFIED (deny-list via editorial human gate) |
| No publish without prior job + approval gate | FROZEN / VERIFIED |
| No auto-publish on Editorial Approval | FROZEN / VERIFIED |

---

## 3. Architecture boundaries (frozen)

Publishing Engine does **NOT** own:

- Website rendering
- Markdown conversion
- HTML generation
- Metadata / OpenGraph / Schema.org
- RSS / Sitemap
- Website deployment
- Social APIs
- Campaign scheduling
- Automation Platform

Compatible with Architecture v2.1 — **100%**.

---

## 4. Implementation SoT (frozen file set)

| Path | Role |
|------|------|
| `src/tools/publishing_engine.py` | Engine core |
| `runner_api_routers/publishing.py` | Additive API |
| `runner_api.py` | Router include only |
| `runner_api_routers/ui.py` | UI routes |
| `templates/publishing_queue.html` | Queue UI |
| `templates/publishing_detail.html` | Detail UI |
| `tests/test_publishing_engine.py` | Focused certification tests |

Changes to these contracts require a new baseline version (e.g. v1.1) and ADR/governance note — not silent edits.

---

## 5. Regression summary (M1.5 certification run)

Environment: `SECRET_KEY` set; `HEARTBEAT_ENABLED=0`

| Suite | Result |
|-------|--------|
| Focused `tests/test_publishing_engine.py` | **16 passed** |
| Full `tests/` | **296 passed**, **8 failed**, **4 errors** |
| New regressions vs M1 | **0** |
| Historical failures | Unchanged (crews unit, utilities unit, orchestration API, prospecting UI) |

---

## 6. Impact verification (M1.5)

| Dimension | Impact |
|-----------|--------|
| Architecture impact | **NONE** |
| Runtime impact | **NONE** |
| API impact | **NONE** |
| Database impact | **NONE** |
| Code changes | **NONE** |
| Git operations | **NONE** |

---

## 7. Website Engine readiness

| Item | Status |
|------|--------|
| Publishing baseline frozen | YES |
| Website checklist prepared | YES |
| Website Engine implementation started | **NO** |
| Authorized next sprint | **M2 — Website Engine Core** |

---

## 8. Final verdict

# **PUBLISHING ENGINE v1.0 BASELINE FROZEN**

**READY FOR M2 — WEBSITE ENGINE CORE**

**NO CODE CHANGES REQUIRED**
