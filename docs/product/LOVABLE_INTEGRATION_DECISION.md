# Lovable Integration Decision

**Sprint:** MDG0  
**Date:** 2026-08-13  
**Mode:** DECISION ONLY — Lovable NOT used in MDG0

## Use Lovable now?

**NO**

## Recommended role

**PROTOTYPE_ONLY** (design exploration / visual mockups)

## Role matrix

| Potential role | Classification |
|----------------|----------------|
| 1. Visual prototype only | **RECOMMENDED** |
| 2. Executive cockpit redesign prototype | **POSSIBLE_WITH_CONTROLS** |
| 3. Operator workflow visual prototype | **POSSIBLE_WITH_CONTROLS** |
| 4. Future SaaS shell prototype | **POSSIBLE_WITH_CONTROLS** |
| 5. Production frontend generation | **NOT_RECOMMENDED** |
| 6. Design-system exploration | **RECOMMENDED** |

## Architectural rule (non-negotiable)

```
LOVABLE / MODERN FRONTEND
        ↓
FOUNDER OS EXISTING APIs
        ↓
FROZEN DOMAIN CONTRACTS
        ↓
CANONICAL SoTs
```

**Forbidden:**

```
LOVABLE APP → NEW DATABASE → DUPLICATE SALES/MARKETING/REVENUE LOGIC
```

Lovable MUST NOT become a second backend or Source of Truth.

## D1 — Production safety answers

| Question | Answer |
|----------|--------|
| Can generated frontend consume current APIs? | **YES** — `/api/v1/cockpit`, `/api/v1/operator`, MC04/MC06 routes |
| Can existing authentication be reused? | **PARTIAL** — API key + operator env; no proper user login on shell |
| Can trusted-human authority remain server-enforced? | **YES** — if client never supplies trusted identity |
| Can Jinja coexist during migration? | **YES** — parallel client risk of UX drift |
| Can routes migrate incrementally? | **YES** — with discipline |
| Would generated code duplicate business rules? | **RISK YES** unless API-only |
| Would it introduce another database? | **MUST NO** |
| Would it require rewriting frozen APIs? | **MUST NO** |
| Would it weaken server-side authority? | **RISK YES** if mutations move client-side |
| Can cockpit/operator rebuild without altering SoTs? | **YES** — UI composition only |

Because auth/tenancy are not SaaS-ready and authority is easy to weaken: **Lovable = PROTOTYPING ONLY** until after MDG1 and a deliberate frontend/auth architecture sprint.

## Timing

**AFTER_MDG1** for prototypes; **AFTER_SAAS_ARCHITECTURE** (or never) for production frontend generation.

| Field | Decision |
|-------|----------|
| Lovable can reuse existing APIs | YES |
| Lovable new backend required | NO |
| Lovable new SoT required | NO |
| Preserve frozen domain contracts | CONDITIONAL (only if API composition + server authority) |
| Recommended Lovable timing | AFTER_MDG1 |
