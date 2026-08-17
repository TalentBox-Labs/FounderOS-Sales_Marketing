"""Persisted connector credentials — the "vault" behind credentials_vault.py.

Values are Fernet-encrypted before they ever reach a Column; this table
only ever holds ciphertext, never a raw SMTP password or API token.

S4: organization_id scopes tenant-owned credentials. NULL organization_id
rows are GLOBAL_BY_DESIGN legacy/system credentials.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, Text, UniqueConstraint

from revenue_os.models.base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


class ConnectorCredentialRecord(Base):
    __tablename__ = "connector_credentials"

    id = Column(String(36), primary_key=True, default=_new_id)
    organization_id = Column(String(36), nullable=True, index=True)
    connector_name = Column(String(64), nullable=False, index=True)
    category = Column(String(32), nullable=False)
    encrypted_config = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "connector_name",
            name="uq_connector_org_name",
        ),
    )


class OrganizationIntegrationBinding(Base):
    """Trusted inbound integration identity → Organization (S4)."""

    __tablename__ = "organization_integration_bindings"

    id = Column(String(36), primary_key=True, default=_new_id)
    organization_id = Column(String(36), nullable=False, index=True)
    integration_name = Column(String(64), nullable=False, index=True)
    inbound_secret = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "integration_name",
            name="uq_org_integration_name",
        ),
    )
