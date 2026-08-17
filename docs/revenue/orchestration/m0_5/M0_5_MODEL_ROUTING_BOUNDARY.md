# M0.5 Model Routing Boundary

**Sprint:** REV-ORCH M0.5  
**Date:** 2026-08-17

---

## Do not implement multi-model routing in M1.

This document freezes **ownership**, not a router.

---

## Ownership

| Concern | Owner |
|---------|--------|
| Provider credentials (`OPENAI_API_KEY`, future Gemini) | Platform / AIService / ConnectorCredentialRecord (S4.5) — **never the worker** |
| Model name selection | AIService / config (`settings.OPENAI_MODEL`) |
| Reasoning contract (inputs/outputs) | Specialized worker |
| Tenant-scoped prompt data | Orchestrator (prepares minimum context) |

---

## Permitted future mapping (conceptual)

| Worker | May use different model later |
|--------|-------------------------------|
| Research Worker | Provider A |
| Personalization Worker | Provider B |
| Objection Worker | Provider C |

Workers **must not**:

- hold API keys
- pick `credential_id`
- call OpenAI client directly once AIService is the boundary (`ai_service.py` is the current wrapper; `sdr_agent._build_llm` is LEGACY and must not be the pattern)

---

## M1

Single platform OpenAI path via `AIService` is **SAFE_WITH_M1_RESTRICTIONS** (M0 platform connector boundary). Data remains TenantContext-scoped before the call.

---

*End of M0.5 Model Routing Boundary*
