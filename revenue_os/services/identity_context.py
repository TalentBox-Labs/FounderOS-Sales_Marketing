"""Canonical request identity for primary runner_api (SaaS S1).

Outer wrapper only. No tenant_id / organization_id / workspace_id.
Future TenantContext = IdentityContext + organization context.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.tools.editorial_approval import is_human_approver

MVP_ROLES: tuple[str, ...] = ("owner", "admin", "member", "viewer")

ROLE_SEMANTICS: dict[str, str] = {
    "owner": "Instance bootstrap human; full future tenant authority (S2).",
    "admin": "Privileged operator; not yet endpoint-enforced (S2).",
    "member": "Standard operator; default User.role; HUMAN_ONLY gates still apply.",
    "viewer": "Read-intended; mutation RBAC deferred to S2. HUMAN_ONLY still applies.",
}


class PrincipalKind(str, Enum):
    HUMAN = "HUMAN"
    SERVICE = "SERVICE"
    AGENT = "AGENT"
    AI = "AI"
    ANONYMOUS = "ANONYMOUS"


class AuthMethod(str, Enum):
    SESSION = "session"
    LEGACY_OPERATOR_ENV = "legacy_operator_env"
    API_KEY = "api_key"
    NONE = "none"


class ApiKeyUsage(str, Enum):
    """Classification of RUNNER_API_KEY (SaaS S1)."""

    HUMAN_AUTH = "HUMAN_AUTH"
    SERVICE_AUTH = "SERVICE_AUTH"
    LEGACY_INTERNAL = "LEGACY_INTERNAL"
    TEST_ONLY = "TEST_ONLY"


# Canonical product classification: service/internal, never human authority.
RUNNER_API_KEY_USAGE = (ApiKeyUsage.SERVICE_AUTH, ApiKeyUsage.LEGACY_INTERNAL)


@dataclass(frozen=True)
class IdentityContext:
    principal_kind: PrincipalKind
    auth_method: AuthMethod
    is_human: bool
    user_id: str | None = None
    email: str | None = None
    display_name: str | None = None
    role: str | None = None
    request_id: str | None = None

    def as_public_dict(self) -> dict[str, str | bool | None]:
        return {
            "principal_kind": self.principal_kind.value,
            "auth_method": self.auth_method.value,
            "is_human": self.is_human,
            "user_id": self.user_id,
            "email": self.email,
            "display_name": self.display_name,
            "role": self.role,
        }


def normalize_role(value: str | None) -> str:
    role = (value or "member").strip().lower()
    if role not in MVP_ROLES:
        return "member"
    return role


def anonymous_identity() -> IdentityContext:
    return IdentityContext(
        principal_kind=PrincipalKind.ANONYMOUS,
        auth_method=AuthMethod.NONE,
        is_human=False,
    )


def service_identity() -> IdentityContext:
    return IdentityContext(
        principal_kind=PrincipalKind.SERVICE,
        auth_method=AuthMethod.API_KEY,
        is_human=False,
        display_name="runner_api_service",
    )


def classify_actor_label(name: str) -> PrincipalKind:
    """Classify a free-text actor label. Never treat API credentials as human."""
    token = (name or "").strip().lower()
    if not token:
        return PrincipalKind.ANONYMOUS
    if token in {"ai", "llm", "gpt", "claude", "openai"} or token.startswith("ai:"):
        return PrincipalKind.AI
    if token in {
        "agent",
        "bot",
        "automation",
        "crewai",
        "openclaw",
        "auto",
        "machine",
    } or token.startswith("agent:") or token.startswith("bot:"):
        return PrincipalKind.AGENT
    if token in {"system", "service", "runner", "runner_api_service"}:
        return PrincipalKind.SERVICE
    if is_human_approver(name):
        return PrincipalKind.HUMAN
    return PrincipalKind.ANONYMOUS


def bind_requested_by(ctx: IdentityContext) -> str:
    """Trusted requested_by for frozen APIs. Non-humans never bind."""
    kind = ctx.principal_kind
    if kind is PrincipalKind.HUMAN:
        name = (ctx.display_name or "").strip()
        if not ctx.is_human or not is_human_approver(name):
            raise PermissionError("Human IdentityContext required to bind requested_by")
        return name
    if kind is PrincipalKind.SERVICE:
        raise PermissionError("SERVICE identity cannot bind human requested_by")
    if kind is PrincipalKind.AGENT:
        raise PermissionError("AGENT identity cannot bind human requested_by")
    if kind is PrincipalKind.AI:
        raise PermissionError("AI identity cannot bind human requested_by")
    if kind is PrincipalKind.ANONYMOUS:
        raise PermissionError("Anonymous identity cannot bind requested_by")
    unused: PrincipalKind = kind
    raise AssertionError(f"unhandled principal kind: {unused}")
