# CP4 — Pre-Mortem (Top 3)

**Sprint:** CP4  
**Date:** 2026-08-13

## 1. J — Operator Flow Completion (recommended)

If we spend the next sprint here and Founder OS does not improve materially, why?

| Failure | How |
|---------|-----|
| Product-value | Surface becomes another read-only dashboard; Founder still uses curl |
| Engineering | Scope includes CRM SPA remount, JWT dual-stack, or new SoT |
| Architecture | Cockpit mutation set silently rewritten, breaking UI2.5 |
| Adoption | Trusted operator env unset; buttons 503; workflow unused |
| Dependency | None external — failure would be self-inflicted scope |

**Mitigation:** New `/operate` (or equivalent) Jinja page; proxy only A3.5 / MC04 reject / MC06 endpoints; `FOUNDER_OS_OPERATOR_NAME`; no UI2.5 mutation-count change; no billing.

---

## 2. C — Marketing Demand Generation

| Failure | How |
|---------|-----|
| Product-value | Form exists but no traffic (domain pending) or spam floods QD |
| Engineering | Invents a second demand SoT instead of MC04 handoff |
| Architecture | Public write bypasses human gate |
| Adoption | Founder never publishes the form |
| Dependency | FDR-N05 / Turnstile / hosting |

Demand without an operable downstream loop still strands leads in API-only Sales.

---

## 3. D — MC04.1 QD Operator Completion

| Failure | How |
|---------|-----|
| Product-value | Reject button is polish; Deal/CO remain curl-only |
| Engineering | Forced into frozen cockpit (UI2.5 conflict) |
| Architecture | Shared SoT or MC04.5 rewrite |
| Adoption | Low reject volume |
| Dependency | None |

Safe but **insufficient** as the sole next sprint after MC06.5.
