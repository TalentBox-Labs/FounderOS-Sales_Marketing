# P1 — Engineering Complexity

**Sprint:** P1  
**Agent:** NOVA  
**Scale:** 1–5 where **5 = highest complexity/risk**

---

## Scores

| Factor | Social | Email | Campaign | SEO Phase 2 |
|--------|--------|-------|----------|-------------|
| Backend changes | 3 | 4 | 4 | 2 |
| Frontend changes | 2 | 3 | 3 | 2 |
| DB impact | 2 | 5 | 4 | 2 |
| API surface | 3 | 4 | 4 | 3 |
| External integration | 4 | 4 | 3 | 4 |
| OAuth | 4 | 2 | 2 | 3 |
| Secrets | 4 | 3 | 3 | 3 |
| Rate limits | 4 | 3 | 3 | 2 |
| Queue/retry | 3 | 4 | 4 | 1 |
| Scheduling | 2 (defer) | 3 | 5 | 1 |
| Observability | 3 | 4 | 4 | 2 |
| Test burden | 3 | 5 | 4 | 2 |
| Provider lock-in | 3 | 4 | 3 | 3 |
| Failure recovery | 3 | 4 | 4 | 2 |
| Production blast radius | 3 | 5 | 5 | 2 |
| **Composite (mean ≈)** | **3.1** | **4.0** | **3.7** | **2.3** |

---

## Notes

- **Social S0:** Replace LinkedIn stub adapter; keep Publishing/Editorial gates; defer scheduler → medium complexity.  
- **Email:** New SoT + compliance + delivery → highest complexity.  
- **Campaign:** Premature multi-channel orchestration increases blast radius without payoff.  
- **SEO Phase 2:** Local work is easy; meaningful Phase 2 needs GSC/domain (integration complexity rises then).
