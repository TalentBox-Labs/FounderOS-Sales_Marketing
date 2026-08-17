# 06 — Architecture Decision Log

Decisions evidenced across Sprints A–E2. Status: **Accepted** | **Deferred** | **Rejected**.

---

| ID | Decision | Status | Evidence |
|----|----------|--------|----------|
| ADR-M01 | Founder OS is the canonical product and engineering repository | **Accepted** | [15_BASELINE_FREEZE.md](../../architecture-audit/15_BASELINE_FREEZE.md), [05_EXECUTIVE_SUMMARY.md](../05_EXECUTIVE_SUMMARY.md) |
| ADR-M02 | CMS (`CMS_OS_V1` docs + `workcrew-cms-os` executable) is capability reference only | **Accepted** | [01_CAPABILITY_MATRIX.md](../01_CAPABILITY_MATRIX.md), [07_REPOSITORY_STATUS.md](07_REPOSITORY_STATUS.md) |
| ADR-M03 | Blind repository merge of CMS into Founder is rejected | **Rejected** | [02_CONSOLIDATION_STRATEGY.md](../02_CONSOLIDATION_STRATEGY.md), Sprint B |
| ADR-M04 | Architecture Baseline v1.0 frozen; no redesign during migration | **Accepted** | [15_BASELINE_FREEZE.md](../../architecture-audit/15_BASELINE_FREEZE.md) |
| ADR-M05 | Slice 0: repair Founder marketing generate path before CMS publish migration | **Accepted** (implemented D0) | [03_MIGRATION_SLICES.md](../03_MIGRATION_SLICES.md), [D0_IMPLEMENTATION.md](../../implementation/D0_IMPLEMENTATION.md) |
| ADR-M06 | Read-first Content Studio migration approved (list/detail before write/UX) | **Accepted** (implemented E2) | [09_FIRST_IMPLEMENTATION_UNIT.md](../content-studio/09_FIRST_IMPLEMENTATION_UNIT.md), [E2_IMPLEMENTATION.md](../content-studio/E2_IMPLEMENTATION.md) |
| ADR-M07 | Content Studio implemented natively on Founder SoT (`tracker.csv` + `input/`) | **Accepted** | [04_CONTENT_STUDIO_READ_BASELINE.md](04_CONTENT_STUDIO_READ_BASELINE.md) |
| ADR-M08 | CMS Flask runtime not imported into Founder | **Accepted** | [03_FILE_MIGRATION_MANIFEST.md](../content-studio/03_FILE_MIGRATION_MANIFEST.md) |
| ADR-M09 | Google Sheets not imported as Content Studio SoT | **Accepted** | [06_DEPENDENCY_BOUNDARY.md](../content-studio/06_DEPENDENCY_BOUNDARY.md) |
| ADR-M10 | OpenClaw runtime not imported; playbooks may be deferred separately | **Deferred** | [01_CAPABILITY_MATRIX.md](../01_CAPABILITY_MATRIX.md) |
| ADR-M11 | n8n workflow library merge deferred to Automation/Publishing slices | **Deferred** | [03_MIGRATION_SLICES.md](../03_MIGRATION_SLICES.md) |
| ADR-M12 | Writing/edit/stage lifecycle requires ADR before implementation | **Deferred** | [04_DATA_MODEL_MAPPING.md](../content-studio/04_DATA_MODEL_MAPPING.md), [08_RISK_REGISTER.md](../content-studio/08_RISK_REGISTER.md) |
| ADR-M13 | Repository governance: CMS REFERENCE ONLY; Founder ACTIVE | **Accepted** | [07_REPOSITORY_STATUS.md](07_REPOSITORY_STATUS.md) |
| ADR-M14 | Runtime Baseline v1.1 frozen with PARTIAL status and 0 blockers | **Accepted** | [08_RUNTIME_BASELINE_V1_1.md](../../runtime-certification/08_RUNTIME_BASELINE_V1_1.md) |
| ADR-M15 | Stale 8 unit-test failures left intentional (non-blocking) | **Accepted** | [07_PRODUCTION_READINESS_REVIEW.md](../../runtime-certification/07_PRODUCTION_READINESS_REVIEW.md) |

---

## Summary counts

| Status | Count |
|--------|------:|
| Accepted | 11 |
| Deferred | 3 |
| Rejected | 1 |
