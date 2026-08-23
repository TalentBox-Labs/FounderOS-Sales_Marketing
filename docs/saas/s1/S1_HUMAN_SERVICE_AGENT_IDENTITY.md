# SaaS S1 — Human / Service / Agent / AI Identity

**Sprint:** FOUNDER OS SaaS S1

## Separation

| Kind | How it authenticates | `is_human` | HUMAN_ONLY mutations |
|------|----------------------|------------|----------------------|
| HUMAN | bcrypt User + session cookie | true | Allowed if `is_human_approver(display_name)` |
| SERVICE | `RUNNER_API_KEY` Bearer | false | **Blocked** (does not bind `requested_by`) |
| AGENT | Label / forged cookie `kind=AGENT` / env `agent` | false | **Blocked** (UI1.1 + S1) |
| AI | Label / forged cookie `kind=AI` / env `ai` | false | **Blocked** |
| ANONYMOUS | none | false | **Blocked** (or 303 on gated HTML) |

Agents and AI **never** become human because they hold an API key.

## Frozen HUMAN_ONLY gate

Unchanged: `require_human_mutation_authority` / `is_human_approver` in `revenue_os/services/mutation_authority.py`.

S1 wraps Founder UI proxies so the string passed into that gate is **server-bound**, not client `requested_by`.

## Classification helper

`classify_actor_label(name)` maps denylist tokens (`agent`, `ai`, `system`, …) to AGENT / AI / SERVICE. Valid human names map to HUMAN.

## Tests

S1 focused suite covers: API key ≠ HUMAN; AGENT cookie cannot mutate; AI cookie cannot mutate; valid session human still mutates via MDG1 → MC04.5 `register_marketing_handoff`.
