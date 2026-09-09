"""Durable HUMAN session JTI revocation — DB-backed, fail-closed."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import revenue_os.models  # noqa: F401 — register tables
import revenue_os.services.tenant_resolution as tenant_resolution_mod
import runner_api_routers.identity as identity_mod
from revenue_os.auth import create_access_token, hash_password
from revenue_os.config import settings
from revenue_os.models.base import Base
from revenue_os.models.organization import (
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationStatus,
)
from revenue_os.models.session_revocation import SessionRevocation
from revenue_os.models.user import User
from revenue_os.services.session_revocation import (
    SessionRevocationStoreUnavailable,
    is_jti_revoked,
    revoke_jti,
)
from runner_api import app

_EMAIL = "revoke-owner@example.com"
_PASSWORD = "correct-horse-battery"
_NAME = "Revoke Owner"
_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_ORG_M1 = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_ORG_M2 = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")


@pytest.fixture(autouse=True)
def _reset_identity_ephemeral() -> None:
    identity_mod._revoked_jtis.clear()
    identity_mod._login_failures.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def revoke_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> sessionmaker:
    engine = create_engine(f"sqlite:///{tmp_path / 'durable_revoke.db'}")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    monkeypatch.setattr(identity_mod, "SessionLocal", session_factory)
    monkeypatch.setattr(tenant_resolution_mod, "SessionLocal", session_factory)
    return session_factory


@pytest.fixture
def owner_user(revoke_db: sessionmaker) -> User:
    db = revoke_db()
    try:
        user = User(
            email=_EMAIL,
            hashed_password=hash_password(_PASSWORD),
            full_name=_NAME,
            role="owner",
            is_active=1,
        )
        db.add(user)
        db.flush()
        org = Organization(
            id=_ORG_A, name="Revoke Org", slug="revoke-org", status=OrganizationStatus.ACTIVE
        )
        db.add(org)
        db.flush()
        db.add(
            OrganizationMembership(
                user_id=user.id,
                organization_id=org.id,
                role="owner",
                status=MembershipStatus.ACTIVE,
            )
        )
        db.commit()
        db.refresh(user)
        db.expunge(user)
        return user
    finally:
        db.close()


def _login(client: TestClient) -> None:
    r = client.post(
        "/api/v1/identity/login",
        json={"email": _EMAIL, "password": _PASSWORD},
    )
    assert r.status_code == 200, r.text


def _cookie_token(client: TestClient) -> str:
    raw = client.cookies.get(identity_mod.IDENTITY_COOKIE)
    assert raw, "expected identity cookie"
    return raw


def _decode(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])


def test_t1_issued_human_token_works_before_revocation(
    client: TestClient, owner_user: User
) -> None:
    _login(client)
    me = client.get("/api/v1/identity/me")
    assert me.status_code == 200
    identity = me.json()["identity"]
    assert identity["is_human"] is True
    assert identity["principal_kind"] == "HUMAN"
    assert identity["email"] == _EMAIL


def test_t2_logout_persists_revocation(
    client: TestClient, owner_user: User, revoke_db: sessionmaker
) -> None:
    _login(client)
    token = _cookie_token(client)
    jti = _decode(token)["jti"]
    out = client.post("/api/v1/identity/logout")
    assert out.status_code == 200
    db = revoke_db()
    try:
        row = db.get(SessionRevocation, jti)
        assert row is not None
        assert row.expires_at is not None
    finally:
        db.close()


def test_t3_same_token_rejected_after_logout(
    client: TestClient, owner_user: User
) -> None:
    _login(client)
    token = _cookie_token(client)
    assert client.post("/api/v1/identity/logout").status_code == 200
    # Retain the pre-logout JWT despite cookie clear.
    client.cookies.set(identity_mod.IDENTITY_COOKIE, token)
    me = client.get("/api/v1/identity/me").json()["identity"]
    assert me["principal_kind"] == "ANONYMOUS"
    assert me["is_human"] is False


def test_t4_revocation_survives_process_local_reset(
    client: TestClient, owner_user: User, revoke_db: sessionmaker
) -> None:
    _login(client)
    token = _cookie_token(client)
    assert client.post("/api/v1/identity/logout").status_code == 200
    identity_mod._revoked_jtis.clear()
    # New app client / request path; same DB-backed SessionLocal.
    client2 = TestClient(app)
    client2.cookies.set(identity_mod.IDENTITY_COOKIE, token)
    me = client2.get("/api/v1/identity/me").json()["identity"]
    assert me["principal_kind"] == "ANONYMOUS"
    assert is_jti_revoked(_decode(token)["jti"], session_factory=revoke_db) is True


def test_t5_cross_context_same_database_observes_revocation(
    revoke_db: sessionmaker, owner_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Context A and B share one engine via two independent sessionmakers.
    probe = revoke_db()
    try:
        bind = probe.get_bind()
    finally:
        probe.close()
    factory_a = sessionmaker(bind=bind)
    factory_b = sessionmaker(bind=bind)

    jti = "cross-context-jti-001"
    expires = datetime.now(timezone.utc) + timedelta(hours=1)
    revoke_jti(jti, expires, session_factory=factory_a)
    assert is_jti_revoked(jti, session_factory=factory_b) is True

    monkeypatch.setattr(identity_mod, "SessionLocal", factory_b)
    token = create_access_token(
        {
            "sub": str(owner_user.id),
            "email": owner_user.email,
            "name": owner_user.full_name,
            "role": "owner",
            "kind": "HUMAN",
            "jti": jti,
            "iss": "founder_os_runner_api",
        }
    )
    client_b = TestClient(app)
    client_b.cookies.set(identity_mod.IDENTITY_COOKIE, token)
    me = client_b.get("/api/v1/identity/me").json()["identity"]
    assert me["principal_kind"] == "ANONYMOUS"


def test_t6_duplicate_logout_is_safe(client: TestClient, owner_user: User) -> None:
    _login(client)
    token = _cookie_token(client)
    assert client.post("/api/v1/identity/logout").status_code == 200
    client.cookies.set(identity_mod.IDENTITY_COOKIE, token)
    assert client.post("/api/v1/identity/logout").status_code == 200
    client.cookies.set(identity_mod.IDENTITY_COOKIE, token)
    me = client.get("/api/v1/identity/me").json()["identity"]
    assert me["principal_kind"] == "ANONYMOUS"


def test_t7_expired_revocation_does_not_block_future_tokens(
    revoke_db: sessionmaker, owner_user: User, client: TestClient
) -> None:
    stale_jti = "expired-jti-should-not-block"
    revoke_jti(
        stale_jti,
        datetime.now(timezone.utc) - timedelta(minutes=5),
        session_factory=revoke_db,
    )
    assert is_jti_revoked(stale_jti, session_factory=revoke_db) is False
    _login(client)
    me = client.get("/api/v1/identity/me").json()["identity"]
    assert me["is_human"] is True
    assert me["principal_kind"] == "HUMAN"


def test_t8_malformed_token_fails_closed(client: TestClient, owner_user: User) -> None:
    client.cookies.set(identity_mod.IDENTITY_COOKIE, "not.a.jwt")
    me = client.get("/api/v1/identity/me").json()["identity"]
    assert me["principal_kind"] == "ANONYMOUS"
    assert me["is_human"] is False


def test_t9_service_api_key_cannot_become_human(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RUNNER_API_KEY", "durable-revoke-service-key")
    monkeypatch.delenv("FOUNDER_OS_OPERATOR_NAME", raising=False)
    headers = {"Authorization": "Bearer durable-revoke-service-key"}
    me = client.get("/api/v1/identity/me", headers=headers).json()["identity"]
    assert me["principal_kind"] == "SERVICE"
    assert me["is_human"] is False
    assert me["auth_method"] == "api_key"


def test_t10_service_api_key_cannot_establish_tenant(
    client: TestClient, revoke_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RUNNER_API_KEY", "durable-revoke-service-key")
    headers = {"Authorization": "Bearer durable-revoke-service-key"}
    r = client.get("/api/v1/tenant/me", headers=headers)
    assert r.status_code == 200
    assert r.json().get("tenant") is None


def test_t11_anonymous_fails_closed_where_human_required(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_REQUIRE_LOGIN", "1")
    monkeypatch.delenv("FOUNDER_OS_OPERATOR_NAME", raising=False)
    r = client.get("/cockpit", follow_redirects=False)
    assert r.status_code == 303
    assert "/login" in r.headers["location"]


def test_t12_zero_membership_fails_closed(
    client: TestClient, revoke_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = revoke_db()
    try:
        user = User(
            email="nomember@example.com",
            hashed_password=hash_password(_PASSWORD),
            full_name=_NAME,
            role="owner",
            is_active=1,
        )
        db.add(user)
        db.commit()
    finally:
        db.close()
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _NAME)
    r = client.post(
        "/api/v1/identity/login",
        json={"email": "nomember@example.com", "password": _PASSWORD},
    )
    assert r.status_code == 200
    tenant = client.get("/api/v1/tenant/me")
    assert tenant.status_code == 200
    assert tenant.json().get("tenant") is None
    require = client.get("/api/v1/tenant/require")
    assert require.status_code == 403


def test_t13_multi_org_without_selected_tenant_fails_closed(
    client: TestClient, revoke_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = revoke_db()
    try:
        user = User(
            email="multi@example.com",
            hashed_password=hash_password(_PASSWORD),
            full_name=_NAME,
            role="owner",
            is_active=1,
        )
        db.add(user)
        db.flush()
        org1 = Organization(
            id=_ORG_M1,
            name="M1",
            slug="m1",
            status=OrganizationStatus.ACTIVE,
        )
        db.add(org1)
        db.flush()
        org2 = Organization(
            id=_ORG_M2,
            name="M2",
            slug="m2",
            status=OrganizationStatus.ACTIVE,
        )
        db.add(org2)
        db.flush()
        db.add(
            OrganizationMembership(
                user_id=user.id,
                organization_id=org1.id,
                role="owner",
                status=MembershipStatus.ACTIVE,
            )
        )
        db.add(
            OrganizationMembership(
                user_id=user.id,
                organization_id=org2.id,
                role="owner",
                status=MembershipStatus.ACTIVE,
            )
        )
        db.commit()
    finally:
        db.close()
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _NAME)
    r = client.post(
        "/api/v1/identity/login",
        json={"email": "multi@example.com", "password": _PASSWORD},
    )
    assert r.status_code == 200
    # Login must not auto-select when multi-org; tenant/me must fail closed.
    client.cookies.delete(tenant_resolution_mod.ORGANIZATION_COOKIE)
    tenant = client.get("/api/v1/tenant/me")
    assert tenant.status_code in {403, 503}


def test_t15_secret_key_behavior_unchanged(
    client: TestClient, owner_user: User
) -> None:
    before = settings.SECRET_KEY
    _login(client)
    token = _cookie_token(client)
    payload = jwt.decode(token, before, algorithms=["HS256"])
    assert payload.get("jti")
    assert settings.SECRET_KEY == before


def test_t16_logout_clears_human_cookie(client: TestClient, owner_user: User) -> None:
    _login(client)
    assert client.cookies.get(identity_mod.IDENTITY_COOKIE)
    out = client.post("/api/v1/identity/logout")
    assert out.status_code == 200
    # Starlette TestClient may retain jar entries; Set-Cookie delete must be present.
    set_cookie_headers = out.headers.get_list("set-cookie") if hasattr(out.headers, "get_list") else [
        v for k, v in out.headers.multi_items() if k.lower() == "set-cookie"
    ]
    joined = " ".join(set_cookie_headers).lower()
    assert identity_mod.IDENTITY_COOKIE.lower() in joined
    assert "max-age=0" in joined or "expires=" in joined


def test_t17_identity_me_rejects_revoked_retained_token(
    client: TestClient, owner_user: User
) -> None:
    _login(client)
    token = _cookie_token(client)
    assert client.post("/api/v1/identity/logout").status_code == 200
    client.cookies.set(identity_mod.IDENTITY_COOKIE, token)
    me = client.get("/api/v1/identity/me")
    assert me.status_code == 200
    assert me.json()["identity"]["principal_kind"] == "ANONYMOUS"


def test_t18_db_failure_during_revocation_check_fails_closed(
    client: TestClient, owner_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _login(client)
    token = _cookie_token(client)

    def _boom(*_a, **_k):
        raise SessionRevocationStoreUnavailable("forced")

    monkeypatch.setattr(identity_mod, "is_jti_revoked", _boom)
    client.cookies.set(identity_mod.IDENTITY_COOKIE, token)
    me = client.get("/api/v1/identity/me").json()["identity"]
    assert me["principal_kind"] == "ANONYMOUS"
    assert me["is_human"] is False


def test_t18b_db_failure_during_logout_does_not_clear_cookie(
    client: TestClient, owner_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _login(client)
    token = _cookie_token(client)

    def _boom(*_a, **_k):
        raise SessionRevocationStoreUnavailable("forced")

    monkeypatch.setattr(identity_mod, "revoke_jti", _boom)
    out = client.post("/api/v1/identity/logout")
    assert out.status_code == 503
    set_cookie_headers = [
        v for k, v in out.headers.multi_items() if k.lower() == "set-cookie"
    ]
    # Must not clear identity cookie when durable revoke failed.
    assert not any(
        identity_mod.IDENTITY_COOKIE.lower() in h.lower()
        and ("max-age=0" in h.lower() or "expires=" in h.lower())
        for h in set_cookie_headers
    )
    # Without a durable revoke row, retained token still authenticates.
    client.cookies.set(identity_mod.IDENTITY_COOKIE, token)
    me = client.get("/api/v1/identity/me").json()["identity"]
    assert me["principal_kind"] == "HUMAN"


def test_token_without_jti_does_not_crash(
    client: TestClient, owner_user: User, revoke_db: sessionmaker
) -> None:
    token = create_access_token(
        {
            "sub": str(owner_user.id),
            "email": owner_user.email,
            "name": owner_user.full_name,
            "role": "owner",
            "kind": "HUMAN",
            "iss": "founder_os_runner_api",
        }
    )
    assert "jti" not in jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    client.cookies.set(identity_mod.IDENTITY_COOKIE, token)
    me = client.get("/api/v1/identity/me").json()["identity"]
    assert me["principal_kind"] == "HUMAN"


def test_process_local_revoked_jtis_not_authoritative(
    client: TestClient, owner_user: User
) -> None:
    """Auth must not depend on the in-memory shim."""
    _login(client)
    token = _cookie_token(client)
    jti = _decode(token)["jti"]
    identity_mod._revoked_jtis.add(jti)
    me = client.get("/api/v1/identity/me").json()["identity"]
    assert me["principal_kind"] == "HUMAN"
    assert client.post("/api/v1/identity/logout").status_code == 200
    identity_mod._revoked_jtis.clear()
    client.cookies.set(identity_mod.IDENTITY_COOKIE, token)
    me2 = client.get("/api/v1/identity/me").json()["identity"]
    assert me2["principal_kind"] == "ANONYMOUS"
