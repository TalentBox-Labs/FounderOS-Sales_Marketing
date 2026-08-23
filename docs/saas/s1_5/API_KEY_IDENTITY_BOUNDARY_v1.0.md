# API KEY IDENTITY BOUNDARY v1.0

**STATUS: FROZEN**  
**Sprint:** FOUNDER OS SaaS S1.5  
**Secret:** `RUNNER_API_KEY`  
**Verifier:** `runner_api_routers.utils._verify_api_key`

## Classification

| Class | Applies |
|-------|---------|
| HUMAN_AUTH | **NO — PROHIBITED** |
| SERVICE_AUTH | **YES** |
| LEGACY_INTERNAL | **YES** |
| TEST_ONLY | Partial (many tests override dependency) |

## Frozen invariant

```
RUNNER_API_KEY  ↛  HUMAN IdentityContext
RUNNER_API_KEY  →  SERVICE IdentityContext (is_human=False)
```

Successful Bearer match via `identity_context_for_request` yields `service_identity()`.

SERVICE cannot `bind_requested_by`.

## Scope retained

Pipeline / orchestration / CRM JSON routes may continue requiring the API key where already configured. Removal is **not** part of S1.5.

## Human path

Cookie session from `/login` only.
