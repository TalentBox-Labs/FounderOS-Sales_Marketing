# E2 — Content Studio Read API Implementation

Sprint E2 — Small implementation slice  
Date: 2026-08-09  
Repository: `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`

---

# Scope

Implemented **only** the approved first Content Studio unit:

- Read-only JSON **list** endpoint over Founder `tracker.csv`
- Read-only JSON **detail** endpoint over Founder `tracker.csv` + `input/` artifact presence via `_week_artifacts`

**Not implemented:** write/create/edit/stage/publish/schedule/UI redesign/DB/CMS Sheets/n8n/OpenClaw.

Source of truth unchanged: `tracker.csv` + `input/`.

---

# Files Changed

| File | Action | Reason | Risk | Rollback |
|------|--------|--------|------|----------|
| `runner_api_routers/content_studio.py` | CREATE | List/detail router | Low | Delete + unwire |
| `runner_api.py` | MODIFY | Import + `include_router(content_studio_router)` | Low | Revert include |
| `tests/test_content_studio_api.py` | CREATE | Focused contract + read-only tests | Low | Delete |
| `docs/migration/content-studio/E2_IMPLEMENTATION.md` | CREATE | Sprint record | None | Delete |

---

# API Contract

Prefix: `/api/v1/content-studio`  
Auth: `_verify_api_key` (same soft-open pattern as other Founder routers)

| Method | Path | Success | Errors |
|--------|------|---------|--------|
| GET | `/api/v1/content-studio/content` | `200` `{"ok": true, "count": N, "items": [...]}` | — |
| GET | `/api/v1/content-studio/content/{content_id}` | `200` `{"ok": true, "item": {...}}` | `404` missing; `400` invalid id format |

**Item fields (tracker.csv only + derived artifacts):**

`content_id`, `title`, `status`, `qa_status`, `current_step`, `next_step`, `draft_path`, `qa_output_path`, `final_output_path`, `artifact_folder`, `artifacts`

`artifacts` = boolean map from existing `_week_artifacts` (lookup uses `artifact_folder` when set, else `content_id`).

**Omitted (unsupported on Founder tracker):** `slug`, CMS `stage` enum, `publish_date`, `channels`, `author`, etc.

**Existing endpoints:** unchanged (`/weeks`, `/pipeline`, `/health`, etc.).

---

# Read-Only Guarantee

Implementation performs only:

- `_read_tracker()` (CSV read)
- `_week_artifacts()` / `_validate_week_id()` (path checks / filesystem `is_file`)

Does **not** write `tracker.csv`, modify `input/`, call `_run` / `_apply_week_if_set`, publish, Celery business tasks, Sheets, or DB writers.

Verified by `TestContentStudioReadOnly` (SHA-256 of tracker + input tree before/after; forbidden monkeypatch on `_run` / `_apply_week_if_set`).

---

# Test Results

### Focused (`tests/test_content_studio_api.py`)

**8 passed / 8 total**

### Integration (`tests/test_routers_integration.py`)

**18 passed / 18 total**

### Combined focused + integration

**26 passed**

---

# Runtime Results

Local `TestClient` against `runner_api:app` (D0/D1 working tree):

| Check | Result |
|-------|--------|
| `GET /api/v1/content-studio/content` | **200** — `ok=true`, `count=13`, item keys as contracted |
| `GET /api/v1/content-studio/content/W01` | **200** — `ok=true`, artifacts present |
| `GET .../MISSING99` | **404** — `Content not found` |
| `GET .../.bad` | **400** — `Invalid week ID format` |
| `GET /weeks` | **200** (unchanged) |
| `GET /health` | **200** (unchanged) |

---

# Regression Result

Full `pytest -q`:

| Metric | Count |
|--------|------:|
| Passed | **228** |
| Failed | **8** |
| Errors | **0** |

Failed set = same Baseline v1.1 intentional leave-behinds (QA/Editor validate_output, FileOperations abstract BaseCrew, markdown structure). **No new failures.**

Delta vs D1.5 baseline (220 passed / 8 failed): **+8 passed** (new Content Studio tests).

---

# Architecture Impact

## NO ARCHITECTURAL CHANGE

Additive Marketing OS / Content Studio read API on existing SoT. No new runtime, DB schema, or CMS import.

---

# Known Deferred Items

- write / create content
- edit mutation
- stage / status lifecycle
- Kanban / calendar UX
- publishing
- ID / lifecycle ADRs (CMS `W01-001` vs Founder `W01`)
