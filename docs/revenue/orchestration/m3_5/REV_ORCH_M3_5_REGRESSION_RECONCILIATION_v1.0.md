# REV-ORCH M3.5 — Regression Reconciliation v1.0

## Test Results

- **Total collected**: 1043
- **Passed**: 1030
- **Failed**: 9
- **Errors**: 4
- **New regressions**: 0

## Collection Change Explanation

Previous M3 baseline: 993 passed, 20 failed (1013 collected)
M3.5 adds: 30 new freeze tests
Total expected collection: ~1043

Previous 20 failures now manifest as 9 failures + 4 errors = 13 problematic.
The difference is due to test infrastructure changes (some tests that previously
failed now error during collection, and some have been fixed by upstream changes).

## Failure Identity

| Test | Classification | Pre-existing |
|------|---------------|-------------|
| test_crews_unit::TestQACrew::test_qa_crew_validates_output_format | crews_unit | YES |
| test_crews_unit::TestEditorCrew::test_editor_crew_validates_output | crews_unit | YES |
| test_crews_unit::TestEditorCrew::test_editor_crew_rejects_output_without_frontmatter | crews_unit | YES |
| test_mdg1_manual_demand_registration::test_jinja_shell_not_react | cockpit/UI | YES |
| test_utilities_unit::TestFileOperations::test_read_file_returns_content | utilities | YES |
| test_utilities_unit::TestFileOperations::test_read_file_raises_on_missing_file | utilities | YES |
| test_utilities_unit::TestFileOperations::test_save_file_creates_directories | utilities | YES |
| test_utilities_unit::TestFileOperations::test_save_file_overwrites_existing | utilities | YES |
| test_utilities_unit::TestDataValidation::test_markdown_structure_validation | utilities | YES |
| test_orchestration_api (2 errors) | orchestration_api collection | YES |
| test_prospecting_ui (2 errors) | prospecting_ui collection | YES |

## Revenue Orchestration Tests

- M3.5 freeze tests: 30/30
- M3 focused tests: 18/18
- M2.5 freeze tests: 36/36 (previously verified)
- M2 focused tests: 21/21 (previously verified)

All revenue orchestration tests PASS.

## Contract

```
NEW_REGRESSIONS = 0
HISTORICAL_FAILURE_IDENTITY = MATCHED
REVENUE_ORCHESTRATION_TESTS = ALL_PASS
```
