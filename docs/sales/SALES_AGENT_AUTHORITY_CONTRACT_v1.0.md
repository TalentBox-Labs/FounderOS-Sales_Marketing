# Sales Agent Authority Contract v1.0

**STATUS: FROZEN**  
**VERSION: v1.0**  
**Sprint:** SALES A1.5  
**Date:** 2026-08-13  
**ADR:** [Architecture_ADR_005.md](../architecture/Architecture_ADR_005.md)  
**Source:** [SALES_AGENT_AUTHORITY_MATRIX.md](SALES_AGENT_AUTHORITY_MATRIX.md) (A1)

**References (do not replace):**

- [PLATFORM_AGENT_REGISTRY.md](../governance/PLATFORM_AGENT_REGISTRY.md)  
- [MULTI_AGENT_EXECUTION_STANDARD.md](../governance/MULTI_AGENT_EXECUTION_STANDARD.md)  
- [AGENT_OWNERSHIP_MATRIX.md](../governance/AGENT_OWNERSHIP_MATRIX.md)  

This contract **extends** Founder OS agent governance for Sales domain actions. It is **not** a competing registry.

---

## Freeze statement

**Agent Governance Boundary: FROZEN**

Cursor sprint agents ≠ Founder OS runtime agents.

---

## 1. Classification vocabulary (frozen)

`AUTONOMOUS_ALLOWED` · `HUMAN_APPROVAL_REQUIRED` · `HUMAN_ONLY` · `PROHIBITED`

---

## 2. Frozen prohibitions (agents must not)

- Autonomously modify frozen Sales contracts / baselines  
- Bypass human approval gates  
- Activate integrations or change credentials  
- Mutate Marketing-owned publish/editorial state  
- Mutate Revenue-owned financial/forecast models  
- Create new Sales domain authorities without ADR  
- Perform destructive CRM operations (delete contact/deal) without HUMAN_ONLY path  
- Silently promote Contact.status or Deal.stage  

---

## 3. Matrix summary (binding)

| Class | Examples |
|-------|----------|
| AUTONOMOUS_ALLOWED | Research; draft outreach; score **recommend** (no status write) |
| HUMAN_APPROVAL_REQUIRED | Enrichment API; send email/LI; agent-initiated CRM create/modify; calendar write; deal create via planner |
| HUMAN_ONLY | Qualification decision; pipeline stage change; deal value; forecast; deletes; commercial commitment; pricing |
| PROHIBITED | Autonomous bulk outreach; agent pricing/discount changes |

Full matrix: A1 `SALES_AGENT_AUTHORITY_MATRIX.md` — frozen by reference.

---

## 4. Known gaps (frozen as known; not remediated)

| Gap | Required class | Gate |
|-----|----------------|------|
| LeadScorer auto status | HUMAN_APPROVAL_REQUIRED | Future migration sprint |
| API-key CRM writes without strong actor audit | Operator auth / adapter | Future adapter sprint |

---

## 5. Registry amendment rule

Permanent Sales runtime agents require Platform Agent Registry amendment. Temporary Cursor agents do not auto-register.
