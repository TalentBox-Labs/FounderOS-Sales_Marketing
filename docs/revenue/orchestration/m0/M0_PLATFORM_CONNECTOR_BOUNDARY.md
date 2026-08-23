# M0 Platform Connector Boundary

**Sprint:** REV-ORCH M0  
**Date:** 2026-08-17

---

## S4.5 Context

Connector credential tenancy frozen. Env-backed connectors remain **documented MEDIUM risk** (GLOBAL_BY_DESIGN).

---

## OpenAI

| Aspect | Current | M1 Classification |
|--------|---------|-------------------|
| Credential source | `OPENAI_API_KEY` env | **SAFE_PLATFORM_GLOBAL** |
| Tenant relationship | Not per-org | Platform bears cost |
| Request data | Contact context from caller | **Must be TenantContext-scoped before call** |
| Mutation | None — text return | **SAFE_WITH_M1_RESTRICTIONS** |
| Provenance | Not logged | M1 gap (F2 sprint) |

**Verdict:** **SAFE_WITH_M1_RESTRICTIONS**

Conditions:
- All M1 OpenAI calls must receive pre-authorized tenant-scoped context only
- No model tool calling
- Draft output → ApprovalRequest, never direct send

Does **not** block M1.

---

## n8n

| Aspect | Current | M1 Classification |
|--------|---------|-------------------|
| Outbound credential | `N8N_WEBHOOK_BASE_URL`, `N8N_API_KEY` env | **SAFE_PLATFORM_GLOBAL** |
| Inbound tenant binding | S4.5 org binding | **Preserved** |
| Execution role | Connector/executor post-approval | **SAFE_WITH_M1_RESTRICTIONS** |
| Payload tenant authority | contact_id in payload | Must validate org at execute |

**Verdict:** **SAFE_WITH_M1_RESTRICTIONS**

Conditions:
- n8n is **executor**, not orchestrator
- Send only via ApprovalRequest executor
- Inbound webhooks use S4.5 binding (no payload tenant authority)

Does **not** block M1.

---

## Per-Tenant Credentialization

**Not required for M1.** Deferred to REV-ORCH-A2 (AUTONOMY phase).

---

## BLOCKS_M1 Assessment

| Connector | Blocks M1? |
|-----------|------------|
| OpenAI | **NO** |
| n8n | **NO** |

---

*End of M0 Platform Connector Boundary*
