"""approval_request_idempotency

Revision ID: f3a8b2c1d4e5
Revises: e8278e1169e6
Create Date: 2026-08-24 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3a8b2c1d4e5"
down_revision: Union[str, Sequence[str], None] = "e8278e1169e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _backfill_identities(connection) -> None:
    from revenue_os.services.approval_request_identity import backfill_identity_from_row

    rows = connection.execute(
        sa.text(
            "SELECT id, action_type, target_id, payload, status FROM approval_requests"
        )
    ).fetchall()
    seen_pending: set[tuple[str, str, str]] = set()
    for row in rows:
        rid, action_type, target_id, payload, status = row
        org_id, family, logical_key = backfill_identity_from_row(
            action_type, target_id, payload
        )
        if not org_id:
            continue
        if status == "pending" and family and logical_key:
            key = (org_id, family, logical_key)
            if key in seen_pending:
                connection.execute(
                    sa.text(
                        "UPDATE approval_requests SET status = 'superseded', "
                        "decision_note = 'superseded during idempotency migration' "
                        "WHERE id = :id"
                    ),
                    {"id": rid},
                )
                continue
            seen_pending.add(key)
        connection.execute(
            sa.text(
                "UPDATE approval_requests SET organization_id = :org_id, "
                "approval_family = :family, logical_key = :logical_key "
                "WHERE id = :id"
            ),
            {
                "org_id": org_id,
                "family": family,
                "logical_key": logical_key,
                "id": rid,
            },
        )


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
    _backfill_identities(connection)

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
