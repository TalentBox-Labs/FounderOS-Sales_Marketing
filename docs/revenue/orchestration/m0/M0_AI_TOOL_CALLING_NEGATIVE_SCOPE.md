# M0 AI Tool Calling Negative Scope

**Sprint:** REV-ORCH M0  
**Date:** 2026-08-17

---

## Finding

Repository search confirms **general LLM tool/function calling is NOT implemented** in the revenue path:

- No `tools=` parameter in OpenAI client calls (`revenue_os/services/ai_service.py`)
- No `function_call` / `tool_calls` handling
- CrewAI agents use Task descriptions only — no Founder OS domain tool registry

---

## Policy Declaration

```
GENERAL_LLM_TOOL_CALLING: PROHIBITED_FOR_M1
```

Unless a future **policy-layer sprint** explicitly authorizes tool calling with:

1. Fixed allowlist of tools (no model-selected tool registry)
2. Server-side argument validation (reject model-supplied tenant/org/credential IDs)
3. Human approval gate before any side-effecting tool
4. Audit provenance on every tool invocation proposal

---

## Prohibited Tool Capabilities (if ever introduced)

The model must **never** directly select or control:

| Category | Reason |
|----------|--------|
| Tenant / organization_id | S2.5 server-derived only |
| Identity / requested_by | S1.5 server-bound |
| Connector credential | S4.5 org-scoped vault |
| CRM mutation (status, stage) | A3/A4 frozen human-only |
| Send action | ApprovalRequest required |
| QualifiedDemand / CommercialOutcome accept | MC04.5 / MC06.5 frozen |
| Privileged domain operations | mutation_authority |

---

## Acceptable M1 Pattern (no tool calling)

AI returns **structured JSON in response body** → validated by Python → filed as ApprovalRequest → human approves → deterministic executor calls domain API.

This preserves: **AI proposes, policy decides, services mutate.**

---

## M0 Action

**No implementation.** Documentation only. M0 tests verify absence of tool-calling patterns in revenue services.

---

*End of M0 AI Tool Calling Negative Scope*
