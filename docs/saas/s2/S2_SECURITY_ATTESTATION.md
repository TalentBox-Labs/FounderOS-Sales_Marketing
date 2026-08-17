# SaaS S2 — Security Attestation

## Phase 0 — Browser auth precondition

| Control | S1.5 status | S2 classification |
|---------|-------------|---------------------|
| JWT / Cookie (HttpOnly, SameSite=Lax, HS256) | PARTIAL | **SUFFICIENT_FOR_BOUNDED_S2** |
| CSRF (SameSite=Lax only) | PARTIAL | **SUFFICIENT_FOR_BOUNDED_S2** |

S2 proceeds with documented limitations from Identity Foundation Baseline v1.0. SaaS S1.6 recommended before public multi-tenant onboarding.

## S2 additions

- Server-derived tenant authority
- Membership validation on org hints
- VIEWER mutation block
- Cross-tenant ID-only mutation guards on bounded slice

## Client spoofing

Organization cookie without membership → 403. Role in client body ignored.
