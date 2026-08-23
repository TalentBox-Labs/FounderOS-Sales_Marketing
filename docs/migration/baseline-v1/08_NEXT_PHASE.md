# 08 — Next Phase (Approved Roadmap)

Approved sequence from Sprint B slices and E1/E2 outcomes.  
No speculative phases beyond repository-approved slice order.

Evidence: [03_MIGRATION_SLICES.md](../03_MIGRATION_SLICES.md), [09_FIRST_IMPLEMENTATION_UNIT.md](../content-studio/09_FIRST_IMPLEMENTATION_UNIT.md), [10_SPRINT_E1_VERDICT.md](../content-studio/10_SPRINT_E1_VERDICT.md).

---

## Roadmap

```
Current
  ↓
Content Studio Read          ← COMPLETED (Sprint E2)
  ↓
Content Studio UI            ← Phase 2 (adapt CMS UX onto Founder SoT)
  ↓
Kanban                       ← stage-board UX (requires lifecycle projection ADR)
  ↓
Calendar                     ← requires publish_date / date source ADR
  ↓
Lifecycle ADR                ← ID skew + stage enum mapping
  ↓
Write APIs                   ← metadata update over tracker/frontmatter
  ↓
Stage workflow               ← status transitions (Founder adapter)
  ↓
Publishing                   ← Slice 3 Publishing Engine
  ↓
Remaining Engine migrations  ← Campaign / SEO / Social / Email / Brand / n8n per Sprint B
  ↓
CMS archive                  ← retire reference runtime after capability parity
```

---

## Phase 2 entry criteria (satisfied)

| Criterion | Status |
|-----------|--------|
| Architecture Baseline v1.0 frozen | Yes |
| Runtime Baseline v1.1 frozen | Yes |
| Content Studio read API complete | Yes |
| No new regressions from E2 | Yes |
| Repository governance certified | Yes |

---

## Explicit non-goals for immediate next work

- Blind CMS folder copy  
- Sheets-as-SoT  
- Flask dual-runtime  
- OpenClaw import  
- DB schema as Content Studio SoT (without separate ADR)
