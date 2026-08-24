"""approval_request_idempotency

Revision ID: f3a8b2c1d4e5
Revises: e8278e1169e6
Create Date: 2026-08-24 11:30:00.000000

"""
from typing import Sequence, Union
import json
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa
from revenue_os.services.approval_request_identity import (
    build_logical_key,
    classify_approval_family,
)


revision: str = "f3a8b2c1d4e5"
down_revision: Union[str, Sequence[str], None] = "e8278e1169e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PENDING_STATUS = "pending"
SUPERSEDED_STATUS = "superseded"


def _parse_payload(payload: object) -> dict:
    if payload is None:
        return {}
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        try:
            value = json.loads(payload)
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            return {}
    return {}


def _lookup_contact_org_id(connection, contact_id: str) -> str | None:
    if not contact_id:
        return None
    try:
        row = connection.execute(
            sa.text("SELECT organization_id FROM contacts WHERE id = :cid"),
            {"cid": contact_id},
        ).fetchone()
    except Exception:
        return None
    if not row:
        return None
    org = row[0]
    return str(org) if org else None


def _derive_identity_for_row(
    connection,
    *,
    action_type: str,
    target_id: str | None,
    payload: object,
) -> tuple[str | None, str | None, str | None]:
    payload_dict = _parse_payload(payload)

    org_id = payload_dict.get("organization_id")
    if org_id is None:
        # Backfill legacy tenant identity from the contact record if possible.
        contact_id = payload_dict.get("contact_id") or target_id
        if contact_id:
            org_id = _lookup_contact_org_id(connection, str(contact_id))

    org_id_str = str(org_id) if org_id else None
    if not org_id_str:
        return None, None, None

    try:
        family = classify_approval_family(action_type)
    except Exception:
        return org_id_str, None, None

    # build_logical_key expects the canonical payload shape (including org_id).
    payload_dict = dict(payload_dict)
    payload_dict["organization_id"] = org_id_str
    try:
        logical_key = build_logical_key(
            approval_family=family,
            organization_id=org_id_str,
            target_id=str(target_id) if target_id else None,
            payload=payload_dict,
        )
    except Exception:
        logical_key = None

    return org_id_str, family, logical_key


def upgrade() -> None:
    op.add_column(
        "approval_requests",
        sa.Column("organization_id", sa.String(length=36), nullable=True),
    )
    op.add_column(
        "approval_requests",
        sa.Column("approval_family", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "approval_requests",
        sa.Column("logical_key", sa.String(length=255), nullable=True),
    )

    connection = op.get_bind()

    rows = connection.execute(
        sa.text(
            "SELECT id, action_type, target_id, payload, status, created_at FROM approval_requests"
        )
    ).fetchall()

    total_rows = len(rows)
    pending_rows = sum(1 for r in rows if r[4] == PENDING_STATUS)

    missing_org_rows = 0
    missing_family_rows = 0
    missing_logical_key_rows = 0
    unresolved_rows = 0

    derived: list[dict[str, object]] = []
    pending_groups: dict[tuple[str, str, str], list[str]] = {}

    for row in rows:
        rid, action_type, target_id, payload, status, created_at = row
        payload_dict = _parse_payload(payload)
        org_missing_in_payload = payload_dict.get("organization_id") is None

        org_id, family, logical_key = _derive_identity_for_row(
            connection,
            action_type=str(action_type),
            target_id=str(target_id) if target_id else None,
            payload=payload,
        )

        if org_missing_in_payload:
            missing_org_rows += 1
        if not family:
            missing_family_rows += 1
        if not logical_key:
            missing_logical_key_rows += 1
        if not org_id or not family or not logical_key:
            unresolved_rows += 1

        derived.append(
            {
                "id": str(rid),
                "status": str(status),
                "created_at": created_at,
                "org_id": org_id,
                "family": family,
                "logical_key": logical_key,
            }
        )

        if status == PENDING_STATUS and org_id and family and logical_key:
            key = (str(org_id), str(family), str(logical_key))
            pending_groups.setdefault(key, []).append(str(rid))

    duplicate_pending_groups = sum(1 for v in pending_groups.values() if len(v) > 1)

    print(
        "APPROVAL_REQUEST_IDEMPOTENCY_MIGRATION_PREFLIGHT "
        f"TOTAL_ROWS={total_rows} PENDING_ROWS={pending_rows} "
        f"MISSING_ORGANIZATION={missing_org_rows} "
        f"MISSING_APPROVAL_FAMILY={missing_family_rows} "
        f"MISSING_LOGICAL_KEY={missing_logical_key_rows} "
        f"DUPLICATE_PENDING_GROUPS={duplicate_pending_groups} "
        f"UNRESOLVABLE_ROWS={unresolved_rows}"
    )

    # Hard contract: abort before any NOT NULL enforcement.
    if unresolved_rows != 0:
        raise RuntimeError(
            "approval_requests identity backfill aborted: "
            f"UNRESOLVABLE_ROWS={unresolved_rows} "
            f"(TOTAL_ROWS={total_rows}, PENDING_ROWS={pending_rows}, "
            f"MISSING_ORGANIZATION={missing_org_rows}, "
            f"MISSING_APPROVAL_FAMILY={missing_family_rows}, "
            f"MISSING_LOGICAL_KEY={missing_logical_key_rows}, "
            f"DUPLICATE_PENDING_GROUPS={duplicate_pending_groups})"
        )

    # 1) Backfill identity columns for all rows first (pending + terminal).
    for d in derived:
        connection.execute(
            sa.text(
                "UPDATE approval_requests SET organization_id = :org_id, "
                "approval_family = :family, logical_key = :logical_key "
                "WHERE id = :id"
            ),
            {
                "org_id": d["org_id"],
                "family": d["family"],
                "logical_key": d["logical_key"],
                "id": d["id"],
            },
        )

    # 2) Resolve duplicate pending identities by deterministically keeping one.
    for (org_id, family, logical_key), ids in pending_groups.items():
        if len(ids) <= 1:
            continue

        group_rows = [d for d in derived if str(d["id"]) in set(ids)]

        def _sort_key(item: dict[str, object]) -> tuple[str, str]:
            created_at = item.get("created_at")
            if created_at is None:
                ts = datetime(9999, 1, 1, tzinfo=timezone.utc)
            else:
                ts = created_at
            return (str(ts), str(item["id"]))

        group_rows_sorted = sorted(group_rows, key=_sort_key)
        canonical_id = str(group_rows_sorted[0]["id"])

        for loser_id in ids:
            if loser_id == canonical_id:
                continue
            connection.execute(
                sa.text(
                    "UPDATE approval_requests SET status = :status, "
                    "decision_note = :note WHERE id = :id"
                ),
                {
                    "status": SUPERSEDED_STATUS,
                    "note": "superseded during idempotency migration (duplicate pending identity)",
                    "id": loser_id,
                },
            )

    op.alter_column("approval_requests", "organization_id", nullable=False)
    op.alter_column("approval_requests", "approval_family", nullable=False)
    op.alter_column("approval_requests", "logical_key", nullable=False)

    op.create_index(
        "ix_approval_requests_org_status",
        "approval_requests",
        ["organization_id", "status"],
    )
    op.create_index(
        "uq_approval_requests_pending_identity",
        "approval_requests",
        ["organization_id", "approval_family", "logical_key"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
        sqlite_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    op.drop_index("uq_approval_requests_pending_identity", table_name="approval_requests")
    op.drop_index("ix_approval_requests_org_status", table_name="approval_requests")
    op.drop_column("approval_requests", "logical_key")
    op.drop_column("approval_requests", "approval_family")
    op.drop_column("approval_requests", "organization_id")
