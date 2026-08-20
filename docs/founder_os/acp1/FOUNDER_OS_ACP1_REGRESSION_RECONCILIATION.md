# Founder OS ACP-1 — Regression Reconciliation

## ACP-1 focused

`tests/test_founder_os_acp1_authority_tenant_hardening.py` — **19 passed**

Covers: tenant enumeration (allowlist / ACTIVE Organization / Contact-not-authorization), missing-tenant fail closed, cross-tenant score isolation, follow-up scan requires org, Hermes Deal prohibition + provenance, create_deal org stamp ≠ eligibility, agent cannot approve, COS-5 INLINE preserved, optional_tenant not imported by autonomous modules, no new send/book, Gmail requires orgs, propose≠execute registry, deterministic rescore, blocked provenance.

## Core regression (executed)

| Suite | Result |
|-------|--------|
| ACP-1 | PASS |
| COS-5 | PASS |
| COS-4 | PASS |
| COS-3 | PASS |
| Tenant remediation v1 | PASS |
| COS-2 | PASS |
| COS-1 | PASS |
| MC04 qualified demand tenant v2 | PASS |
| UI-D2 governed booking | PASS |
| SaaS S3 CRM tenant isolation | PASS |
| SaaS S3.5 baseline freeze | PASS |

**Executed total (core):** **205 passed**

## Extended matrix notes (not ACP-1 regressions)

On **clean baseline** `de5d896` (ACP-1 stashed), these already fail:

| Test | Failure | ACP-1 related? |
|------|---------|----------------|
| `test_ui_d1_5_live_demo_baseline_freeze` (several) | Template expects `snapshot.decision_loop` (COS-3+) vs D1.5 fixture | **NO** — pre-existing |
| `test_saas_s2_5…::test_freeze_service_identity_no_human_mutation` | expects 503, gets 403 | **NO** — pre-existing |

Frozen tests were **not** modified to green ACP-1.

## Frozen tests modified

**0**
