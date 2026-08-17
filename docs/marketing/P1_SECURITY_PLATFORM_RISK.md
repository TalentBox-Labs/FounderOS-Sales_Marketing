# P1 — Security / Platform Risk

**Sprint:** P1  
**Agent:** CIPHER  
**Scale:** 1–5 where **5 = highest risk**

---

## Scores

| Area | Social | Email | Campaign | SEO Phase 2 |
|------|--------|-------|----------|-------------|
| OAuth / credentials | 4 | 2 | 2 | 3 |
| Platform policy / account bans | 4 | 2 | 3 | 2 |
| PII / consent / compliance | 2 | **5** | 4 | 2 |
| Accidental publish / launch | 3 | 4 | **5** | 1 |
| External account dependence | 4 | 4 | 3 | 4 |
| Data ingestion risk | 2 | 3 | 3 | 3 |
| **Composite ≈** | **3.2** | **3.3** | **3.3** | **2.5** |

---

## Highlights

### Social
OAuth token storage and LinkedIn platform policy dominate risk. Human Editorial + manual Publishing gates reduce accidental launch. Prefer official API over aggregators.

### Email
Highest **compliance** risk: consent, unsubscribe, suppression, sender reputation. Using CRM contacts as marketing list = ownership leakage + regulatory exposure.

### Campaign
Cross-channel automation without real adapters risks “launch theater” or accidental multi-channel blast once stubs are filled carelessly. Human campaign gate required before any engine.

### SEO Phase 2
GSC/analytics credentials and search-platform dependence; activation must remain blocked until domain ratification. Local technical/readiness engines already read-only/safe.

---

## Production SEO

Remains **BLOCKED PENDING DOMAIN** regardless of P1 recommendation.
