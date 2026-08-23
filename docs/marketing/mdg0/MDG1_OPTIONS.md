# MDG1 Options

**Sprint:** MDG0  
**Date:** 2026-08-13  
**Mode:** OPTIONS ONLY — do not implement in MDG0

## Constraint

Preserve OF1.5 / MC04.5 / MC06.5 / UI2.5 / Sales A*.5. Prefer composition over new SoT. Public forms require abuse controls.

## OPTION A — Public website demand capture form → MC04.5

Public CTA/form on Cloudflare Pages site posts to a Founder OS inbound endpoint that validates, rate-limits, then registers Marketing handoff (or a thin Marketing demand record that a human promotes to QD).

| Criterion | Score (0–5) |
|-----------|------------:|
| Founder value | 5 |
| Commercial value | 5 |
| Implementation readiness | 2 |
| Security risk | 4 (high risk if rushed) |
| Reuse of existing capability | 4 (MC04.5 payload) |
| External dependency | 3 (hosting + bot protection) |
| Time-to-value | 3 |

**Type:** BUILD_NEW (capture surface) + CONNECT_EXISTING (MC04.5)

## OPTION B — Content CTA → demand registration endpoint → attribution → qualification

Article-level CTA components emit attributed events into a registration endpoint; operator qualifies into MC04.5.

| Criterion | Score (0–5) |
|-----------|------------:|
| Founder value | 4 |
| Commercial value | 4 |
| Implementation readiness | 1 |
| Security risk | 4 |
| Reuse | 3 |
| External dependency | 3 |
| Time-to-value | 2 |

**Type:** BUILD_NEW (CTA + attribution path)

## OPTION C — Manual Founder demand registration UI → MC04.5

Jinja operator/marketing form that registers `POST /api/v1/marketing/qualified-demand/handoff` with trusted operator identity (closes “API-only register” break without public internet exposure).

| Criterion | Score (0–5) |
|-----------|------------:|
| Founder value | 4 |
| Commercial value | 2 |
| Implementation readiness | 5 |
| Security risk | 1 |
| Reuse | 5 |
| External dependency | 0 |
| Time-to-value | 5 |

**Type:** COMPLETE_EXISTING / CONNECT_EXISTING

## OPTION D — Website form → Marketing Signal store → human promote to QD

Introduce a minimal Marketing-owned inbound record (new SoT) before MC04. Highest correctness for Marketing ownership; highest contract risk.

| Criterion | Score (0–5) |
|-----------|------------:|
| Founder value | 4 |
| Commercial value | 4 |
| Implementation readiness | 1 |
| Security risk | 4 |
| Reuse | 2 |
| External dependency | 3 |
| Time-to-value | 2 |

**Type:** BUILD_NEW (new SoT — requires ADR)

## Recommendation

**MDG1 Slice: OPTION C — Manual Founder Demand Registration on Operator/Marketing surface**

**Implementation type: CONNECT_EXISTING**

### Why

1. Closes the remaining CP4 operating break (QD **registration** UI) without opening untrusted public intake.
2. Reuses frozen MC04.5 contract and OF1.5 operator composition.
3. Avoids spam/Turnstile/rate-limit productization in the first slice.
4. Unblocks real Founder usage of Demand→Revenue while MDG2 can add public capture with security scope.

### Explicitly defer to MDG2+

Public website form (Option A), CTA attribution pipeline (Option B), new Marketing Signal SoT (Option D), social→demand, SEO domain go-live.

### Freeze constraints for MDG1

- No CRM SPA mount
- No cockpit mutation-set expansion beyond UI2.5 unless separately approved
- No DB migration unless ADR proves necessary (prefer AgentActionLog path)
- No credentials / paid tools
- No frozen contract rewrite
