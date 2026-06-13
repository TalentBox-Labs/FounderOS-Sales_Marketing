from __future__ import annotations

import base64
import json
import os
import re
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from revenue_os.config import settings

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


def _get_credentials():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds_path = settings.GMAIL_CREDENTIALS_PATH
    token_path = os.path.join(
        os.path.dirname(creds_path) if creds_path else ".", "gmail_token.json"
    )

    creds = None
    if os.path.exists(token_path):
        with open(token_path) as f:
            creds = Credentials.from_authorized_user_info(json.load(f), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path or not os.path.exists(creds_path):
                raise FileNotFoundError(
                    f"Gmail credentials not found at {creds_path}. "
                    "Set GMAIL_CREDENTIALS_PATH in .env"
                )
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return creds


def _get_service():
    from googleapiclient.discovery import build

    creds = _get_credentials()
    return build("gmail", "v1", credentials=creds)


def inject_tracking(body_html: str, activity_id: str, domain: str) -> str:
    tracking_pixel = (
        f'<img src="{domain}/track/open/{activity_id}.png" '
        f'width="1" height="1" style="display:none" alt="" />'
    )

    def wrap_link(match: re.Match) -> str:
        original = match.group(0)
        url = match.group(1) or match.group(2)
        if not url:
            return original
        wrapped = f"{domain}/track/click/{activity_id}?url={url}"
        return match.group(0).replace(url, wrapped)

    body_html = re.sub(
        r'href=["\'](https?://[^"\']+)["\']', wrap_link, body_html
    )
    body_html += tracking_pixel
    return body_html


def send_email(
    to: str,
    subject: str,
    body_text: str,
    body_html: str | None = None,
    thread_id: str | None = None,
) -> dict[str, Any]:
    service = _get_service()

    message = MIMEMultipart("alternative")
    message["To"] = to
    message["Subject"] = subject

    if body_html:
        message.attach(MIMEText(body_text, "plain"))
        message.attach(MIMEText(body_html, "html"))
    else:
        message.attach(MIMEText(body_text, "plain"))

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    body: dict[str, Any] = {"raw": raw}
    if thread_id:
        body["threadId"] = thread_id

    sent = (
        service.users()
        .messages()
        .send(userId="me", body=body)
        .execute()
    )

    return {
        "message_id": sent.get("id"),
        "thread_id": sent.get("threadId"),
        "label_ids": sent.get("labelIds", []),
    }


def fetch_thread(thread_id: str) -> list[dict[str, Any]]:
    service = _get_service()
    thread = (
        service.users()
        .threads()
        .get(userId="me", id=thread_id)
        .execute()
    )

    messages = []
    for msg in thread.get("messages", []):
        payload = msg.get("payload", {})
        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
        messages.append(
            {
                "id": msg.get("id"),
                "thread_id": thread_id,
                "from": headers.get("From"),
                "to": headers.get("To"),
                "subject": headers.get("Subject"),
                "date": headers.get("Date"),
                "snippet": msg.get("snippet", ""),
            }
        )
    return messages


def fetch_new_messages(
    after: datetime | None = None,
    known_emails: set[str] | None = None,
    max_results: int = 50,
) -> list[dict[str, Any]]:
    service = _get_service()

    query_parts = []
    if after:
        query_parts.append(f"after:{int(after.timestamp())}")
    if known_emails:
        email_query = " OR ".join(
            f"from:{e}" for e in known_emails
        )
        query_parts.append(f"({email_query})")

    query = " ".join(query_parts) if query_parts else ""
    result = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )

    messages = []
    for msg_ref in result.get("messages", []):
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_ref["id"])
            .execute()
        )
        payload = msg.get("payload", {})
        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
        messages.append(
            {
                "id": msg.get("id"),
                "thread_id": msg.get("threadId"),
                "from": headers.get("From"),
                "to": headers.get("To"),
                "subject": headers.get("Subject"),
                "date": headers.get("Date"),
                "snippet": msg.get("snippet", ""),
            }
        )

    return messages
