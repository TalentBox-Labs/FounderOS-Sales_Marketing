# Founder OS COS-5 Regression Reconciliation

**Gate:** COS-5 focused + COS-4 + COS-3 + tenant remediation + COS-2 + COS-1 + MC04 v2 + D1.x + S3

## COS-5 focused

`tests/test_founder_os_cos5_command_operating_surface.py`

Proofs: eligibility, QD/approval existing paths, cross-tenant denial, booking/follow-up navigate-only, no mutation primitives, no new SoT, refresh after accept, COS-3/4 coexistence.

## Frozen tests

None modified.

## Known residual

Operator optional_tenant paths remain available on `/operator` (pre-existing). COS-5 does not expose them inline.
