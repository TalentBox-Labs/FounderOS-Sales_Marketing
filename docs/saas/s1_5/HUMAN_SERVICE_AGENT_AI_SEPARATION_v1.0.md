# HUMAN / SERVICE / AGENT / AI SEPARATION v1.0

**STATUS: FROZEN**  
**Sprint:** FOUNDER OS SaaS S1.5

## Separation table

| Kind | How authenticated | `is_human` | HUMAN_ONLY mutations |
|------|-------------------|------------|----------------------|
| HUMAN | bcrypt User + `founder_os_identity` cookie | true | Allowed if `is_human_approver(display_name)` |
| SERVICE | `RUNNER_API_KEY` Bearer | false | **Blocked** |
| AGENT | forged cookie `kind=AGENT` / agent labels / env | false | **Blocked** |
| AI | forged cookie `kind=AI` / AI labels / env | false | **Blocked** |
| ANONYMOUS | none | false | **Blocked** / HTML redirect |

## Attack vectors that MUST NOT grant HUMAN_ONLY

- client `requested_by`
- display_name spoof in body
- role field alone
- custom headers
- `RUNNER_API_KEY`
- forged cookie with HUMAN-looking name but `kind` ≠ HUMAN / missing User
- direct service-layer call with agent/AI label (UI1.1)

## Frozen gate

`revenue_os.services.mutation_authority.require_human_mutation_authority` remains authoritative for domain mutations. S1 adapters feed it a **server-bound** name on Founder UI proxies.
