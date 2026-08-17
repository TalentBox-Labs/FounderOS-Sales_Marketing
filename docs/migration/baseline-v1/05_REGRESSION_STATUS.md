# 05 — Regression Status

Evidence: [05_REGRESSION_ANALYSIS.md](../../runtime-certification/05_REGRESSION_ANALYSIS.md), [07_PRODUCTION_READINESS_REVIEW.md](../../runtime-certification/07_PRODUCTION_READINESS_REVIEW.md), [E2_IMPLEMENTATION.md](../content-studio/E2_IMPLEMENTATION.md), [03_TEST_RESULTS.md](../../runtime-verification/03_TEST_RESULTS.md)

---

## Existing repository failures

**8 FAILED** (unchanged leave-behinds since Sprint C intentional class-B set):

| Test |
|------|
| `TestQACrew::test_qa_crew_validates_output_format` |
| `TestEditorCrew::test_editor_crew_validates_output` |
| `TestEditorCrew::test_editor_crew_rejects_output_without_frontmatter` |
| `TestFileOperations::test_read_file_returns_content` |
| `TestFileOperations::test_read_file_raises_on_missing_file` |
| `TestFileOperations::test_save_file_creates_directories` |
| `TestFileOperations::test_save_file_overwrites_existing` |
| `TestDataValidation::test_markdown_structure_validation` |

Classification: stale / obsolete contracts + architecture debt (abstract `BaseCrew`). **Non-blocking.**  
Detail: [07_PRODUCTION_READINESS_REVIEW.md](../../runtime-certification/07_PRODUCTION_READINESS_REVIEW.md).

---

## Resolved failures

| Item | When | Evidence |
|------|------|----------|
| Marketing generate `ModuleNotFoundError` for `revenue_os.agents.marketing_crew` | D0 | [D0_IMPLEMENTATION.md](../../implementation/D0_IMPLEMENTATION.md) |
| Full suite **4 errors** (Sprint C) | Cleared by D1 | [01_TEST_CERTIFICATION.md](../../runtime-certification/01_TEST_CERTIFICATION.md) |
| Passed count 216 → 220 | D1 | Same |
| Passed count 220 → 228 | E2 (+8 Content Studio tests) | [E2_IMPLEMENTATION.md](../content-studio/E2_IMPLEMENTATION.md) |

---

## New failures

**None** attributable to D0 or E2.

E2 failure set identical to D1.5 leave-behinds.

---

## Current status

| Metric | Value |
|--------|-------|
| Full pytest passed | 228 |
| Full pytest failed | 8 |
| Full pytest errors | 0 |
| D0 regressions | **NO** |
| E2 new failures | **0** |

---

## Sprint E2 architectural regression statement

# Sprint E2 introduced no architectural regressions.

Additive read-only router only; existing API contracts preserved; SoT unchanged; no DB schema change.
