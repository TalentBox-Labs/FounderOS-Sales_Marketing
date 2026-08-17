"""SaaS S2 — TenantContext = IdentityContext + Organization membership."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from revenue_os.services.identity_context import (
    IdentityContext,
    MVP_ROLES,
    PrincipalKind,
    normalize_role,
)


@dataclass(frozen=True)
class TenantContext:
    identity: IdentityContext
    organization_id: str
    organization_name: str
    organization_slug: str
    membership_id: str
    membership_role: str
    membership_status: str

    @property
    def is_human(self) -> bool:
        return self.identity.is_human

    @property
    def principal_kind(self) -> PrincipalKind:
        return self.identity.principal_kind

    @property
    def user_id(self) -> str | None:
        return self.identity.user_id

    def as_public_dict(self) -> dict[str, str | bool | None]:
        base = self.identity.as_public_dict()
        base.update(
            {
                "organization_id": self.organization_id,
                "organization_name": self.organization_name,
                "organization_slug": self.organization_slug,
                "membership_id": self.membership_id,
                "membership_role": self.membership_role,
                "membership_status": self.membership_status,
            }
        )
        return base


def membership_role_allows_mutation(role: str | None) -> bool:
    """VIEWER is read-only; OWNER/ADMIN/MEMBER may mutate (subject to HUMAN_ONLY)."""
    normalized = normalize_role(role)
    return normalized in {"owner", "admin", "member"}


def membership_role_allows_admin(role: str | None) -> bool:
    normalized = normalize_role(role)
    return normalized in {"owner", "admin"}


def parse_org_uuid(value: str | None) -> UUID | None:
    if not value:
        return None
    try:
        return UUID(str(value))
    except ValueError:
        return None


def assert_valid_membership_role(role: str) -> str:
    normalized = normalize_role(role)
    if normalized not in MVP_ROLES:
        return "member"
    return normalized
