# N0 — Engineering Complexity (Nova)

**Sprint:** N0  
**Date:** 2026-08-10  
**Scale:** 1 = low · 5 = highest complexity/risk  

---

## Dimension scores

| Dimension | SEO | Social | Email | Campaign |
|-----------|----:|-------:|------:|---------:|
| Backend work | 2 | 4 | 5 | 4 |
| Frontend work | 2 | 3 | 3 | 4 |
| Database impact | 2 | 3 | 4 | 4 |
| API work | 2 | 4 | 4 | 4 |
| External API dependency | 1 | 5 | 4 | 3 |
| Authentication / OAuth | 1 | 5 | 3 | 2 |
| Rate limits | 1 | 5 | 4 | 2 |
| Scheduling | 1 | 4 | 4 | 5 |
| Queue requirements | 1 | 4 | 4 | 5 |
| Observability | 2 | 4 | 4 | 4 |
| Test complexity | 2 | 4 | 5 | 4 |
| Failure recovery | 2 | 5 | 5 | 4 |
| Provider lock-in | 1 | 4 | 4 | 2 |
| **Average (complexity)** | **1.5→2** | **4.2→4** | **4.1→4** | **3.6→4** |

Rounded complexity score used in matrix: **SEO 2 · Social 4 · Email 5 · Campaign 4**

---

## Nova notes

- **SEO v0** can score local bundles + live HTML without external APIs.  
- **Social** inherits OAuth, policy, rate limits, and suspension risk.  
- **Email** adds PII, deliverability, bounce/complaint loops — highest ops complexity.  
- **Campaign** is medium-high orchestration complexity but **blocked** until channels exist.
