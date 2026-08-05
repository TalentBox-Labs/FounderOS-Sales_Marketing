"""Encrypted credentials vault for third-party connector configs.

Values are encrypted with a key derived from SECRET_KEY before they ever
reach the database — this protects a DB dump/backup from casually exposing
an SMTP password or API token. It is NOT protection against someone who
already has SECRET_KEY and DB access (they could derive the same key) —
that's an already-fully-trusted position in this app's threat model.
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Static, versioned salt — not a secret on its own. The actual key material
# is SECRET_KEY, which is required to be a strong random value (see config.py).
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


def save_credentials(connector_name: str, category: str, config: dict[str, Any]) -> None:
    """Encrypt and persist a connector's config."""
    ciphertext = _get_fernet().encrypt(json.dumps(config).encode()).decode()
    db = _vault_db()
    if db is None:
        raise RuntimeError("Database unavailable — cannot save credentials")
    try:
        from revenue_os.models.integrations import ConnectorCredentialRecord

        row = db.get(ConnectorCredentialRecord, connector_name)
        if row is None:
            row = ConnectorCredentialRecord(connector_name=connector_name)
            db.add(row)
        row.category = category
        row.encrypted_config = ciphertext
        db.commit()
    finally:
        db.close()


def load_credentials(connector_name: str) -> dict[str, Any] | None:
    """Decrypt and return a connector's config, or None if never configured."""
    db = _vault_db()
    if db is None:
        return None
    try:
        from revenue_os.models.integrations import ConnectorCredentialRecord

        row = db.get(ConnectorCredentialRecord, connector_name)
        if row is None:
            return None
        plaintext = _get_fernet().decrypt(row.encrypted_config.encode())
        return json.loads(plaintext)
    except Exception as e:
        logger.warning(f"Could not decrypt credentials for {connector_name}: {e}")
        return None
    finally:
        db.close()


def delete_credentials(connector_name: str) -> bool:
    db = _vault_db()
    if db is None:
        return False
    try:
        from revenue_os.models.integrations import ConnectorCredentialRecord

        row = db.get(ConnectorCredentialRecord, connector_name)
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
        tenant_id=config.get("tenant_id", ""), access_token=config.get("access_token", ""),
    )


_HYDRATORS = {
    "email_smtp": _hydrate_email,
    "slack": _hydrate_slack,
    "whatsapp": _hydrate_whatsapp,
    "google_calendar": _hydrate_google_calendar,
    "outlook_calendar": _hydrate_outlook_calendar,
}


def hydrate_all_connectors() -> None:
    """Restore every vaulted connector's in-memory config after a restart.

    Without this, a founder would have to re-enter SMTP passwords, Slack
    webhooks, etc. after every deploy — the vault would just be a slower
    way to lose the same state the old in-memory-only classes already lost.
    """
    for name, hydrate in _HYDRATORS.items():
        config = load_credentials(name)
        if not config:
            continue
        try:
            hydrate(config)
            logger.info(f"Connector hydrated from vault: {name}")
        except Exception as e:
            logger.warning(f"Connector hydration failed ({name}): {e}")


def list_configured_connectors() -> dict[str, dict[str, Any]]:
    """Map of connector_name -> {category, updated_at} for every vaulted connector.

    Status/listing only — never returns decrypted values.
    """
    db = _vault_db()
    if db is None:
        return {}
    try:
        from revenue_os.models.integrations import ConnectorCredentialRecord

        return {
            row.connector_name: {
                "category": row.category,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            }
            for row in db.query(ConnectorCredentialRecord).all()
        }
    finally:
        db.close()
