# Founder OS ACP-4 — Pause / Kill / Resume (Distributed)

## Source of truth

Pause / kill / resume flags are read from **process environment** (`os.environ`):

| Control | Env |
|---------|-----|
| PAUSE | `HEARTBEAT_ENABLED=0` |
| KILL | `ACP2_AUTONOMOUS_EXECUTION_ENABLED=0` |
| RESUME exec | `ACP3_RESUME_ENABLED=0` blocks recovery execution only |

This is **not** distributed consensus. Replicas can disagree if deployment
configuration is inconsistent.

## Truthful attestation

| Axis | Verdict |
|------|---------|
| Pause Process Safety | **PASS** — fence + job gate on that process |
| Pause Distributed Safety | **CONFIG-DEPENDENT** — requires identical env on all replicas |
| Kill Process Safety | **PASS** |
| Kill Distributed Safety | **CONFIG-DEPENDENT** |
| Resume Safety | **PASS** (bounded; claim+fence on recovery) |

**Production gate:** all API replicas must receive consistent deployment
configuration for these env vars. Rolling partial updates can leave a replica
still executing while another is paused/killed.

## Semantics (unchanged)

- Pause/kill do **not** roll back committed external effects.
- Mid-flight in-process executor may complete after fence was already passed.
- Observational reconcile remains available under pause/kill.
