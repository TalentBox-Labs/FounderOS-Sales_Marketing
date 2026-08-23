# E6A — Editorial Parity Test Plan

Do not write tests in E6A. Plan only.

---

## Parity dimensions

| Dimension | Assert | Existing Founder tests to reuse | Missing |
|-----------|--------|----------------------------------|---------|
| Draft input preserved | Staging/canonical `04_Draft.md` unchanged by validate-only | staging/guard tests | e2e promote+edit |
| Editor processing | Editor produces `05_Final.md` from draft under staging | `test_editor_*`, `test_crews_unit.py` | API `/edit` success with staging args |
| QA invocation | Optional QACrew soft-fail path | `test_pipeline_runner.py` | enable_crewai_qa default policy test |
| Validation | DEFAULT_VALIDATORS produce reports | `test_validator_steps_integration.py`, `test_validate_all_tracker_weeks.py` | dedicated unit for structure/draft/research |
| Artifact output | Final frontmatter schema | `test_final_frontmatter_lint.py`, `test_metadata_checker.py` | — |
| Failure behavior | Non-zero exit on gate fail; no silent pass | pipeline/validate_staged | promote without approver (exists in code; strengthen test) |
| No silent fallback | No demo content on API error | Content Studio patterns | editorial readiness API (future) |
| No publishing side effect | `/validate` does not go-live; promote ≠ publish | pipeline validate contract | explicit editorial readiness test |
| Brand boundary | Validators enforce; Brand Guide not mutated | draft_validator banned claims | brand ownership regression |
| SEO boundary | metadata validates; SEO plan not rewritten by validators | metadata + research_mapper | editor SEO hint already tested |
| Approval behavior | promote requires approver | partial audit tests | dedicated promote CLI test |
| Existing API contract | Content Studio GET unchanged | `test_content_studio_*` | — |

---

## First-unit test focus (readiness read model)

1. Readiness endpoint/page renders for known `content_id`
2. Surfaces existing QA report presence/verdicts without re-running crews
3. Uses tracker `status`/`qa_status` exact strings (no invented lifecycle)
4. Explicit error if reports/tracker unavailable
5. GET only — no POST/PUT/PATCH/DELETE
6. No sheet_sync / OpenClaw / publish calls
7. Content Studio list/detail/kanban unchanged
8. Malformed week id → 400

---

## CMS ritual parity (later, not first unit)

Map each of 6 CMS tests to Founder coverage:

| CMS ritual | Founder today | Gap |
|------------|---------------|-----|
| hallucination-gate | partial (draft claims / QACrew) | checklist adapt |
| brand-voice | banned phrases + Brand Guide | ritual score shape |
| cta-clarity | quality/checklist partial | explicit ritual |
| visual-caption | weak/none in default validators | DEFER |
| link-capture | partial | DEFER |
| grammar-fluency | QACrew optional | DEFER |
