# UI1 — UI Architecture Options

**Sprint:** UI1  
**Date:** 2026-08-13  
**Scale:** 1–5 (higher = better)

| Option | Effort | Consistency | Reuse | Data | Governance | Maintain | Usability | Scale | **Total /40** |
|--------|-------:|------------:|------:|-----:|-----------:|---------:|----------:|------:|--------------:|
| **A** Extend Jinja shell | 5 | 5 | 4 | 5 | 5 | 5 | 4 | 4 | **37** |
| **B** New parallel shell | 2 | 2 | 3 | 4 | 4 | 2 | 4 | 3 | **24** |
| **C** Cockpit route in Jinja | 5 | 5 | 5 | 5 | 5 | 5 | 4 | 4 | **38** |
| **D** Mount React + new page | 3 | 3 | 4 | 4 | 4 | 3 | 5 | 4 | **30** |

---

## Recommendation: **OPTION C**

**Dedicated Executive Cockpit route inside current Jinja application** (`GET /cockpit` or `/executive`), extending `base.html`.

**Rationale:**
- Primary live shell is already Jinja (`ui.py`)
- SEO, editorial, publishing, sales prospecting already mounted there
- React CRM **unmounted** locally — building UI2 in React adds mount dependency
- Composition: reuse existing API fetches (vanilla JS pattern in templates)
- Governance: human-gated mutations call existing runner endpoints with `requested_by` field
- No parallel frontend architecture

**Not recommended now:** Option B (new shell), full React cockpit until CRM mount/refactor sprint.
