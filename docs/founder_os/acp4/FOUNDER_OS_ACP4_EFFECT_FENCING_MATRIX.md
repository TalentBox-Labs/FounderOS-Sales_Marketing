# Founder OS ACP-4 — Effect Fencing Matrix

## Required invariant

`PAST ELIGIBILITY != CURRENT EXECUTION AUTHORITY`

## Stale executor scenario (mandatory)

Worker A becomes eligible. Then one of: KILL, PAUSE, tenant disabled, authority → HUMAN_REQUIRED/PROHIBITED, claim lost, newer generation. Worker A wakes and attempts the effect.

### Can current runtime stop it?

**NO (reliably).**

| Mechanism today | Stops stale A? |
|-----------------|----------------|
| `gate_new_mutating_work` at job start | **No** — already passed |
| `evaluate_authority` kill check | **Only if re-run**; `run_work` does not re-evaluate when state is `ELIGIBLE` |
| Pause in `evaluate_authority` | **Never checked** there |
| Tenant allowlist | Only at evaluate time; not immediately before `executor()` |
| Claim/lease | **Absent** |
| Fence token / generation | **Absent** |

Evidence: `orchestrate` → `evaluate_authority` → `run_work` → `executor` with no second gate (`acp2_orchestration.py`).

## Minimum fence required (design)

Immediately **after claim acquisition** and **before** external/domain mutating effect:

1. Re-read `HEARTBEAT_ENABLED` / `ACP2_AUTONOMOUS_EXECUTION_ENABLED` / `ACP3_RESUME_ENABLED` as applicable
2. Re-resolve tenant: org present + in `resolve_autonomous_organization_ids` (ACTIVE ∩ allowlist)
3. Re-resolve effect mode from catalog / ACP-1 (PROHIBITED / HUMAN_REQUIRED / AUTONOMOUS)
4. For HUMAN_REQUIRED: require live ApprovalRequest evidence in allowed status; approval alone ≠ permanent authority
5. Confirm claim still held (xact lock) / optional generation match
6. Re-check `_already_succeeded` / domain proof

On any narrowing: **abort without effect**, emit fence-reject provenance, do not mark success.

## Optional generation

An incrementing **execution generation** stored only in provenance detail (not a SoT) can help founders see stale rejects; not required if advisory lock + env/tenant revalidation are atomic with the attempt.
