# CP4 — Candidate Scoring

**Sprint:** CP4  
**Date:** 2026-08-13

Weights (100%): FOV 20 · CRI 20 · VCB 15 · PUI 15 · EE 10 · Reuse 5 · EDR 5 · GAS 5 · TTV 5  

Scale 0–5. EDR/GAS/EE: higher = better (lower risk / more executable).

---

## A — Social S1 Live LinkedIn

| FOV | CRI | VCB | PUI | EE | Reuse | EDR | GAS | TTV | **W** |
|----:|----:|----:|----:|---:|------:|----:|----:|----:|------:|
| 2.5 | 3.0 | 2.5 | 2.5 | 2.0 | 3.0 | 1.5 | 3.5 | 1.5 | **2.53** |

Adapter `NOT_IMPLEMENTED`. FD-01 OPEN. ES-01..03 unverified. Live publish BLOCKED. Audience still does not create Demand.

---

## B — Social S1 Fake-First / Adapter

| FOV | CRI | VCB | PUI | EE | Reuse | EDR | GAS | TTV | **W** |
|----:|----:|----:|----:|---:|------:|----:|----:|----:|------:|
| 1.5 | 1.5 | 1.5 | 1.0 | 4.0 | 3.5 | 4.5 | 4.0 | 3.0 | **2.13** |

Engineering completeness without Founder/customer value. Penalized on FOV/PUI/CRI.

---

## C — Marketing Demand Generation

| FOV | CRI | VCB | PUI | EE | Reuse | EDR | GAS | TTV | **W** |
|----:|----:|----:|----:|---:|------:|----:|----:|----:|------:|
| 4.0 | 4.5 | 5.0 | 3.5 | 3.0 | 3.5 | 3.0 | 3.5 | 3.0 | **3.93** |

Closes first material break (Audience→Demand). Public form is CONDITIONAL (abuse, domain). Demand created today still cannot be fully operated downstream from UI.

---

## D — MC04.1 QualifiedDemand Operator Completion

| FOV | CRI | VCB | PUI | EE | Reuse | EDR | GAS | TTV | **W** |
|----:|----:|----:|----:|---:|------:|----:|----:|----:|------:|
| 3.5 | 2.5 | 2.5 | 3.5 | 4.5 | 5.0 | 5.0 | 4.0 | 4.5 | **3.48** |

Reject + pending visibility. READY. Incomplete vs full operator flow (no Deal/CO). UI2.5 forbids reject *in cockpit* without a new surface or ADR.

---

## E — Sales A5 Companies on Runner

| FOV | CRI | VCB | PUI | EE | Reuse | EDR | GAS | TTV | **W** |
|----:|----:|----:|----:|---:|------:|----:|----:|----:|------:|
| 2.5 | 2.0 | 2.0 | 2.5 | 4.5 | 4.5 | 5.0 | 5.0 | 4.0 | **2.95** |

JWT Company CRUD exists; runner/UI missing. CRM completeness, not throughput. Sales still saturated for isolated features.

---

## F — Domain-Independent SEO Phase 2

| FOV | CRI | VCB | PUI | EE | Reuse | EDR | GAS | TTV | **W** |
|----:|----:|----:|----:|---:|------:|----:|----:|----:|------:|
| 2.5 | 2.5 | 2.0 | 2.0 | 4.0 | 4.0 | 4.0 | 4.0 | 3.5 | **2.78** |

Technical completeness ≠ demand generation. Production sampling still domain-blocked.

---

## G — Production SEO Activation

| FOV | CRI | VCB | PUI | EE | Reuse | EDR | GAS | TTV | **W** |
|----:|----:|----:|----:|---:|------:|----:|----:|----:|------:|
| 3.0 | 3.5 | 3.0 | 2.5 | 1.0 | 3.0 | 1.0 | 3.0 | 1.0 | **2.63** |

FDR-N05 OPEN. **BLOCKED.**

---

## H — Executive Cockpit Follow-On / UI3

| FOV | CRI | VCB | PUI | EE | Reuse | EDR | GAS | TTV | **W** |
|----:|----:|----:|----:|---:|------:|----:|----:|----:|------:|
| 3.5 | 2.5 | 2.5 | 3.5 | 4.0 | 4.5 | 5.0 | 3.0 | 4.0 | **3.30** |

U1–U3 are not material. Stale CO copy is real but insufficient alone. Expanding cockpit mutations conflicts with UI2.5 freeze (exactly two POSTs). CONDITIONAL.

---

## I — Revenue OS Next Capability

| FOV | CRI | VCB | PUI | EE | Reuse | EDR | GAS | TTV | **W** |
|----:|----:|----:|----:|---:|------:|----:|----:|----:|------:|
| 2.5 | 3.0 | 3.0 | 2.0 | 3.0 | 3.5 | 4.5 | 2.5 | 2.5 | **2.78** |

Billing/recognition frozen out. Operator cannot even accept MC06 from UI. Premature subsystem depth.

---

## J — End-to-End Founder Operating Flow

| FOV | CRI | VCB | PUI | EE | Reuse | EDR | GAS | TTV | **W** |
|----:|----:|----:|----:|---:|------:|----:|----:|----:|------:|
| 5.0 | 3.5 | 4.0 | 5.0 | 4.0 | 5.0 | 5.0 | 4.0 | 4.0 | **4.35** |

Closes the product gap: Founder cannot run Deal stage → CO handoff → Revenue accept (and QD reject) without curl. Reuses A3.5/A4.5/MC04.5/MC06.5. No credentials. No new SoT. Bounded as a **new Jinja operator surface** so UI2.5 cockpit mutation freeze stays intact.

---

## Rank

| Rank | ID | Score | Exec |
|------|----|------:|------|
| 1 | **J** | **4.35** | READY |
| 2 | C | 3.93 | CONDITIONAL |
| 3 | D | 3.48 | READY |
| 4 | H | 3.30 | CONDITIONAL |
| 5 | E | 2.95 | READY |
| 6 | F | 2.78 | READY |
| 6 | I | 2.78 | CONDITIONAL |
| 8 | G | 2.63 | BLOCKED |
| 9 | A | 2.53 | BLOCKED |
| 10 | B | 2.13 | CONDITIONAL |

Highest raw-value: **J**  
Highest executable: **J**  
Highest product-usability: **J** (PUI 5.0)
