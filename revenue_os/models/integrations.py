"""Persisted connector credentials — the "vault" behind credentials_vault.py.

Values are Fernet-encrypted before they ever reach a Column; this table
only ever holds ciphertext, never a raw SMTP password or API token.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, Text

from revenue_os.models.base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ConnectorCredentialRecord(Base):
    __tablename__ = "connector_credentials"

    connector_name = Column(String(64), primary_key=True)
    category = Column(String(32), nullable=False)
    encrypted_config = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)
