# CP2 — Founder OS Capability Map (ATLAS)

**Sprint:** CP2 — Cross-OS Capability Maturity Review  
**Date:** 2026-08-13  
**Repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
**Mode:** Read-only portfolio assessment — no runtime or contract changes  
**Evidence:** `docs/governance/CP1_*`, `docs/marketing/*`, `docs/sales/*`, `docs/operations/*`, codebase spot-check  
**Cross-Agent Conflicts:** 0

---

## Classification legend

| Class | Meaning |
|-------|---------|
| **FROZEN** | Baseline, contract, or behavioral spec is frozen; change requires ADR + approved sprint |
| **OPERABLE** | End-to-end usable by a human operator on the primary runner path (with known limitations documented) |
| **PARTIAL** | Substantial implementation exists; material gaps prevent treating as complete |
| **CONDITIONAL** | Work may proceed under stated preconditions (Founder decision, external setup, domain, fakes-only) |
| **BLOCKED** | Cannot reach target state without resolving a hard blocker |
| **MISSING** | No implementation; contract or intent may exist |

---

## Executive maturity summary

| Domain | Maturity | Headline |
|--------|----------|----------|
| **Website** | **OPERABLE** (baselines **FROZEN**) | Production static site LIVE on Cloudflare Pages; M-series complete |
| **SEO** | **FROZEN** + **OPERABLE** (read-only) | Readiness + Technical SEO engines frozen; live production sampling **CONDITIONAL** on branded domain |
| **Social** | **MISSING** (runtime) / **CONDITIONAL** (S1) | Architecture defined; no Social Engine; live LinkedIn **BLOCKED** |
| **Sales — A1.5** | **FROZEN** | Sales OS Architecture Baseline v1.0 |
| **Sales — A3.5** | **FROZEN** + **OPERABLE** | Runner deal stage update human-gated and frozen |
| **Sales — A4.5** | **FROZEN** + **OPERABLE** | LeadScorer / Contact.status human gate frozen |
| **Revenue** | **PARTIAL** | Entity SoT LIVE; dual API stack; no CommercialOutcome |
| **QualifiedDemand** | **MISSING** | Cross-OS contract frozen; zero runtime |
| **CRM UI** | **PARTIAL** | React SPA preserved; `/app` unmounted (`503 not_built`) |
| **Integrations** | **FROZEN** (disposition) / **PARTIAL** (activation) | 14/14 classified; **0 external integrations activated** |

**Portfolio posture:** Marketing engines and Sales governance baselines are **mature and frozen**. **Demand ingress** (QualifiedDemand) and **post-close handoff** (CommercialOutcome) remain the primary value-chain breaks. Social is the largest **MISSING** marketing runtime. CRM UI is the largest **PARTIAL** operator surface.

---

## 1. Website

| Attribute | Value |
|-----------|-------|
| **Maturity** | **OPERABLE** |
| **Baseline status** | **FROZEN** — Publishing v1.0 (M1.5), Website Engine Core v1.0 (M2.5), Static Provider v1.0 (M3.5), Deployment Adapter (M5.5), Production v1.0 (M7.5) |
| **Production** | LIVE — `https://founderos-staging.pages.dev` (Cloudflare Pages) |
| **Code** | `src/tools/website_engine/*`, `src/tools/publishing_engine.py`, deployment adapter artifacts |

### What works

- Editorial approval → Publishing orchestration → Static Website Provider → Deployment Adapter → Cloudflare path verified through M7.5 production baseline freeze.
- Portable static output (HTML, sitemap, RSS) with rollback via Cloudflare history + local snapshots.
- Staging RC1 frozen (M6.5); production cutover complete (M7).

### Known limitations (not freeze blockers)

| Limitation | Impact |
|------------|--------|
| Root `/` returns 404 | No landing page in Static v1.0 |
| Branded `workcrew.ai` DNS CNAME pending | Production URL is Pages default, not certified branded origin |
| Publishing → Website auto-invoke | Website channel remains **PLACEHOLDER**; production used RC1 static + adapter path |
| Project slug `founderos-staging` | Naming debt while serving production branch |

### CP2 verdict

**OPERABLE** for static website publishing and production hosting. Baselines **FROZEN**. Branded domain and full Publishing→Website wire are **CONDITIONAL** follow-ons, not blockers to current operability.

---

## 2. SEO

| Attribute | Value |
|-----------|-------|
| **Maturity** | **FROZEN** (engines) · **OPERABLE** (local/read-only audit) · **CONDITIONAL** (production live sampling) |
| **Baselines** | SEO Readiness Engine v1.0 (S1.5), Technical SEO Engine v1.0 (S2.5) |
| **Code** | `src/tools/seo_engine/*` (readiness + technical families), `src/tools/site_origin.py` |
| **Tests** | S1 34/34, S2 27/27, combined Website+SEO gate 92/92 at S2.5 freeze |

### Frozen scope

- 12 readiness check categories; 72 technical SEO rules across 10 families.
- Read-only guarantee, origin/indexing safety, API + UI contracts frozen.
- Robots analysis: **PARTIAL — ACCEPTED DOCUMENTED LIMITATION** (`WEBSITE-SEO-ROBOTS-001`).

### Production activation

| Gate | Status |
|------|--------|
| Engine correctness | PASS |
| Live production URL sampling | **BLOCKED PENDING DOMAIN** — 8/8 domain blockers remain DOMAIN_BLOCKED at S2.5 |
| Branded origin certification | **CONDITIONAL** on DNS/TLS (N0.5) |

### CP2 verdict

**FROZEN** and **OPERABLE** for operator-driven SEO readiness and technical audits against static artifacts. Production SEO activation against live branded origin is **CONDITIONAL** / **BLOCKED** until domain cutover. Not **MISSING**.

---

## 3. Social

| Attribute | Value |
|-----------|-------|
| **Maturity** | **MISSING** (runtime) · **CONDITIONAL** (S1 engineering start) · **BLOCKED** (live publish) |
| **Architecture** | **DEFINED** — Editorial → Publishing → Social → LinkedIn Adapter (S0) |
| **Code** | No Social Engine package; Publishing LinkedIn channel = stub (`NOT_IMPLEMENTED`); `revenue_os/integrations/social_publisher.py` = STALE/ADJACENT (I08 **RETIRE**) |

### Readiness matrix

| Layer | State |
|-------|-------|
| Editorial + Publishing human gates | IMPLEMENTED |
| Social Engine / Marketing OS LinkedIn adapter | **NOT IMPLEMENTED** |
| Social UI | **NOT IMPLEMENTED** |
| OAuth / token bind (Marketing OS) | **NOT IMPLEMENTED** |
| Measurement | **PARTIAL** |

### Blockers (S0 / S0-R / CP1)

| ID | Class | Prevents |
|----|-------|----------|
| FD-01 | **FOUNDER_DECISION** | Publishing identity (person vs org vs configurable) |
| ES-01..03 | **EXTERNAL** | Live LinkedIn API calls (developer app, OAuth, token) |
| ES-04 | **EXTERNAL** (conditional) | Org identity page admin |
| IB-01..03 | **ENGINEERING** | S1 scope — not a pre-start hard stop behind fakes |

### CP2 verdict

**MISSING** as an operable marketing channel. **CONDITIONAL GO** to begin S1 (LinkedIn manual publisher) behind fakes and frozen contracts. **BLOCKED** for live publish until FD-01 + ES complete. Highest Marketing OS runtime gap after Website/SEO freeze.

---

## 4. Sales — A1.5 (Architecture Baseline)

| Attribute | Value |
|-----------|-------|
| **Maturity** | **FROZEN** |
| **Baseline** | Sales OS Architecture Baseline v1.0 |
| **ADR** | ADR-005 |
| **Date frozen** | 2026-08-13 |

### Frozen artifacts (10 + binding A1 sources)

- Domain model, Marketing boundary, Revenue boundary, Agent authority, Integration disposition, CRM UI disposition.
- Parent freezes respected: Architecture v2.2, Marketing M-series, SEO baselines, Toolchain v1.0.

### Verification at freeze

| Metric | Value |
|--------|-------|
| Focused tests | 15/17 |
| Known exceptions | 2 (environment-dependent prospecting UI) |
| Feature/runtime/DB/integration activation | 0 |
| New regressions | 0 |

### CP2 verdict

**FROZEN**. Defines destination Sales OS ownership and cross-OS contracts. Does not by itself make Sales **OPERABLE** — implementation maturity is tracked under A3.5, A4.5, and capability register.

---

## 5. Sales — A3.5 (Runner Deal Stage Update)

| Attribute | Value |
|-----------|-------|
| **Maturity** | **FROZEN** + **OPERABLE** |
| **Baseline** | Sales Runner Deal Stage Update v1.0 |
| **ADR** | ADR-007 |
| **Code** | `runner_api_routers/crm.py` (`PATCH .../deals/{id}/stage`), `revenue_os/services/deal_automation_service.py`, `revenue_os/models/deal.py` |

### Behavioral contract (frozen)

- Human-gated stage mutation on primary runner CRM path.
- Reuses `apply_deal_stage_update` / `advance_deal_stage`; sets `closed_at` on terminal stages.
- Prohibited: agent/AI stage mutation, silent CommercialOutcome, CRM mount side effect, external integration activation.

### Verification at freeze

| Suite | Result |
|-------|--------|
| `tests/test_a3_runner_deal_stage.py` | 15/15 |
| A1.5 focused | 15/17 |
| Full regression | 412/424 (historical failures unchanged) |

### CP2 verdict

**FROZEN** and **OPERABLE**. Closes prior MC05/C20 runner gap (writable pipeline on primary path). Value-chain secondary break (CommercialOutcome) intentionally deferred.

---

## 6. Sales — A4.5 (LeadScorer / Contact.status Gate)

| Attribute | Value |
|-----------|-------|
| **Maturity** | **FROZEN** + **OPERABLE** |
| **Baseline** | LeadScorer / Contact.status Baseline v1.0 |
| **Parent** | Sales OS Architecture v1.0 unchanged; A3.5 sibling unchanged |
| **Code** | `revenue_os/services/lead_scoring_service.py`, `runner_api_routers/crm.py` (`POST/PATCH .../contacts/{id}/score|status`), scheduler/tasks/hermes score-only paths |

### Behavioral contract (frozen)

- LeadScorer remains advisory; **Contact.status mutation human-only** via runner PATCH.
- No agent path mutates status via LeadScorer flow.
- Audit: `LEAD_SCORED` + `CONTACT_STATUS_CHANGED`.
- Does not emit CommercialOutcome.

### Verification at freeze

| Suite | Result |
|-------|--------|
| `tests/test_a4_runner_contact_status.py` | 15/15 |
| A3.5 sibling | 15/15 |
| Full regression | 427/439 (+15 vs A3.5; 0 new regressions) |

### CP2 verdict

**FROZEN** and **OPERABLE**. Closes A1.5 authority debt on autonomous Contact.status promotion. CP1 Candidate B — **delivered and frozen**.

---

## 7. Revenue OS

| Attribute | Value |
|-----------|-------|
| **Maturity** | **PARTIAL** |
| **Role** | CRM entity SoT — Contact, Company, Deal, Pipeline, Activity |
| **Code** | `revenue_os/models/*`, `revenue_os/services/*`, `runner_api_routers/crm.py` |

### Operable surfaces

| Capability | State |
|------------|-------|
| Contact / Deal / Activity CRUD (runner) | **OPERABLE** |
| Pipeline summary | **OPERABLE** (read-only aggregates) |
| Deal stage update (runner) | **OPERABLE** (A3.5 frozen) |
| Contact score + status gate (runner) | **OPERABLE** (A4.5 frozen) |
| Approvals queue | **OPERABLE** |
| Forecasting APIs | **OPERABLE** (API; limited UI) |
| CSM health | **OPERABLE** |

### Gaps keeping Revenue **PARTIAL**

| Gap | Class | Notes |
|-----|-------|-------|
| Dual API stacks (runner vs JWT `revenue_os.main`) | **PARTIAL** | I03 **DEFER**; ACCEPTED_LEGACY |
| CommercialOutcome handoff | **MISSING** | Contract frozen; not implemented |
| Companies on runner | **PARTIAL** | JWT API_ONLY (C19); no operator UI (MC08) |
| Owner FK / RBAC | **MISSING** | Orphan UUID assignment (MC07) |
| Relational PipelineStage entity | **MISSING** | Enum+CSV model (MC09) |
| Revenue recognition / billing | **MISSING** | Future finance scope |

### CP2 verdict

**PARTIAL**. Core entity SoT and human-gated Sales ops on runner are **OPERABLE**. Revenue is not a duplicate CRM problem — it is the **authoritative store** with incomplete cross-OS handoff and consolidation debt.

---

## 8. QualifiedDemand (Marketing → Sales)

| Attribute | Value |
|-----------|-------|
| **Maturity** | **MISSING** |
| **Contract** | **FROZEN** — `SALES_MARKETING_BOUNDARY_CONTRACT_v1.0.md` |
| **Runtime** | **None** — grep shows zero Python references |

### Frozen contract (not built)

```
Marketing Signal → Marketing Qualification → QualifiedDemand → Sales Intake → Sales Qualification
```

- Minimum payload: `demand_id`, `occurred_at`, `source`, `person`, optional channel/company/consent/attribution.
- Rules: idempotency, duplicate-email merge, rejection audit (`SalesDemandRejected`).
- Prohibited: Marketing writing Revenue CRM tables directly; agent bypass of handoff.

### Dependencies for implementation

| Side | Requirement |
|------|-------------|
| Marketing | Emitter (forms, social, web — none wired) |
| Sales | Intake handler + policy |
| Cross-OS | Coordination sprint (MC04); CP1 raw score highest (3.70) but not most executable |

### CP2 verdict

**MISSING**. Primary value-chain break per CP1 value-chain analysis. Contract **FROZEN** and **ready for BUILD**; no partial implementation to classify as PARTIAL.

---

## 9. CRM UI

| Attribute | Value |
|-----------|-------|
| **Maturity** | **PARTIAL** |
| **Disposition** | **FROZEN** — `RETAIN_AND_REFACTOR_LATER` (A1.5 / ADR-005) |
| **Source** | `frontend/` (`workcrew-crm-frontend`, Vite/React) |
| **Mount** | **UNMOUNTED** — `frontend/dist` absent; `GET /app` → **503** `not_built` |
| **Alternate entry** | Jinja `/sales` **OPERABLE** (prospecting ops shell) |

### Frozen pre-mount conditions

1. Approved implementation sprint (post-A1.5; typically A6 in A2 sequence).
2. Runner stage-mutation API — **now satisfied** (A3.5).
3. Contact.status human gate — **now satisfied** (A4.5).
4. Explicit nav link decision in Founder shell.
5. Controlled `frontend/dist` build (Docker/ops — not silent local mount).

### Remaining incompatibilities

- SPA expects runner `/api/v1/crm/*` — runner now has stage + status APIs; refactor still required for authority UX.
- Dual JWT stack not primary SPA target.
- Mounting without refactor would expose partial CRM as complete.

### CP2 verdict

**PARTIAL**. Source preserved; primary React CRM **not operable** to founders. Preconditions for mount improved post-A3.5/A4.5 but refactor sprint not started. Not **MISSING** (substantial UI code exists).

---

## 10. Integrations

| Attribute | Value |
|-----------|-------|
| **Maturity** | **FROZEN** (disposition) · **PARTIAL** (runtime activation) |
| **Baseline** | Sales Integration Disposition v1.0 (A1.5) — 14/14 classified |
| **External integrations activated** | **0** |

### Disposition summary

| Class | Count | Examples |
|-------|------:|----------|
| RETAIN_CORE | 4 | PostgreSQL, Runner API-key auth, OpenAI/Gemini, Credentials vault |
| RETAIN_OPTIONAL | 6 | n8n (I04), SMTP (I05), Gmail (I06), Proxycurl (I07), Calendar (I09), ChromaDB (I11) |
| DEFER | 3 | JWT stack (I03), WhatsApp (I10), HubSpot/SF/Pipedrive (I14) |
| RETIRE | 1 | RevenueOS LinkedIn UGC publisher (I08) → Marketing Social path |

### Activation reality

| Integration | Config present | Activated | Blocker |
|-------------|----------------|-----------|---------|
| PostgreSQL | When `DATABASE_URL` set | **OPERABLE** | Ops |
| Runner API key | When key set | **OPERABLE** | Auth hygiene |
| LLM providers | When keys set | **CONDITIONAL** | Paid usage / Founder |
| n8n, SMTP, Gmail, Proxycurl, Calendar | Code exists | **MISSING** (inactive) | Founder enable + credentials |
| HubSpot/SF/Pipedrive | None | **MISSING** | Product ADR |
| LinkedIn publish (Sales) | I08 retired | **BLOCKED** | Marketing Social SoT |

### CP2 verdict

**FROZEN** classification is complete. Runtime maturity is **PARTIAL** — core infra **OPERABLE** when configured; outbound/enrichment/CRM-sync integrations **MISSING** activation. No disposition drift since A1.5.

---

## Cross-OS value chain (CP2)

```mermaid
flowchart TD
  subgraph marketing [Marketing OS]
    WEB[Website OPERABLE FROZEN]
    SEO[SEO FROZEN OPERABLE]
    SOC[Social MISSING]
  end

  subgraph handoff1 [Demand ingress]
    QD[QualifiedDemand MISSING]
  end

  subgraph sales [Sales OS]
    A15[A1.5 FROZEN]
    A35[A3.5 FROZEN OPERABLE]
    A45[A4.5 FROZEN OPERABLE]
    PROS[/sales OPERABLE]
  end

  subgraph revenue [Revenue OS PARTIAL]
    CRM[Entity SoT OPERABLE]
    CO[CommercialOutcome MISSING]
  end

  subgraph ui [Operator surfaces]
    APP[CRM UI PARTIAL unmounted]
  end

  WEB --> SEO
  SOC -.->|BLOCKED live| QD
  marketing -->|no emitter| QD
  QD -->|not implemented| PROS
  PROS --> CRM
  A35 --> CRM
  A45 --> CRM
  CRM -->|closed_won fields only| CO
  APP -.->|503| CRM
```

---

## Capability matrix (CP2 rollup)

| Capability | Class | Baseline / evidence | Primary gap |
|------------|-------|---------------------|-------------|
| Website publish + deploy | **OPERABLE** / **FROZEN** | M7.5 production baseline | Branded DNS; auto Publishing→Website wire |
| SEO readiness + technical audit | **FROZEN** / **OPERABLE** | S1.5 + S2.5 | Live domain sampling; robots partial |
| Social (LinkedIn) | **MISSING** | S0 CONDITIONAL GO | No engine; FD-01 + ES for live |
| Sales architecture | **FROZEN** | A1.5 / ADR-005 | — |
| Deal stage ops (runner) | **FROZEN** / **OPERABLE** | A3.5 / ADR-007 | CommercialOutcome deferred |
| Contact.status authority | **FROZEN** / **OPERABLE** | A4.5 | — |
| Revenue entity SoT | **PARTIAL** | `revenue_os/*` | Dual stack; no CommercialOutcome |
| QualifiedDemand | **MISSING** | Contract frozen | No emitter or intake |
| CommercialOutcome | **MISSING** | Contract frozen | Post-close handoff |
| CRM React SPA | **PARTIAL** | RETAIN_AND_REFACTOR | Unmounted; no dist build |
| Integrations (external) | **PARTIAL** | I01–I14 frozen | 0 activated optional integrations |
| Prospecting `/sales` | **OPERABLE** | C01 LIVE | Not full CRM |

---

## Top gaps (CP2 priority order)

### P0 — Value chain breaks

1. **QualifiedDemand (MISSING)** — No Marketing→Sales demand handoff; manual Contact creation only. Highest strategic leverage (CP1 score 3.70); requires Marketing emitter + Sales intake BUILD.
2. **CommercialOutcome (MISSING)** — No Sales→Revenue post-close event; `closed_won` updates Deal fields only. Unblocks CS/Client lifecycle.

### P1 — Operator surface and channel

3. **CRM UI (PARTIAL / UNMOUNTED)** — Full React CRM unavailable (`/app` 503). A3.5/A4.5 removed key API blockers; refactor/mount sprint (A6) still required.
4. **Social runtime (MISSING)** — No Social Engine or LinkedIn adapter; live publish **BLOCKED** on FD-01 + ES-01..03.

### P2 — Production completeness

5. **Branded domain + SEO live activation (CONDITIONAL/BLOCKED)** — `workcrew.ai` DNS pending; production SEO sampling domain-blocked.
6. **Website Publishing auto-wire (PARTIAL)** — Website channel PLACEHOLDER in Publishing Engine; manual/RC1 path used in production.

### P3 — Platform debt

7. **External integrations inactive (PARTIAL)** — n8n, SMTP, Gmail, Proxycurl, Calendar classified but not activated; outreach send (C10) remains PARTIAL.
8. **Revenue dual API stack (PARTIAL)** — JWT vs runner consolidation deferred (I03).
9. **Companies runner + UI (MISSING/PARTIAL)** — JWT API_ONLY; no operator org screens (C19/MC08).

---

## Frozen baseline inventory (must not break)

| OS / domain | Frozen baseline | ADR / manifest |
|-------------|-----------------|------------------|
| Architecture | v2.2 | Platform docs |
| Publishing | v1.0 | M1.5 |
| Website Engine | v1.0 | M2.5 |
| Static Provider | v1.0 | M3.5 |
| Production Website | v1.0 | M7.5 |
| SEO Readiness | v1.0 | S1.5 |
| Technical SEO | v1.0 | S2.5 |
| Sales OS Architecture | v1.0 | A1.5 / ADR-005 |
| Runner Deal Stage | v1.0 | A3.5 / ADR-007 |
| LeadScorer Contact.status | v1.0 | A4.5 |
| Integration disposition | v1.0 | A1.5 |
| CRM UI disposition | v1.0 | A1.5 |

---

## Outstanding Founder decisions (CP2 carry-forward)

| ID | Topic | Affects |
|----|-------|---------|
| FD-01 | LinkedIn publishing identity (person / org / configurable) | Social S1 live publish |
| — | Branded domain cutover (`workcrew.ai`) | Website certified URL, SEO live sampling |
| — | Optional integration enablement (n8n, SMTP, Proxycurl, etc.) | Outreach send, enrich |

---

## CP2 verdict

Founder OS has **strong frozen baselines** across Website, SEO, and Sales governance (A1.5, A3.5, A4.5). **Operable** founder-facing paths exist for static website production, SEO audit, prospecting (`/sales`), and human-gated CRM mutations on the runner API.

The portfolio remains **PARTIAL** at the OS level because:

- **Demand does not flow** from Marketing to Sales (QualifiedDemand **MISSING**).
- **Revenue handoff** after close is undefined in runtime (CommercialOutcome **MISSING**).
- **Social** and **CRM SPA** are the largest incomplete operator experiences.
- **Integrations** are classified but largely inactive.

**Recommended CP2 planning focus:** QualifiedDemand (cross-OS) or Social S1 (Marketing lane, **CONDITIONAL**) or CRM UI mount prep (Sales lane, preconditions now met) — selection depends on Founder priority between value-chain repair vs external channel vs operator UX.

---

**Document:** `docs/portfolio/cp2/CP2_FOUNDER_OS_CAPABILITY_MAP.md`  
**Agent:** ATLAS  
**Status:** COMPLETE
