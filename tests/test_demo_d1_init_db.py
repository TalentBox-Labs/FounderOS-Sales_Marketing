"""DEMO-D1 — canonical init_db compatibility."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, inspect

import revenue_os.database as db_mod
from revenue_os.database import init_db


def test_init_db_imports_successfully() -> None:
    assert callable(init_db)


def test_init_db_creates_metadata_and_is_idempotent(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'demo_d1.db'}")
    monkeypatch.setattr(db_mod, "engine", engine)

    init_db()
    tables_first = set(inspect(engine).get_table_names())
    assert "contacts" in tables_first

    init_db()
    tables_second = set(inspect(engine).get_table_names())
    assert tables_second == tables_first
