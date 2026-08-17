# Architecture ADR-003 — Architecture v2.2 (Marketing OS Future Engines)

**ADR ID:** Architecture_ADR_003  
**Status:** Accepted  
**Sprint:** A1  
**Date:** 2026-08-10  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`

**Decision type:** Governance refinement of destination architecture  
**Implementation changes in this ADR:** **NONE**

Supersedes destination structure in [Architecture_ADR_002.md](Architecture_ADR_002.md) / Architecture **v2.1** for Marketing OS module inventory and shipped-status reflection.  
v2.0 / v2.1 freeze history remains valid as prior baselines.

---

## Context

Architecture v2.1 named Marketing OS engines through Brand Engine and separated Publishing vs Website. Since then, Marketing OS has shipped:

- Content Studio (read + kanban)
- Editorial Engine (readiness + Approval Phase 1)
- Publishing Engine (orchestration Phase 1)
- Website Engine (Core + Static Provider)

Long-term destination must also name **Video**, **Newsletter**, and **Community** engines without implementing them, so future sprints have stable ownership language.

---

## Decision

1. **Adopt** Founder OS Architecture **v2.2** as the canonical destination ([Architecture_v2.2.md](Architecture_v2.2.md)).
2. **Retain** all v2.1 Marketing OS engines and Publishing ↔ Website split.
3. **Add** future Marketing OS engines (destination only):
   - Video Engine  
   - Newsletter Engine  
   - Community Engine  
4. **Document** mission, responsibilities, inputs, outputs, dependencies, and current vs future status for each Marketing OS engine in [Marketing_OS_v2.2.md](Marketing_OS_v2.2.md).
5. **Confirm** zero code/runtime/API/DB impact for Sprint A1; no sprint invalidated; compatibility 100%.

---

## Canonical Marketing OS delta (v2.1 → v2.2)

```diff
 Marketing OS
   ├── Content Studio
   ├── Editorial Engine
   ├── Publishing Engine
   ├── Website Engine
   ├── Campaign Engine
   ├── SEO Engine
   ├── GEO Engine
   ├── AEO Engine
   ├── Social Engine
   ├── Email Engine
   ├── Brand Engine
+  ├── Video Engine              (FUTURE)
+  ├── Newsletter Engine         (FUTURE)
+  └── Community Engine          (FUTURE)
```

---

## Consequences

### Positive

- Destination map matches shipped Marketing OS reality
- Future video / newsletter / community work has named owners before code
- Newsletter Engine named separately from Email Engine to avoid premature conflation

### Neutral / deferred

- No implementation of Video / Newsletter / Community in A1
- Email Engine vs Newsletter Engine specialization deferred to a future ADR if needed
- SEO/GEO/AEO/Social/Campaign/Brand remain destination or partial as before

### Costs

- Implementers must not invent parallel engine names outside this inventory

---

## Compatibility

| Item | Compatible? |
|------|-------------|
| Architecture v2.1 (ADR-002) | YES — superseded for destination; history retained |
| M1–M3.5 Publishing / Website baselines | YES |
| E7 Editorial Approval | YES |
| Content Studio baselines | YES |
| All prior sprints | YES — none invalidated |

---

## Impact verification

| Dimension | Impact |
|-----------|--------|
| Runtime | **NONE** |
| API | **NONE** |
| Database | **NONE** |
| Business logic (code) | **NONE** |
| Git / code (A1) | **NONE** |

---

## Rollback

Supersede with a new ADR restoring v2.1 Marketing OS engine list (no Video/Newsletter/Community). No runtime rollback required.

---

## Verdict

**ARCHITECTURE v2.2 FROZEN**

Ready for **G2 — Platform Agent Registry**.
