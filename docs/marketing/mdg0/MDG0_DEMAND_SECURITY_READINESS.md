# MDG0 — Demand Security Readiness

**Sprint:** MDG0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY — no controls implemented

## Overall

**Public inbound demand intake: MISSING**  
**MC04 human handoff API: PARTIAL → READY** (human gate, validation, idempotency, audit)

Any future public form is **untrusted external input**. MDG1 must treat abuse controls as first-class scope, not polish.

## Control matrix

| Control | Public form (future) | MC04 handoff (today) |
|---------|----------------------|----------------------|
| Validation | MISSING | PARTIAL (Pydantic lengths, UUID `demand_id`) |
| Rate limiting | MISSING | MISSING (no runtime limiter found) |
| Spam / bot (Turnstile, honeypot) | MISSING | N/A (human API) |
| Payload limits | MISSING | PARTIAL (field max_length; unbounded optional JSON blobs) |
| HTML/script sanitization | MISSING | PARTIAL (no form path; website markdown escapes separately) |
| PII handling / retention | MISSING | PARTIAL (email lands on Contact at accept) |
| Consent | MISSING | PARTIAL (optional field only) |
| Duplicate submission | MISSING | PARTIAL (email merge on Sales accept; no pre-handoff demand SoT) |
| Idempotency | MISSING | READY (`demand_id` → AgentActionLog) |
| Audit / provenance | MISSING | READY (handoff/accept/reject logs) |
| Secure handoff into Marketing | MISSING | READY for human operator only |

## MDG1 implication

Do not expose an open internet form that writes directly into CRM Contact or Deal.

Prefer: capture → validate/abuse gate → Marketing demand or controlled QD register → frozen MC04.5 → OF1.5 operator path.
