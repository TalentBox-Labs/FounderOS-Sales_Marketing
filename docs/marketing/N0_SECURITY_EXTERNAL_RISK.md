# N0 — Security / External Platform Risk (Cipher)

**Sprint:** N0  
**Date:** 2026-08-10  
**Secrets:** names only  

---

## Per-engine risk

| Concern | SEO | Social | Email | Campaign |
|---------|-----|--------|-------|----------|
| Credentials required | Optional later (`GSC` / SERP) — **not** for local v0 | Platform tokens (LinkedIn/X/IG/…) | SMTP/ESP API keys | Aggregates channel secrets |
| OAuth | Optional | **Required** | Provider-dependent | Indirect |
| Token management | Low | High (refresh, scopes) | Medium | Medium |
| PII exposure | Low (URLs/keywords) | Medium (profiles) | **High** (emails) | Medium–High |
| Compliance | Low–Medium | Platform ToS | **CAN-SPAM/GDPR/consent** | Attribution privacy |
| External platform risk | Low | **High** (API breakage) | High (ESP) | Medium |
| Account suspension risk | Negligible | **High** | High (spam) | Indirect |
| API policy dependency | Low | **High** | High | Medium |
| Security boundary | Read artifacts + optional analytics | Outbound publish | Outbound + list store | Orchestration + secrets fan-out |
| **Risk score (1–5)** | **1** | **5** | **4** | **3** |

---

## Cipher verdict

SEO is the only candidate with a **credible zero-external-credential first slice**. Social and Email force Shared Platform secret stores and human publish gates before any automation.
