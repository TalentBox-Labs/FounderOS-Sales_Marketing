# Sales OS Architecture Baseline v1.0

**STATUS: FROZEN**  
**VERSION: v1.0**  
**Sprint:** SALES A1.5 — Sales OS Architecture Baseline Freeze  
**Date:** 2026-08-13  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`

**Parent architecture:** Founder OS Architecture v2.2 (FROZEN)  
**Governing ADRs:** [Architecture_ADR_004.md](../architecture/Architecture_ADR_004.md), [Architecture_ADR_005.md](../architecture/Architecture_ADR_005.md)

**Nature:** Governance freeze of the Sales OS destination architecture established in SALES A1.  
**Does not change:** implementation, APIs, database, runtime, Marketing OS, Revenue OS code, integrations, or CRM mount state.

**Source of truth (A1):** [SALES_OS_ARCHITECTURE.md](SALES_OS_ARCHITECTURE.md)

---

## Freeze statement

**SALES OS ARCHITECTURE BASELINE v1.0 FROZEN**

After this freeze, implementation agents may implement **against** these contracts. They may **NOT** reinterpret ownership, entities, boundaries, agent authority, integration disposition, or CRM UI disposition without an explicit ADR / approved unfreeze sprint.

---

## 1. Exactly one canonical Sales architecture

| Layer | Document | Authority |
|-------|----------|-----------|
| Destination ownership | This baseline + A1 `SALES_OS_ARCHITECTURE.md` | **CANONICAL** |
| ADR-004 | Sales domain & cross-OS boundaries | **BINDING** |
| A0 audit pack | Evidence history | HISTORICAL |
| Co-located `revenue_os/` code | CURRENT IMPLEMENTATION | ACCEPTED_LEGACY — not ownership proof |

Ambiguity remaining (documented, not silently resolved): physical package extraction (`sales_os/`) deferred; dual API stacks remain ACCEPTED_LEGACY until a migration sprint.

---

## 2. Frozen Sales OS ownership

### Owns

- Prospecting plans & SDR workflows  
- Outreach sequence **operations** (enroll, propose, execute after approval)  
- Sales qualification **workflow** & engagement state transitions (policy)  
- Pipeline **operations** (stage movement as sales process)  
- Sales operator surfaces (`/sales`; future CRM shell per UI disposition)  
- Sales agent **assist** (draft only — no send)  
- Marketing demand **intake** after `QualifiedDemand` accept  
- Emission of `CommercialOutcome` handoff requests to Revenue  

### Does NOT own

- CRM entity SoT (`Contact`, `Company`, `Deal`, `Pipeline`, `Activity`) → **Revenue OS**  
- Billing, invoices, payments, recognized revenue → **Revenue OS**  
- Editorial / publish / website / SEO / social publish → **Marketing OS**  
- LLM providers / agent runtime → **AI Platform**  
- Celery / n8n transport / queues → **Automation Platform**  
- AuthN/RBAC / vault / audit infra → **Shared Platform**  

---

## 3. Frozen lifecycle boundaries

```
Marketing OS  --QualifiedDemand-->  Sales OS  --CommercialOutcome-->  Revenue OS
```

- Before handoff: Marketing owns demand generation & marketing qualification.  
- After Sales intake accept: Sales owns accepted sales lifecycle ops.  
- At closed commercial outcome: Revenue owns CRM close recording, forecast, CS handoff path.

---

## 4. Frozen entities, services, API, persistence, UI, automation

| Concern | Frozen rule |
|---------|-------------|
| Canonical entities | Per [SALES_DOMAIN_MODEL_CONTRACT_v1.0.md](SALES_DOMAIN_MODEL_CONTRACT_v1.0.md) |
| Services | Sales ops consume Revenue SoT; no parallel CRM schema |
| API ownership | Runner Sales/CRM facades = CURRENT; target = Sales facade over Revenue SoT |
| Persistence | Revenue OS owns entity tables |
| UI | Jinja `/sales` LIVE; React `/app` **RETAIN_AND_REFACTOR_LATER** (unmounted) |
| Automation | Automation Platform executes jobs; Sales owns business policy |
| Agents | [SALES_AGENT_AUTHORITY_CONTRACT_v1.0.md](SALES_AGENT_AUTHORITY_CONTRACT_v1.0.md) |

---

## 5. LIVE capabilities preserved (12/12)

C01, C02, C03, C07, C08, C09, C11, C12, C13, C14, C15, C17 — must not be deleted or behaviorally changed by architecture work alone.

---

## 6. Change control

Changes to this baseline require:

1. Explicit ADR amending ADR-004/005 or superseding this freeze, **and**  
2. Approved sprint that names unfreeze scope  

See [SALES_A1_5_BASELINE_MANIFEST.md](SALES_A1_5_BASELINE_MANIFEST.md) and Development Rulebook Sales freeze clause.

---

## Compatibility

| Domain | Impact of freeze |
|--------|------------------|
| Marketing OS frozen engines | None |
| Revenue OS runtime | None |
| Architecture v2.2 | Unchanged (additive ADR-005 only) |

**Canonical Sales Architecture: PASS**
