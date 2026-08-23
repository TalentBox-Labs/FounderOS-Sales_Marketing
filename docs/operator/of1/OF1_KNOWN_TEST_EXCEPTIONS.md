# OF1 — Known Test Exceptions

**Sprint:** FOUNDER OS OF1  
**Date:** 2026-08-13

OF1 focused suite: no exceptions (required 100%).

Inherited A1.5 (unchanged):

| Test | Class |
|------|-------|
| `test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads` | ENVIRONMENT_DEPENDENCY |
| `test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score` | ENVIRONMENT_DEPENDENCY |

Full-regression historical identity unchanged: 8 FAILED (`test_crews_unit` 3, `test_utilities_unit` 5); 4 ERROR (`test_orchestration_api` 2, `test_prospecting_ui` 2).
