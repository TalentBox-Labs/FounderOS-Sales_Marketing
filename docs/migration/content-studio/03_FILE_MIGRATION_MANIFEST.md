# 03 — File Migration Manifest

Sprint E1 — Analysis only  
Each row: one classification. Directories not bulk-classified without content inspection.

Classifications: MIGRATE | ADAPT | REFERENCE ONLY | SUPERSEDED BY FOUNDER | RETIRE | OUT OF SCOPE | NOT VERIFIED

---

## CMS `dashboard/` (inspected)

| Source file | Capability | Classification | Rationale |
|-------------|------------|----------------|-----------|
| `dashboard/app.py` | Pipeline/calendar/detail/edit + content APIs | **ADAPT** | Flask routes → Founder FastAPI/Jinja patterns; do not copy Flask app wholesale |
| `dashboard/app_clean.py` | Slimmer twin without edit/update | **REFERENCE ONLY** | Subset of `app.py`; no unique studio capability beyond simpler baseline |
| `dashboard/sheets_integration.py` | Sheets/FS/mock content loaders | **SUPERSEDED BY FOUNDER** (SoT) / **REFERENCE ONLY** (field map) | Founder SoT is `tracker.csv`; column map informs adapters only |
| `dashboard/content_manifest.json` | Static 22-item catalog | **REFERENCE ONLY** | Not loaded by top-level `app.py`; inventory sample for field parity |
| `dashboard/templates/pipeline.html` | Kanban by stage | **ADAPT** | UX pattern → Founder Content Studio UI |
| `dashboard/templates/calendar.html` | Date calendar | **ADAPT** | Requires Founder publish_date source (frontmatter/sheet sync) |
| `dashboard/templates/content_detail.html` | Detail + progress (+ publish UI) | **ADAPT** (studio sections) / **OUT OF SCOPE** (publish buttons) | Split UI when porting |
| `dashboard/templates/content_edit.html` | Metadata edit form | **ADAPT** | Port form fields onto Founder update API |
| `dashboard/templates/articles.html` | All-articles table | **ADAPT** | Wired in nested app only; useful list UX |
| `dashboard/templates/pipeline_detail.html` | Placeholder | **REFERENCE ONLY** | Empty/placeholder |
| `dashboard/templates/media.html` | Media placeholder | **DEFER** → treat as **OUT OF SCOPE** for first unit | Assets engine later |
| `dashboard/templates/queue.html` | Publish queue | **OUT OF SCOPE** | Publishing Engine |
| `dashboard/templates/base.html` | Nav shell | **REFERENCE ONLY** | Founder has `templates/base.html` |
| `dashboard/crewai_qa.py` | Article QA helpers | **OUT OF SCOPE** / **REFERENCE ONLY** | Editorial/QA slice; unwired in top-level app |
| `dashboard/linkedin_*.py`, `auth.py`, `scheduler.py` | Auth/publish/oauth | **OUT OF SCOPE** | Not Content Studio |
| `dashboard/credentials.json`, `data/users.json` | Secrets/users | **RETIRE** (do not copy) | Secrets must not migrate into Founder tree |

---

## CMS `content/` & batches (inspected at layout level)

| Source | Capability | Classification | Rationale |
|--------|------------|----------------|-----------|
| `content/blog/*.md`, `content/drafts/`, `content/briefs/`, `content/research/` | Draft bodies / briefs | **REFERENCE ONLY** | Founder SoT is `input/{week}/`; optional one-time content import is a separate ops task, not Slice 1 code migrate |
| `content/seo-briefs/` | SEO brief artifacts | **OUT OF SCOPE** (SEO Engine) / **REFERENCE ONLY** templates | Not Content Studio CRUD |
| `content/linkedin|twitter|instagram|email/` | Channel packs | **OUT OF SCOPE** | Social/Email/Publishing |
| `content/distribution/**` | Distribution packs + manifests | **OUT OF SCOPE** (Publishing/Social) | May REFERENCE for detail links later |
| `content-batches/*.md`, `content-batches/images/` | Batch drafts/images | **REFERENCE ONLY** | Scanner regex already broken vs filenames; not primary migrate |

---

## CMS nested duplicate apps

| Source | Classification | Rationale |
|--------|----------------|-----------|
| `workcrew-cms-os/workcrew-cms-os/dashboard/app.py` (manifest sync, `/api/qa`) | **NOT VERIFIED** as runtime primary; **REFERENCE ONLY** if patterns needed | Nested tree; start script evidence points to top-level |

---

## CMS_OS_V1 docs

| Source | Classification | Rationale |
|--------|----------------|-----------|
| `CMS_OS_V1/*.md` describing content tracker / dashboard | **REFERENCE ONLY** | Docs pack; 0 Python |

---

## Founder files (destinations — not CMS migrate sources)

| Founder file | Role in Slice 1 | Note |
|--------------|-----------------|------|
| `tracker.csv` | Canonical inventory SoT | KEEP |
| `input/**` | Artifact SoT | KEEP |
| `data/runtime_config.json`, `data/week_runtime/**` | Active week | KEEP |
| `runner_api_routers/ui.py`, `templates/weeks.html`, `week_detail.html`, `pipeline.html` | Existing UI | KEEP + later ADAPT targets |
| `runner_api_routers/utils.py` | Tracker/artifact helpers | KEEP / extend |
| `src/tools/csv_reader.py`, `tracker_updater.py`, `sheet_sync.py` | Tracker IO / optional sheet sync | KEEP; sheet sync not Sheets-as-SoT |
| `revenue_os/models/content.py` `Article` | Bridge model | Do **not** require DB migration for first unit |

---

## Migrate vs Adapt summary

| Classification | Intent |
|----------------|--------|
| **MIGRATE** | None as whole-file binary copy into Founder for Slice 1 first unit |
| **ADAPT** | CMS UX + API *behaviors* into Founder FastAPI/Jinja (or React later) over tracker SoT |
| **SUPERSEDED** | Sheets primary store |
| **OUT OF SCOPE** | Publish/n8n/social/oauth/secrets |
