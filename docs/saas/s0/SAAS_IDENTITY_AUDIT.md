# SaaS S0 — Identity Audit

**Sprint:** SaaS S0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY

## Answers

| Field | Value |
|-------|-------|
| Current User Model | `User` ORM (email, password hash, `role` string) on secondary JWT app; unused for primary Jinja shell ACL |
| Current Authentication Model | Shared Bearer `RUNNER_API_KEY` on primary APIs; JWT register/login on `revenue_os.main` only |
| Current Authorization Model | Human-name denylist (`is_human_approver`) + API key possession; **no RBAC enforcement** |
| Current Operator Identity Model | `FOUNDER_OS_OPERATOR_NAME` env → `_trusted_cockpit_operator()` for cockpit/operator/MDG |
| Current Session Model | None on Jinja; SPA stores API key in `localStorage` |

## Identity scope

| Mechanism | Scope |
|-----------|-------|
| `RUNNER_API_KEY` | **GLOBAL** (per deployment) |
| `FOUNDER_OS_OPERATOR_NAME` | **INSTANCE_SCOPED** (per deployment) |
| Client `requested_by` | Free-text string — **not** User FK |
| JWT `sub` | **USER_SCOPED** id only — no org claim |
| Workspace / Organization identity | **ABSENT** |

## Spoofing / privilege risks

| Risk | Severity |
|------|----------|
| Auth disabled when `RUNNER_API_KEY` unset | CRITICAL (misconfig) |
| Shared API key = full platform | HIGH for SaaS |
| Client `requested_by` accepted on CRM/QD/CO with only denylist | HIGH |
| Trusted-operator paths ignore client spoof | Mitigated (cockpit/operator/MDG) |
| Open `/auth/register` on secondary app | HIGH if exposed |
| JWT role unused | HIGH if JWT app is primary |

## Classification

Identity today is **INSTANCE_SCOPED GLOBAL operator + GLOBAL shared secret**, not USER_SCOPED SaaS identity.
