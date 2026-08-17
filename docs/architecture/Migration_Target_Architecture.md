# Migration Target Architecture — Founder OS v2.2

**Status:** FROZEN (migration target definition only)  
**Sprint:** A1 (updated from G1)  
**Date:** 2026-08-10  
**Parent:** [Architecture_v2.2.md](Architecture_v2.2.md)

Governance only. **No migration execution in A1.**

---

## 1. Purpose

Define the **target architecture** that future migration / M-sprints move toward.  
Current implementation remains the operational baseline until an implementation sprint lands changes.

---

## 2. Target state (summary)

Founder OS per Architecture **v2.2**:

- Marketing OS engines own content → editorial → publish orchestration → website / social / email → campaigns / SEO/GEO/AEO / brand
- Future Marketing engines named: Video, Newsletter, Community (not implemented)
- Publishing Engine ≠ Website Engine
- Sales / Revenue / CS / Executive / Ops / Knowledge OS own their verticals
- AI / Automation / Shared Platforms as in v2.1 law

Canonical control flow:

**Agent → Recommendation → Human Approval (when required) → Automation → Execution → Audit**

---

## 3. Mapping: current → target (delta notes)

| Current locus | Target owner |
|---------------|--------------|
| Content Studio / Editorial / Publishing routers | Marketing OS (SHIPPED cores) |
| `src/tools/website_engine` + static provider | Marketing OS / Website Engine |
| Publishing channel PLACEHOLDER for website | Future thin wire to Website Engine |
| Social/email channel NOT_IMPLEMENTED | Social Engine / Email Engine |
| Marketing agent UI SEO/GEO/AEO labels | Formal SEO/GEO/AEO engines (destination) |
| No video/newsletter/community modules | FUTURE engines — do not invent code in A1 |
| Celery / Redis / n8n | Automation Platform |
| Auth dual model | Shared Platform |

---

## 4. Migration principles

Unchanged from v2.1, plus:

7. **Named future engines** — Video / Newsletter / Community require dedicated sprints; naming alone is not authorization to implement in A1.
8. **Publishing ≠ Website** — still mandatory.

---

## 5. Impact of A1 on migration

| Dimension | Impact |
|-----------|--------|
| Migration execution | **NONE** |
| Code / API / DB / runtime | **NONE** |
| Target clarity | **UPDATED TO v2.2 / FROZEN** |

---

## 6. Next

After A1: **G2 Platform Agent Registry** (platform governance).  
Website public reachability remains **M4 deployment decision** (separate).
