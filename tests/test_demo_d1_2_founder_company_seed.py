"""DEMO-D1.2 — Founder demo Contact–Company relationship seed."""

from __future__ import annotations

import importlib.util
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import revenue_os.models  # noqa: F401
from revenue_os.models.base import Base
from revenue_os.models.contact import Company, Contact
from revenue_os.models.organization import Organization

_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "seed_founder_demo",
    _ROOT / "scripts" / "seed_founder_demo.py",
)
assert _SPEC is not None and _SPEC.loader is not None
seed_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(seed_mod)

CONTACT_ID = uuid.UUID(seed_mod.CONTACT_ID)
CONTACT_EMAIL = seed_mod.CONTACT_EMAIL


@pytest.fixture
def seed_session(tmp_path, monkeypatch: pytest.MonkeyPatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'founder_demo_d12.db'}")
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(seed_mod, "SessionLocal", factory)
    monkeypatch.setattr(seed_mod, "init_db", lambda: None)
    return factory


def _run_seed(seed_session) -> None:
    seed_mod.seed()


def test_founder_demo_company_created(seed_session) -> None:
    _run_seed(seed_session)
    db = seed_session()
    try:
        company = (
            db.query(Company)
            .filter(Company.domain == seed_mod.DEMO_COMPANY_DOMAIN)
            .one()
        )
        assert company.name == "Acme Labs"
    finally:
        db.close()


def test_contact_company_is_orm_instance(seed_session) -> None:
    _run_seed(seed_session)
    db = seed_session()
    try:
        contact = db.query(Contact).filter(Contact.email == CONTACT_EMAIL).one()
        assert isinstance(contact.company, Company)
        assert contact.company.name == "Acme Labs"
        assert contact.id == CONTACT_ID
    finally:
        db.close()


def test_contact_company_id_matches_company(seed_session) -> None:
    _run_seed(seed_session)
    db = seed_session()
    try:
        contact = db.query(Contact).filter(Contact.email == CONTACT_EMAIL).one()
        company = (
            db.query(Company)
            .filter(Company.domain == seed_mod.DEMO_COMPANY_DOMAIN)
            .one()
        )
        assert isinstance(contact.company, Company)
        assert contact.company_id == company.id
    finally:
        db.close()


def test_contact_organization_id_is_demo_org(seed_session) -> None:
    _run_seed(seed_session)
    db = seed_session()
    try:
        contact = db.query(Contact).filter(Contact.email == CONTACT_EMAIL).one()
        org = db.query(Organization).filter(Organization.slug == "demo-workspace").one()
        assert contact.organization_id == org.id
    finally:
        db.close()


def test_repeated_seed_does_not_duplicate_company(seed_session) -> None:
    _run_seed(seed_session)
    _run_seed(seed_session)
    db = seed_session()
    try:
        count = (
            db.query(Company)
            .filter(Company.domain == seed_mod.DEMO_COMPANY_DOMAIN)
            .count()
        )
        assert count == 1
        assert db.query(Company).filter(Company.name == "Acme Labs").count() == 1
    finally:
        db.close()


def test_repeated_seed_does_not_duplicate_contact(seed_session) -> None:
    _run_seed(seed_session)
    _run_seed(seed_session)
    db = seed_session()
    try:
        assert db.query(Contact).filter(Contact.email == CONTACT_EMAIL).count() == 1
        assert db.query(Contact).filter(Contact.id == CONTACT_ID).count() == 1
    finally:
        db.close()
