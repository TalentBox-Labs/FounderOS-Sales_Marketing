# SALES A2 — Priority Scorecard

**Sprint:** SALES A2  
**Date:** 2026-08-13  
**Principle:** COMPLETE > REUSE > CONNECT > BUILD NEW  
**Weights:** as specified in A2 brief (sum 100%)

Scale: **1–5** per dimension. Weighted total also expressed on **1–5** scale.

| Dim | Weight |
|-----|--------|
| Founder Workflow Value | 20% |
| Revenue Proximity | 15% |
| Workflow Gap Closure | 15% |
| Existing Implementation Reuse | 15% |
| Dependency Leverage | 10% |
| Automation Leverage | 5% |
| Engineering Effort (higher = easier) | 7.5% |
| External Dependency Independence | 5% |
| Operational Risk (higher = safer) | 2.5% |
| Architecture Fit | 5% |

No alternate repo framework superseded this model.

---

## Candidates scored (8)

Dispositions: COMPLETE_EXISTING · CONNECT_EXISTING · BUILD_NEW · DEFER · REJECT

| ID | Candidate | Type | WF | Rev | Gap | Reuse | Lev | Auto | Eff | Ext | Risk | Fit | **Score** |
|----|-----------|------|---:|----:|----:|------:|----:|-----:|----:|----:|-----:|----:|----------:|
| **A** | **Runner Deal Stage Update (C20+MC05+C05 complete)** | **CONNECT_EXISTING** | 5 | 5 | 5 | 5 | 5 | 4 | 4 | 5 | 4 | 5 | **4.85** |
| B | Marketing→Sales `QualifiedDemand` (MC04/C27) | BUILD_NEW | 4 | 3 | 4 | 2 | 4 | 3 | 2 | 4 | 3 | 5 | **3.38** |
| C | Closed-won Client/Customer (MC06/C28) | BUILD_NEW | 3 | 5 | 3 | 2 | 3 | 3 | 2 | 5 | 3 | 4 | **3.23** |
| D | LeadScorer human gate (C12 debt) | COMPLETE_EXISTING | 3 | 2 | 2 | 4 | 3 | 5 | 4 | 5 | 5 | 5 | **3.28** |
| E | Outreach send n8n completion (C10) | COMPLETE_EXISTING | 4 | 4 | 3 | 3 | 3 | 4 | 3 | 1 | 2 | 4 | **3.33** |
| F | Companies on runner + thin API (C19) | CONNECT_EXISTING | 3 | 2 | 2 | 4 | 3 | 2 | 4 | 5 | 4 | 4 | **3.05** |
| G | Forecast UI surface (C21) | BUILD_NEW/UI | 2 | 4 | 1 | 3 | 2 | 2 | 3 | 5 | 4 | 3 | **2.78** |
| H | Mount CRM SPA (C18) | REJECT now | 3 | 2 | 2 | 4 | 4 | 2 | 2 | 5 | 2 | 2 | **2.85** |

**H** disposition **REJECT** for A3: violates frozen **RETAIN_AND_REFACTOR_LATER** (refactor/mount not authorized; stage API should precede mount).

**MC02/MC03** Opportunity/Lead naming: **REJECT** build — already RESOLVED_BY_CONTRACT in A1.5.

**MC01** `sales_os` package: **DEFER** — no founder workflow value vs stage ops.

**MC09** relational stages: **DEFER** — enum sufficient for A3.

---

## Weighted calculation (winner A)

```
0.20×5 + 0.15×5 + 0.15×5 + 0.15×5 + 0.10×5 + 0.05×4
+ 0.075×4 + 0.05×5 + 0.025×4 + 0.05×5 = 4.85
```

## Ranking

1. **A — Runner Deal Stage Update — 4.85**  
2. **B — QualifiedDemand — 3.38**  
3. **E — Outreach send — 3.33** (shown in premortem as #3 operational; D 3.28 close)

Top-3 pressure test uses **A, B, E** (highest non-deferred with distinct outcomes). D retained as near-miss governance slice.

**Score Margin (1st − 2nd): 1.47**

Evidence distinguishes top candidates; **no FOUNDER PRIORITY DECISION REQUIRED**.
