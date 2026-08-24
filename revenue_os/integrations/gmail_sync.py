"""Gmail inbound-email sync — real OAuth2 + Gmail REST API, read-only.

No scraping, no IMAP guesswork: this is Google's own OAuth2 authorization-
code flow (offline access for a refresh token) against the official Gmail
API (`gmail.readonly` scope). Matched messages are logged to the sending
contact's timeline; unmatched senders are skipped rather than dumped in as
noise — this is about aligning mail to an existing account, not an inbox
importer.

A matched message from a known contact is treated as a reply: it's logged
as EMAIL_REPLY (not EMAIL, which is outbound-only) and any of that
contact's still-pending outreach-sequence steps are cancelled, so a
sequence stops messaging someone who already wrote back.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"
_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
_TIMEOUT = 15
_MAX_MESSAGES_PER_SYNC = 25

CONNECTOR_NAME = "gmail"


def _vault_config() -> dict[str, Any] | None:
    from revenue_os.services.credentials_vault import load_credentials

    return load_credentials(CONNECTOR_NAME)


def build_authorize_url(client_id: str, redirect_uri: str, state: str = "") -> str:
    """Build the Google OAuth2 consent URL. offline+consent so we get a refresh_token."""
    from urllib.parse import urlencode

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": _SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{_AUTH_URL}?{urlencode(params)}"


def exchange_code_for_tokens(code: str, client_id: str, client_secret: str, redirect_uri: str) -> dict[str, Any]:
    """Exchange an authorization code for access + refresh tokens. Never raises."""
    import requests

    try:
        resp = requests.post(
            _TOKEN_URL,
            data={
                "code": code, "client_id": client_id, "client_secret": client_secret,
                "redirect_uri": redirect_uri, "grant_type": "authorization_code",
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return {"ok": True, **resp.json()}
    except Exception as e:
        logger.warning(f"Gmail token exchange failed: {e}")
        return {"ok": False, "error": str(e)}


def _refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> dict[str, Any]:
    import requests

    try:
        resp = requests.post(
            _TOKEN_URL,
            data={
                "client_id": client_id, "client_secret": client_secret,
                "refresh_token": refresh_token, "grant_type": "refresh_token",
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return {"ok": True, **resp.json()}
    except Exception as e:
        logger.warning(f"Gmail token refresh failed: {e}")
        return {"ok": False, "error": str(e)}


_ADDR_RE = re.compile(r"<([^>]+)>")


def _extract_email(from_header: str) -> str:
    """Pull a bare email address out of a From header like 'Name <a@b.com>'."""
    match = _ADDR_RE.search(from_header or "")
    return (match.group(1) if match else (from_header or "")).strip().lower()


def _list_message_ids(access_token: str, max_results: int) -> list[str]:
    import requests

    resp = requests.get(
        f"{_API_BASE}/messages",
        params={"maxResults": max_results, "labelIds": "INBOX"},
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return [m["id"] for m in resp.json().get("messages", [])]


def _get_message(access_token: str, message_id: str) -> dict[str, Any]:
    import requests

    resp = requests.get(
        f"{_API_BASE}/messages/{message_id}",
        params={"format": "metadata", "metadataHeaders": ["From", "Subject", "Date"]},
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def sync_inbox(*, organization_ids: list[str] | None = None) -> dict[str, Any]:
    """Pull recent inbox messages and log matched-contact ones to their timeline.

    ACP-1: commercial contact matching requires explicit organization_ids.
    Without authorized orgs, fail closed (no global Contact email scan).
    """
    from revenue_os.services.acp1_autonomous_boundary import (
        BLOCKED_MISSING_TENANT,
        assert_contact_org,
        log_autonomous_blocked,
        org_uuid_or_none,
    )

    if not organization_ids:
        return log_autonomous_blocked(
            actor="heartbeat",
            action_type="gmail_sync_blocked",
            reason=BLOCKED_MISSING_TENANT,
            detail={"note": "Gmail sync requires explicit autonomous organization scope"},
        )

    config = _vault_config()
    if not config or not config.get("refresh_token"):
        return {"ok": False, "reason": "Gmail is not connected — connect it on the Integrations page."}

    refreshed = _refresh_access_token(config["client_id"], config["client_secret"], config["refresh_token"])
    if not refreshed.get("ok"):
        return {"ok": False, "reason": f"Could not refresh Gmail access token: {refreshed.get('error')}"}
    access_token = refreshed["access_token"]

    try:
        message_ids = _list_message_ids(access_token, _MAX_MESSAGES_PER_SYNC)
    except Exception as e:
        logger.warning(f"Gmail message list failed: {e}")
        return {"ok": False, "reason": str(e)}

    from revenue_os.database import SessionLocal
    from revenue_os.models.activity import Activity, ActivityType, EmailActivity
    from revenue_os.models.contact import Contact
    from revenue_os.services.activity_log import log_agent_action
    from revenue_os.services.outreach_service import cancel_pending_sequence_steps

    org_uuids = [u for u in (org_uuid_or_none(o) for o in organization_ids) if u is not None]
    if not org_uuids:
        return log_autonomous_blocked(
            actor="heartbeat",
            action_type="gmail_sync_blocked",
            reason=BLOCKED_MISSING_TENANT,
            detail={"note": "No valid organization UUIDs for Gmail sync"},
        )

    db = SessionLocal()
    checked = matched = created = sequence_steps_cancelled = 0
    try:
        already_synced = {
            row.message_id for row in
            db.query(EmailActivity.message_id).filter(EmailActivity.message_id.in_(message_ids)).all()
        }
        contacts_by_email = {
            c.email.lower(): c
            for c in db.query(Contact)
            .filter(Contact.email.isnot(None), Contact.organization_id.in_(org_uuids))
            .all()
        }

        for message_id in message_ids:
            checked += 1
            if message_id in already_synced:
                continue
            try:
                message = _get_message(access_token, message_id)
            except Exception as e:
                logger.warning(f"Gmail message fetch failed ({message_id}): {e}")
                continue

            headers = {h["name"]: h["value"] for h in message.get("payload", {}).get("headers", [])}
            sender = _extract_email(headers.get("From", ""))
            contact = contacts_by_email.get(sender)
            if contact is None:
                continue  # not a known in-scope contact — skip rather than dump inbox noise

            org_id = str(contact.organization_id) if contact.organization_id else None
            if org_id is None or not assert_contact_org(contact, org_id):
                continue

            matched += 1
            activity = Activity(
                contact_id=contact.id, activity_type=ActivityType.EMAIL_REPLY, direction="inbound",
                subject=headers.get("Subject", "")[:500], body=message.get("snippet", ""),
                status="completed",
            )
            db.add(activity)
            db.flush()
            db.add(EmailActivity(
                activity_id=activity.id, message_id=message_id,
                from_address=sender,
            ))
            contact.last_contacted_at = datetime.now(timezone.utc)
            db.add(contact)
            sequence_steps_cancelled += cancel_pending_sequence_steps(
                db, contact.id, reason=f"Replied: {headers.get('Subject', '')[:120]}"
            )
            created += 1
            log_agent_action(
                actor="heartbeat",
                action_type="gmail_inbound_matched",
                target_type="contact",
                target_id=str(contact.id),
                organization_id=org_id,
                detail={"message_id": message_id},
            )

        db.commit()
    finally:
        db.close()

    return {
        "ok": True,
        "checked": checked,
        "matched": matched,
        "created": created,
        "organizations": list(organization_ids),
        "sequence_steps_cancelled": sequence_steps_cancelled,
    }
