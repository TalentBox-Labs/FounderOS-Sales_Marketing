# MC06 — Test Evidence

**Sprint:** FOUNDER OS MC06  
**Date:** 2026-08-13  
**Suite:** `tests/test_mc06_commercial_outcome.py`

Covered:

- valid eligible closed-won handoff + accept
- invalid Deal rejection
- non-closed-won / closed_lost rejection
- duplicate submission safety (same Deal, new outcome_id)
- idempotent retry (handoff + accept)
- provenance preservation
- authorized human path
- unauthorized / agent / AI / spoofed `requested_by`
- acceptance audit
- rejection audit
- Sales state protection
- Revenue boundary (no Client/invoice/billing)
- no shared SoT
- A3.5 `commercial_outcome_emitted: false` preserved
- A4.5 Contact.status path untouched
- MC04.5 accept still `commercial_outcome_emitted: false`
- runner 403/422 paths

## Results (2026-08-13)

| Suite | Result |
|-------|--------|
| MC06 focused | **28/28** |
| A3.5 | **15/15** |
| A4.5 | **15/15** |
| MC04.5 | **12/12** |
| A1.5 | **15/17** (2 historical ENVIRONMENT_DEPENDENCY errors) |
| UI2.5 | **20/20** |
| Full regression | **519 passed**; 8 failed; 4 errors |

Historical failures unchanged (`test_crews_unit` 3, `test_utilities_unit` 5, `test_orchestration_api` 2 errors, `test_prospecting_ui` 2 errors). **New regressions: 0.**

Command:

```
SECRET_KEY=test-secret-key-for-pytest-only-not-production \
  .venv/bin/python -m pytest tests/test_mc06_commercial_outcome.py
```
