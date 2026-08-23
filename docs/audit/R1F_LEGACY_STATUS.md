# R1F — Legacy Remnant Status (SCOUT)

**Sprint:** R1F  
**Date:** 2026-08-13  
**Mode:** MEASUREMENT ONLY — no removals

Re-check of R1E inventory themes against live tree.

---

## Reference Repositories (FOUNDER DECISION)

| Ref | Path | Why it remains | Blocks Social? |
|-----|------|----------------|----------------|
| CMS OS reference | `/Users/krishna/Documents/workcrew-cms-os` | Migration/parity evidence for Content Studio; **external** to canonical repo | **NO** |
| CMS docs pack | `/Users/krishna/Documents/CMS_OS_V1` | Historical docs pack for migration citations | **NO** |

**Classification: FOUNDER DECISION — NON-BLOCKING**

Evidence for later disposition:

| Decision | Evidence required |
|----------|-------------------|
| KEEP | Ongoing citation in active migration/parity work |
| ARCHIVE | Founder confirms parity complete; archive location named; no open citations in active sprints |
| REMOVE | Founder confirms no recovery need **and** archive already exists |

Coordinator does **not** decide KEEP/ARCHIVE/REMOVE in R1F.

---

## Runtime / Config Remnants

| Theme | Measured | Class |
|-------|----------|-------|
| `workcrew.ai` emitters (`marketing_crew`, `runner_api` OpenAPI/examples, go_live helpers, related) | **4** primary surfaces | **ACTIVE COMPATIBILITY** / brand — **DEFERRED** rename (Founder) |
| Hashnode optional publish + status + social publisher | **3** remnant surfaces | **ACTIVE COMPATIBILITY** |
| CMS/Sheets mirror family | **1** family (multi-file tools) | **ACTIVE COMPATIBILITY** |
| Site-origin denylist / old host strings | Present in SEO safety | **ACTIVE** safety — keep |
| Publishing stubs / stub provider | Present | **ACTIVE COMPATIBILITY** |
| Sibling CMS trees | Outside repo; present on disk | **FOUNDER DECISION REQUIRED** |
| Old org/repo name strings in docs | Present | **HISTORICAL** |
| Legacy deploy refs in historical M-series docs | Present | **HISTORICAL** |

---

## Counts for Exit Gate

**Legacy Runtime Remnants Remaining: 8** (4 + 3 + 1)

| Bucket | N |
|--------|--:|
| SAFE FUTURE REMOVAL | 0 (none approved) |
| STALE RUNTIME (emitters pending brand FD) | 4 (brand URLs; still emit) |
| STALE CONFIG | 0 new |
| DEFERRED | Founder themes (brand, Hashnode SoT, CMS archive timing) |
| FOUNDER DECISION REQUIRED | Reference repos (+ brand/domain open items) |

---

## Social Engine Impact

None of the retained remnants **must** be deleted before Social S0. Social Engine should treat Hashnode/WorkCrew branding as **compatibility context**, not blockers. Domain/brand Founder decisions remain open but are product/identity gates, not cleanup gates.
