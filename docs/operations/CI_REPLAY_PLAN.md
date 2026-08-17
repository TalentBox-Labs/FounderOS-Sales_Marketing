# CI Replay Plan — Post-Outage Verification

**Agent:** Beacon  
**Sprint:** M5.5  
**Date:** 2026-08-10  
**Purpose:** When remote Git CI returns, replay this ladder to certify parity with local M5.5 baseline  

**Secrets:** Document **names only** — never commit values.

---

## 1. Runner setup

```bash
cd "${GITHUB_WORKSPACE:-.}"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-api.txt
```

(Optional: install test deps if split in repo CI today.)

---

## 2. Required environment variables (names only)

| Name | Purpose |
|------|---------|
| `SECRET_KEY` | Runner API / test app boot (required for full suite collection) |
| `HEARTBEAT_ENABLED` | Set to `0` in CI to disable heartbeat side effects |

Optional for **future staging deploy job** (not M5.5):

| Name | Purpose |
|------|---------|
| `CLOUDFLARE_API_TOKEN` | Wrangler / Pages API |
| `CLOUDFLARE_ACCOUNT_ID` | Account scope |

---

## 3. Required services

| Service | M5.5 CI replay |
|---------|----------------|
| PostgreSQL / DB | **Not required** for deployment adapter tests |
| Redis | **Not required** |
| Cloudflare | **Not required** for test replay |
| External HTTP | **Not required** (Static Provider `external_http=False`) |

---

## 4. Test commands (exact order)

```bash
export SECRET_KEY=ci-replay-placeholder
export HEARTBEAT_ENABLED=0

.venv/bin/python -m pytest tests/test_website_deployment.py -q --tb=no
.venv/bin/python -m pytest tests/test_website_engine.py tests/test_static_provider.py -q --tb=no
.venv/bin/python -m pytest tests/test_publishing_engine.py -q --tb=no
.venv/bin/python -m pytest tests/test_editorial_approval.py tests/test_editorial_readiness.py -q --tb=no
.venv/bin/python -m pytest tests/test_routers_integration.py tests/test_content_studio_api.py \
  tests/test_publishing_engine.py::TestPublishingAPI tests/test_publishing_engine.py::TestPublishingUI -q --tb=no

.venv/bin/python -m pytest tests/test_website_deployment.py tests/test_website_engine.py \
  tests/test_static_provider.py tests/test_publishing_engine.py tests/test_routers_integration.py -q --tb=no

.venv/bin/python -m pytest tests/ -q --tb=no
```

---

## 5. Expected test counts

| Step | Expected pass |
|------|---------------|
| Deployment | **7** |
| Website + Static | **24** |
| Publishing | **16** |
| Editorial | **33** |
| UI/API integration | **32** |
| **Focused certification** | **65** |
| **Full suite** | **327 passed** |

---

## 6. Baseline known failures (do not treat as new regressions)

**Failed (8):**

- `tests/test_crews_unit.py::TestQACrew::test_qa_crew_validates_output_format`
- `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_validates_output`
- `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_rejects_output_without_frontmatter`
- `tests/test_utilities_unit.py::TestFileOperations::test_read_file_returns_content`
- `tests/test_utilities_unit.py::TestFileOperations::test_read_file_raises_on_missing_file`
- `tests/test_utilities_unit.py::TestFileOperations::test_save_file_creates_directories`
- `tests/test_utilities_unit.py::TestFileOperations::test_save_file_overwrites_existing`
- `tests/test_utilities_unit.py::TestDataValidation::test_markdown_structure_validation`

**Errors (4):**

- `tests/test_orchestration_api.py::test_orchestration_plan_endpoint_returns_strategy`
- `tests/test_orchestration_api.py::test_orchestration_run_with_mocked_backend_and_audit_persistence`
- `tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads`
- `tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score`

**New regression criterion:** Any failure/error **not** in the lists above after M5.5 freeze.

---

## 7. Deployment checks (optional CI job)

```bash
.venv/bin/python -c "
from pathlib import Path
import tempfile, shutil, json
# Minimal: run tests/test_website_deployment.py logic via pytest instead in CI
"
```

**Preferred:** rely on `tests/test_website_deployment.py` (7 tests) for automated deployment adapter coverage.

---

## 8. Artifact checks (optional manual/scheduled job)

After a fixture publish to `output/website/`:

```bash
.venv/bin/python -c "
from src.tools.website_deployment import DeploymentAdapter
r = DeploymentAdapter().export_package()
assert r.ok, r.message
print(r.deployment_id)
"
```

Verify:

- Public package excludes `metadata.json` / `source.md`  
- `deployment-manifest.json` present  
- SHA-256 entries validate  

---

## 9. Rollback checks (optional manual job)

Replay procedure in [M5_5_ROLLBACK_EVIDENCE.md](M5_5_ROLLBACK_EVIDENCE.md) in a temp directory (no production paths).

**Pass criteria:** `rollback_ok: true`, docroot matches package A after rollback.

---

## 10. Pass/fail criteria for CI replay

| Gate | Pass |
|------|------|
| Focused 65/65 | All pass |
| Full 327/339 | 327 pass; exactly 8 fail + 4 error from baseline lists |
| New regressions | **0** |
| Deployment tests | 7/7 |
| No secrets in logs | Required |

---

## Verdict

**CI Replay Package: READY**
