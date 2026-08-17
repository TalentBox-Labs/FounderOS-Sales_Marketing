# M0.5 Agent Taxonomy v1.0

**Sprint:** REV-ORCH M0.5  
**Date:** 2026-08-17  
**Status:** FROZEN vocabulary for revenue orchestration

---

## Freeze statement

Founder OS supports **multiple specialized AI workers** with distinctive cognitive responsibilities.

Founder OS supports **zero autonomous revenue agents**.

Do not call every module an "agent". Use the taxonomy below in M1+ design and code comments.

---

## 1. REVENUE WORKFLOW ORCHESTRATOR

**Canonical implementation:** `WorkflowOrchestrator` (`revenue_os/agents/orchestration.py`)

**Owns:**
- workflow sequencing
- state transitions between workflow steps
- invoking specialized workers
- policy checkpoints
- ApprovalRequest handoff
- deterministic executor handoff
- event emission
- audit coordination

**Does NOT:**
- unconstrained AI reasoning
- tenant selection
- credential selection
- privileged CRM mutation
- outbound send

**Count:** **ONE** for revenue.

---

## 2. SPECIALIZED AI WORKER

Bounded reasoning component. May be labeled “agent” in existing code (`cold_email_agent`) — that label is **cognitive identity**, not authority.

**Owns:**
- reasoning, analysis, recommendation, generation
- structured proposals

**Does NOT own:**
- business mutation authority
- tenant authority
- connector credential authority
- send authority
- approval authority

**Allowed count:** **multiple**.

---

## 3. DETERMINISTIC DOMAIN SERVICE

Examples: `lead_scoring_service`, CRM services, `approvals.EXECUTORS`, `linkedin_enrichment`, `credentials_vault`.

**Owns:**
- deterministic calculations
- validated business operations
- authorized persistence
- connector execution after policy

---

## 4. SCHEDULER / WORKFLOW INFRASTRUCTURE

Examples: `HeartbeatScheduler`, Celery, Activity `scheduled_at`.

**Owns:** delayed execution, retries, wake-up.

**Does NOT inherit stale human authority.** Execution-time revalidation is required (M0 stale-authority contract).

---

## 5. HUMAN AUTHORITY GATE

**Canonical:** `ApprovalRequest` + `approvals.decide()` + `require_human_mutation_authority()` / `is_human_approver()`.

**Owns:** authorization for outbound send and frozen HUMAN_ONLY mutations (A3/A4/MC04/MC06).

---

## 6. CONNECTOR EXECUTOR

**Canonical:** `revenue_os/integrations/n8n.py` `trigger_workflow`.

**Owns:** already-authorized external execution.

**Does NOT decide** whether the operation should happen.

---

## 7. EXISTING SoT

Contact, Company, Deal, Activity, QualifiedDemand (audit contract), CommercialOutcome (audit contract).

**Owns:** business truth. Workers never become a parallel SoT.

---

## Mapping of existing names

| Repo name | Taxonomy |
|-----------|----------|
| WorkflowOrchestrator | REVENUE WORKFLOW ORCHESTRATOR |
| sales_agents functions | SPECIALIZED AI WORKER (current implementations need tenant/refactor) |
| AIService | platform LLM adapter under DETERMINISTIC DOMAIN SERVICE |
| AgentCoordinator | registry infrastructure (not an orchestrator) |
| HermesPlanner | planner service (subordinate; not second revenue orchestrator) |
| GoToMarketOrchestrator | marketing adapter (out of revenue taxonomy) |
| n8n_bridge | CONNECTOR EXECUTOR |
| ApprovalRequest | HUMAN AUTHORITY GATE |
| HeartbeatScheduler | SCHEDULER |
| CrewAI sdr/recruiter | LEGACY / QUARANTINED — not workers |

---

## Forbidden collapse

| Incorrect | Correct |
|-----------|---------|
| “Seven AI agents run sales” | One orchestrator + specialized workers + domain services + human gate |
| “Agent approved the deal” | Human approved; worker only proposed |
| “n8n decided to send” | Human approved; n8n executed |

---

*End of M0.5 Agent Taxonomy v1*
