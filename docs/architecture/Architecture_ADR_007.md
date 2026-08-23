# Architecture ADR-007 — Sales Runner Deal Stage Update Baseline v1.0 Freeze

**ADR ID:** Architecture_ADR_007  
**Status:** Accepted  
**Sprint:** SALES A3.5  
**Date:** 2026-08-13  

**Decision type:** Behavioral baseline freeze  
**Implementation changes in this ADR:** **NONE**

Parent: ADR-005 (Sales OS Architecture Baseline v1.0) — **UNCHANGED**  
Selection: ADR-006 (A3 slice) — implemented in A3; frozen here

Related:

- [SALES_RUNNER_DEAL_STAGE_BASELINE_v1.0.md](../sales/SALES_RUNNER_DEAL_STAGE_BASELINE_v1.0.md)  
- [SALES_A3_5_BASELINE_MANIFEST.md](../sales/SALES_A3_5_BASELINE_MANIFEST.md)  

---

## Context

SALES A3 delivered human-gated runner deal stage update (CONNECT_EXISTING). A3.5 independently verified A3 claims, reconciled A1.5’s 15/17 exceptions by exact identity and failure reason, and freezes the behavioral contract.

---

## Decision

1. Freeze **Sales Runner Deal Stage Update Baseline v1.0**.  
2. Bind future work to the frozen runner contract; amendments need a new ADR.  
3. Keep A1.5 Sales OS Architecture Baseline and cross-OS contracts **mutable only via their own ADR process** — not rewritten by A3.5.  
4. Accept A1.5 focused **15/17** only with verified exception MATCH.  
5. Do **not** auto-start SALES A4; next work requires Founder OS cross-OS priority checkpoint.

---

## Compatibility

| Area | Impact |
|------|--------|
| Runtime | None beyond already-shipped A3 |
| A1.5 contracts | Unchanged |
| Marketing / Revenue implementation | Unchanged |

---

## Verification snapshot

A3 15/15 · A1.5 15/17 (2 verified exceptions) · Full 412/424 · Historical UNCHANGED · New regressions 0 · Cross-agent conflicts 0
