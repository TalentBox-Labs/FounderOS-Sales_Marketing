"""google_sheets_verify CLI — env errors without calling Google."""

from __future__ import annotations

from src.tools import google_sheets_verify as gsv


def test_verify_missing_sa_env(monkeypatch):
    monkeypatch.delenv("WORKCREW_GOOGLE_SERVICE_ACCOUNT", raising=False)
    monkeypatch.delenv("WORKCREW_GOOGLE_SHEET_ID", raising=False)
    assert gsv.verify() == 2


def test_verify_missing_sheet_id(monkeypatch, tmp_path):
    fake = tmp_path / "sa.json"
    fake.write_text('{"client_email":"x@y.iam.gserviceaccount.com"}', encoding="utf-8")
    monkeypatch.setenv("WORKCREW_GOOGLE_SERVICE_ACCOUNT", str(fake))
    monkeypatch.delenv("WORKCREW_GOOGLE_SHEET_ID", raising=False)
    assert gsv.verify() == 2


def test_verify_invalid_json(monkeypatch, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    monkeypatch.setenv("WORKCREW_GOOGLE_SERVICE_ACCOUNT", str(bad))
    monkeypatch.setenv("WORKCREW_GOOGLE_SHEET_ID", "abc")
    assert gsv.verify() == 2
