# S1.5 — Baseline Manifest

**Baseline:** FOUNDER OS IDENTITY FOUNDATION BASELINE v1.0  
**Status:** FROZEN  
**Date:** 2026-08-15  
**Freeze sprint:** FOUNDER OS SaaS S1.5  
**Implementation sprint:** FOUNDER OS SaaS S1

## Artifacts

| Path | Role |
|------|------|
| `docs/saas/s1_5/IDENTITY_FOUNDATION_BASELINE_v1.0.md` | Behavioral baseline |
| `docs/saas/s1_5/CANONICAL_USER_CONTRACT_v1.0.md` | User identity semantics |
| `docs/saas/s1_5/IDENTITY_CONTEXT_CONTRACT_v1.0.md` | IdentityContext |
| `docs/saas/s1_5/AUTHENTICATION_CONTRACT_v1.0.md` | Auth behavior |
| `docs/saas/s1_5/AUTH_COOKIE_TOKEN_SECURITY_ATTESTATION.md` | Cookie/JWT/CSRF |
| `docs/saas/s1_5/HUMAN_SERVICE_AGENT_AI_SEPARATION_v1.0.md` | Principal separation |
| `docs/saas/s1_5/REQUESTED_BY_SERVER_BINDING_v1.0.md` | Trusted actor binding |
| `docs/saas/s1_5/API_KEY_IDENTITY_BOUNDARY_v1.0.md` | RUNNER_API_KEY boundary |
| `docs/saas/s1_5/ROLE_VOCABULARY_v1.0.md` | Role vocab; RBAC deferred |
| `docs/saas/s1_5/OWNER_BOOTSTRAP_CONTRACT_v1.0.md` | Bootstrap Owner |
| `docs/saas/s1_5/TENANT_CONTEXT_EXTENSION_BOUNDARY_v1.0.md` | S2 seam |
| `docs/saas/s1_5/S1_5_KNOWN_TEST_EXCEPTIONS.md` | Exceptions register |
| `docs/saas/s1_5/S1_5_RUNTIME_CHANGE_RECONCILIATION.md` | S1 runtime ×2 |
| `docs/saas/s1_5/S1_5_BASELINE_MANIFEST.md` | This manifest |

## Tests

| Path | Role |
|------|------|
| `tests/test_saas_s1_5_identity_foundation_baseline_freeze.py` | Freeze suite |
| `tests/test_saas_s1_identity_foundation.py` | S1 focused (26) |

## Runtime evidence map (verification)

| Concern | Path |
|---------|------|
| User model | `revenue_os/models/user.py` |
| Password / JWT helpers | `revenue_os/auth.py` |
| IdentityContext | `revenue_os/services/identity_context.py` |
| Login/logout/cookie | `runner_api_routers/identity.py` |
| Trusted actor adapter | `runner_api_routers/cockpit.py` → `resolve_trusted_human` |
| HTML gate | `runner_api_routers/ui.py` |
| Process wiring | `runner_api.py` |
| API key verify | `runner_api_routers/utils.py` |

## Change control (S1.5 freeze sprint)

| Item | Count |
|------|------:|
| Feature code changes | 0 |
| Runtime changes | 0 |
| Database migrations | 0 |
| External integrations | 0 |
| Credentials committed | 0 |
| Frozen business contract changes | 0 |

## Parents preserved

A1.5 · A3.5 · A4.5 · MC04.5 · MC06.5 · UI2.5 · OF1.5 · MDG1.5 — **8/8 UNCHANGED**

## Next

SaaS S2 — ORGANIZATION + TENANT CONTEXT & QUERY ISOLATION  
Do not implement in S1.5.
