# R1E — Legacy Consolidation Manifest

**Date:** 2026-08-12  
**Destructive removals:** 0  
**Archive moves:** 0  
**Consolidation:** 1 index document

| ID | Path | Previous | Final | Action | Reason | Risk | Rollback | Tests | Conf |
|----|------|----------|-------|--------|--------|------|----------|-------|------|
| L01–L02 | Sibling CMS trees | KEEP→ARCHIVE | DEFER — FOUNDER DECISION | none | External refs; parity archive timing | High if deleted | N/A | N/A | HIGH |
| L04–L08 | Branding / WORKCREW_* / crm names | ACTIVE | KEEP — ACTIVE COMPATIBILITY | none | Live contracts | High if renamed blindly | N/A | N/A | HIGH |
| L09–L10 | workcrew.ai emitters | STALE RUNTIME | DEFER — FOUNDER DECISION | none | Domain/brand FD | Med | N/A | N/A | HIGH |
| L11 | site_origin denylist | ACTIVE | KEEP — ACTIVE COMPATIBILITY | none | SEO safety | High if removed | N/A | SEO tests | HIGH |
| L12 | input FM hosts | CONTENT | KEEP — MIGRATION EVIDENCE | none | Content history | High | N/A | N/A | HIGH |
| L13–L15 | Hashnode paths | ACTIVE | KEEP — ACTIVE COMPATIBILITY / FD | none | Optional publish still wired | High | N/A | hashnode tests | HIGH |
| L16–L17 | Sheets mirror / SoT policy | ACTIVE / ME | KEEP | none | Ops mirror + SoT law | High | N/A | sheet tests | HIGH |
| L18–L19 | Publishing/Website stubs | ACTIVE | KEEP — ACTIVE COMPATIBILITY | none | Frozen contracts | Critical | N/A | publishing/website tests | HIGH |
| L20 | `*.py.old` | SAFE REMOVE | already removed R1A | none | Done | — | git | — | HIGH |
| L22 | Dual `@app` handlers | STALE | DEFER — NEEDS VERIFICATION | none | Route ownership risk | Med | N/A | N/A | HIGH |
| L23–L26 | Hist comments / migration / audit packs | HISTORICAL | KEEP — GOVERNANCE / MIGRATION | none | Evidence | Critical if deleted | N/A | N/A | HIGH |
| L27 | Root Phase docs | STALE | KEEP — GOVERNANCE; ARCHIVE cand | index only | Discoverability | Low | delete index | N/A | MED |
| L28 | n8n bridge | ACTIVE | KEEP — ACTIVE COMPATIBILITY | none | Automation platform | High | N/A | N/A | HIGH |
| NAV | `docs/audit/R1E_LEGACY_NAV_INDEX.md` | — | CONSOLIDATED nav | **ADD** | Pointer consolidation | Low | delete file | docs-only | HIGH |

**Items Removed: 0 · Items Archived: 0 · Items Consolidated: 1**
