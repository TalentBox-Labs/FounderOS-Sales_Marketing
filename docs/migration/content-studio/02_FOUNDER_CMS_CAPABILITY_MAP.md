# 02 — Founder ↔ CMS Content Studio Capability Map

Sprint E1 — Analysis only  
Founder status values: IMPLEMENTED | PARTIAL | MISSING | LEGACY | TRANSITIONAL | NOT VERIFIED

---

## Capability map

| # | CMS Content Studio capability | CMS evidence | Founder equivalent | Founder status | Evidence |
|---|------------------------------|--------------|--------------------|----------------|----------|
| 1 | Content inventory list | `GET /api/content`, `/` Kanban | `GET /weeks` HTML table from `tracker.csv` | **IMPLEMENTED** | `runner_api_routers/ui.py` `page_weeks`; `utils._read_tracker` |
| 2 | Content detail portal | `GET /content/<id>` | `GET /weeks/{week_id}` | **IMPLEMENTED** | `ui.py` `page_week_detail`; `week_detail.html` |
| 3 | Read-only artifact/file view | Detail + FS reads | `GET /weeks/{id}/file/{filename}` | **IMPLEMENTED** | `ui.py` `page_file_view`; `file_view.html` |
| 4 | Metadata edit form + update API | `/content/<id>/edit`, `POST /api/content/<id>/update` | None for tracker fields | **MISSING** | No Founder JSON update for title/stage/date |
| 5 | Stage / lifecycle transitions | `POST .../stage/<stage>`, batch stage | QA updater + go-live step only | **PARTIAL** | `src/tools/tracker_updater.py`; `go_live_helpers.record_live`; no stage enum API |
| 6 | Calendar (date grid) | `GET /calendar` | `/weeks` titled “Content Calendar” but filter table | **PARTIAL** / **TRANSITIONAL** | `weeks.html`; tracker has **no** `publish_date` column |
| 7 | Pipeline Kanban by stage | `GET /` → `pipeline.html` stages | Step chips on weeks; `/pipeline` = runner UI | **PARTIAL** / **TRANSITIONAL** | `ui.py` `_week_pipeline_steps`; `templates/pipeline.html` run controls |
| 8 | Weeks grouping API | `GET /api/weeks` | Missing JSON | **MISSING** | — |
| 9 | Content stats API | `GET /api/stats` | Dashboard HTML stats only | **PARTIAL** | `ui.py` `_dashboard_stats` |
| 10 | Create content record | No create API in top-level CMS | No new-week row API; `/generate` creates artifacts | **PARTIAL** | `runner_api_routers/pipeline.py` `POST /generate` |
| 11 | Draft body storage | `content/blog`, `content-batches` | `input/{week}/04_Draft.md`, `05_Final.md` | **IMPLEMENTED** | `input/`, tracker `draft_path`/`final_output_path` |
| 12 | Week runtime profile | Sheets week column | `data/runtime_config.json` + `data/week_runtime/*.json` | **IMPLEMENTED** | Founder-only strength |
| 13 | Active week switch | NOT VERIFIED in CMS studio | `POST /switch-week` | **IMPLEMENTED** | `pipeline.py` |
| 14 | Studio validators / QA reports | Checklist + nested `crewai_qa` | Five validators + `output/qa_reports/` | **IMPLEMENTED** | `ui.py` `_validator_results`; `src/tools/*_checker.py` |
| 15 | Content ID model `W01-001` | Manifest/Sheets IDs | Tracker `content_id` like `W01`, `W05A` | **TRANSITIONAL** | ID skew CMS vs Founder (adapter needed) |
| 16 | Google Sheets as SoT | `sheets_integration.py` primary | `tracker.csv` SoT + optional `sheet_sync.py` outbound | **IMPLEMENTED** (Founder path) / CMS Sheets **SUPERSEDED** | Founder `tracker.csv`; `src/tools/sheet_sync.py` |
| 17 | Static JSON manifest SoT | `content_manifest.json` | Not used | **MISSING** in Founder (by design) | CMS top-level app does not load it |
| 18 | DB `Article` bridge | N/A | `revenue_os.models.content.Article` | **LEGACY** / unused as week API | Model docstring: bridge to tracker + final.md; no weeks CRUD router |
| 19 | Parallel DB content library | N/A | `/api/v1/social/content*` `ContentLibrary` | **LEGACY** (parallel, not week SoT) | Not Content Studio weeks |
| 20 | Editorial generate/edit crews | CMS SOUL personas (out of studio core) | `POST /generate`, `POST /edit` | **IMPLEMENTED** | Keep Founder; not CMS migrate |

---

## Summary

| Founder status | Count (approx.) |
|----------------|-----------------|
| IMPLEMENTED | Inventory list/detail/file view, FS drafts, runtime profiles, validators, switch-week, generate/edit |
| PARTIAL / TRANSITIONAL | Calendar, Kanban, stage lifecycle, create, stats, ID model |
| MISSING | Metadata edit API, stage API, JSON content/weeks APIs, CMS calendar grid |
| LEGACY | Unused `Article` ORM as week API; social ContentLibrary parallel |

**Decision alignment (Sprint B):** MERGE — Founder runtime SoT + CMS UX patterns (`docs/migration/01_CAPABILITY_MATRIX.md` Content Studio rows; `02_CONSOLIDATION_STRATEGY.md`).
