# UI1.1 — UI2 Action Safety Review

**Sprint:** UI1.1  
**Date:** 2026-08-13  
**Constraint:** UI2 exposes at most 1–2 mutation controls initially

---

## Action classification

| Action | Classification | Rationale |
|--------|---------------|-----------|
| QualifiedDemand accept | **SAFE_FOR_UI2** | Frozen MC04.5; dual route+service gate; audit via AgentActionLog; creates LEAD only (no auto-qualify); reversible via reject before accept |
| QualifiedDemand reject | **SAFE_FOR_UI2** | Audit-only mutation; no CRM entity; strong human gate |
| Contact.status PATCH | **SAFE_FOR_UI2** | A4.5 frozen; service authority enforced; EventBus audit; bounded blast radius |
| Deal stage PATCH | **DEFER** | Higher blast radius (pipeline/commercial preconditions); defer until cockpit read-model proven |
| Editorial approve/reject | **DEFER** | Existing `/editorial/*` UI sufficient; link from cockpit rather than duplicate control |
| Publishing human promote | **DEFER** | Existing `/publishing` UI sufficient; channel dispatch complexity |
| Marketing handoff register | **DEFER** | Marketing-operator action; lower cockpit priority vs Sales intake |

---

## Recommended initial UI2 mutation controls (max 2)

1. **QualifiedDemand accept** — highest value-chain impact; MC04.5 mature; clear audit trail; no deal/outcome side effects
2. **Contact.status PATCH (qualify)** — complements accept flow; A4.5 authority now service-enforced; reversible to prior status manually

---

## Read-only cockpit surfaces (UI2)

- QualifiedDemand queue (pending handoffs)
- Contact status + lead score (read)
- Deal pipeline snapshot (read)
- Editorial pending count (link to `/editorial`)
- Publishing queue status (link to `/publishing`)

---

## UI2 Action-Capable Readiness

**READY** — with recommended limit of 2 initial mutation controls (accept + contact qualify)

---

## Safe vs deferred lists

**Safe UI2 human actions:**
- QualifiedDemand accept
- Contact.status PATCH (with `requested_by`)

**Deferred UI2 human actions:**
- QualifiedDemand reject (safe but deprioritized vs accept for v1)
- Deal stage PATCH
- Editorial approve/reject
- Publishing human promote
- Marketing handoff register

Note: Reject is technically safe; deferred for UI2 v1 scope minimization, not authority concern.
