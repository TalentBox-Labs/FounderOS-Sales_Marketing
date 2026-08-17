# UI1.1 — Mutation Authority Map

**Sprint:** UI1.1  
**Date:** 2026-08-13  
**Rule:** Security decision MUST occur at authoritative domain/service mutation boundary.

---

## Protected actions (UI1 human-gated candidates)

### 1. QualifiedDemand accept

| Layer | Location | Guard |
|-------|----------|-------|
| UI route | None (API-only) | — |
| API route | `POST /api/v1/sales/intake/demand/accept` | `_verify_api_key` + `_human_gate` |
| Runner command | N/A | — |
| Service/domain | `accept_qualified_demand()` | **`require_human_mutation_authority`** (UI1.1) |
| Persistence | `Contact` create/link + `AgentActionLog` | Audit mandatory |
| Authentication | Runner API key | PASS |
| Authorization | Human identity via `requested_by` | PASS (service + route) |
| Human-only guard | `is_human_approver` | **PASS** |
| Agent prohibition | Blocks `agent:`, `ai:`, forbidden names | **PASS** |
| Validation | Handoff must exist; idempotent accept | PASS |
| Audit emission | `AgentActionLog` + EventBus `CONTACT_IMPORTED` | PASS |
| **Authoritative boundary** | **`accept_qualified_demand()`** | **PASS** |

### 2. QualifiedDemand reject

| Layer | Location | Guard |
|-------|----------|-------|
| API route | `POST /api/v1/sales/intake/demand/reject` | `_verify_api_key` + `_human_gate` |
| Service/domain | `reject_qualified_demand()` | **`require_human_mutation_authority`** (UI1.1) |
| Persistence | `AgentActionLog` only | PASS |
| **Authoritative boundary** | **`reject_qualified_demand()`** | **PASS** |

### 3. QualifiedDemand Marketing handoff (6th HUMAN_ONLY action)

| Layer | Location | Guard |
|-------|----------|-------|
| API route | `POST /api/v1/marketing/qualified-demand/handoff` | `_verify_api_key` + `_human_gate` |
| Service/domain | `register_marketing_handoff()` | **`require_human_mutation_authority`** (UI1.1) |
| Persistence | `AgentActionLog` only (no CRM write) | PASS |
| **Authoritative boundary** | **`register_marketing_handoff()`** | **PASS** |

### 4. Contact.status mutation

| Layer | Location | Guard |
|-------|----------|-------|
| UI route | None | — |
| API route (canonical) | `PATCH /api/v1/crm/contacts/{id}/status` | `_verify_api_key` + `is_human_approver` |
| API route (legacy JWT) | `PUT /api/v1/contacts/{id}` | **403 on status change** (UI1.1) |
| Service/domain | `apply_contact_status_update()` | **`require_human_mutation_authority`** (UI1.1) |
| Persistence | `Contact.status` via service only | PASS |
| n8n ingress | `meeting.booked` | **No status mutation** (UI1.1) |
| **Authoritative boundary** | **`apply_contact_status_update()`** | **PASS** |

### 5. Deal stage mutation

| Layer | Location | Guard |
|-------|----------|-------|
| API route | `PATCH /api/v1/crm/deals/{id}/stage` | `_verify_api_key` + `is_human_approver` |
| Service/domain | `apply_deal_stage_update()` | **`require_human_mutation_authority`** (UI1.1) |
| Persistence | `Deal.stage` via `advance_deal_stage` | PASS |
| **Authoritative boundary** | **`apply_deal_stage_update()`** | **PASS** |

### 6. Editorial approve/reject

| Layer | Location | Guard |
|-------|----------|-------|
| UI route | `/editorial/*` (Jinja) | Mounted |
| API route | `POST /api/v1/editorial/{id}/approve`, `/reject` | Session/API |
| Service/domain | `src/tools/editorial_approval.py` | **`is_human_approver(approver)`** at promote boundary |
| Persistence | JSONL decisions + staging promote | PASS |
| **Authoritative boundary** | **`editorial_approval.record_decision()`** | **PASS** (pre-existing) |

### 7. Publishing human promote

| Layer | Location | Guard |
|-------|----------|-------|
| UI route | `/publishing` (Jinja) | Mounted |
| API route | Publishing engine endpoints | API key |
| Service/domain | `src/tools/publishing_engine.py` | **`is_human_requester(requested_by)`** |
| Persistence | Job audit + channel dispatch | PASS |
| **Authoritative boundary** | **Publishing engine promote functions** | **PASS** (pre-existing) |

---

## Authority enforcement stack (post UI1.1)

```
PUBLIC ENTRY POINT
        ↓
AUTHENTICATION (API key / JWT / n8n secret)
        ↓
AUTHORIZATION (route human gate where applicable)
        ↓
HUMAN / AGENT AUTHORITY (require_human_mutation_authority at service)
        ↓
CANONICAL DOMAIN MUTATION
        ↓
AUDIT (AgentActionLog / EventBus / JSONL)
        ↓
PERSISTENCE
```

---

## Bypass closure summary

| Bypass | Pre-fix boundary gap | Post-fix boundary |
|--------|---------------------|-------------------|
| UI1-B1 | JWT PUT bypassed runner gate | 403 at JWT PUT; canonical path unchanged |
| UI1-B2 | n8n bypassed A4 gate | Recommendation-only; no CRM status write |
| UI1-B3 | Service callable without gate | `mutation_authority.py` enforced |

---

## Frozen contract impact

**NONE** — runner API semantics, MC04 payload, A3/A4 stage rules unchanged. Only authority layering added.
