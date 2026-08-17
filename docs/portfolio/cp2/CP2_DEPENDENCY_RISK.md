# CP2 — Dependency Risk (LEDGER)

**Sprint:** CP2  
**Date:** 2026-08-13  
**Scale:** 0–5 (higher = lower risk / better)

---

## Dependency dimensions

| Candidate | Low arch risk | Low external | Low Founder dec | Low credential | Low domain | Cross-OS contract | Reversibility | **Avg** |
|-----------|-------------:|-------------:|----------------:|---------------:|-------------:|------------------:|--------------:|--------:|
| **A** | 5 | 5 | 5 | 5 | 5 | 5 | 5 | **5.0** |
| **B1** | 3 | 1 | 2 | 1 | 5 | 4 | 3 | **2.7** |
| **B2** | 4 | 5 | 4 | 5 | 5 | 4 | 4 | **4.4** |
| **C** | 4 | 4 | 5 | 5 | 5 | 4 | 3 | **4.3** |
| **D1** | 5 | 5 | 5 | 5 | 5 | 5 | 5 | **5.0** |
| **D2** | 3 | 2 | 1 | 3 | 1 | 4 | 2 | **2.3** |
| **E** | 4 | 5 | 5 | 5 | 5 | 4 | 3 | **4.4** |

---

## Executability classification

| Candidate | Class | Blocker |
|-----------|-------|---------|
| **A** | **READY** | None |
| **B1** | **BLOCKED** | FD-01 + ES-01..03 |
| **B2** | **CONDITIONAL** | Engineering scope; low commercial activation |
| **C** | **CONDITIONAL** | Soft: bounded Marketing emitter + Sales intake in one sprint |
| **D1** | **READY** | Incremental only |
| **D2** | **BLOCKED** | FDR-N05 production domain |
| **E** | **READY** | BUILD_NEW but no external hard blockers |

**Highest executable (no soft deps):** A (Companies) and D1 (SEO incremental) tie on dependency; A faster TTOV for Sales lane.

**Highest raw-value with acceptable executability:** C — soft dependency is in-repo coordination, not external credentials.
