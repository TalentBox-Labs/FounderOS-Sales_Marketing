# E4A — Content Studio Read-Only Kanban

Sprint E4A — Founder-native read-only Kanban over Content Studio API  
Date: 2026-08-09  
Repository: `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`

---

# Scope

Implemented one read-only visualization:

- Route: `GET /content-studio/kanban`
- Columns derived from **exact** distinct `status` strings returned by Content Studio list API
- Cards show API fields (`content_id`, `title`, `current_step`, `qa_status`)
- Card links to existing `GET /content-studio/{content_id}`
- Client-side search / status / week filters (DOM only; no writes)
- Empty-column placeholder markup
- Explicit API failure UI (no fallback board)

**Not implemented:** drag/drop, status mutation, stage workflow, calendar, create/edit/delete/publish, POST/PUT/PATCH/DELETE, lifecycle ADR, Sheets, Flask/CMS import.

---

# Files Changed

| File | Action | Reason | Risk | Rollback |
|------|--------|--------|------|----------|
| `runner_api_routers/ui.py` | MODIFY | Add `GET /content-studio/kanban` before `{content_id}` | Low | Remove route |
| `templates/content_studio_kanban.html` | CREATE | Kanban board template | Low | Delete |
| `templates/base.html` | MODIFY | Sidebar “Studio Kanban” nav | Low | Revert nav |
| `templates/content_studio.html` | MODIFY | List → Kanban link | Low | Revert link |
| `tests/test_content_studio_kanban.py` | CREATE | Focused Kanban tests | Low | Delete |
| `docs/migration/content-studio/E4A_KANBAN_IMPLEMENTATION.md` | CREATE | Sprint record | None | Delete |

---

# Status Mapping

| Rule | Implementation |
|------|----------------|
| Column source | Distinct `item.status` values from `build_content_list()` |
| Normalization | **None** — strings used as returned |
| Blank status | Separate column labeled `—` (display only); `data-status=""` |
| Invented stages | **Forbidden** — no IDEA / BRIEF / SCHEDULED / PUBLISHED columns unless present in API `status` |

**Live runtime evidence (smoke):** tracker/API currently yields a single column `QA Passed` for all cards. That is valid Founder SoT visualization, not a reason to invent CMS lifecycle columns in UI.

**Lifecycle ADR:** Not required for E4A because Kanban does not redefine or invent status semantics. Richer multi-stage boards remain deferred until Founder exposes additional status values (or an ADR defines lifecycle).

---

# Read-Only Guarantee

PASS.

- Route: GET only
- Data: `build_content_list()` (same builders as E2); no tracker.csv parse in UI
- No forms; no drag handlers; no `ondrop` / `draggable`
- No calls to `/run`, `/generate`, `/edit`, publish, or Content Studio write APIs
- Tests assert absence of mutation surface on Kanban HTML

---

# Focused Tests

`tests/test_content_studio_kanban.py`:

| # | Coverage | Result |
|---|----------|--------|
| 1 | Kanban renders | PASS |
| 2 | Exact status → columns (no invented lifecycle) | PASS |
| 3 | Cards render API data | PASS |
| 4 | Card links to detail | PASS |
| 5 | Empty-column markup | PASS |
| 6 | Search/filter controls | PASS |
| 7 | API failure explicit | PASS |
| 8 | Blank status safe column | PASS |
| 9 | No mutation requests | PASS |
| 10 | List/detail unchanged | PASS |

**Focused Kanban: 10/10**

Also re-run: `test_content_studio_ui.py` + `test_content_studio_api.py` + `test_routers_integration.py` → **39/39**.

---

# Regression Result

Full suite (`pytest -q`):

**251 passed / 259 total; 8 failed; 0 errors**

Failed tests are the same pre-existing stale leave-behinds (QA/Editor `validate_output`, abstract `BaseCrew` FileOperations, markdown structure). **New regressions: 0** (E3 baseline was 241 passed + 8 failed; E4A adds +10 Kanban tests).

---

# Runtime Verification

Smoke via TestClient against live Founder app:

| Check | Result |
|-------|--------|
| `GET /content-studio/kanban` → 200 HTML | PASS |
| Board + cards render | PASS |
| Detail links present | PASS |
| Columns = live API statuses (`QA Passed`) | PASS |
| No form / no drag surface | PASS |
| API error path (unit) | PASS |

---

# Architecture Impact

**NO ARCHITECTURAL CHANGE**

- Reuses existing FastAPI + Jinja Content Studio UI surface
- Reuses E2 `build_content_list` / detail routes (no API contract change)
- No DB / Alembic / persistence changes
- No second source of truth
- No new frontend framework

---

# Deferred Calendar Work

Explicitly out of E4A (unchanged):

- Calendar view
- Scheduling / publish dates visualization
- Any write path for schedule or stage
- Lifecycle ADR / stage taxonomy redesign

Next visualization slice may add Calendar under the same read-only constraints when product prioritizes it.
