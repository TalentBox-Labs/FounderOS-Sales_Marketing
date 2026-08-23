# E6A — First Editorial Implementation Unit

## Recommendation

**Editorial Readiness Read Model** (read-only).

Smallest independently testable Editorial Engine unit with lowest blast radius.

---

## Why this unit

| Criterion | Assessment |
|-----------|------------|
| Founder capability gap | Operators see tracker + scattered `output/qa_reports/*` but no Editorial readiness aggregate; Content Studio shows inventory not validation posture |
| CMS unique value | Scorecard/readiness **shape** from QA rituals is REFERENCE ONLY — do not import OpenClaw |
| Blast radius | GET-only; no crew kickoff; no promote; no Sheets; no DB |
| Architecture | Additive read surface under Marketing OS → Editorial Engine (or thin Content Studio extension) |
| Side effects | None if GET-only |

**Explicitly not first unit:** crew migration, CMS OpenClaw port, Sheets stages, prompt rewrites, `/edit` mutation fix (valuable but higher blast — schedule after readiness).

---

## Exact capability

Expose per-`content_id` **editorial readiness** from existing Founder data:

- tracker fields already on Content Studio item (`status`, `qa_status`, `current_step`, …)
- presence/summary of existing validator reports under `output/qa_reports/` for known suffixes (Research_Map, Draft_Validation, Structure_Check, Metadata_Check, Publish_Checklist_Check, optional CrewAI_QA / Content_Quality)
- explicit missing-report states (no invented PASS)
- link to Content Studio detail

No re-run of validators or crews in v1 (or optional later behind explicit POST — out of first unit).

---

## Exact Founder destination

| Layer | Destination |
|-------|-------------|
| API | New read routes e.g. under `runner_api_routers/` (`editorial` or extend `content_studio` with readiness resource) — decision at implement time; prefer clear Editorial Engine module boundary |
| UI (optional thin) | Read-only section on Content Studio detail **or** `/content-studio/{id}/readiness` — Jinja only |
| Data | Existing tracker + `output/qa_reports/` via Founder helpers — **no** new SoT |

---

## Exact CMS source (if applicable)

| CMS path | Use |
|----------|-----|
| `reports/qa/*-qa-scorecard.md` | REFERENCE ONLY — field naming / presentation ideas |
| `agents/qa/SOUL.md` + `tests/*.md` | REFERENCE ONLY — checklist labels for future adapt |
| `reference-design/**` | **Excluded** — SUPERSEDED |
| Sheets / OpenClaw / Flask write APIs | **Excluded** |

---

## Files proposed for change (implement sprint — not E6A)

| File | Role |
|------|------|
| `runner_api_routers/editorial.py` **or** `content_studio.py` (extend) | Readiness builder + GET routes |
| `runner_api.py` | Router include if new module |
| `templates/content_studio_detail.html` and/or new readiness template | Optional UI |
| `tests/test_editorial_readiness.py` (new) | Focused GET tests |
| docs under `docs/migration/editorial-engine/` | Implementation record |

## Files explicitly excluded

- All CMS `reference-design/src/**` crew/validator ports
- `dashboard/sheets_integration.py`, OpenClaw runtime, n8n
- Prompt/YAML edits
- `promote_staged` / `/edit` / `/generate` (follow-up)
- DB/Alembic
- Calendar

---

## Impacts

| Impact | Assessment |
|--------|------------|
| API | Additive GET only; existing CS contract unchanged |
| Database | **NONE** |
| Architecture | **NO ARCHITECTURAL CHANGE** (additive read) |
