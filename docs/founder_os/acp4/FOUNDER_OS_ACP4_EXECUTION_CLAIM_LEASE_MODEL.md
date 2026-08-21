# Founder OS ACP-4 — Claim / Lease Model

## Discovery decision (preserved)

**CLAIM_REQUIRED_EXISTING_PRIMITIVES_SUFFICIENT** — no new Work/Lease table.

Discovery audit of pre-ACP-4 races remains historically accurate in prior sections of the ACP-4 doc set.

## Implemented mechanism

### Deterministic claim identity

```
material = "acp4:claim:v1:{organization_id}:{idempotency_key}"
digest   = SHA-256(UTF-8(material))
(k1, k2) = first 8 bytes as two signed int32 (big-endian)
```

- Tenant is mandatory in material (cross-tenant never share intentionally).
- Never uses Python `hash()`.
- Collision assumption: 64-bit SHA-256 prefix; birthday collision risk accepted as negligible for operational claim keys.

### Production (PostgreSQL)

`SELECT pg_try_advisory_xact_lock(k1, k2)` on the caller session.

- Non-blocking try
- Releases automatically on transaction commit/rollback
- `distributed_safety_claimed = True`

### Non-PostgreSQL (SQLite tests / single-process)

Process-local `threading.Lock.acquire(blocking=False)`.

- `distributed_safety_claimed = False`
- Documented: not proof of multi-replica safety

### Lifecycle

DISCOVER → derive key → try claim → if unavailable: cancel/suppress → fence → idempotency → execute → provenance → release (xact end / process-local finally)

CLAIMED ≠ AUTHORIZED ≠ SUCCEEDED.

### SELECT FOR UPDATE

Not used as the general work claim. Reserved for future domain-row cases only when a canonical mutable row exists.
