# SEO Readiness UI Contract v1.0

**Sprint:** S1.5 freeze  
**Agent:** NOVA  
**Status:** FROZEN  
**Templates:** `templates/seo_readiness.html`, `templates/seo_readiness_detail.html`  
**Routes:** `runner_api_routers/ui.py`

---

## 1. Routes (frozen)

| Method | Path | Template | Purpose |
|--------|------|----------|---------|
| `GET` | `/seo` | `seo_readiness.html` | Site readiness list |
| `GET` | `/seo/{slug}` | `seo_readiness_detail.html` | Page readiness detail |

Nav: Overview → “SEO Readiness” in `templates/base.html`.

---

## 2. Data sources

| Page | Call |
|------|------|
| `/seo` | `analyze_site().to_dict()` |
| `/seo/{slug}` | `analyze_page_artifact(default_artifact_root(), slug)` |

Read-only analysis. No form POSTs from these templates.

---

## 3. Displayed information

### Site (`/seo`)

- Boundary banner (no auto-fix/publish/index/submit)
- Aggregate `status`, `page_count`, `configured_origin`, truncation note
- Table: slug (link), status, score, blocker/error/warning counts

### Detail (`/seo/{slug}`)

- Status · score · title · canonical · origin
- **DOMAIN BLOCKERS** section (“What prevents SEO-ready?”)
- Errors section
- Warnings section
- Full checks table (id, status, message)
- Back link to `/seo` only

---

## 4. Actions inventory (verified)

| Action | Present? |
|--------|----------|
| Fix button | **No** |
| Rewrite / AI rewrite | **No** |
| Publish | **No** |
| Submit / Index | **No** |
| Mutate content | **No** |
| Navigation to `/seo` list | Yes (read-only) |

UI is strictly read-only for readiness.

---

## 5. Operator contract alignment

Detail page answers: **What prevents this page from being SEO-ready?** via `domain_blockers` first, then errors/warnings — matching BEACON S1 operator guide.
