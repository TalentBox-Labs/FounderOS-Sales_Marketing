# 04 — Data Model Mapping

Sprint E1 — Analysis only  
No migrations created.

**Founder SoT:** `tracker.csv` + `input/{week}/*.md` + `data/week_runtime/{week}.json` + frontmatter on `05_Final.md`  
**CMS SoT (live):** Google Sheets “Content Tracker” via `sheets_integration.py` (fallback FS/mock); optional static `content_manifest.json`

Field classes: ALREADY EXISTS | MAP DIRECTLY | MAP WITH ADAPTER | DO NOT MIGRATE | NEEDS ADR | NOT VERIFIED

---

## Identity & core

| CMS field | CMS source | Founder field / locus | Classification |
|-----------|------------|----------------------|----------------|
| `id` / `content_id` (`W01-001`) | Sheets A / manifest | `tracker.content_id` (`W01`, `W05A`) | **MAP WITH ADAPTER** (ID skew) — **NEEDS ADR** if dual IDs retained |
| `week` | Sheets B | Often equals `content_id` / `artifact_folder` | **MAP WITH ADAPTER** |
| `title` | Sheets C / manifest | `tracker.title` (programme labels like `M1/Wk1`) vs article title in frontmatter `article_title` | **MAP WITH ADAPTER** |
| `stage` | Sheets H → IDEA…ARCHIVED | `tracker.status`, `current_step`, `qa_status` + frontmatter `status`/`publish_status` | **MAP WITH ADAPTER** — enums differ |
| `publish_date` | Sheets F / manifest | Not in tracker columns; may appear via `sheet_sync` / ops | **NEEDS ADR** or derive from frontmatter / sheet sync — **NOT VERIFIED** as Founder tracker column |
| body / draft markdown | `content/blog`, batches | `input/{week}/04_Draft.md`, `05_Final.md` | **ALREADY EXISTS** (Founder paths) — body migrate = content import ops, not schema |
| timestamps (`qa_date`, etc.) | Sheets O–R / manifest | File mtimes / QA report dates; no CMS-identical columns | **MAP WITH ADAPTER** / **NOT VERIFIED** per field |

---

## Metadata

| CMS field | Founder locus | Classification |
|-----------|---------------|----------------|
| `target_keyword` | Frontmatter `primary_keyword` | **MAP DIRECTLY** (name adapter) |
| `cta` | Frontmatter `cta_type` (different semantics) | **MAP WITH ADAPTER** |
| `word_count` | `Article.word_count` ORM unused; computable from draft | **MAP WITH ADAPTER** / optional |
| `author` | Not in tracker | **NEEDS ADR** or **DO NOT MIGRATE** for Slice 1 |
| `channels` | Not in tracker; social artifacts separate | **DO NOT MIGRATE** into tracker for Slice 1 (Social/Publishing) |
| `published_url` | Frontmatter `canonical_url`; go-live helpers | **MAP DIRECTLY** (name adapter) |
| `slug` (FS scan) | Derived from canonical URL / filename | **MAP WITH ADAPTER** |
| `tags` (FS scan) | NOT VERIFIED in Founder tracker | **DO NOT MIGRATE** / **NOT VERIFIED** |

---

## Checklist / workflow

| CMS field | Founder locus | Classification |
|-----------|---------------|----------------|
| `brief_done`, `draft_done`, `edited`, `seo_final`, `assets_done` | Artifact existence via `_week_artifacts` + pipeline steps | **MAP WITH ADAPTER** (derive from files, do not require Sheets TRUE flags) |
| `qa_score`, `qa_reports` JSON | `output/qa_reports/*`; `qa_status` on tracker | **MAP WITH ADAPTER** |
| `qa_status` | `tracker.qa_status` | **ALREADY EXISTS** |
| Workflow stage enum CMS | Founder `status`/`current_step` | **MAP WITH ADAPTER** — **NEEDS ADR** for canonical lifecycle enum |

---

## Relationships & storage

| Concept | CMS | Founder | Classification |
|---------|-----|---------|----------------|
| Artifact paths | Implicit FS + `file_path` scan | Explicit `draft_path`, `final_output_path`, `qa_output_path`, `artifact_folder` | **ALREADY EXISTS** |
| Runtime active week | NOT VERIFIED | `runtime_config.active_week` | **ALREADY EXISTS** (Founder-only) |
| ORM `articles` table | None | `Article` bridge model | **DO NOT MIGRATE** CMS→DB for Slice 1; **NEEDS ADR** before activating as SoT |
| `ContentLibrary` | None | Social content library | **DO NOT MIGRATE** (wrong domain) |

---

## Compatibility conclusions

1. **No Alembic / schema change required** for first Content Studio unit if SoT remains `tracker.csv` + filesystem.  
2. **API additive JSON** can project tracker + artifacts without DB.  
3. **Blocking semantic gap:** CMS `Wxx-001` IDs + `stage` enum vs Founder week IDs + `status`/`current_step` → adapter or ADR before write-path parity.  
4. **publish_date** required for true calendar parity — not in Founder tracker header today (`content_id,title,status,qa_status,current_step,next_step,draft_path,qa_output_path,final_output_path,artifact_folder`).
