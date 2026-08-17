# 07 — Parity Test Plan

Sprint E1 — Analysis only  
Do **not** write tests in this sprint. Plan only.

---

## Required coverage (before/after implementation)

| Capability | Assertion | Side-effect constraints |
|------------|-----------|-------------------------|
| Create content | If implemented: new tracker row and/or week profile appears; else document DEFERRED | No publish calls |
| Read content (list) | JSON/HTML list returns tracker rows with stable IDs/titles | Read-only |
| Read content (detail) | Detail includes status, paths, artifact presence | Read-only |
| Update/edit content | Metadata fields persist to Founder SoT (tracker and/or frontmatter per ADR) | No n8n/Sheets required |
| Status/lifecycle | Stage/status transition updates Founder fields via adapter | No auto-publish |
| Metadata preservation | Mapped fields round-trip without loss for MAP DIRECTLY keys | — |
| Artifact/path preservation | `draft_path` / `final_output_path` / `_week_artifacts` unchanged unless intentionally edited | — |
| API contract | Existing `/weeks`, `/pipeline`, pipeline POSTs unchanged (backward compatible) | Additive APIs only |
| UI rendering | Weeks/detail still 200; new Studio views 200 when enabled | Marketing UI Known 500 unrelated |
| Database persistence | If no DB unit: assert filesystem/tracker persistence; if Article used later: ORM tests | Default: **no DB required** |
| No publishing side effects | Studio tests must not call `/api/publish*` or n8n | Mock network |
| No external side effects | No live Sheets/Google/LinkedIn | Offline fixtures |

---

## Existing Founder tests to reuse

| Test | File | Parity role |
|------|------|-------------|
| `TestUIPages::test_weeks_page_lists_content` | `tests/test_routers_integration.py` | List UI baseline |
| `test_week_detail_returns_specific_week` | same | Detail UI baseline |
| `test_week_detail_returns_404_for_missing_week` | same | Negative detail |
| `test_invalid_week_id_format_rejected` | same | ID validation |
| `test_get_active_content_*` | `tests/test_csv_reader.py`, `test_utilities_unit.py` | Active content resolution |
| `test_update_tracker_*` | `tests/test_tracker_updater.py` | Status write patterns |
| `test_artifact_paths_*` / staging / frontmatter lint | multiple under `tests/` | Path + metadata contracts |
| Pipeline structure tests | `test_routers_integration.py`, `test_runner_api.py` | Ensure ops APIs unchanged |

---

## CMS tests (reference only — not runnable as Founder suite)

| Test | Limitation |
|------|------------|
| `workcrew-cms-os/tests/smoke_test.py` | Manifest/stats oriented; not Founder |
| `test_w03_publish.py` | Expects `GET /api/content/<id>` missing on top-level CMS app; publish-focused |

**Do not port CMS tests blindly.**

---

## Missing tests (to add in implementation sprint)

1. `GET` Content Studio list JSON over `tracker.csv` (shape + auth)  
2. `GET` Content Studio detail JSON (artifacts + status projection)  
3. `POST` metadata update → tracker/frontmatter (when edit lands)  
4. `POST` lifecycle/stage adapter (when stage lands)  
5. Regression: existing `/weeks` HTML unchanged  
6. Negative: unknown content id → 404  
7. Guarantee: update/stage paths do not invoke publish/n8n (mock assert)  
8. Calendar/Kanban UI smoke (when UX port lands)  
9. ID adapter unit tests (`W01-001` ↔ `W01`) if dual IDs supported  

---

## Gate criteria for “parity enough to proceed”

| Gate | Bar |
|------|-----|
| Read parity | List + detail over Founder SoT green |
| Write parity | Deferred until edit/stage unit; must not block read unit |
| No regression | Integration 18/18 + full suite not worse than Baseline v1.1 (220/8/0) |
| No publish coupling | Explicit test or code review checklist |
