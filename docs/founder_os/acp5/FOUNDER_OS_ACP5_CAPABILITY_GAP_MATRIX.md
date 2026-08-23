# Founder OS ACP-5 — Capability Gap Matrix

**Baseline:** `founder-os-acp4-v1.0` @ `954af7b34590a45991dd098afb21235dfef71fd2`
**Classification legend:**

| Class | Meaning |
|-------|---------|
| DELIBERATE_HUMAN_GOVERNANCE | Contract requires human authority — preserve |
| AGENT_AUTONOMOUS | Catalog AUTONOMOUS and wired (or wireable under freeze) |
| COVERAGE_GAP | Manual today because product/automation incomplete — not true HITL |
| SAFE_BUT_UNOPERABLE | Safe primitives exist; founders cannot operate them as a loop |
| OBSERVATIONAL | Read/flag/metrics; no commercial mutation |

## A. Effect catalog inventory (`acp2_effect_catalog.py`)

### AUTONOMOUS

| Work kind | Wired into heartbeat? | Class |
|-----------|----------------------|-------|
| `lead_score` | YES (`job_score_new_leads`) | AGENT_AUTONOMOUS |
| `follow_up_propose` | YES (`job_scan_follow_up_eligibility`) | AGENT_AUTONOMOUS |
| `booking_propose` | NO — HTTP/API only | COVERAGE_GAP + SAFE_BUT_UNOPERABLE |
| `deal_at_risk_flag` | YES | AGENT_AUTONOMOUS / OBSERVATIONAL |
| `gmail_inbound_match` | YES | AGENT_AUTONOMOUS |
| `metrics_snapshot` | YES (plain `orchestrate` class C residual) | OBSERVATIONAL |
| `hermes_score` | Via Hermes goal job | AGENT_AUTONOMOUS |
| `hermes_qualify_recommend` | Via Hermes; recommend-only | OBSERVATIONAL / COVERAGE_GAP (no Command handoff) |

### HUMAN_REQUIRED (deliberate)

| Work kind | Class |
|-----------|-------|
| `follow_up_send` | DELIBERATE_HUMAN_GOVERNANCE |
| `outbound_send` | DELIBERATE_HUMAN_GOVERNANCE |
| `booking_execute` | DELIBERATE_HUMAN_GOVERNANCE |
| `qualified_demand_decide` | DELIBERATE_HUMAN_GOVERNANCE |
| `approval_decide` | DELIBERATE_HUMAN_GOVERNANCE |

### PROHIBITED (deliberate)

| Work kind | Class |
|-----------|-------|
| `hermes_deal_create` | DELIBERATE_HUMAN_GOVERNANCE (autonomous deal create blocked) |
| `deal_stage_mutation` | DELIBERATE_HUMAN_GOVERNANCE |
| `contact_status_mutation` | DELIBERATE_HUMAN_GOVERNANCE |

## B. Routine sales journey (COS-1 spine)

| Step | Today | Classification |
|------|-------|----------------|
| QD accept/reject | Command INLINE | DELIBERATE_HUMAN_GOVERNANCE |
| Lead score | Heartbeat / Hermes claimed | AGENT_AUTONOMOUS |
| Qualify Contact.status | Human CRM / Hermes recommend only | DELIBERATE for mutation; COVERAGE_GAP for qualify→decision handoff |
| Research → outreach draft | `research-to-outreach` API / sales agents ad hoc | COVERAGE_GAP |
| Outbound send | Approval `decide` | DELIBERATE_HUMAN_GOVERNANCE |
| Follow-up propose | Heartbeat claimed | AGENT_AUTONOMOUS |
| Follow-up send | Approval | DELIBERATE_HUMAN_GOVERNANCE |
| Inbound Gmail match | Heartbeat claimed | AGENT_AUTONOMOUS |
| Reply handle / assess | Rev-orch services; not heartbeat play | COVERAGE_GAP |
| Booking propose | Catalog AUTONOMOUS; no scheduler job | COVERAGE_GAP |
| Booking execute | Approval | DELIBERATE_HUMAN_GOVERNANCE |
| Deal create | Approval only; Hermes PROHIBITED | DELIBERATE_HUMAN_GOVERNANCE |
| At-risk flag | Heartbeat / Hermes | AGENT_AUTONOMOUS / OBSERVATIONAL |
| Agent oversight on Command | Summary computed; **not rendered** | SAFE_BUT_UNOPERABLE |

## C. Ranked gaps (safe execution → operable through agents)

| Rank | Gap | Why it matters |
|------|-----|----------------|
| 1 | No founder-supervised sales agent operating loop | Primitives exist; not composed into plays founders can run/supervise |
| 2 | AUTONOMOUS propose steps not scheduled (outreach draft, booking propose) | Founders still trigger per-contact HTTP for routine work |
| 3 | ACP oversight invisible on Command | Supervision surface exists in snapshot, not in UI |
| 4 | Hermes goals cannot close commercial outcomes | Plans include PROHIBITED deal create; false closed-loop |
| 5 | Qualify recommendations not in decision loop | Dead-end recommendations |
| 6 | Sales crew draft agents ad hoc | Draft+approve exists; no routine cadence |
| 7 | Hermes class B residual (qualify micro-steps) | Observability/delegation incomplete |
| 8 | Metrics class C residual | Lower product impact |

## D. False-HITL (do not call these “governance”)

| Item | Why false-HITL |
|------|----------------|
| Manual `research-to-outreach` per contact | Propose/draft path allowed; not play-bound |
| Manual `booking/propose` after COS “ready” | Catalog AUTONOMOUS; no agent job |
| Hermes qualify without Command decision item | Recommendation with no governed handoff surface |
| Hermes pipeline/deals goals that call blocked deal create | Plan theater |
| `agent_orchestration` unused on Command | Supervision gap, not authority |
| Sales agents only when something invokes them | No routine crew cadence |
