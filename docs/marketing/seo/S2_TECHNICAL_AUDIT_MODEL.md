# S2 — Technical SEO Audit Model

**Sprint:** S2  
**Agent:** LEDGER

---

## Storage

| Path | Contents |
|------|----------|
| `output/seo/technical/site.json` | Site technical report |
| `output/seo/technical/{slug}.json` | Optional page report |

Writer: `write_technical_audit()` — non-authoritative, `mutates_content: false`.

---

## Finding schema

Each finding exposes:

| Field | Purpose |
|-------|---------|
| `id` | Rule ID |
| `category` | Family |
| `severity` | DOMAIN_BLOCKED / CRITICAL / ERROR / WARNING / INFO / PASS / N/A |
| `artifact` | Where |
| `expected` / `actual` | Why |
| `recommendation` | What next |
| `evidence` | Structured extras |
| `ownership` | SEO_ENGINE / WEBSITE_ENGINE / CONTENT / DOMAIN / EXPECTED |
| `blocking` | bool |

Operator can answer: **WHAT / WHERE / WHY / EXPECTED / ACTUAL / NEXT**.

---

## Live API / UI read models

- `GET /api/v1/seo/technical` (+ `/technical/site`)
- `GET /api/v1/seo/technical/{slug}`
- `/seo/technical` (Jinja, read-only)

S1 readiness endpoints and UI remain frozen separately.
