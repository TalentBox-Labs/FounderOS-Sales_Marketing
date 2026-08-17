# 01 — Content Studio Scope (from code)

Sprint E1 — Analysis only  
**Canonical product:** Founder OS `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
**CMS executable source:** `/Users/krishna/Documents/workcrew-cms-os`  
**CMS docs pack:** `/Users/krishna/Documents/CMS_OS_V1` (0 `.py` files; corroboration only)

There is no product string “Content Studio” in CMS code. Scope = content lifecycle workspace capabilities evidenced in the CMS Flask dashboard + content filesystem, excluding later-slice engines unless inseparable.

---

## In scope (CMS evidence)

| Capability | Evidence |
|------------|----------|
| Content records inventory | `dashboard/sheets_integration.py` `COLUMN_MAP` + `get_content_data()`; mock rows in `dashboard/app.py`; static catalog `dashboard/content_manifest.json` (22 items; **not loaded** by top-level `app.py`) |
| Week / content workspace grouping | `get_week_groups()` + `GET /api/weeks` in `dashboard/app.py` (~L227–235, L881–886); week packs under `content/distribution/<id>/`, `content/blog/`, `content-batches/` |
| Draft / artifact storage (filesystem) | `content/blog/`, `content/drafts/`, `content/briefs/`, `content/research/`, `content/seo-briefs/`, channel folders; `content-batches/*.md` |
| Content lifecycle / status | Stages constant in `app.py` (~L204–214): `IDEA → BRIEF → DRAFT → REVIEW → REVISE → SCHEDULED → PUBLISHED → ARCHIVED`; stage APIs |
| Content metadata | Sheet/manifest fields: title, stage, publish_date, channels, word_count, author, target_keyword, cta, week, published_url, checklist flags, qa_* |
| Content assets (paths) | `get_image_path_for_content()` → `content-batches/images/`; media template placeholder |
| Content retrieval | `GET /api/content`, `GET /content/<id>`, calendar/pipeline HTML |
| Content update / edit | `GET /content/<id>/edit` + `POST /api/content/<id>/update` (Sheets write); nested app also writes manifest |
| Content UI | Templates: `pipeline.html`, `calendar.html`, `content_detail.html` (mixed), `content_edit.html`, `articles.html` (nested wiring) |
| Content API | List/stats/weeks/stage/update (see 05) |
| Studio-owned validation (light) | Progress checklist `calculate_progress()`; stage enum; nested `/api/qa/<id>` + `crewai_qa.py` (unwired in top-level `app.py`) |

---

## Explicitly out of scope for Slice 1 (later slices unless inseparable)

| Area | Why excluded | Evidence |
|------|--------------|----------|
| Publishing / multi-platform publish | Publishing Engine | `POST /api/publish*`, `/api/publish-all`, `/queue`, `queue.html` |
| Social distribution | Social Engine | LinkedIn OAuth routes; `linkedin_*.py`; channel publish helpers |
| Email distribution | Email Engine | `content/email/` packaging consumed by publish; not studio CRUD |
| SEO Engine (keyword DB / SEO plan generation) | SEO Engine | Founder owns `GenerationCrew` SEO + `/api/v1/seo`; CMS `seo-briefs/` are artifacts only |
| Campaign orchestration | Campaign Engine | No campaign CRUD in dashboard app |
| Brand Engine | Brand Engine | `brand/` + voice gates — separate |
| AI platform internals / OpenClaw | AI Platform | `agents/`, SOUL packs — not Content Studio runtime |
| n8n runtime / workflow library | Automation Platform | Used by publish webhooks, not list/edit/stage |
| Hashnode | Publishing Engine | Not in Content Studio CRUD paths |

**Borderline kept in scope as read-only artifact references:** LinkedIn post files used by detail/preview text — preview/publish **actions** deferred; path discovery helpers may be referenced when adapting detail UX.

---

## CMS runtime locus note

| Fact | Evidence |
|------|----------|
| Primary Mac/runtime app | Top-level `dashboard/app.py` (~952 lines) |
| Nested duplicate tree | `workcrew-cms-os/workcrew-cms-os/...` richer manifest sync — **not** treated as primary without start-script proof; classify REFERENCE / NOT VERIFIED for nested-only routes |
| CMS_OS_V1 | Docs only; names `workcrew-cms-os` as implementation workspace (`TOOLS.md` / `README`) |

---

## Scope statement for migration

**Content Studio Slice 1 migrates:** CMS inventory UX patterns (pipeline board, calendar, detail/edit metadata forms) and list/stage/update **concepts**, adapted onto Founder SoT (`tracker.csv` + `input/` + `data/week_runtime/`).

**Content Studio Slice 1 does not migrate:** Sheets-as-primary store, n8n publish, OpenClaw, Flask runtime, or channel publish APIs.
