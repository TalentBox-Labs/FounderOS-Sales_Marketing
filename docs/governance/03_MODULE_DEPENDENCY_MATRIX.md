# 03 — Module Dependency Matrix

Sprint P0 — Documentation only  
Date: 2026-08-09

Legend:

| Mark | Meaning |
|------|---------|
| **H** | Hard dependency — blocked without upstream |
| **S** | Soft dependency — can proceed with mocks/contracts; integrate later |
| **I** | Independent — safe concurrent work if file boundaries respected |

---

## Primary chain (Marketing content)

```
Shared Platform / Runtime / Authentication
        ↓ H
AI Runtime
        ↓ S
Content Studio (read)          ← I relative to Sales/CRM
        ↓ S (display only)
Editorial Engine (readiness H← artifacts; approval H← promote tools)
        ↓ S (FDR-003: not publish auth by default)
Publishing
        ↓ S
Campaigns
        ↓ S
Automation / Integrations
```

---

## Revenue / Sales chain

```
Shared Platform / Authentication / DB
        ↓ H
CRM
        ↓ H/S
Sales OS
        ↓ S
Revenue OS (services, forecasting, CSM)
        ↓ S
Analytics
        ↓ S
Automation (events/Celery)
```

---

## Matrix (row depends on column)

| ↓ depends on → | Platform | Auth | AI Runtime | Content Studio | Editorial | Publishing | Marketing | Sales | CRM | Revenue | Analytics | Integrations | Automation | Knowledge |
|----------------|----------|------|------------|----------------|-----------|------------|-----------|-------|-----|---------|-----------|--------------|------------|-----------|
| Platform | — | S | I | I | I | I | I | I | I | I | I | I | S | I |
| Auth | H | — | I | I | I | I | I | I | I | I | I | I | I | I |
| AI Runtime | H | S | — | I | I | I | I | I | I | I | I | I | I | S |
| Content Studio | H | S | I | — | I | I | S | I | I | I | I | I | I | I |
| Editorial | H | S | S | S | — | I | S | I | I | I | I | I | I | I |
| Publishing | H | S | I | S | S | — | S | I | I | I | I | S | S | I |
| Marketing OS | H | S | S | S | S | S | — | I | I | I | I | S | S | I |
| Sales OS | H | H | S | I | I | I | I | — | H | S | I | S | S | I |
| CRM | H | H | I | I | I | I | I | S | — | S | I | I | I | I |
| Revenue OS | H | H | S | I | I | I | I | S | H | — | S | S | S | S |
| Analytics | H | S | I | I | I | I | I | S | S | H | — | I | I | S |
| Integrations | H | S | I | I | I | S | S | S | I | S | I | — | S | I |
| Automation | H | S | I | I | I | S | S | S | I | S | I | S | — | I |
| Knowledge | H | S | S | I | I | I | I | I | I | S | S | I | I | — |

---

## Independence summary

| Module | Can develop independently? |
|--------|----------------------------|
| Content Studio read extensions | Yes (additive GET/UI) |
| Editorial Approval Command | No — needs FDR + promote contracts |
| Sales / CRM | Yes vs Marketing Editorial (avoid shared file thrash on `runner_api.py`) |
| Ruff / toolchain | Yes |
| Publishing | Soft-wait Editorial artifacts + FDR-003 |
| Campaigns / KB | Later; soft deps |
