# MC04.5 — Authority Attestation (SENTINEL)

**Sprint:** FOUNDER OS MC04.5  
**Date:** 2026-08-13

---

## Route-level gates (verified)

| Endpoint | API key | Human gate |
|----------|---------|------------|
| Marketing handoff | `_verify_api_key` | `is_human_approver` |
| Sales accept | `_verify_api_key` | `is_human_approver` |
| Sales reject | `_verify_api_key` | `is_human_approver` |

## Adversarial results (re-run MC04 tests)

| Vector | Result |
|--------|--------|
| Agent handoff | **403** |
| AI intake | **403** |
| Unauthenticated (key set) | **401** (pattern from A4 tests) |

## Service-layer direct invocation

`accept_qualified_demand()` is callable programmatically (internal service API) — **same pattern as A3.5 `apply_deal_stage_update` and A4.5 `apply_contact_status_update`**.

| Check | Result |
|-------|--------|
| Agent runtime path invokes service directly | **NO** — grep confirms router + tests only |
| Hermes/heartbeat/Celery invoke MC04 service | **NO** |

**Direct Mutation Boundary Verification: PASS** — authoritative external/agent paths cannot mutate Sales state without human-gated runner routes.

## A4.5 interaction

MC04 accept sets `ContactStatus.LEAD` only — does **not** bypass A4.5 human gate for status promotion.

**Authority Contract: FROZEN**
