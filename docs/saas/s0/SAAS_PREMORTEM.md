# SaaS S0 — Premortem

**Sprint:** SaaS S0  
**Date:** 2026-08-13  
**Assumption:** SaaS conversion fails. Identify failure modes before build.

| # | Failure mode | Likelihood | Impact | Detection | Mitigation |
|---|--------------|------------|--------|-----------|------------|
| 1 | Cross-tenant data leakage via ID-only lookups | High | Critical | Tenant isolation tests; IDOR suites | Require org_id on all owned queries |
| 2 | Authorization bypass (role unused / auth-off) | High | Critical | Auth-off CI fail; RBAC tests | Fail closed; enforce roles |
| 3 | Tenant-less legacy records after migration | High | High | Null org_id audit | Backfill strategy; block writes without org |
| 4 | Migration corruption (empty Alembic + create_all) | Medium | Critical | Migration dry-run; schema diff | Real Alembic revisions before multi-tenant |
| 5 | Spoofed human identity (`requested_by`) | High | High | Authority adversarial tests | Bind identity to session User |
| 6 | Global integration credentials shared | High | Critical | Vault key = (org, connector) tests | Per-org vault |
| 7 | Broken audit provenance (wrong actor/org) | Medium | High | Audit fixtures | Stamp org_id + user_id on AgentActionLog |
| 8 | Frontend/backend authority divergence | Medium | High | Freeze suites + E2E | Keep server gates; no client trust |
| 9 | Lovable-generated duplicate backend/SoT | Medium | Critical | Architecture review gate | DO_NOT_USE for backend/DB |
| 10 | Frozen contract erosion (“temporary” rewrite) | Medium | Critical | Baseline freeze tests | Outer wrapper only; ADR for version bumps |
| 11 | Filesystem SoT crosstalk (`output/`, tracker) | Medium | High | Path isolation tests | Per-org storage prefix or DB migration of FS |
| 12 | Public MDG2 before rate-limit/bot controls | Medium | High | Security review | Keep MDG2 PARKED |

Highest Critical SaaS Risk: **Cross-tenant data leakage via ID-only mutations.**
