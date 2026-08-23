# M2 — Architecture & Regression Audit

**Status:** COMPLETE  
**Date:** 2026-08-09  
**Agent:** C — Architecture & Regression Auditor  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
**Architecture:** v2.1 (ADR-002)  
**Prerequisite baseline:** Publishing Engine v1.0 FROZEN ([M1_5_PUBLISHING_BASELINE.md](M1_5_PUBLISHING_BASELINE.md))  
**Implementation under audit:** [M2_WEBSITE_ENGINE_REPORT.md](M2_WEBSITE_ENGINE_REPORT.md)  
**Parallel Agent B:** [FOUNDER_OS_UI_HARDENING_PLAN.md](../governance/FOUNDER_OS_UI_HARDENING_PLAN.md) (`templates/base.html` dead-nav removal only)

**Audit mode:** Read-only code verification + test runs.  
**Write scope:** This document only. Application code was not modified.

---

## Final verdict

| Gate | Result |
|------|--------|
| **Architecture** | **PASS** |
| **New Regressions** | **0** |
| **Boundary Violations** | **0** |
| E7 / M1 frozen contracts | **VALID** |
| Publishing API regression | **NONE** |
| Editorial API regression | **NONE** |
| DB migration | **NONE** |
| New external dependencies | **NONE** |

---

## 1. Scope verified

| Item | Evidence |
|------|----------|
| Website Engine Core package | `src/tools/website_engine/*` (9 modules) |
| M2 focused tests | `tests/test_website_engine.py` |
| Publishing Engine still PLACEHOLDER for website | `src/tools/publishing_engine.py` `_adapter_website` |
| Agent B UI hardening | Dead `/qa`, `/publish`, `/settings` removed from `templates/base.html`; live `/publishing` retained |
| No app-code writes by Agent C | Confirmed — audit doc only |

---

## 2. Architecture boundary checks

### 2.1 Publishing Engine remains orchestration-only — PASS

Verified in `src/tools/publishing_engine.py`:

- Module docstring still declares orchestration-only ownership.
- State machine, job queue, audit, channel registry, human requester gate unchanged in role.
- `_adapter_website` still returns M1 PLACEHOLDER shape:
  - `status: "PLACEHOLDER"`
  - `website_engine_invoked: False`
  - `rendering_performed: False`
  - message states Website Engine not invoked by Publishing in M1 path
- **No import** of `src.tools.website_engine` in Publishing Engine or `runner_api_routers/publishing.py`.
- Job flags remain `orchestration_only: True`, `website_engine: False`, `social_engine: False`, `campaign_engine: False`.

Bridge readiness (`publish_from_job`) exists **inside Website Engine only**; wiring into `_adapter_website` is intentionally deferred (matches M2 report). This preserves Publishing v1.0 baseline tests.

### 2.2 Website Engine owns website-specific behavior — PASS

Verified package owns:

| Concern | Module |
|---------|--------|
| Bundle → content model (`input/{week}/05_Final.md`) | `content_model.py` |
| Slug + canonical URL | `urls.py` |
| Title/description/OG/Schema.org Article | `metadata.py` |
| Markdown → HTML (stdlib converter) | `render.py` |
| Sitemap + RSS contracts | `feeds.py` |
| Provider interface + in-process stub | `provider.py` |
| Channel-compatible result shape | `publish_result.py` |
| Site publish entrypoints | `engine.py` |

Stub provider writes under `output/website/` only; `external_http: false` / `external_api_called: false`. No WordPress/Ghost/HTTP publish.

### 2.3 Internal Founder UI ≠ public Website Engine — PASS

| Surface | Role | Confusion? |
|---------|------|------------|
| Founder Jinja shell (`/`, `/content-studio`, `/editorial`, `/publishing`, …) | Internal ops UI | No |
| Website Engine | Canonical public site render/publish contracts | No |
| Agent B nav fix | Removed dead `/publish` (Go-Live); kept `/publishing` orchestration UI | Reinforces separation |

No Website Engine HTML routes or nav items were added. Templates mention Website Engine only as “not implemented here” on the Publishing queue page — correct ownership messaging.

### 2.4 No Social / Campaign / SEO Engine leaks into M2 — PASS

Grep across `src/tools/website_engine/` found **no** social API, campaign, LinkedIn/Twitter/Instagram/newsletter delivery, SEO scoring, WordPress/Ghost HTTP, or `httpx`/`requests` usage.

Allowed non-leak usages (documented ownership):

- Optional read of `02_SEO_Plan.md` for **description hint only** (`content_model._seo_description_hint`) — not SEO Engine scoring/optimization.
- OpenGraph + Schema.org **site metadata contracts** — Website Engine ownership per v2.1; not Social Engine posting.

Publishing social/newsletter adapters remain `NOT_IMPLEMENTED`.

### 2.5 No API contract regression — PASS

Publishing API (`/api/v1/publishing`):

| Method | Path | Still present |
|--------|------|---------------|
| GET | `/channels` | YES |
| GET | `/jobs` | YES |
| POST | `/jobs` | YES |
| GET | `/{job_id}` | YES |
| POST | `/{job_id}/publish` | YES |
| POST | `/{job_id}/retry` | YES |
| POST | `/{job_id}/cancel` | YES |

Response still exposes `orchestration_only: True`, `website_engine: False`, `social_engine: False`. No Website Engine endpoints added under Publishing.

Editorial API (`/api/v1/editorial`) unchanged in shape:

| Method | Path | Frozen rule |
|--------|------|-------------|
| GET | `/readiness/{content_id}` | Read-only readiness |
| GET | `/pending` | Additive E7 |
| GET | `/{content_id}` | Additive E7 |
| POST | `/{content_id}/approve` | Human approve; promote only |
| POST | `/{content_id}/reject` | Audit only |
| POST | `/{content_id}/request-changes` | Audit only |

`authorizes_publish: false` still set on approval views (FDR-003).

Focused contract suites green: publishing 16, editorial 19, content studio UI 13.

### 2.6 No DB migration — PASS

- No new/changed Alembic revision under `alembic/versions` (directory absent / no migration artifacts for M2).
- Website Engine consumes filesystem editorial bundles; invents no CMS/DB publish queue.
- `requirements*.txt` / dependency manifests show no M2 migration tooling changes.

### 2.7 No new external dependencies — PASS

Website Engine imports are **stdlib + existing repo modules only**:

`dataclasses`, `datetime`, `html`, `json`, `pathlib`, `re`, `typing`, `urllib.parse`, `xml.etree.ElementTree`, `src.tools.runtime_paths`.

No `markdown`, BeautifulSoup, feedgen, lxml, WordPress/Ghost SDKs added to `requirements.txt` / `requirements-api.txt` / `requirements-revenue.txt`. No `pyproject.toml` present to mutate.

### 2.8 E7 / M1 frozen contracts remain valid — PASS

| Freeze | Status after M2 |
|--------|-----------------|
| E7 human-only approval; no publish authorization | VALID — editorial responses still `authorizes_publish: false`; Publishing still requires separate human publish job |
| M1 Publishing state machine / channel registry | VALID — PLACEHOLDER website adapter retained |
| M1 channel result required fields | VALID on Publishing path (`ok`, `status`, `channel`, `owner_engine`, `message`) |
| M1.5 `website_engine_invoked: false` **via Publishing adapter** | VALID — adapter still false; Website Engine may return true only when called directly (bridge not wired) |
| M1.5 checklist: replace PLACEHOLDER behind channel interface without expanding Publishing API | VALID — deferred bridge matches checklist §4 |

---

## 3. Intentional non-wiring note (not a violation)

M2 delivers Website Engine Core **without** replacing `_adapter_website`.  
Publishing v1.0 baseline therefore remains green (`website_engine_invoked is False` in `tests/test_publishing_engine.py`).

This is an accepted staging boundary: Website Engine is ready; Publishing bridge is a coordinated follow-up requiring a new Publishing baseline (v1.1) when wired.

---

## 4. Test results

**Environment:**

```bash
SECRET_KEY=test-secret-key-for-pytest-m2-parallel-32 HEARTBEAT_ENABLED=0
.venv/bin/python -m pytest
```

### 4.1 Focused suites

| Suite | Result |
|-------|--------|
| `tests/test_website_engine.py` | **12 passed** |
| `tests/test_publishing_engine.py` | **16 passed** |
| `tests/test_editorial_approval.py` | **19 passed** |
| `tests/test_content_studio_ui.py` | **13 passed** |
| **Combined focused** | **60 passed** |

### 4.2 Full suite (`tests/`)

| Metric | M1.5 baseline | M2 audit run | Delta |
|--------|---------------|--------------|-------|
| Passed | 296 | **308** | **+12** (matches new `test_website_engine.py`) |
| Failed | 8 | **8** | 0 |
| Errors | 4 | **4** | 0 |
| New regressions | 0 expected | **0** | — |

### 4.3 Failing / error test IDs (historical — unchanged set)

**FAILED (8)** — crews unit QA/Editor + utilities unit file ops/markdown:

1. `tests/test_crews_unit.py::TestQACrew::test_qa_crew_validates_output_format`
2. `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_validates_output`
3. `tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_rejects_output_without_frontmatter`
4. `tests/test_utilities_unit.py::TestFileOperations::test_read_file_returns_content`
5. `tests/test_utilities_unit.py::TestFileOperations::test_read_file_raises_on_missing_file`
6. `tests/test_utilities_unit.py::TestFileOperations::test_save_file_creates_directories`
7. `tests/test_utilities_unit.py::TestFileOperations::test_save_file_overwrites_existing`
8. `tests/test_utilities_unit.py::TestDataValidation::test_markdown_structure_validation`

**ERROR (4)** — orchestration API + prospecting UI:

1. `tests/test_orchestration_api.py::test_orchestration_plan_endpoint_returns_strategy`
2. `tests/test_orchestration_api.py::test_orchestration_run_with_mocked_backend_and_audit_persistence`
3. `tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads`
4. `tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score`

**New failing tests vs historical set:** **none**.  
Classification as historical is based on exact ID match to the M1.5-known categories (crews_unit QA/Editor, utilities_unit file ops/markdown, orchestration_api errors, prospecting_ui errors) plus unchanged fail/error counts.

---

## 5. Checklist summary

| # | Check | Verdict |
|---|-------|---------|
| 1 | Publishing Engine orchestration-only | **PASS** |
| 2 | Website Engine owns website-specific behavior | **PASS** |
| 3 | Internal Founder UI not confused with Website Engine | **PASS** |
| 4 | No Social/Campaign/SEO leaks into M2 | **PASS** |
| 5 | No API contract regression (publishing/editorial) | **PASS** |
| 6 | No DB migration | **PASS** |
| 7 | No new external dependencies | **PASS** |
| 8 | E7/M1 frozen contracts remain valid | **PASS** |

---

## 6. Recommendations (informational; out of Agent C write scope)

1. When wiring `_adapter_website` → `publish_from_job`, open Publishing baseline **v1.1** and update PLACEHOLDER assertions deliberately.
2. Keep Founder UI (`/publishing`) and Website Engine public-site ownership wording distinct in future templates.
3. Historical 8 fails / 4 errors remain outside M2; track separately from Marketing OS website work.

---

## 7. One-line certification

**M2 Website Engine Core is architecture-compliant with zero new regressions; Publishing remains PLACEHOLDER-orchestrated; E7/M1 contracts hold.**
