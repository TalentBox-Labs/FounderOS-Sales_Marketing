# OF1 — Security Attestation

**Sprint:** FOUNDER OS OF1  
**Date:** 2026-08-13

| Control | Result |
|---------|--------|
| Client `requested_by` trusted | **NO** — schemas omit it; server uses `FOUNDER_OS_OPERATOR_NAME` |
| Agent / AI operator env | **503** |
| API key when configured | **401** without bearer |
| UI1.1 service bypass | **BLOCKED** (`HumanAuthorityError`) |
| A3.5 / A4.5 / MC04.5 / MC06.5 validation | Reused, not copied |
| New credentials | **0** |
