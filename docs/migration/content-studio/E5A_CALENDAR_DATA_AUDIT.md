# E5A — Content Studio Calendar Data & Semantic Audit

Sprint E5A — Analysis and ADR only  
Date: 2026-08-09  
Repository (canonical): `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
CMS reference: `/Users/krishna/Documents/workcrew-cms-os` (REFERENCE ONLY)

No feature implementation, Calendar UI, write API, DB migration, lifecycle change, or refactor in this sprint.

Related: [E4_5_KANBAN_BASELINE_FREEZE.md](E4_5_KANBAN_BASELINE_FREEZE.md), [04_DATA_MODEL_MAPPING.md](04_DATA_MODEL_MAPPING.md), [ADR_CONTENT_STUDIO_CALENDAR_SEMANTICS.md](../../architecture/adr/ADR_CONTENT_STUDIO_CALENDAR_SEMANTICS.md)

---

# Date Field Inventory

Fields relevant to Marketing / Content Studio content. Invented fields omitted. Empty/absent optional keys are still inventoried when code or schema references them.

| Field | Location | Type | Source of truth | Current usage | Consumers | Mutation path | Evidence |
|-------|----------|------|-----------------|---------------|-----------|---------------|----------|
| *(no date columns)* | `tracker.csv` header | N/A | Tracker column set is SoT for Content Studio inventory | Content inventory without dates | Content Studio API/UI, weeks UI | `tracker_updater` / pipeline updates non-date cols | Header: `content_id,title,status,qa_status,current_step,next_step,draft_path,qa_output_path,final_output_path,artifact_folder` |
| *(no date fields)* | Content Studio API item | N/A | `build_content_list` / `build_content_detail` ← tracker + artifacts | List/detail/Kanban | `/api/v1/content-studio/*`, Studio UI | **None** (read-only) | `runner_api_routers/content_studio.py` `_TRACKER_FIELDS` |
| `content_id` / week id (`W01`…) | tracker / API | string identifier | tracker | Programme content id | CS API/UI, runtime | Tracker / ops | Not a datetime |
| `title` (e.g. `M1/Wk1`) | tracker | string label | tracker | Programme month/week label | sheet_sync Month/Week fallback | Tracker | Not a calendar date |
| `publish_status` | `input/*/05_Final.md` frontmatter | string enum | frontmatter | Lifecycle token (includes `scheduled` as **status**, not datetime) | frontmatter lint / metadata QA | Editor / content files | e.g. `input/W01/05_Final.md`; `REQUIRED_KEYS` omits `publish_date` |
| `status` (FM) | `05_Final.md` frontmatter | string | frontmatter | Editorial/publish lifecycle word | lint | Editor | Same files |
| `publish_date` | **Optional** FM key; **absent in live** `05_Final.md` | date string (tests: `YYYY-MM-DD`) | Intended: frontmatter | Intended sheet “Publish Date”; **currently empty in repo content** | `src/tools/sheet_sync.py` `_publish_date_for_sheet` | Would be manual/bootstrap FM edit; bootstrap template can write it | Reader: `sheet_sync.py:226–240`; live: `rg publish_date input` → no matches |
| `publish_date_{content_id}` | Optional FM override | date string | frontmatter | Per-split-week sheet date | sheet_sync only | Manual FM | `sheet_sync.py:230–239` |
| `Publish Date` | Google Sheet column (via sync) | string | **Derived from FM** when syncing; live sheet values **NOT VERIFIED** in this audit | Board mirror | Google Sheets | `sheet_sync --write` | `sheet_sync.py` compose `"Publish Date": publish_date` |
| `Month/Week` | Sheet / `_MONTH_WEEK_BY_CONTENT_ID` | string `M#/Wk#` | Programme map / tracker title | Programme period label | Sheets | sync | Not ISO date |
| `created` | `obsidian_vault/02 - Weeks/W*.md` | date string | vault note FM | Vault note stamp | Obsidian humans | vault tooling | All sampled weeks = `2026-06-11` (not distinct per content) |
| filesystem mtime | `input/**` files | OS timestamp | filesystem | Incidental file age | OS / tools | file writes | e.g. W01/W02 `05_Final.md` mtime `2026-08-07` — not Content Studio API |
| `timestamp_utc` / audit stamps | sheet_sync dry-run/write audits | ISO UTC | sync clock | Sync operation metadata | Operators | Generated per sync | `sheet_sync.py` audit paths |
| `created_at` / `updated_at` | Postgres `knowledge_bases`, `kb_articles`, `content_library`, `social_posts`, `articles` | `DateTime(timezone=True)` | DB defaults | KB / social / unused Article | Revenue OS APIs | ORM / social/KB APIs | `revenue_os/models/content.py` |
| `published_at` | Postgres `ContentLibrary`, `SocialPost` | tz-aware DateTime, nullable | DB / social API | Social/library publish | `revenue_os/api/v1/social.py` | social create/publish | **Not wired to Content Studio** |
| `scheduled_at` | Postgres `SocialPost` | tz-aware DateTime, nullable | social API body | Social schedule | social API | POST/PUT social posts | **Not wired to Content Studio** |
| `Article.created_at` / `updated_at` | Postgres `articles` | tz-aware DateTime | DB | Model exported; **no Content Studio consumer found** | None verified for CS | None found for Marketing CS | `content.py` `Article`; docs: unused for Slice 1 |
| scaffold `date` → FM `publish_date` | `scripts/bootstrap_remaining_weeks.py` | hardcoded ISO dates for W07B/W09A/W09B/W10 only | script constants | Bootstrap would write FM; **live finals lack `publish_date`** | Bootstrap only | script run | Lines 22–67, 148 |

**Content Studio read API exposes dates?** **No.**

---

# Semantic Classification

Exact one class per observed field (ambiguity → UNKNOWN / NOT VERIFIED).

| Field | Classification | Rationale |
|-------|----------------|-----------|
| tracker date columns | N/A — none exist | — |
| Content Studio API dates | N/A — none exposed | — |
| `content_id` (`W01`…) | WEEK/PERIOD IDENTIFIER | Programme id, not a datetime |
| tracker `title` / Sheet `Month/Week` | WEEK/PERIOD IDENTIFIER | `M1/Wk1`-style labels |
| FM `publish_status` / `status` | UNKNOWN as calendar date | Status tokens, not dates; `scheduled` ≠ `scheduled_at` |
| FM `publish_date` (code path) | SCHEDULED PUBLISH DATE **or** ACTUAL PUBLISH DATE — **NOT VERIFIED** | sheet_sync labels it “Publish Date”; no domain doc proves scheduled vs actual; **live values absent** |
| Sheet `Publish Date` | DERIVED mirror of FM intent — semantic same as FM | Sheets not Founder CS SoT |
| Obsidian `created` | SYSTEM/AUDIT TIMESTAMP (vault) | Identical `2026-06-11` across weeks — not content publish calendar |
| filesystem mtime | SYSTEM/AUDIT TIMESTAMP | File write time; not editorial calendar SoT |
| sheet_sync `timestamp_utc` | SYSTEM/AUDIT TIMESTAMP | Sync audit clock |
| Postgres KB/social `created_at`/`updated_at` | SYSTEM/AUDIT TIMESTAMP | ORM defaults; not CS inventory |
| `ContentLibrary.published_at` / `SocialPost.published_at` | ACTUAL PUBLISH DATE (social/library surface) | Separate product surface from Content Studio tracker |
| `SocialPost.scheduled_at` | SCHEDULED PUBLISH DATE (social surface) | Not CS tracker |
| `Article` timestamps | SYSTEM/AUDIT TIMESTAMP | Bridge model unused by CS API |
| bootstrap script `date` | UNKNOWN / transitional scaffold | Partial hardcoded dates; not live SoT |

---

# Source of Truth

| Store | Date fields for CS calendar | Classification | Notes |
|-------|----------------------------|----------------|-------|
| `tracker.csv` | None | CANONICAL for CS inventory **fields that exist**; dates **absent** | CS API SoT for list/detail |
| `input/**/05_Final.md` frontmatter | `publish_date` path exists; **unpopulated** | CANONICAL candidate for publish date **if populated and contracted**; today **NOT VERIFIED as live SoT** | Required schema does not include `publish_date` |
| Google Sheets | `Publish Date` | LEGACY / TRANSITIONAL mirror | CMS calendar depended on Sheets; Founder must not treat Sheets as CS SoT |
| Postgres content models | social/KB/Article dates | CANONICAL for Revenue OS social/KB; **NOT** CS SoT | **Not wired** to Content Studio routers |
| `data/runtime_config.json` / `week_runtime` | No calendar dates | CANONICAL for active week/paths only | |
| Filesystem mtimes | mtime | DERIVED | Unsafe as editorial calendar |
| Obsidian week notes | `created` | LEGACY / vault | Not CS API |
| Bootstrap script constants | partial ISO dates | TRANSITIONAL | Must not be treated as production calendar map |

**Do not create a new source of truth in E5A.** No new DB field approved by this audit.

---

# Calendar Use Cases

| Use case | Classification | Evidence |
|----------|----------------|----------|
| A. Editorial Calendar (due/review dates) | **NOT SUPPORTED** | No `due_date` / `review_date` in tracker, FM required schema, or CS API |
| B. Publishing Calendar (scheduled/actual publish) | **ADR REQUIRED** → currently **NOT SUPPORTED** for implementation | Intended FM `publish_date` → sheet path exists but **live content has zero `publish_date`**; CS API does not expose it; scheduled vs actual semantics **NOT VERIFIED** |
| C. Campaign Calendar | **NOT SUPPORTED** | No campaign date fields on CS inventory |
| D. Historical Content Calendar | **PARTIAL** at best / **NOT SUPPORTED** for CS | `publish_status: published` without dates; filesystem mtimes/Obsidian `created` are system stamps, not verified publish history; social `published_at` is a different surface |

---

# Week / Date Relationship

| Question | Finding |
|----------|---------|
| Do `W01`, `W02`, … encode calendar dates? | **No** in tracker, CS API, or runtime JSON |
| Programme labels | `M1/Wk1` etc. are period labels, not ISO dates |
| Complete W## → calendar map in code | **Not found** |
| Partial scaffold | `bootstrap_remaining_weeks.py` hardcodes four dates (W07B/W09A/W09B/W10) for bootstrap only; live FM lacks `publish_date` |

**WEEK IDENTIFIER IS NOT A CALENDAR DATE**

Do not invent W## → date mapping rules for Calendar UI.

---

# Timezone Evidence

| Layer | Evidence | Classification |
|-------|----------|----------------|
| Celery | `timezone="UTC"`, `enable_utc=True` (`revenue_os/tasks/__init__.py`) | UTC for task runtime |
| sheet_sync audits | `datetime.now(timezone.utc)` | UTC |
| Revenue OS general | widespread `timezone.utc` | UTC-first |
| `Settings` / `.env` | No APP/LOCAL `TIMEZONE` key found | No local canonical config |
| Content Studio / FM `publish_date` | Absent live; tests treat date-only strings | Content calendar TZ **NOT VERIFIED** |
| Marketing playbook prose | “8-9 AM timezone” unspecified | NOT VERIFIED |

**Content Studio calendar timezone: NOT VERIFIED**

Operational clocks are UTC-first. Future scheduling/publishing operations require an explicit TZ ADR; not solved in E5A.

---

# CMS Reference Findings

Reference repo: `workcrew-cms-os` (not canonical).

| Topic | Finding |
|-------|---------|
| Capability | `GET /calendar` → `dashboard/templates/calendar.html` |
| Intended date | `publish_date` from Sheets col F (“Publish Date”) |
| Authoritative? | **No** — template demo grid (`range(1,31)`, mock “today”); variable mismatch (`items`/`date`/`status` vs route `content_items`/`publish_date`/`stage`) |
| Sheets dependency | **Yes** for live publish dates (`get_content_data` Sheets-first) |
| Reuse in Founder | UX idea only (month grid by a publish date). **Do not** copy Sheets `COLUMN_MAP`, demo stub, or CMS stage enums into Founder without a Founder date SoT |

---

# Risks

| ID | Risk | Severity |
|----|------|----------|
| R-C1 | Implementing Calendar by mapping `W##` → invented dates | High — fabricates semantics |
| R-C2 | Using Sheets `Publish Date` as Founder CS SoT | High — second source of truth / CMS assumption |
| R-C3 | Using filesystem mtime or Obsidian `created` as publish calendar | High — wrong semantic |
| R-C4 | Wiring Postgres `SocialPost.scheduled_at` into Content Studio Calendar without product decision | Medium — surface conflation |
| R-C5 | Treating empty FM `publish_date` path as sufficient for E5B | High — empty board or silent wrongness |
| R-C6 | Timezone undefined for future schedule/publish ops | Medium — ADR issue for later mutation slices |

---

# E5B Readiness

| Gate | Result |
|------|--------|
| Calendar date source is canonical | **FAIL** — no populated canonical CS date field |
| Semantics are explicit | **FAIL** — publish_date scheduled vs actual NOT VERIFIED; week ≠ date |
| No new DB field required | Would need either populated FM contracted into CS API **or** new storage — neither approved/populated now |
| No new lifecycle meaning | Cannot invent calendar axis without new semantics |
| No mutation required | Read-only alone still needs a date axis |

**E5B Read-Only Calendar: BLOCKED**

Unblock requires a follow-on data decision (outside E5B UI work), for example:

1. Populate and contract frontmatter `publish_date` into Content Studio read API with explicit semantic (scheduled vs actual), **or**
2. Add a Founder-canonical date column to tracker (DB/Sheets not preferred), with ADR-approved meaning,

…then freeze that contract before any Calendar UI.

See ADR: [ADR_CONTENT_STUDIO_CALENDAR_SEMANTICS.md](../../architecture/adr/ADR_CONTENT_STUDIO_CALENDAR_SEMANTICS.md).
