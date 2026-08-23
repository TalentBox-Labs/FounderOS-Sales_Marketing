# A3 — Security & Authority Audit (SENTINEL)

**Sprint:** SALES A3  
**Date:** 2026-08-13

## Current gap

Runner CRM mutations require API key only — **no** `requested_by` human gate on create deal. A3 stage endpoint **must** add HUMAN_ONLY beyond API key.

## Enforcement design for A3

1. `Depends(_verify_api_key)` — unauthenticated → 401 when key configured  
2. Body field `requested_by: str` — required  
3. `is_human_approver(requested_by)` — reject ai/agent/bot/system/… → **403**  
4. Pipeline stage change classified **HUMAN_ONLY** (A1.5 authority contract)

## Can an AI/agent currently trigger stage mutation on runner?

**Before A3:** No runner stage endpoint existed.  
**JWT PUT:** No human-name gate (known legacy gap — out of A3 scope to rewrite JWT stack).  
**After A3:** Runner stage path blocks forbidden identities; agents calling with `requested_by=agent` fail.

## Risks

| Risk | Mitigation |
|------|------------|
| API key as shared secret | Existing runner model; key ≠ human identity — `requested_by` required |
| Impersonation of human name | Accept residual; same as Publishing/Editorial |
| Replay | Same-stage → no-op success; no idempotency key in A3 |

**Agent Mutation Blocked (runner A3 path): required PASS**
