# M6.1 — Application Baseline (Sentinel)

**Sprint:** M6.1  
**Date:** 2026-08-10  
**Agent:** Sentinel  
**Purpose:** Confirm local health; test whether Cloudflare failure originates in application code  

**Environment:** `SECRET_KEY=test-secret-m6-1` · `HEARTBEAT_ENABLED=0`

---

## Tests run

| Suite | Command scope | Result |
|-------|---------------|--------|
| Deployment | `tests/test_website_deployment.py` | Included in focused run |
| Website Engine | `tests/test_website_engine.py` | Included |
| Static Provider | `tests/test_static_provider.py` | Included |
| Publishing | `tests/test_publishing_engine.py` | Included |
| Integration | `tests/test_routers_integration.py` | Included |

**Focused combined:**

```bash
.venv/bin/python -m pytest tests/test_website_deployment.py tests/test_website_engine.py \
  tests/test_static_provider.py tests/test_publishing_engine.py tests/test_routers_integration.py -q
```

| Exit code | Passed | Failed | Errors |
|-----------|--------|--------|--------|
| **0** | **65/65** | **0** | **0** |

---

## Does any test prove Cloudflare failure is in-app?

| Question | Answer |
|----------|--------|
| Tests call Cloudflare APIs? | **NO** |
| Tests require `CLOUDFLARE_API_TOKEN`? | **NO** |
| Deployment adapter export/local deploy tests pass? | **YES** (7/7 in deployment module) |
| Failure reproduced in pytest? | **NO** |

Cloudflare staging failure is **not explained** by failing application tests in this scope.

---

## Verdict

**Local baseline: HEALTHY**  
**Application cause of M6 Cloudflare FAIL: NO**
