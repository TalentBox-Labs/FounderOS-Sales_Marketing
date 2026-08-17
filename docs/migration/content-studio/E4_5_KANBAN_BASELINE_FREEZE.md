# E4.5 — Content Studio Kanban Baseline Freeze

Sprint E4.5 — Documentation and certification only  
Date: 2026-08-09  
No feature, code, test, API, DB, lifecycle, or Calendar changes in this sprint.

Evidence: [E4A_KANBAN_IMPLEMENTATION.md](E4A_KANBAN_IMPLEMENTATION.md), [E3_5_UI_BASELINE_FREEZE.md](E3_5_UI_BASELINE_FREEZE.md), [E3_IMPLEMENTATION.md](E3_IMPLEMENTATION.md), [E2_IMPLEMENTATION.md](E2_IMPLEMENTATION.md), [04_DATA_MODEL_MAPPING.md](04_DATA_MODEL_MAPPING.md)

---

# Repository Baseline

| Field | Value |
|-------|-------|
| Branch | `develop` |
| HEAD | `e1efc0892ea13dad856b952110c7cc38d24565c3` |
| Working tree | Dirty — Content Studio E2–E4A + prior sprint docs/deltas uncommitted |
| Network / commit / tag | None performed in E4.5 |

## Exact E4A files changed

| File | Action in E4A |
|------|---------------|
| `runner_api_routers/ui.py` | MODIFY — add `GET /content-studio/kanban` (before `{content_id}`) |
| `templates/content_studio_kanban.html` | CREATE — Kanban board template |
| `templates/base.html` | MODIFY — “Studio Kanban” nav item |
| `templates/content_studio.html` | MODIFY — list topbar link to Kanban |
| `tests/test_content_studio_kanban.py` | CREATE — focused Kanban tests |
| `docs/migration/content-studio/E4A_KANBAN_IMPLEMENTATION.md` | CREATE — E4A sprint record |

This freeze document is additive certification only:

| File | Action in E4.5 |
|------|----------------|
| `docs/migration/content-studio/E4_5_KANBAN_BASELINE_FREEZE.md` | CREATE — this baseline |

---

# Frozen Kanban Capability

Frozen **read-only** Content Studio Kanban:

| Capability | Status |
|------------|--------|
| Kanban route/view | Implemented — `GET /content-studio/kanban` |
| Status columns | Implemented — distinct exact API `status` strings (no invented taxonomy) |
| Content cards | Implemented — `content_id`, `title`, `current_step`, `qa_status` from API |
| Detail navigation | Implemented — card href → `/content-studio/{content_id}` |
| Search / filter | Implemented — client DOM filters (search, status, week/`content_id`) |
| Empty column state | Implemented — `data-testid="kb-empty-column"` placeholder |
| Empty board state | Implemented — when API returns zero items |
| Explicit API error | Implemented — `data-testid="kb-api-error"`; no fallback board |

## Explicit non-capabilities (frozen out)

- **NO DRAG AND DROP**
- **NO STATUS MUTATION**
- **NO STAGE TRANSITIONS**
- No create / edit / delete / publish / schedule
- No POST / PUT / PATCH / DELETE from Kanban
- No Calendar (deferred; see E5 Readiness)

---

# Status Contract

Observation contract only. No normalization. No invented lifecycle values.

### Column derivation rule (frozen)

Columns = distinct `item.status` values from `build_content_list()` / `GET /api/v1/content-studio/content`, used as exact strings. Blank/`None` → empty string column displayed as `—`.

### Observed values (live Founder SoT at freeze)

Evidence: `build_content_list()` against current tracker — `ok=True`, `count=13`.

| Source field | Observed value | Displayed column | Evidence source | Count |
|--------------|----------------|------------------|-----------------|-------|
| `status` (Content Studio list item ← `tracker.csv` column `status`) | `QA Passed` | `QA Passed` | Live `build_content_list()`; E4A smoke; tracker rows W01–W13 | 13 |

### Related fields (not Kanban columns)

| Field | Role | Notes |
|-------|------|-------|
| `qa_status` | Card meta only | e.g. `PASS` — **not** a column axis |
| `current_step` | Card meta only | e.g. `Completed`, `Publish Review` — **not** a column axis |
| `next_step` | Exposed on item; not primary card axis | Not used as Kanban column |

### Contract constraints

- UI must not map `status` → CMS IDEA/BRIEF/SCHEDULED/PUBLISHED/etc. unless those exact strings appear in API `status`.
- Multi-status boards appear only when Founder SoT returns multiple distinct `status` values.
- Blank status is a safe empty-string column (tested); not an invented lifecycle name.

---

# Data Flow

```
Kanban UI (GET /content-studio/kanban)
  → Content Studio read builders / GET /api/v1/content-studio/content
  → Founder source of truth (tracker.csv + input/ via content_studio module only)
```

| Guarantee | Confirmed |
|-----------|-----------|
| No direct `tracker.csv` access from Kanban UI / templates | Yes — UI calls `build_content_list()` |
| No direct `input/` filesystem access from Kanban UI | Yes — Kanban does not read files; cards link to existing detail UI |
| No Sheets | Yes |
| No Flask | Yes |
| No CMS runtime import | Yes |
| No mutation endpoint | Yes — GET only |
| No database change | Yes |
| E2 API JSON contract unchanged by E4A | Yes |

---

# Read-Only Guarantee

**PASS** (E4A certification; unchanged in E4.5).

- Page route: GET only  
- Data path: Content Studio read API builders only  
- No Content Studio POST/PUT/PATCH/DELETE  
- No drag/drop, status change, stage transition, publish, or schedule controls  

---

# Test Baseline

| Suite | E4A / E4.5 recorded result |
|-------|----------------------------|
| Focused Kanban (`tests/test_content_studio_kanban.py`) | **10/10** |
| Full pytest | **251 passed / 259 total**; **8 failed**; **0 errors** |

### Compare against E3.5

| Suite | E3.5 | E4A / E4.5 | Delta |
|-------|------|------------|-------|
| Full passed | 241/249 | 251/259 | **+10** (new Kanban tests) |
| Failed | 8 | 8 | 0 |
| Errors | 0 | 0 | 0 |

---

# Regression Status

| Check | Result |
|-------|--------|
| New failures introduced by E4A | **0** |
| **NEW REGRESSIONS** | **0** |
| Same 8 historical leave-behinds | Unchanged (stale unit contracts; not reclassified) |
| Architecture regressions | **None** |

---

# Rollback Boundary

Document only — **rollback not performed**.

To remove **only** the E4A Kanban slice while preserving E2/E3 Content Studio list/detail:

| File | Role in E4A | Rollback effect |
|------|-------------|-----------------|
| `runner_api_routers/ui.py` | Kanban route `page_content_studio_kanban` | Remove Kanban route only; keep list/detail |
| `templates/content_studio_kanban.html` | Board template | Delete file |
| `templates/base.html` | “Studio Kanban” nav | Remove Kanban nav item only |
| `templates/content_studio.html` | List → Kanban link | Remove Kanban link only; keep list page |
| `tests/test_content_studio_kanban.py` | Focused Kanban tests | Delete file |
| `docs/migration/content-studio/E4A_KANBAN_IMPLEMENTATION.md` | E4A record | Optional delete/retain for history |
| `docs/migration/content-studio/E4_5_KANBAN_BASELINE_FREEZE.md` | This freeze | Optional delete/retain for history |

Do **not** revert `runner_api_routers/content_studio.py` or list/detail templates as part of E4A-only rollback (those are E2/E3).

---

# Architecture Status

**UNCHANGED**

**NO ARCHITECTURAL CHANGE** from E4A. Additive Jinja Kanban view over existing Content Studio read API. Architecture Baseline v1.0, Migration Baseline v1.0, and Content Studio UI Baseline v1.0 remain intact.

---

# E5 Readiness

Gate question: can a read-only Calendar be driven by fields **already** represented on the Content Studio read API without new lifecycle/scheduling semantics?

| Check | Evidence |
|-------|----------|
| Date / schedule fields on list/detail item | **None** — item keys: `content_id`, `title`, `status`, `qa_status`, `current_step`, `next_step`, `draft_path`, `qa_output_path`, `final_output_path`, `artifact_folder`, `artifacts` |
| `publish_date` in tracker header | **Not present** ([04_DATA_MODEL_MAPPING.md](04_DATA_MODEL_MAPPING.md): publish_date **NEEDS ADR** / not verified as tracker column) |
| Safe calendar axis without new semantics | **Not available** from current Content Studio API contract |

**Determination:**

**CALENDAR REQUIRES DATA/SEMANTIC ADR**

E5 must not proceed until Founder exposes calendar-usable date fields (or an ADR defines derivation) without inventing scheduling/lifecycle semantics in the UI.

---

# Certification

Freeze criteria met:

| Criterion | Status |
|-----------|--------|
| Kanban remains read-only | PASS |
| Existing status semantics unchanged | PASS |
| No API contract change | PASS |
| No DB changes | PASS |
| Focused Kanban tests green | PASS (10/10) |
| No new regressions | PASS (0) |
| Architecture unchanged | PASS |

## Certification statement

**CONTENT STUDIO KANBAN BASELINE v1.0 FROZEN**
