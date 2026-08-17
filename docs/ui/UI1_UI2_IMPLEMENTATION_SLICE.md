# UI1 — UI2 Implementation Slice

**Sprint:** UI1 defines; **UI2 implements**  
**Date:** 2026-08-13

---

## UI2 — Minimum Viable Executive Cockpit

**Name:** UI2 — EXECUTIVE COCKPIT v1 (Jinja composition)

### IN_SCOPE_UI2

| Item | Detail |
|------|--------|
| Shell | One new Jinja route `GET /cockpit` extending `base.html` |
| Navigation | Add "Executive Cockpit" to sidebar |
| Read surfaces (3–5) | (1) Attention queue summary (2) Sales snapshot (3) Marketing/SEO snapshot (4) Commercial flow honesty panel (5) System/heartbeat status |
| Data | Existing GET APIs only + optional one read-only MC04 pending aggregation |
| Mutations (max 1–2) | QualifiedDemand accept/reject forms OR link-outs to existing editorial/publishing — **only** via frozen human-gated APIs with `requested_by` |
| Auth | Reuse `_verify_api_key` / existing session pattern from templates |

### OUT_OF_SCOPE_UI2

| Item | Reason |
|------|--------|
| React CRM mount/refactor | RETAIN_AND_REFACTOR_LATER |
| New SoT tables | Prohibited |
| Autonomous mutations | Prohibited |
| Social live publish UI | Blocked FD-01/ES |
| Production SEO activation | Domain blocked |
| CommercialOutcome UI | Not implemented |
| Fake/placeholder metrics | Prohibited |
| JWT dual-stack exposure | Bypass risk |
| Full analytics platform | Scope creep |

---

## Composition approach

```
templates/cockpit.html
  → fetch /api/v1/crm/contacts, /deals (read)
  → fetch /api/v1/seo/readiness/summary
  → fetch /api/v1/heartbeat/status
  → fetch /api/v1/editorial/pending (count)
  → optional: qualified-demand pending read endpoint
  → render decision cards with links to existing mounted pages
```

**Estimated reusable components:** 20+ Jinja pages/API patterns; 5+ API domains; 0 new business rules.

---

## Prerequisites (non-blocking)

- Document JWT contact bypass as known defect (do not route UI2 through JWT stack)
- Optional: read-only MC04 pending list endpoint (UI2 or UI2.1)

**Verdict for UI2:** **READY** (conditional on composition-only scope)
