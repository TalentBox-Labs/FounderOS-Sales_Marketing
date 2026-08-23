# R1B — Security Remediation Register (LEDGER)

**Date:** 2026-08-12  
**Sprint:** R1B  
**Rule:** Secret values never recorded here.

---

## R0 “7 findings” mapping

R0 actionable set = **SEC-01 + SEC-03..SEC-08** (SEC-02/09/10 supportive). All re-verified.

| ID | R0 finding | Final classification | Severity | Path | Evidence | Action | Files changed | External action | Rotation | Status | Verification | Rollback |
|----|------------|----------------------|----------|------|----------|--------|---------------|-----------------|----------|--------|--------------|----------|
| SEC-01 | `.env.local` present | B HYGIENE + C SENSITIVE LOCAL | MEDIUM (local) / LOW (VCS) | `.env.local` | Exists; gitignored via `.env.*`; contains Cloudflare-related keys (names only confirmed); **never in git history** | Keep local; ignore verified; template names added to `.env.example` | `.env.example` | None required for git | **No** (never committed) | **RESOLVED** | `git check-ignore` PASS; `git log` empty | N/A |
| SEC-02 | `.env.example` tracked | E FALSE POSITIVE (safe template) | INFORMATIONAL | `.env.example` | Placeholders / comments only | Enrich placeholder names (CLOUDFLARE_*, SECRET_KEY) | `.env.example` | None | No | **FALSE POSITIVE** (kept) | Manual review | revert example |
| SEC-03 | `.crewai_home/.../secret.key` | B HYGIENE GAP → resolved | HIGH if committed; **contained** | `.crewai_home/` | Untracked; R1A ignore | Keep local; ignore | (R1A `.gitignore`) | None | No | **RESOLVED** | `git check-ignore` PASS | revert ignore |
| SEC-04 | `.crewai_storage/` | B → resolved | LOW | `.crewai_storage/` | Untracked; R1A ignore | Keep local; ignore | (R1A) | None | No | **RESOLVED** | check-ignore PASS | revert ignore |
| SEC-05 | `.wrangler/cache` | C GENERATED → resolved | LOW | `.wrangler/` | Untracked; R1A ignore | Keep local; ignore | (R1A) | None | No | **RESOLVED** | check-ignore PASS | revert ignore |
| SEC-06 | `pytest_local.db` / `*.db` | E FALSE POSITIVE / already ignored | LOW | `*.db` | Pattern present pre-R1A | None | — | None | No | **FALSE POSITIVE** | check-ignore PASS | — |
| SEC-07 | `output/` website/deploy packages | C GENERATED → selective ignore | MEDIUM if committed; **contained** | `output/website*`, `publishing/` | R1A selective ignore; tracked `qa_reports` retained | Ignore runtime packages; keep QA evidence tracked | (R1A) + R1B `output/.staging_runtime/` | None | No | **RESOLVED** | check-ignore PASS; deploy tests PASS | revert ignore |
| SEC-08 | `__pycache__` / `.pytest_cache` / `.venv` | E FALSE POSITIVE / already ignored | INFORMATIONAL | caches | Pre-existing ignore | None | — | None | No | **FALSE POSITIVE** | patterns present | — |

---

## Additional findings from R1B re-scan

| ID | Finding | Classification | Severity | Action | Status |
|----|---------|----------------|----------|--------|--------|
| NEW-01 | `docker-compose.yml` `SECRET_KEY` default `change-me-in-production` | D CONFIGURATION | MEDIUM | Require `${SECRET_KEY:?…}` | **RESOLVED** |
| NEW-02 | `docker-compose.demo.yml` demo passwords | D / intentional demo | LOW | No change in R1B | **DEFERRED** |
| NEW-03 | `docs/INTEGRATIONS_DEEP.md` `BEGIN PRIVATE KEY...` ellipsis | E FALSE POSITIVE | INFORMATIONAL | None | **FALSE POSITIVE** |
| NEW-04 | Credentials vault module tracked | E / F KEEP | INFORMATIONAL | Keep code; secrets in env/DB | **FALSE POSITIVE** |
| NEW-05 | Middleware logs method/path not Auth headers | E (adequate) | INFORMATIONAL | None | **FALSE POSITIVE** |
| NEW-06 | Deploy export excludes `metadata.json` / `source.md` | F KEEP (verified) | INFORMATIONAL | Confirmed by tests | **RESOLVED** (verification only) |
| NEW-07 | Local Cloudflare token in `.env.local` | C SENSITIVE LOCAL | MEDIUM local | Contained by ignore; Founder may rotate if shared outside repo | **RESOLVED** (containment); optional Founder hygiene |

---

## Status summary

| Status | Count |
|--------|------:|
| RESOLVED | 8 (7 R0 + NEW-01; NEW-06 verify) |
| FALSE POSITIVE | 5 |
| DEFERRED | 1 (demo compose) |
| EXTERNAL ACTION REQUIRED | **0** |
| FOUNDER DECISION REQUIRED | **0** (optional CF rotate if leaked outside git — not required) |
| Credential rotations required | **0** |

**Critical remaining: 0 · High remaining: 0 · Known active secrets exposed in repo: 0**
