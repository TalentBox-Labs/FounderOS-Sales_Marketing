# 09 — First Implementation Unit

Sprint E1 — Analysis only  
Selection criterion: repository evidence + **lowest blast radius** (not preference).

---

## Recommendation

### Canonical Content Studio **read model** + **list/detail JSON API** over Founder `tracker.csv`

| Field | Value |
|-------|-------|
| **Capability** | Read-only content inventory + detail projection (status, paths, artifact presence, optional checklist derived from `_week_artifacts`) |
| **Why smallest** | Reuses existing `_read_tracker`, `_week_artifacts`, `_validate_week_id`; no Sheets; no DB migration; no stage writes; no CMS Flask port; no publish coupling |
| **Founder destination** | New router module under Marketing OS / Content Studio, e.g. `runner_api_routers/content_studio.py` included from `runner_api.py`; helpers remain in `runner_api_routers/utils.py` |
| **Owning domain** | Marketing OS → Content Studio |
| **CMS source (adapt patterns)** | Behaviors of `GET /api/content`, `GET /content/<id>`, stats/weeks grouping from `workcrew-cms-os/dashboard/app.py` — **not** file copy |
| **CMS source files not copied** | `sheets_integration.py`, publish routes, Flask templates (UI port = later unit) |
| **API contract changes** | **Additive only** (new endpoints). Existing `/weeks` HTML unchanged → **NO breaking API change** |
| **Database changes** | **NONE** |
| **Alembic migration** | **NONE** |
| **Dependencies** | Filesystem + tracker.csv only |

---

## Explicitly deferred to later units (same Slice 1 theme)

| Unit order | Capability | Why later |
|------------|------------|-----------|
| 2 | Kanban / calendar UX adapt from CMS templates | Needs read API + date/stage ADR |
| 3 | Metadata edit API + form | Write path; ID/lifecycle ADR (R1/R2) |
| 4 | Stage transition API | Write path; enum ADR |
| 5 | Optional Article ORM sync | DB impact; not required |

---

## Independently testable acceptance (unit 1)

1. List endpoint returns all tracker `content_id` rows.  
2. Detail endpoint returns one week with artifact map.  
3. Unknown id → 404.  
4. Existing integration UI tests still pass.  
5. No network calls to Sheets/n8n.

---

## Alternatives considered (rejected for first unit)

| Alternative | Why not first |
|-------------|---------------|
| Port CMS Kanban HTML first | Higher UI blast radius; stage model unresolved |
| Metadata edit first | Requires write ADR + SoT writers |
| Sheets bridge as SoT | Violates Founder canonical SoT (R4) |
| Activate `Article` table | Database impact without need |
