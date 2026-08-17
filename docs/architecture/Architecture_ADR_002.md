# Architecture ADR-002 — Architecture v2.1 (Website Engine)

**ADR ID:** Architecture_ADR_002  
**Status:** Accepted (historical) — **destination superseded by** [Architecture_ADR_003.md](Architecture_ADR_003.md) / Architecture **v2.2**  
**Sprint:** G1  
**Date:** 2026-08-09  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`

**Decision type:** Governance refinement of destination architecture  
**Implementation changes in this ADR:** **NONE**

> Current canonical destination: [Architecture_v2.2.md](Architecture_v2.2.md).

Supersedes destination structure in [Architecture_ADR_001.md](Architecture_ADR_001.md) / Architecture v2.0 **only** where Website Engine and Publishing Engine boundaries are refined.  
v2.0 freeze history remains valid as prior baseline.

---

## Context

Architecture v2.0 frozen Marketing OS with Publishing Engine owning production publish / go-live broadly. Publishing Engine implementation has **not** started.

A final refinement was approved: the **Website Engine** becomes a dedicated Marketing OS engine so that:

- **Publishing** = orchestration (channels, jobs, queue)
- **Website Management** = canonical site rendering, metadata, site deploy

This prevents Publishing Engine from absorbing website CMS concerns (HTML, slugs, sitemap, WordPress/Ghost, cache invalidation).

---

## Decision

1. **Adopt** Founder OS Architecture **v2.1** as the canonical destination ([Architecture_v2.1.md](Architecture_v2.1.md)).
2. **Add** **Website Engine** under Marketing OS.
3. **Narrow** Publishing Engine to publication orchestration only (no rendering, no SEO ownership, no social APIs, no website implementation knowledge).
4. **Assign** website publishing exclusively to Website Engine.
5. **Refine** Marketing OS engine responsibility matrix per G1 brief (Content Studio through Brand Engine).
6. **Confirm** zero code/runtime/API/DB impact for G1; current implementation remains valid; no sprint invalidated.

---

## Canonical structure delta (v2.0 → v2.1)

```diff
 Marketing OS
   ├── Content Studio
   ├── Editorial Engine
   ├── Publishing Engine
+  ├── Website Engine
   ├── Campaign Engine
   ├── SEO Engine
   ├── GEO Engine
   ├── AEO Engine
   ├── Social Engine
   ├── Email Engine
   └── Brand Engine
```

---

## Responsibility split (accepted)

| Engine | Owns | Does not own |
|--------|------|--------------|
| Publishing Engine | Destination channels, publish jobs, publish queue; consumes approved editorial artifacts | Website rendering, SEO, social APIs, site CMS |
| Website Engine | Canonical Founder website: MD→HTML, slugs, URLs, metadata, OG, Schema.org, RSS, sitemap, assets, site API, future WP/Ghost, search index hooks, cache invalidation, deploy hooks; **website publishing only** | Campaign logic, social publishing |

---

## Consequences

### Positive

- Clean M1 Publishing Engine Phase 1 scope (orchestration only)
- Website concerns have a named long-term home before any publish code lands
- Social/Email/Campaign remain separate channel owners

### Neutral

- Existing go-live / hashnode helpers remain valid *current* code until future M-sprints remap ownership
- SEO Engine still owns SEO scoring/strategy; Website Engine owns on-site metadata emission for the site

### Costs

- Implementers must not put HTML/sitemap logic inside Publishing Engine in M1+

---

## Compatibility

| Item | Compatible? |
|------|-------------|
| Architecture v2.0 (ADR-001) | YES — superseded for destination; history retained |
| Content Studio / Editorial / E7 | YES |
| Runtime / Migration baselines | YES |
| All prior sprints | YES — none invalidated |
| Publishing Engine impl started? | NO — safe to refine |

---

## Impact verification

| Dimension | Impact |
|-----------|--------|
| Runtime | **NONE** |
| API | **NONE** |
| Database | **NONE** |
| Business logic (code) | **NONE** |
| Git / code changes (G1) | **NONE** |

---

## Rollback

Supersede with a new ADR restoring v2.0 Marketing OS engine list (no Website Engine). No runtime rollback required.

---

## Verdict

**ARCHITECTURE v2.1 FROZEN**

Ready for **M1 — Publishing Engine Phase 1**.
