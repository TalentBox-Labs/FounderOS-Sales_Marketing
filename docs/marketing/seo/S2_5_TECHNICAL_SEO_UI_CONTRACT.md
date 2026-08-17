# Technical SEO UI Contract v1.0

**Sprint:** S2.5  
**Status:** **FROZEN v1.0**  
**Routes:** `runner_api_routers/ui.py`  
**Template:** `templates/seo_technical.html`  
**Nav:** `templates/base.html` → “Technical SEO”

Breaking UI changes require explicit governance.

---

## 1. Routes (frozen)

| Method | Path | View | Purpose |
|--------|------|------|---------|
| `GET` | `/seo/technical` | `seo_technical.html` | Technical SEO site summary |

Registered **before** `/seo/{slug}` so `technical` is not captured as a readiness slug.

### Related but separately frozen (S1.5)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/seo` | Readiness site list |
| `GET` | `/seo/{slug}` | Readiness page detail |

---

## 2. Data source

`analyze_technical_site().to_dict()` — read-only.

No form POSTs, no action buttons that mutate.

---

## 3. Displayed information

- Boundary banner: no fix / rewrite / publish / index / submit / internet crawl; S1 contract unchanged  
- Site `status` · technical `score` · page count · configured origin · site finding count  
- Site-wide findings list (non-PASS / non-N/A): severity · category · id · message  
- Pages table: slug, status, score, crawlable, blockers, critical, errors, warnings  

Severity representation uses finding `severity` values including **DOMAIN_BLOCKED**.

---

## 4. Actions inventory

| Action | Present |
|--------|---------|
| Fix / Rewrite / Publish / Index / Submit / Crawl | **No** |
| Link to `/seo` (readiness) | Yes (navigation only) |

---

## 5. Operator contract

UI supports distinguishing domain blockers vs technical issues via severity labels and counts. No keyword strategy, copy generation, or LLM remediation.
