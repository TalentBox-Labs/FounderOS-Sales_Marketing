# 08 — Risk Register

Sprint E1 — Analysis only  
Severity: LOW | MEDIUM | HIGH | BLOCKER

---

| ID | Risk | Evidence | Impact | Mitigation | Rollback | Severity |
|----|------|----------|--------|------------|----------|----------|
| R1 | Content ID skew (`W01-001` vs `W01`/`W05A`) | CMS manifest/Sheets vs Founder `tracker.csv` | Broken joins, wrong detail pages | Adapter layer + ADR; prefer Founder IDs as canonical | Disable adapter; HTML weeks only | **HIGH** |
| R2 | Lifecycle enum mismatch (CMS stages vs tracker status/steps) | CMS `STAGES` in `app.py`; Founder `status`/`current_step` | Incorrect stage board / bad writes | Read-only projection first; ADR before writes | Feature-flag stage API off | **HIGH** |
| R3 | Calendar needs `publish_date` absent from tracker | Tracker header has no publish_date | Calendar UX incomplete | Defer calendar or derive from frontmatter/sheet_sync | Keep `/weeks` table | **MEDIUM** |
| R4 | Accidental Sheets-as-SoT reintroduction | CMS `sheets_integration.py` primary | Dual SoT drift | Forbid Sheets writes in Studio unit; Founder tracker only | Revert writers | **HIGH** |
| R5 | Publish UI mixed into detail template | `content_detail.html` multi-platform section | Side effects / scope creep | Port studio sections only; strip publish | Remove new UI | **MEDIUM** |
| R6 | Nested CMS app confusion | Duplicate `workcrew-cms-os/workcrew-cms-os/...` | Migrating wrong source | Use top-level `dashboard/app.py` only | N/A | **MEDIUM** |
| R7 | Route collision `/pipeline` meanings | Founder runner vs CMS Kanban | UX/API confusion | New Studio board path; keep Founder `/pipeline` | Remove new route | **MEDIUM** |
| R8 | Activating `Article` ORM as SoT without ADR | `revenue_os/models/content.py` bridge unused | Unexpected DB/schema work | First unit filesystem/tracker only | Drop ORM usage | **MEDIUM** |
| R9 | Docker API image lag (pre-D0) | Runtime Baseline v1.1 | Live demo mismatch | Rebuild API before live Studio demos | N/A (ops) | **LOW** (Environment) |
| R10 | Marketing HTML 500 (`integration_status`) | D1.5 review | Studio nav confusion if linked | Do not block Slice 1; Known non-blocking | N/A | **LOW** |
| R11 | UI/API drift inside CMS itself | `pipeline.html` posts `/api/bulk-update` vs server `/api/batch/update-stage` | Porting broken CMS contracts | Re-implement against Founder contracts, not CMS bugs | N/A | **MEDIUM** |
| R12 | Content body import from CMS `content/` | Large FS trees; ID skew | Ops risk if treated as code migrate | Keep REFERENCE ONLY; separate import runbook | Leave Founder `input/` | **LOW** |

---

## Blocking risks for starting implementation

| Count | Items |
|------:|-------|
| **BLOCKER** | **0** — no unexplained production blocker prevents a **read-only** first unit |
| **HIGH** (must address before write-path) | R1, R2, R4 |

Slice 1 implementation may start with the read-only unit (see 09) while HIGH risks are ADR’d before edit/stage writes.
