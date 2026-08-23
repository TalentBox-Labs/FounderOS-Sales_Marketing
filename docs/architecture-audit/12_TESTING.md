# 12 — Testing

Evidence from `tests/`, `pytest.ini`, CI, pre-commit, and `COVERAGE.md`.

---

## Testing framework

| Item | Evidence |
|------|----------|
| Framework | `pytest` (`requirements.txt`, `pytest.ini`) |
| Config | `pytest.ini`: `testpaths = tests`, `pythonpath = .`, `addopts = -ra` |
| Shared fixtures | `tests/conftest.py` (`cms_client`, `mock_llm`, patches for CSV/YAML/runtime, etc.) |

---

## Test inventory

| Metric | Count (repository evidence) |
|--------|-----------------------------|
| Test modules `tests/test_*.py` | 41 |
| Test function definitions matching `test_*` | 223 |

### Test modules present

```
test_analytics.py
test_artifact_crew_guard.py
test_content_quality_checker.py
test_crew.py
test_crew_contract.py
test_crew_qa_input.py
test_crews_unit.py
test_csv_reader.py
test_distribution_bundle_checker.py
test_distribution_crew_guard.py
test_editor_crew_guard.py
test_editor_fence_strip.py
test_editor_seo_hint.py
test_final_frontmatter_lint.py
test_generate_week_fixtures.py
test_generation_crew.py
test_go_live_helpers.py
test_google_sheets_verify.py
test_hashnode_publish.py
test_hashnode_retry.py
test_lead_prospecting_service.py
test_mcp_hub.py
test_metadata_checker.py
test_orchestration_api.py
test_pipeline_orchestrator.py
test_pipeline_runner.py
test_promotion_audit.py
test_prospecting_ui.py
test_reader_tab_sync.py
test_routers_integration.py
test_runner_api.py
test_runtime_apply.py
test_runtime_paths.py
test_sales_api_runner.py
test_sheet_orphan_cleanup.py
test_sheet_sync.py
test_staging_overlay.py
test_tracker_updater.py
test_utilities_unit.py
test_validate_all_tracker_weeks.py
test_validator_steps_integration.py
```

---

## Unit tests (examples by filename)

- Crews: `test_crews_unit.py`, `test_crew.py`, `test_generation_crew.py`, guard tests for artifact/editor/distribution
- Tools: `test_csv_reader.py`, `test_runtime_paths.py`, `test_utilities_unit.py`, checker-specific modules
- Contracts: `test_crew_contract.py`, `test_editor_fence_strip.py`, `test_editor_seo_hint.py`

---

## Integration tests

| Module | Focus evidenced by name/contents patterns |
|--------|-------------------------------------------|
| `test_routers_integration.py` | Router integration via TestClient |
| `test_validator_steps_integration.py` | Validator subprocess/integration |
| `test_pipeline_runner.py` / `test_pipeline_orchestrator.py` | Pipeline flows |
| `test_orchestration_api.py` | Orchestration API |
| `test_sales_api_runner.py` | Sales/prospecting API |
| `test_prospecting_ui.py` | Prospecting UI/API |

---

## API tests

- FastAPI `TestClient` fixture `cms_client` in `conftest.py`
- Modules: `test_runner_api.py`, `test_routers_integration.py`, `test_mcp_hub.py`, sales/orchestration/prospecting API tests

---

## Mocking / fixtures

Evidence in `tests/conftest.py` and individual tests:

- `MagicMock` / `monkeypatch` for LLM, YAML loader, CSV/active content, runtime config
- API key dependency override on FastAPI app
- Temporary paths (`tmp_path`) for staging/content
- Env monkeypatches for CrewAI/Ollama settings

---

## CI tests

`.github/workflows/test.yml`:

1. Matrix Python 3.11, 3.12, 3.13
2. `pip install -r requirements.txt`
3. `python -m pytest tests/ -v`
4. `python scripts/generate_week_fixtures.py --verify` with `CI=true`

Pre-commit (`.pre-commit-config.yaml`):

- `pytest tests/ -q`
- fixture verify script
- gitleaks / private-key / large-file hooks

---

## Coverage

| Source | Evidence |
|--------|----------|
| `COVERAGE.md` | Snapshot dated 2026-06-11; states 140 passed; overall 44% (1380/3108 statements) for `src` coverage run |
| How to regenerate (documented in COVERAGE.md) | `python -m pytest tests/ --cov=src --cov-report=html` |

Live coverage percentage at audit time: **Repository evidence not found** beyond the checked-in `COVERAGE.md` snapshot (no fresh coverage run performed for this audit package).
