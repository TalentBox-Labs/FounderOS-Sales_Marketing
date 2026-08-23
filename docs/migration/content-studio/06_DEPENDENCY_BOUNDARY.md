# 06 — Dependency Boundary Check

Sprint E1 — Analysis only  
Cross-cutting runtimes must not be absorbed into Marketing OS / Content Studio solely because CMS used them.

Classifications: KEEP | REPLACE WITH FOUNDER EXISTING | DECOUPLE | DEFER TO LATER SLICE | RETIRE

---

## Per dependency

| Dependency | CMS Content Studio usage | Classification | Evidence / action |
|------------|--------------------------|----------------|-------------------|
| Google Sheets | Primary content CRUD SoT | **REPLACE WITH FOUNDER EXISTING** | Founder `tracker.csv` + `get_active_content`; optional Founder `sheet_sync.py` remains outbound bridge, not SoT |
| Filesystem | Drafts, images, packs | **KEEP** (Founder `input/` + `output/`) | Decouple CMS `content/` path assumptions |
| Flask | Dashboard runtime | **RETIRE** (do not host Flask studio in Founder) | Adapt UX into FastAPI/Jinja |
| n8n | Publish webhooks | **DEFER TO LATER SLICE** | Publishing / Automation Platform |
| LinkedIn OAuth / platform APIs | Publish + auth | **DEFER TO LATER SLICE** | Social / Publishing |
| OpenClaw / agents SOUL | CMS agent collective | **DEFER TO LATER SLICE** | AI Platform — playbooks only if ever |
| CrewAI (`crewai_qa.py`) | Nested QA API | **DEFER TO LATER SLICE** / **REPLACE WITH FOUNDER EXISTING** validators | Founder `src/tools/*` + QACrew |
| Redis | NOT VERIFIED in CMS studio CRUD | **KEEP** (Founder platform) — unused by Slice 1 studio | Shared Platform |
| Celery | NOT VERIFIED in CMS studio CRUD | **KEEP** (Founder platform) — unused by Slice 1 | Shared Platform |
| Postgres | NOT used by CMS studio dicts | **KEEP** Founder DB — **do not require** for first studio unit | `Article` ORM activation = later ADR |
| Hashnode | Not studio CRUD | **DEFER TO LATER SLICE** | Publishing |
| Brand assets (`brand/`) | Not required for list/detail | **DEFER TO LATER SLICE** | Brand Engine |
| SEO logic | seo-briefs as files; QA SEO checks | **DEFER TO LATER SLICE** for engine; artifact display **KEEP** Founder SEO plan file | SEO Engine |
| Publishing workflows | Detail page buttons | **DECOUPLE** from Content Studio UI port | Publishing Engine |
| External Google APIs (Sheets OAuth) | Required for CMS live edit | **RETIRE** as hard dependency for Studio | Use Founder tracker writers |

---

## Boundary rules for implementation

1. Content Studio owns **inventory + lifecycle UX + metadata edit** over Founder SoT.  
2. Generation/edit crews stay **Editorial Engine** (existing `/generate`, `/edit`).  
3. Publish/schedule/n8n stay **Publishing / Automation**.  
4. No new cross-cutting runtime introduced for Slice 1.
