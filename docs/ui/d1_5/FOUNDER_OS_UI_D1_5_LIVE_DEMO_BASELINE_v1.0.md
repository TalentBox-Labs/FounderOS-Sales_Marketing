# Founder OS UI-D1.5 — Live Demo Surface Baseline v1.0

**STATUS: FROZEN**  
**Sprint:** UI-D1.5  
**Branch:** ui-d1  
**Worktree:** TB-FounderOS-UI-D1  
**Original parent baseline:** `1e446ac`  
**Frontend:** FastAPI + Jinja2 (modernized incrementally)  
**Lovable:** NOT USED  
**Booking:** NOT_IMPLEMENTED (M4 CROSS_STREAM_DEPENDENCY)

## Frozen claim

A third party can open Founder OS in a browser and complete a **product demonstration** of the founder revenue operating loop without terminal or API knowledge, using seven primary screens plus the existing Operator Flow.

This is **not** a claim that every external event (inbound email reply) can be generated from the browser.

## Primary product screens (exactly 7)

| # | Surface | Route | Template |
|---|---------|-------|----------|
| 1 | Login | `/login` | `templates/login.html` |
| 2 | Founder Command Center | `/command` | `templates/founder_command.html` |
| 3 | Demand & Contacts | `/demand` | `templates/founder_demand.html` |
| 4 | Contact Revenue Workspace | `/contacts/{id}` | `templates/founder_contact.html` |
| 5 | Approval Inbox | `/pending-approvals` | `templates/founder_approvals.html` |
| 6 | Activity / Provenance | `/activity` | `templates/founder_activity.html` |
| 7 | Revenue Workflow | `/operator` | `templates/operator.html` (OF1.5 linked, not duplicated) |

Reply / next action is a **panel inside** the Contact Revenue Workspace, not an eighth primary screen.

Legacy `/cockpit` remains operable (UI2.5 freeze + UI-D1 `data['items']` fix) under Content Ops, not a primary demo screen.

## Frozen invariants

- Canonical Founder OS APIs remain authoritative
- No new persistent SoT, DB model, migration, or integration
- No new frontend framework
- Server-trusted human identity; no client `requested_by` / `decided_by`
- Tenant reads scoped by server `TenantContext`
- Meeting interest and booking eligibility may display; booking is not implemented
- Demo seed is development-only and is not invoked at startup

## Browser demonstration contract

| Claim | Frozen value |
|-------|----------------|
| Browser-Only Product Demonstration | YES |
| Browser-Only External Reply Injection | NO |
| Inbound reply generation | n8n webhook or API simulation (M3) |
