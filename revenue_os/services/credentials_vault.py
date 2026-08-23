"""Encrypted credentials vault for third-party connector configs.

S4: credentials resolve under Organization ownership when organization_id is supplied.
Legacy rows with organization_id=NULL are GLOBAL_BY_DESIGN and must not satisfy
tenant-owned requests unless explicitly allowed via allow_global_fallback.
"""

from __future__ import annotations

import base64
import json
import logging
import uuid as uuid_lib
from typing import Any

logger = logging.getLogger(__name__)

_VAULT_SALT = b"revenue-os-connector-vault-v1"
_fernet = None


def _get_fernet():
    global _fernet
    if _fernet is None:
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

        from revenue_os.config import settings

        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=_VAULT_SALT, iterations=200_000)
        key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
        _fernet = Fernet(key)
    return _fernet


def _vault_db():
    try:
        from revenue_os.database import SessionLocal

        return SessionLocal()
    except Exception:
        return None


def _normalize_org_id(organization_id: str | None) -> str | None:
    if organization_id is None:
        return None
    value = str(organization_id).strip()
    if not value:
        return None
    try:
        return str(uuid_lib.UUID(value))
    except ValueError:
        return None


def _find_credential_row(db, connector_name: str, organization_id: str | None):  # noqa: ANN001
    from revenue_os.models.integrations import ConnectorCredentialRecord

    org = _normalize_org_id(organization_id)
    query = db.query(ConnectorCredentialRecord).filter(
        ConnectorCredentialRecord.connector_name == connector_name
    )
    if org is None:
        return query.filter(ConnectorCredentialRecord.organization_id.is_(None)).first()
    return query.filter(ConnectorCredentialRecord.organization_id == org).first()


def save_credentials(
    connector_name: str,
    category: str,
    config: dict[str, Any],
    *,
    organization_id: str | None = None,
) -> None:
    """Encrypt and persist a connector's config under organization scope."""
    ciphertext = _get_fernet().encrypt(json.dumps(config).encode()).decode()
    db = _vault_db()
    if db is None:
        raise RuntimeError("Database unavailable — cannot save credentials")
    try:
        from revenue_os.models.integrations import ConnectorCredentialRecord

        row = _find_credential_row(db, connector_name, organization_id)
        if row is None:
            row = ConnectorCredentialRecord(
                connector_name=connector_name,
                organization_id=_normalize_org_id(organization_id),
            )
            db.add(row)
        row.category = category
        row.encrypted_config = ciphertext
        db.commit()
    finally:
        db.close()


def load_credentials(
    connector_name: str,
    *,
    organization_id: str | None = None,
    allow_global_fallback: bool = False,
) -> dict[str, Any] | None:
    """Decrypt connector config for org scope. No cross-org or unsafe global fallback by default."""
    db = _vault_db()
    if db is None:
        return None
    try:
        row = _find_credential_row(db, connector_name, organization_id)
        if row is None and organization_id is not None and allow_global_fallback:
            row = _find_credential_row(db, connector_name, None)
        if row is None:
            return None
        plaintext = _get_fernet().decrypt(row.encrypted_config.encode())
        return json.loads(plaintext)
    except Exception as e:
        logger.warning("Could not decrypt credentials for %s: %s", connector_name, e)
        return None
    finally:
        db.close()


def delete_credentials(
    connector_name: str,
    *,
    organization_id: str | None = None,
) -> bool:
    db = _vault_db()
    if db is None:
        return False
    try:
        row = _find_credential_row(db, connector_name, organization_id)
        if row is None:
            return False
        db.delete(row)
        db.commit()
        return True
    finally:
        db.close()


def _hydrate_email(config: dict[str, Any]) -> None:
    from revenue_os.integrations.email import EmailNotifier

    EmailNotifier.configure_smtp(config)


def _hydrate_slack(config: dict[str, Any]) -> None:
    from revenue_os.integrations.slack import SlackNotifier

    SlackNotifier.set_webhook_url(config.get("webhook_url", ""))


def _hydrate_whatsapp(config: dict[str, Any]) -> None:
    from revenue_os.integrations.whatsapp import WhatsAppClient

    WhatsAppClient.configure(
        api_key=config.get("api_key", ""),
        phone_number_id=config.get("phone_number_id", ""),
        business_account_id=config.get("business_account_id", ""),
    )


def _hydrate_google_calendar(config: dict[str, Any]) -> None:
    from revenue_os.integrations.calendar import GoogleCalendarClient

    GoogleCalendarClient.configure(config)


def _hydrate_outlook_calendar(config: dict[str, Any]) -> None:
    from revenue_os.integrations.calendar import OutlookCalendarClient

    OutlookCalendarClient.configure(
        tenant_id=config.get("tenant_id", ""),
        access_token=config.get("access_token", ""),
    )


_HYDRATORS = {
    "email_smtp": _hydrate_email,
    "slack": _hydrate_slack,
    "whatsapp": _hydrate_whatsapp,
    "google_calendar": _hydrate_google_calendar,
    "outlook_calendar": _hydrate_outlook_calendar,
}


def hydrate_all_connectors() -> None:
    """Restore GLOBAL_BY_DESIGN legacy in-memory config after restart."""
    for name, hydrate in _HYDRATORS.items():
        config = load_credentials(name, organization_id=None)
        if not config:
            continue
        try:
            hydrate(config)
            logger.info("Connector hydrated from vault: %s", name)
        except Exception as e:
            logger.warning("Connector hydration failed (%s): %s", name, e)


def list_configured_connectors(*, organization_id: str | None = None) -> dict[str, dict[str, Any]]:
    """Map connector_name -> metadata; never returns decrypted values."""
    db = _vault_db()
    if db is None:
        return {}
    try:
        from revenue_os.models.integrations import ConnectorCredentialRecord

        query = db.query(ConnectorCredentialRecord)
        org = _normalize_org_id(organization_id)
        if org is not None:
            query = query.filter(ConnectorCredentialRecord.organization_id == org)
        else:
            query = query.filter(ConnectorCredentialRecord.organization_id.is_(None))

        return {
            row.connector_name: {
                "category": row.category,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                "organization_id": row.organization_id,
            }
            for row in query.all()
        }
    finally:
        db.close()
