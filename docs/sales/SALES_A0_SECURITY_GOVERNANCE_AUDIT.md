# SALES A0 — Security & Governance Audit (SENTINEL)

**Sprint:** SALES A0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY — no security behavior changes

---

## Verdict

**Agent Governance Boundary: PARTIAL**

Approvals exist for some outbound/risky actions. CRM mutations via API key and lead-score auto-status updates can change prospect/pipeline-adjacent state without a Marketing-style dual human gate.

---

## Authentication / authorization

| Control | Finding |
|---------|---------|
| Runner CRM | API key via `_verify_api_key` |
| Revenue OS JWT stack | Separate user JWT — parallel |
| Jinja `/sales` | Ops shell (shared Founder UI auth model) |
| RBAC / owner enforcement | **Weak** — `owner_id` not FK’d; not enforced in CRM UI payloads |
| Secrets in git | Not observed for Sales tokens; vault/env pattern |

---

## Human-authorized actions (must remain human)

| Action | Current gate | Required posture |
|--------|--------------|------------------|
| Send outreach email | Approvals → n8n | **Human approve** before send |
| Create deal on behalf of rep (planner path) | Approvals executor | **Human approve** |
| Publish LinkedIn (Marketing Social) | Separate Social gates | Out of Sales A0 |
| Delete CRM records | Limited surfaces | Human + audit |
| Enable revenue-impacting automations | Architecture: Revenue OS | Human + audit |

---

## Autonomous / AI mutation risks (flags)

| Risk | Evidence | Severity |
|------|----------|----------|
| LeadScorer auto-sets Contact.status by score | `lead_scoring_service.LeadScorer.update_contact_status` | **HIGH** — mutates CRM state without approval queue |
| Dual scorers diverge | `scoring_service` vs `lead_scoring_service` | MEDIUM |
| API key holder can create contacts/deals/activities | `crm.py` | MEDIUM — treat key as operator secret |
| Hermes planner proposes outreach | Files approvals (good) | LOW if approvals always used |
| Agent sales assists | Generate copy; should not auto-send | PASS if send remains approval-bound |
| Automation WorkflowEngine | Event-driven actions possible | MEDIUM — needs Revenue ownership clarity |
| EventBus in-memory | Lost on restart; weak audit durability | MEDIUM |

---

## Sensitive data

Contacts store email/phone/LinkedIn URLs/notes. Treat as PII. Logging must not dump payloads. Enrichment calls third parties when configured.

---

## Separation from Marketing Editorial

Revenue OS `/api/v1/approvals` ≠ Editorial Approval (ADR Editorial). **PASS** at governance design level.

---

## Agent permissions (A0 rule)

Agents in this sprint: analysis / classification / read-only / tests only.  
**Forbidden (future):** autonomous contact, email send, CRM mutate, stage change, deal create/delete without explicit later governance approval.

**Agent Governance Boundary: PARTIAL**
