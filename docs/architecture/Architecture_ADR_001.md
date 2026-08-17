# Architecture ADR-001 — Freeze Founder OS Architecture v2.0

**ADR ID:** Architecture_ADR_001  
**Status:** Accepted (historical) — **destination superseded by** [Architecture_ADR_002.md](Architecture_ADR_002.md) / Architecture **v2.1**  
**Sprint:** G0  
**Date:** 2026-08-09  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`

**Decision type:** Governance freeze (destination architecture)  
**Implementation changes in this ADR:** **NONE**

> Current canonical destination: [Architecture_v2.1.md](Architecture_v2.1.md).  
> This ADR remains the G0 freeze record; architectural law and human-gate principles carry forward.

---

## Context

Founder OS has accumulated architecture audits, migration baselines, Marketing OS engine work (Content Studio, Editorial Readiness, Editorial Approval Phase 1), Revenue OS surfaces, AI/crew runtimes, and Automation (Celery/n8n) paths.

Prior documents describe *as-is* and near-term sprints. The repository lacked a single **canonical long-term destination architecture** that:

- Names OS modules vs Platforms
- States the architectural law (business vs infrastructure)
- Codifies agent governance and mandatory human gates
- Supersedes conflicting planning narratives without rewriting running code

Sprint G0 freezes that destination as **Founder OS Architecture v2.0**.

---

## Decision

1. **Adopt** the canonical structure in [Architecture_v2.md](Architecture_v2.md) as Founder OS Architecture **v2.0 FROZEN**.
2. **Bind** principles in [Architecture_Principles.md](Architecture_Principles.md) and boundaries in [Platform_vs_OS_Boundaries.md](Platform_vs_OS_Boundaries.md).
3. **Treat** [Migration_Target_Architecture.md](Migration_Target_Architecture.md) and [Future_Module_Roadmap.md](Future_Module_Roadmap.md) as the migration/roadmap companions — not as authorization to change runtime in G0.
4. **Declare** that Architecture v2.0 supersedes prior *planning* documents for destination structure, while **preserving** frozen implementation baselines and sprint evidence packages.
5. **Require** future structural moves (OS ↔ Platform ownership changes, new OS/Platform, human-gate changes) to amend Architecture v2.0 via ADR.

---

## Canonical structure (accepted)

```
Founder OS
├── Executive OS
├── Sales OS
├── Revenue OS
├── Marketing OS
│   ├── Content Studio
│   ├── Editorial Engine
│   ├── Publishing Engine
│   ├── Campaign Engine
│   ├── SEO Engine
│   ├── GEO Engine
│   ├── AEO Engine
│   ├── Social Engine
│   ├── Email Engine
│   └── Brand Engine
├── Customer Success OS
├── Operations OS
├── Knowledge OS
├── AI Platform
├── Automation Platform
└── Shared Platform
```

---

## Architectural law (accepted)

- Business logic → OS modules  
- Infrastructure → Platforms  
- OS modules never own infrastructure  
- Platforms never own business decisions  

---

## Agent governance (accepted)

**Agent → Recommendation → Human Approval (when required) → Automation Platform → Execution → Audit**

Mandatory human gates: editorial approval; campaign launch; production publishing; brand policy changes; revenue-impacting automations; customer-facing AI policy.

Editorial approval does not authorize publishing (aligned with FDR-003 / E7).

---

## Consequences

### Positive

- Single destination map for all future sprints
- Clear ownership language for Marketing OS engines and Platforms
- Compatible with shipped Studio / Editorial / Approval work
- Prevents conflating Revenue approvals with Editorial Approval

### Neutral / deferred

- Current co-located code (`runner_api`, dual AI paths, Celery under Revenue paths) remains valid until migration sprints
- No immediate package rename or router split required

### Negative / costs

- Implementers must map new work to OS/Platform owners explicitly
- Ambiguous “misc” routers will need ownership tags over time

---

## Compatibility assessment (existing sprints)

| Artifact / sprint | Compatible? | Notes |
|-------------------|-------------|-------|
| Architecture audit v1.x | YES | As-is evidence; not destination |
| Runtime Baseline | YES | Unchanged by G0 |
| Migration Baseline v1 | YES | Current freeze; v2.0 is further destination |
| Content Studio E2–E4.5 | YES | Marketing OS / Content Studio |
| Calendar E5A blocked | YES | Still blocked until date SoT ADR |
| Editorial Readiness E6B | YES | Editorial Engine observational |
| Editorial Approval E7 | YES | Human gate; promote ≠ publish |
| Toolchain Baseline v1.0 | YES | Shared Platform hygiene |
| Governance P0 ownership docs | YES | Align names to v2.0 going forward |
| Revenue OS / Sales surfaces | YES | Remain Revenue/Sales OS; migrate later |

**No sprint is invalidated.**

---

## Impact verification

| Dimension | Impact |
|-----------|--------|
| Architecture impact (running system) | **NONE** |
| Runtime impact | **NONE** |
| API impact | **NONE** |
| Database impact | **NONE** |
| Business logic impact | **NONE** |
| Git operations (G0) | **NONE** |
| Code changes (G0) | **NONE** |

---

## Rollback

Governance rollback = supersede this ADR with a new ADR restoring a prior destination map.  
No runtime rollback required (no runtime change shipped).

---

## References

- [Architecture_v2.md](Architecture_v2.md)
- [Architecture_v2_Diagram.md](Architecture_v2_Diagram.md)
- [Architecture_Principles.md](Architecture_Principles.md)
- [Platform_vs_OS_Boundaries.md](Platform_vs_OS_Boundaries.md)
- [Future_Module_Roadmap.md](Future_Module_Roadmap.md)
- [Migration_Target_Architecture.md](Migration_Target_Architecture.md)
- [adr/ADR_EDITORIAL_APPROVAL_SEMANTICS.md](adr/ADR_EDITORIAL_APPROVAL_SEMANTICS.md)

---

## Verdict

**FOUNDATION ARCHITECTURE v2.0 FROZEN** (G0)

Accepted under Sprint G0 with zero implementation impact.  
**Superseded for active destination by Architecture v2.1 (G1 / ADR-002).**
