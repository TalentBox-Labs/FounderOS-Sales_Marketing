# 07 — Founder Execution Plan

Sprint P0 — Executive summary  
Date: 2026-08-09

---

## What should be built first? Why?

1. **Founder decisions FDR-001 / FDR-002 / FDR-003** — without them, Editorial Approval Command cannot be designed safely.  
2. **E7 Editorial Approval Command** — next product capability on the frozen Marketing path; reuses `promote_staged` + audit; lowest blast vs inventing lifecycle.  
3. **Ruff tooling PR (parallel)** — Toolchain v1.0 ADD NOW; reduces quality drift; does not block E7 design once FDR exists.

---

## What should wait? Why?

| Wait | Why |
|------|-----|
| Calendar | E5A — no canonical date SoT |
| Publishing auto-trigger from approve | FDR-003 / ADR — editorial ≠ publish by default |
| Reject/revoke approval UX | FD-6/FD-7 future |
| Lifecycle “Approved” tracker state | Needs Lifecycle ADR |
| Campaigns engine | Soft-depends on Publishing maturity |
| Kubernetes / LangChain / OpenClaw Editorial | Explicitly rejected |
| Paid monitoring/API suites | Toolchain + Founder paid approval |

---

## What can be parallelized?

| Parallel tracks | Notes |
|-----------------|-------|
| Ruff / deps hygiene | vs Marketing product work |
| Sales/CRM test hardening | vs Editorial (avoid `runner_api.py` thrash) |
| Governance/docs | Always |
| KB/Analytics read improvements | Soft deps; later priority |

---

## What must remain sequential?

```
FDR-001/002/003 → Accept Approval ADR → E7 Approval Command
    → (optional) reject/revoke
        → Publishing Engine enhancements (per FDR-003)
            → Campaigns
```

Platform auth redesign must not interleave with feature sprints.

---

## Critical path

```
F0 Decision Record (Founder)
    → ADR Accepted
        → E7 Approval Command (implement + tests + regression)
            → Production hardening (FD-8 audit, pip-audit)
                → Publishing / Campaigns (phased)
```

**Parallel off critical path:** Ruff · Sales/CRM hardening · docs.

---

## Success posture

| Horizon | Success looks like |
|---------|-------------------|
| Immediate | FDR completed; E7 Ready |
| Near | Approval Command ships; CS/Kanban/Readiness still green |
| Mid | Publishing remains separate; Sales/Revenue improve without Editorial coupling |
| Tooling | Ruff landed under Toolchain v1.0 |
