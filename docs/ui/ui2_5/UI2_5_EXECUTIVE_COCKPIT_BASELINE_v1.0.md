# UI2.5 — Executive Cockpit Baseline v1.0

**STATUS: FROZEN**  
**Sprint:** UI2.5 — Executive Cockpit v1 Baseline Freeze  
**Date:** 2026-08-13  
**Version:** v1.0

---

## Scope

Executive Cockpit v1 is frozen as a **read-model composition layer** inside the canonical Founder OS Jinja shell with **two** human-gated mutation proxies.

## Frozen route contract

| Item | Value |
|------|-------|
| Cockpit page | `GET /cockpit` |
| Shell | `templates/base.html` + `templates/cockpit.html` |
| Composition | `revenue_os/services/cockpit_read_model.py` |
| Mutation API | `runner_api_routers/cockpit.py` |
| UI route | `runner_api_routers/ui.py::page_cockpit` |

**GET /cockpit properties (frozen):**
- Jinja render only; no canonical mutation on page load
- No external integration activation on page load
- Degrades per-panel when sources fail
- No cockpit-owned business SoT

## Frozen five-panel semantic contract

| Panel | Key | Owning domain |
|-------|-----|---------------|
| Attention / Decision Queue | `attention` | Cross-OS read composition |
| Sales Snapshot | `sales` | Sales / Revenue CRM read |
| Marketing / SEO Snapshot | `marketing_seo` | Marketing |
| Commercial Flow | `commercial_flow` | Cross-OS derived honesty |
| Governance / System Health | `governance` | Platform |

## Frozen human actions (cockpit exposure)

| Action | Endpoint | Underlying contract |
|--------|----------|---------------------|
| QualifiedDemand Accept | `POST /api/v1/cockpit/actions/qualified-demand/accept` | MC04.5 |
| Contact.status update | `POST /api/v1/cockpit/actions/contact-status` | A4.5 |

**Trusted operator:** `FOUNDER_OS_OPERATOR_NAME` (server env only; client `requested_by` not accepted).

## Prohibited cockpit mutations (frozen)

- QualifiedDemand reject
- Deal stage mutation
- Editorial approve/reject
- Publishing promote/publish
- Agent/AI/automation identity as operator

## Governance guarantees (frozen)

- UI1.1 authority remediation preserved
- Direct service bypass blocked at canonical mutation layer
- Marketing / Sales / Revenue ownership unchanged
- No new shared SoT
- No fake executive metrics

## Authoritative source count

**UI2 reported:** 11 (UI1 widget plan)  
**Repository verified:** **8** authoritative source integrations (see `UI2_5_COCKPIT_SOURCE_MANIFEST_v1.0.md`)

Discrepancy explained: agent activity feed, standalone lead-score API, and commercial-flow SoT were planned widgets but are implemented as derived/static composition instead of separate integrations.

## Downstream frozen contracts

Sales A1.5, A3.5, A4.5, MC04.5 — **UNCHANGED**

## Test freeze anchor

| Suite | File | Expected |
|-------|------|----------|
| UI2.5 freeze | `tests/test_ui2_5_cockpit_baseline_freeze.py` | 20/20 |
| UI2 | `tests/test_ui2_executive_cockpit.py` | 23/23 |
| UI1.1 | `tests/test_ui1_1_mutation_authority.py` | 10/10 |

---

**Verdict:** EXECUTIVE COCKPIT v1 BASELINE FROZEN
