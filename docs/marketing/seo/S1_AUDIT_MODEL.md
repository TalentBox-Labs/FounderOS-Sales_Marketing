# S1 — SEO Audit Model

**Sprint:** S1  
**Agent:** LEDGER

---

## Principles

1. SEO analysis results are **inspectable**.
2. Persistence is **additive** and **non-authoritative**.
3. Results are **clearly separated** from source content (`input/`).
4. **No new database** for S1 readiness.

---

## Storage

| Path | Contents |
|------|----------|
| `output/seo/readiness/{slug}.json` | Per-page readiness report |
| `output/seo/readiness/site.json` | Site aggregate |

Writers: `src/tools/seo_engine/audit.py` → `write_page_audit`, `write_site_audit`.

Each file includes:

```json
{
  "generated_at": "...",
  "authoritative": false,
  "source_of_truth": "Website Engine artifacts + SEO Engine analysis",
  "mutates_content": false,
  "report": { "...": "PageReadinessResult / SiteReadinessResult" }
}
```

---

## Live read models (no persistence required)

| Surface | Type |
|---------|------|
| `analyze_html` / `analyze_site` return values | In-memory |
| `GET /api/v1/seo/readiness` | JSON API |
| `GET /api/v1/seo/readiness/{slug}` | JSON API |
| `/seo`, `/seo/{slug}` | Jinja read-only UI |

---

## Non-authority statement

- Website Engine artifacts remain the render source of truth.
- Content Studio / Editorial bundles remain the content source of truth.
- SEO readiness JSON never gates publish automatically in S1.
- Regenerating audits is always safe (overwrite allowed under `output/seo/`).

---

## Forbidden

- Writing into `input/**`
- Writing into Website Engine source modules as side effects of analysis
- Storing readiness as a substitute for editorial approval
