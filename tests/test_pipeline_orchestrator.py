"""pipeline_orchestrator: JSON summary + exit code for external runners."""

from __future__ import annotations

import json

import pytest

import src.tools.pipeline_orchestrator as orch


def test_run_with_summary_success_writes_json(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(orch, "REPO_ROOT", root)
    monkeypatch.setattr(
        orch,
        "load_runtime_config",
        lambda: {"active_week": "W01"},
    )
    monkeypatch.setattr(orch, "run_pipeline", lambda: None)

    rec = orch.run_with_summary()
    assert rec["ok"] is True
    assert rec["active_week"] == "W01"
    p = root / orch.SUMMARY_REL
    assert p.is_file()
    loaded = json.loads(p.read_text(encoding="utf-8"))
    assert loaded["ok"] is True


def test_run_with_summary_failure_records_error(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(orch, "REPO_ROOT", root)
    monkeypatch.setattr(
        orch,
        "load_runtime_config",
        lambda: {"active_week": "W99"},
    )

    def boom():
        raise RuntimeError("gate failed")

    monkeypatch.setattr(orch, "run_pipeline", boom)

    rec = orch.run_with_summary()
    assert rec["ok"] is False
    assert "gate failed" in rec["error"]
    assert "traceback" in rec
    p = root / orch.SUMMARY_REL
    assert json.loads(p.read_text(encoding="utf-8"))["ok"] is False


def test_main_exit_code(monkeypatch):
    monkeypatch.setattr(orch, "run_with_summary", lambda: {"ok": True})
    with pytest.raises(SystemExit) as ei:
        orch.main()
    assert ei.value.code == 0

    monkeypatch.setattr(orch, "run_with_summary", lambda: {"ok": False})
    with pytest.raises(SystemExit) as ei:
        orch.main()
    assert ei.value.code == 1
