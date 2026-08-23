# Founder OS ACP-3 — Restart Recovery Matrix

| Boundary | ACP-3 behavior |
|----------|----------------|
| A. Discovery → execution | Latest = PROPOSED/ELIGIBLE facts → **RETRYABLE**; safe retry under gates |
| B. Authority eval → execution | Same; authority **re-evaluated** before run |
| C. External execution → provenance | External kinds without proof → **AMBIGUOUS_EFFECT**; no blind replay. Replay-safe domain proof (e.g. lead_score written) → **SUCCEEDED** |
| D. Failed execution → retry | RETRYABLE if attempts remain; else EXHAUSTED (observable) |
| E. Approval request → approval | WAITING_HUMAN until real ApprovalRequest evidence; never auto-executes HUMAN_REQUIRED |
| F. Delegation → child completion | Child identity independent; parent not marked success from child absence; recovery follows child logs |

**Unknown never silently becomes success.**
