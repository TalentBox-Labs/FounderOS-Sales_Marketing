# SaaS S0 — Query Isolation Audit

**Sprint:** SaaS S0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY

## Pattern today

Mutations resolve by **object_id only** (`db.get(Model, id)` / audit `target_id`).  
SaaS requires **organization_id + object_id**.

## Risk table

| Surface | Pattern | Risk |
|---------|---------|------|
| Runner CRM contact/deal mutate | `db.get` by UUID | **CRITICAL** post-multi-tenant |
| JWT revenue_os contacts/deals | filter by id; unscoped lists | **CRITICAL** |
| QD accept/reject | `_find_audit(demand_id)` | **CRITICAL** |
| CO handoff/accept/reject | `_find_audit(outcome_id)` / Deal get | **CRITICAL** |
| Operator/cockpit/MDG | ID body + trusted operator | **HIGH** (still no tenant) |
| Hermes `Contact.query.all()` | full table | **HIGH** |
| CSM/forecast by Company.id | IDOR | **HIGH** |
| Jinja HTML GET pages | unauthenticated reads | **MEDIUM** (instance exposure) |

## Global query risks

Any authenticated (or auth-off) caller who knows/guesses a UUID can operate on that row without org membership checks.

## Critical Isolation Risks (top)

1. Cross-tenant Contact/Deal IDOR  
2. Cross-tenant AgentActionLog demand/outcome replay  
3. Global credentials vault overwrite/read  
4. Auth-off mode exposing all mutations
