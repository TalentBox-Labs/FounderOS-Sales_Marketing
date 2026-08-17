# Architecture Principles — Founder OS v2.2

**Status:** FROZEN  
**Sprint:** A1 (principles carry forward; parent bumped to v2.2)  
**Date:** 2026-08-10  
**Parent:** [Architecture_v2.2.md](Architecture_v2.2.md)

Governance only. No implementation changes.

**v2.2 note:** Marketing OS future engines (Video, Newsletter, Community) are destination names only until dedicated sprints. P1–P11 law unchanged; Publishing ≠ Website remains mandatory.

---

## P1 — Separation of OS and Platform

- **OS modules** own business decisions, domain workflows, and product outcomes.
- **Platforms** own infrastructure: AI runtime, automation execution, shared cross-cutting services.
- An OS module must not become a platform.
- A platform must not become an OS module.

---

## P2 — Architectural law (non-negotiable)

1. Business logic belongs to OS modules.
2. Infrastructure belongs to Platforms.
3. OS modules may never own infrastructure.
4. Platforms may never own business decisions.

Violations require an ADR and Founder approval before landing.

---

## P3 — Consume, do not re-own

OS modules **consume**:

- AI Platform for models, agents, RAG, prompts, evaluation harnesses
- Automation Platform for schedules, queues, workers, webhooks, retries
- Shared Platform for auth, RBAC, audit, secrets, config, storage, notifications, observability, search infra, API gateway

OS modules must not fork parallel auth, parallel Celery apps, or parallel LLM stacks as long-term homes.

---

## P4 — Agent governance

Canonical flow:

**Agent → Recommendation → Human Approval (when required) → Automation Platform → Execution → Audit**

- Agents recommend.
- Humans approve where required.
- Automation executes.
- All execution is audited.

Agents must never silently satisfy a mandatory human gate.

---

## P5 — Mandatory human gates

The following always require a human before execution:

- Editorial approval
- Campaign launch
- Production publishing
- Brand policy changes
- Revenue-impacting automations
- Customer-facing AI policy

Gates are OS-owned decisions; audit is Shared Platform infrastructure.

**Editorial ≠ Publish.** Editorial approval does not authorize production publishing.

---

## P6 — Additive migration

- Destination architecture is frozen; current implementation remains valid.
- Prefer additive surfaces and ownership clarification over big-bang rewrites.
- Frozen baselines (runtime, Content Studio, Editorial readiness/approval Phase 1, toolchain) remain compatible unless a future ADR explicitly supersedes them.
- No silent API or schema breakage under “architecture cleanup.”

---

## P7 — Single canonical repository

Long-term architecture is defined for the Founder OS canonical repository only.  
External CMS / reference repos inform migration but are not SoT for Founder OS architecture.

---

## P8 — Auditability

- Decisions that pass human gates must leave an audit trail (approver, timestamp, decision, notes, subject, scope/phase as applicable).
- Automation executions must be attributable to a decision or authorized job.
- Audit storage is Shared Platform; audit *meaning* is owned by the OS that made the decision.

---

## P9 — No platform business logic

Especially forbidden inside Automation Platform:

- Editorial approve/reject policy
- Campaign launch criteria as hard-coded business rules without OS ownership
- Publish authorization
- Brand policy authorship
- Revenue deal-stage business rules as Celery-native “truth”

Automation may *carry* payloads decided by OS modules; it must not *decide* them.

---

## P10 — Explicit supersession

Architecture **v2.2** is the current destination structure (ADR-003).  
Architecture v2.1 (ADR-002) and v2.0 (ADR-001) remain historical freezes.  
Neither erases evidence packages, sprint reports, or frozen implementation baselines.  
Conflicts: current Architecture version + ADR wins for destination; sprint freeze docs win for “what is already shipped and must not regress.”

## P11 — Publishing vs Website (v2.1)

- Publishing Engine owns orchestration only (channels, jobs, queue).
- Website Engine owns canonical website rendering and website publishing only.
- Neither owns the other’s domain; Social/Email/Campaign remain separate.

---

## Principle checklist (for future sprints)

| Question | Must answer |
|----------|-------------|
| Which OS or Platform owns this change? | Named owner |
| Is this business logic or infrastructure? | One side only |
| Publishing vs Website vs Social/Email? | Correct engine |
| Does it cross a mandatory human gate? | Gate + audit |
| Does it change frozen baselines? | ADR required |
| Does v2.2 destination still hold? | Yes / amend via ADR |
