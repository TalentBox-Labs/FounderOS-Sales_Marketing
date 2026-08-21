"""ACP-4 distributed claim — PostgreSQL transaction advisory locks.

Deterministic claim identity (never Python hash()):
  material = "acp4:claim:v1:{organization_id}:{idempotency_key}"
  digest   = SHA-256(UTF-8 material)
  (k1, k2) = first 8 bytes as two signed int32 (big-endian)

Tenant is mandatory in the material so cross-tenant work never shares a claim.

Production: pg_try_advisory_xact_lock(k1, k2) — releases on commit/rollback.
Non-PostgreSQL: process-local try-lock fallback for tests/single-process only;
distributed multi-worker safety is NOT claimed on that backend.
"""

from __future__ import annotations

import hashlib
import logging
import threading
from dataclasses import dataclass
from typing import Any

from sqlalchemy import event, text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

CLAIM_NAMESPACE = "acp4:claim:v1"

# Process-local fallback (SQLite / unknown dialect) — NOT distributed safety.
_process_locks: dict[tuple[int, int], threading.Lock] = {}
_process_locks_guard = threading.Lock()


def _release_session_process_claims(session: Session) -> None:
    """Release process-local claims bound to this session (mirrors xact end)."""
    keys = list(session.info.pop("acp4_process_claims", []) or [])
    for claim_key in keys:
        release_process_local_claim(claim_key)


def _ensure_process_claim_session_hooks(db: Session) -> None:
    """Bind process-local claim release to session commit/rollback (not function return)."""
    if db.info.get("acp4_claim_hooks_installed"):
        return
    db.info["acp4_claim_hooks_installed"] = True
    db.info.setdefault("acp4_process_claims", [])

    def _on_commit(session: Session) -> None:
        _release_session_process_claims(session)

    def _on_rollback(session: Session) -> None:
        _release_session_process_claims(session)

    event.listen(db, "after_commit", _on_commit)
    event.listen(db, "after_rollback", _on_rollback)


@dataclass(frozen=True)
class ClaimKey:
    organization_id: str
    idempotency_key: str
    material: str
    k1: int
    k2: int
    digest_hex: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "organization_id": self.organization_id,
            "idempotency_key": self.idempotency_key,
            "material": self.material,
            "k1": self.k1,
            "k2": self.k2,
            "digest_hex": self.digest_hex,
        }


@dataclass
class ClaimResult:
    acquired: bool
    claim_key: ClaimKey | None
    backend: str
    distributed_safety_claimed: bool
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "acquired": self.acquired,
            "backend": self.backend,
            "distributed_safety_claimed": self.distributed_safety_claimed,
            "reason": self.reason,
            "claim_key": self.claim_key.to_dict() if self.claim_key else None,
        }


def _to_signed_i32(unsigned_u32: int) -> int:
    if unsigned_u32 >= 2**31:
        return unsigned_u32 - 2**32
    return unsigned_u32


def derive_claim_key(*, organization_id: str, idempotency_key: str) -> ClaimKey:
    """Deterministic cross-process claim identity. Raises on missing tenant/key."""
    org = str(organization_id or "").strip()
    idem = str(idempotency_key or "").strip()
    if not org:
        raise ValueError("missing_tenant")
    if not idem:
        raise ValueError("missing_idempotency_key")
    material = f"{CLAIM_NAMESPACE}:{org}:{idem}"
    digest = hashlib.sha256(material.encode("utf-8")).digest()
    k1 = _to_signed_i32(int.from_bytes(digest[0:4], "big", signed=False))
    k2 = _to_signed_i32(int.from_bytes(digest[4:8], "big", signed=False))
    return ClaimKey(
        organization_id=org,
        idempotency_key=idem,
        material=material,
        k1=k1,
        k2=k2,
        digest_hex=digest.hex(),
    )


def dialect_name(db: Session) -> str:
    bind = db.get_bind()
    return str(getattr(getattr(bind, "dialect", None), "name", "") or "").lower()


def try_acquire_claim(
    db: Session,
    *,
    organization_id: str,
    idempotency_key: str,
) -> ClaimResult:
    """Attempt non-blocking claim. Does not authorize execution."""
    try:
        key = derive_claim_key(
            organization_id=organization_id, idempotency_key=idempotency_key
        )
    except ValueError as exc:
        return ClaimResult(
            acquired=False,
            claim_key=None,
            backend="none",
            distributed_safety_claimed=False,
            reason=str(exc),
        )

    dialect = dialect_name(db)
    if dialect in ("postgresql", "postgres"):
        acquired = _pg_try_advisory_xact_lock(db, key.k1, key.k2)
        return ClaimResult(
            acquired=bool(acquired),
            claim_key=key,
            backend="postgresql_advisory_xact",
            distributed_safety_claimed=True,
            reason=None if acquired else "claim_unavailable",
        )

    # Explicit non-distributed fallback (tests / single-process SQLite demos).
    # Hold until session commit/rollback (not until run_work_claimed returns),
    # approximating PostgreSQL xact advisory lock lifetime.
    acquired = _process_local_try_lock(key.k1, key.k2)
    if acquired:
        _ensure_process_claim_session_hooks(db)
        db.info.setdefault("acp4_process_claims", []).append(key)
    return ClaimResult(
        acquired=acquired,
        claim_key=key,
        backend="process_local_test_only",
        distributed_safety_claimed=False,
        reason=None if acquired else "claim_unavailable",
    )


def release_process_local_claim(claim_key: ClaimKey | None) -> None:
    """Release process-local claim (no-op for PostgreSQL xact locks)."""
    if claim_key is None:
        return
    pair = (claim_key.k1, claim_key.k2)
    with _process_locks_guard:
        lock = _process_locks.get(pair)
    if lock is not None and lock.locked():
        try:
            lock.release()
        except RuntimeError:
            pass


def _pg_try_advisory_xact_lock(db: Session, k1: int, k2: int) -> bool:
    row = db.execute(
        text("SELECT pg_try_advisory_xact_lock(:k1, :k2)"),
        {"k1": int(k1), "k2": int(k2)},
    ).scalar()
    return bool(row)


def _process_local_try_lock(k1: int, k2: int) -> bool:
    pair = (k1, k2)
    with _process_locks_guard:
        lock = _process_locks.get(pair)
        if lock is None:
            lock = threading.Lock()
            _process_locks[pair] = lock
    return lock.acquire(blocking=False)


def reset_process_local_claims_for_tests() -> None:
    """Test helper — clear process-local claim map."""
    with _process_locks_guard:
        for lock in list(_process_locks.values()):
            if lock.locked():
                try:
                    lock.release()
                except RuntimeError:
                    pass
        _process_locks.clear()
