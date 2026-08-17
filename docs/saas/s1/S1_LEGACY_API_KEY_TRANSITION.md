# SaaS S1 — Legacy API Key Transition

**Sprint:** FOUNDER OS SaaS S1

## Classification of `RUNNER_API_KEY`

| Class | Applies? |
|-------|----------|
| HUMAN_AUTH | **NO** — explicitly blocked |
| SERVICE_AUTH | **YES** — current canonical use |
| LEGACY_INTERNAL | **YES** — runners, tests, internal scripts |
| TEST_ONLY | Partial — many tests override `_verify_api_key` |

## Behavior

- `_verify_api_key` unchanged: timing-safe Bearer compare; optional when unset
- Successful API key auth → `IdentityContext(SERVICE, is_human=False)`
- SERVICE cannot `bind_requested_by`
- Founder HTML login does not use the API key

## Human path (canonical)

Cookie session from `/login`.

## Compatibility

Do not remove the key in S1. Internal pipeline/orchestration routes still depend on it.

Mark **human use of RUNNER_API_KEY as deprecated**. Operators must log in as a User.

## Rotation

Rotate `RUNNER_API_KEY` independently from Owner passwords. Compromised key is a service incident, not a human impersonation if S1 gates hold.
