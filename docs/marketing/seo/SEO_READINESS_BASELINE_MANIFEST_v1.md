# SEO Readiness Baseline Manifest v1.0

**Sprint:** S1.5  
**Agent:** LEDGER  
**Baseline name:** SEO READINESS ENGINE v1.0  
**Baseline version:** v1.0  
**Status:** FROZEN  
**Freeze date:** 2026-08-11

---

## References

| Artifact | Path |
|----------|------|
| Engine baseline | `docs/marketing/seo/S1_5_SEO_READINESS_BASELINE.md` |
| Rule registry | `docs/marketing/seo/SEO_READINESS_RULE_REGISTRY_v1.md` |
| API contract | `docs/marketing/seo/SEO_READINESS_API_CONTRACT_v1.md` |
| UI contract | `docs/marketing/seo/SEO_READINESS_UI_CONTRACT_v1.md` |
| Security attestation | `docs/marketing/seo/S1_5_SECURITY_ATTESTATION.md` |
| Origin contract (S0) | `docs/marketing/seo/S0_SITE_ORIGIN_CONTRACT.md` |
| Architecture (S0) | `docs/marketing/seo/S0_SEO_ENGINE_ARCHITECTURE.md` |
| Domain governance | `docs/governance/SEO_DOMAIN_DECISION_PENDING.md` |
| Architecture platform | Architecture v2.2 (frozen) |

---

## Relevant implementation files

```
src/tools/seo_engine/__init__.py
src/tools/seo_engine/policy.py
src/tools/seo_engine/models.py
src/tools/seo_engine/extract.py
src/tools/seo_engine/rules.py
src/tools/seo_engine/engine.py
src/tools/seo_engine/artifacts.py
src/tools/seo_engine/audit.py
src/tools/seo_engine/readiness.py
src/tools/site_origin.py
runner_api_routers/seo.py          # readiness GET routes only in this freeze
runner_api_routers/ui.py           # /seo routes
templates/seo_readiness.html
templates/seo_readiness_detail.html
templates/base.html                # nav link
```

---

## Relevant tests

```
tests/test_seo_readiness_engine.py
tests/test_seo_readiness.py
tests/test_site_origin.py
```

Focused gate: **34/34**

---

## Domain dependency

| Host | Status |
|------|--------|
| `workcrew.ai` | DEPRECATED FOR FUTURE PRODUCTION |
| `founderos-staging.pages.dev` | TEMPORARY INFRASTRUCTURE ONLY |
| Future production domain | PENDING FOUNDER RATIFICATION |

**Production SEO activation:** BLOCKED PENDING DOMAIN

---

## Known historical failures (full suite leave-behinds)

Verified identical to S1:

### FAILED (8)

- `tests/test_crews_unit.py::TestQACrew::test_qa_crew_validates_output_format`
- `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_validates_output`
- `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_rejects_output_without_frontmatter`
- `tests/test_utilities_unit.py::TestFileOperations::test_read_file_returns_content`
- `tests/test_utilities_unit.py::TestFileOperations::test_read_file_raises_on_missing_file`
- `tests/test_utilities_unit.py::TestFileOperations::test_save_file_creates_directories`
- `tests/test_utilities_unit.py::TestFileOperations::test_save_file_overwrites_existing`
- `tests/test_utilities_unit.py::TestDataValidation::test_markdown_structure_validation`

### ERROR (4) — setup failures

- `tests/test_orchestration_api.py::test_orchestration_plan_endpoint_returns_strategy`
- `tests/test_orchestration_api.py::test_orchestration_run_with_mocked_backend_and_audit_persistence`
- `tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads`
- `tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score`

Full: **361 passed; 8 failed; 4 errors** · New regressions: **0**

---

## Feature code changes in S1.5

**0** (documentation / governance / verification only)

---

## Change control

Any change to frozen contracts requires an explicit subsequent sprint, compatibility assessment, tests, and documented rationale.
