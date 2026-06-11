# Code Coverage Report

Generated: 2026-06-11  
Python: 3.13.7  
Tests: 140 passed

## Summary
- **Overall Coverage**: 44% (1380 / 3108 statements covered)
- **Well-Tested Modules** (>80%):
  - `src/crew.py` — 86%
  - `src/tools/final_frontmatter_lint.py` — 89%
  - `src/tools/tracker_updater.py` — 89%
  - `src/tools/pipeline_runner.py` — 83%
  - `src/tools/distribution_bundle_checker.py` — 83%
  - `src/tools/runtime_paths.py` — 87%

- **Partially Tested** (50–80%):
  - `src/generation_crew.py` — 77%
  - `src/tools/csv_reader.py` — 78%
  - `src/tools/content_quality_checker.py` — 68%
  - `src/tools/promotion_audit.py` — 67%
  - `src/tools/hashnode_publish.py` — 61%

- **Not Tested** (0%):
  - `src/main.py` — 0%
  - `src/tools/draft_validator.py` — 0% (runs as subprocess; integration tested)
  - `src/tools/research_mapper.py` — 0% (runs as subprocess; integration tested)
  - `src/tools/structure_checker.py` — 0% (runs as subprocess; integration tested)
  - `src/tools/promote_staged.py` — 0%
  - `src/tools/runtime_manager.py` — 0%
  - `src/tools/validate_all_tracker_weeks.py` — 0% (integration tested)
  - `src/tools/validate_staged.py` — 0%

## Notes

**Validator modules** (draft_validator, research_mapper, structure_checker) show 0% direct unit coverage because they're tested via subprocess integration tests (`test_validator_steps_integration.py`). This is intentional—validators run as CLI modules in production.

**Low-coverage modules** (sheet_sync, google_sheets_verify, reader_tab_sync, etc.) are external integrations with Google Sheets and Hashnode. They require live API keys and are tested manually or via integration suites.

## View Full Report

```bash
open htmlcov/index.html
```

Or run:
```bash
python -m pytest tests/ --cov=src --cov-report=html
```
