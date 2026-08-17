# 05 — UI / API Mapping

Sprint E1 — Analysis only  
Backward compatibility mandatory: existing Founder routes must keep working.

Decisions: KEEP FOUNDER UI | MIGRATE CMS UX | MERGE | DEFER

---

## CMS Content Studio routes (top-level `dashboard/app.py`)

### UI

| Method | Path | Template | Decision |
|--------|------|----------|----------|
| GET | `/` | `pipeline.html` Kanban | **MIGRATE CMS UX** → Founder Content Studio board (do not replace Founder `/`) |
| GET | `/calendar` | `calendar.html` | **MIGRATE CMS UX** (needs date field ADR) |
| GET | `/content/<content_id>` | `content_detail.html` | **MERGE** with Founder `/weeks/{id}` |
| GET | `/content/<content_id>/edit` | `content_edit.html` | **MIGRATE CMS UX** onto Founder (new edit surface) |
| GET | `/queue` | `queue.html` | **DEFER** (Publishing) |

### API (studio)

| Method | Path | Decision |
|--------|------|----------|
| GET | `/api/content` | **MERGE** — add Founder JSON list over tracker (new path under Founder conventions) |
| GET | `/api/stats` | **MERGE** — optional JSON projection of `_dashboard_stats` |
| GET | `/api/weeks` | **MERGE** — week grouping over tracker |
| POST | `/api/content/<id>/update` | **MIGRATE CMS UX** behavior → Founder tracker/frontmatter writers |
| POST | `/api/content/<id>/stage/<stage>` | **MIGRATE CMS UX** behavior → Founder lifecycle adapter |
| POST | `/api/batch/update-stage` | **MIGRATE CMS UX** (after single-stage) |
| POST | `/api/schedule/<id>` | **DEFER** (Publishing / schedule) |
| GET | `/api/preview/<id>` | **DEFER** (Publishing) |
| POST | `/api/publish*` | **DEFER** / OUT OF SCOPE |

---

## Founder existing routes (keep)

| Method | Path | Decision |
|--------|------|----------|
| GET | `/` | **KEEP FOUNDER UI** (dashboard, not CMS Kanban) |
| GET | `/weeks` | **KEEP FOUNDER UI**; later MERGE board/calendar patterns |
| GET | `/weeks/{week_id}` | **KEEP FOUNDER UI**; MERGE detail enrichment from CMS patterns |
| GET | `/weeks/{week_id}/file/{filename}` | **KEEP FOUNDER UI** |
| GET | `/pipeline` | **KEEP FOUNDER UI** (runner); do not overwrite with CMS Kanban on same path |
| POST | `/run`, `/validate`, `/generate`, `/edit`, `/switch-week`, `/go-live` | **KEEP FOUNDER** (ops; Editorial/Publishing-adjacent) |

---

## Forms / request / response models

| CMS | Founder today | Mapping |
|-----|---------------|---------|
| Edit form: title, stage, publish_date, author, word_count, target_keyword, cta, channels, published_url | No equivalent form | **MIGRATE CMS UX** fields that map to tracker/frontmatter; channels/author **DEFER** or ADR |
| List response: array of content dicts | HTML-only weeks | New JSON response; **no change** to HTML contract |
| Stage POST path params | N/A | New additive API |

---

## Path naming guidance (evidence-based)

- Do **not** mount CMS Kanban at Founder `GET /` (dashboard already owns `/`).  
- Prefer Founder-prefixed additive APIs, e.g. `/api/v1/content-studio/...` or `/api/v1/content/...` reading tracker — exact path **NEEDS** implementation ADR but must not break existing `/weeks` HTML.  
- CMS `/pipeline` HTML nav ≠ Founder `/pipeline` runner — **MERGE concepts, separate routes**.

---

## Compatibility rule

| Change type | Required? |
|-------------|-----------|
| Breaking change to existing Founder HTML/API | **NO** |
| Additive Studio APIs/UI | **YES** (planned) |
| Flask port as second server | **NO** (not architecture target) |
