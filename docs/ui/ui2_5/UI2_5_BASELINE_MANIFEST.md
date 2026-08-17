# UI2.5 — Baseline Manifest

**STATUS: FROZEN**  
**Version:** Executive Cockpit v1.0  
**Date:** 2026-08-13

---

## Frozen runtime files

| File | Role |
|------|------|
| `runner_api_routers/ui.py` | `GET /cockpit` page route |
| `runner_api_routers/cockpit.py` | Cockpit API + mutation proxies |
| `revenue_os/services/cockpit_read_model.py` | Read-model composition |
| `templates/cockpit.html` | Cockpit Jinja template |
| `templates/base.html` | Shell nav + Founder OS branding |
| `runner_api.py` | `cockpit_router` include |
| `.env.example` | `FOUNDER_OS_OPERATOR_NAME` documentation |

## Frozen test files

| File | Purpose |
|------|---------|
| `tests/test_ui2_5_cockpit_baseline_freeze.py` | UI2.5 freeze regression (20 tests) |
| `tests/test_ui2_executive_cockpit.py` | UI2 cockpit tests (23 tests) |
| `tests/test_ui1_1_mutation_authority.py` | UI1.1 authority tests (10 tests) |

## Frozen documentation

| Document |
|----------|
| `docs/ui/ui2_5/UI2_5_EXECUTIVE_COCKPIT_BASELINE_v1.0.md` |
| `docs/ui/ui2_5/UI2_5_COCKPIT_SOURCE_MANIFEST_v1.0.md` |
| `docs/ui/ui2_5/UI2_5_COCKPIT_ACTION_AUTHORITY_v1.0.md` |
| `docs/ui/ui2_5/UI2_5_KNOWN_TEST_EXCEPTIONS.md` |
| `docs/ui/ui2_5/UI2_5_BASELINE_MANIFEST.md` |

## UI2 implementation docs (reference, not re-frozen)

| Document |
|----------|
| `docs/ui/ui2/UI2_IMPLEMENTATION_REPORT.md` |
| `docs/ui/ui2/UI2_DATA_SOURCE_MAP.md` |
| `docs/ui/ui2/UI2_ACTION_AUTHORITY_MAP.md` |

## Change policy post-freeze

Any change to frozen semantic behavior requires explicit baseline version bump (v1.1+) and updated freeze attestation.

## UI2.5 implementation delta

| Category | Count |
|----------|------:|
| Feature code changes | 0 |
| Runtime changes | 0 |
| Test additions | 1 file (20 tests) |
| Documentation | 5 files |
