"""PostgreSQL-backed HUMAN session JTI revocation.

Authoritative store for logout revocation — not process-local memory.
Lookup failures fail closed (caller must deny the session).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from revenue_os.database import SessionLocal as _default_session_factory
from revenue_os.models.session_revocation import SessionRevocation

logger = logging.getLogger(__name__)

SessionFactory = Callable[[], Session]


class SessionRevocationStoreUnavailable(RuntimeError):
    """Revocation store cannot be read or written — callers must fail closed."""


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def revoke_jti(
    jti: str,
    expires_at: datetime,
    *,
    session_factory: SessionFactory | sessionmaker | None = None,
) -> None:
    """Persist a revocation until expires_at. Idempotent for duplicate jti."""
    cleaned = (jti or "").strip()
    if not cleaned:
        return
    factory = session_factory or _default_session_factory
    exp = _as_utc(expires_at)
    now = datetime.now(timezone.utc)
    db = factory()
    try:
        # Opportunistic cleanup of records that can no longer affect auth.
        db.query(SessionRevocation).filter(SessionRevocation.expires_at <= now).delete(
            synchronize_session=False
        )
        existing = db.get(SessionRevocation, cleaned)
        if existing is not None:
            # Keep the later expiry if a stale shorter row somehow exists.
            if _as_utc(existing.expires_at) < exp:
                existing.expires_at = exp
                db.commit()
            return
        db.add(
            SessionRevocation(
                jti=cleaned,
                expires_at=exp,
                revoked_at=now,
            )
        )
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            # Concurrent duplicate insert — already revoked.
    except SessionRevocationStoreUnavailable:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.warning("Session revocation persist failed")
        raise SessionRevocationStoreUnavailable("revocation persist failed") from exc
    except Exception as exc:
        db.rollback()
        logger.warning("Session revocation persist failed")
        raise SessionRevocationStoreUnavailable("revocation persist failed") from exc
    finally:
        db.close()


def is_jti_revoked(
    jti: str,
    *,
    session_factory: SessionFactory | sessionmaker | None = None,
) -> bool:
    """Return True if jti is actively revoked. Raises if store is unavailable."""
    cleaned = (jti or "").strip()
    if not cleaned:
        return False
    factory = session_factory or _default_session_factory
    now = datetime.now(timezone.utc)
    db = factory()
    try:
        row = db.get(SessionRevocation, cleaned)
        if row is None:
            return False
        if _as_utc(row.expires_at) <= now:
            db.delete(row)
            db.commit()
            return False
        return True
    except SQLAlchemyError as exc:
        db.rollback()
        logger.warning("Session revocation lookup failed")
        raise SessionRevocationStoreUnavailable("revocation lookup failed") from exc
    except Exception as exc:
        db.rollback()
        logger.warning("Session revocation lookup failed")
        raise SessionRevocationStoreUnavailable("revocation lookup failed") from exc
    finally:
        db.close()
