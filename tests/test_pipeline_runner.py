"""Pipeline config and failure handling (no full pipeline side effects)."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock

import pytest

import src.tools.pipeline_runner as pr


def test_validator_ids_from_config_uses_list(monkeypatch):
    monkeypatch.setattr(
        pr,
        "load_runtime_config",
        lambda: {"validators": ["research_mapper", "draft_validator"]},
    )
    assert pr._validator_ids_from_config() == ["research_mapper", "draft_validator"]


def test_validator_ids_empty_list_falls_back_to_default(monkeypatch):
    monkeypatch.setattr(pr, "load_runtime_config", lambda: {"validators": []})
    assert pr._validator_ids_from_config() == pr.DEFAULT_VALIDATORS


def test_validator_ids_omitted_falls_back_to_default(monkeypatch):
    monkeypatch.setattr(pr, "load_runtime_config", lambda: {})
    assert pr._validator_ids_from_config() == pr.DEFAULT_VALIDATORS


def test_unknown_validator_raises(monkeypatch):
    monkeypatch.setattr(
        pr,
        "load_runtime_config",
        lambda: {"validators": ["not_a_real_validator"]},
    )
    with pytest.raises(ValueError, match="Unknown validator"):
        pr._validator_ids_from_config()


def test_run_validation_pipeline_raises_on_fail_verdict(monkeypatch):
    bad = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="## Final Verdict\nFAIL\n",
        stderr="",
    )
    monkeypatch.setattr(pr, "_validator_ids_from_config", lambda: ["draft_validator"])
    monkeypatch.setattr(pr, "_run_subprocess_step", lambda _vid: bad)

    with pytest.raises(RuntimeError, match="Gate reported FAIL"):
        pr.run_validation_pipeline()


def test_run_validation_pipeline_raises_on_nonzero_exit(monkeypatch):
    bad = subprocess.CompletedProcess(
        args=[],
        returncode=1,
        stdout="error",
        stderr="",
    )
    monkeypatch.setattr(pr, "_validator_ids_from_config", lambda: ["draft_validator"])
    monkeypatch.setattr(pr, "_run_subprocess_step", lambda _vid: bad)

    with pytest.raises(RuntimeError, match="Step failed"):
        pr.run_validation_pipeline()


def test_display_name():
    assert pr._display_name("research_mapper") == "Research Mapper"


def test_maybe_run_crewai_qa_noop_when_disabled(monkeypatch):
    monkeypatch.setattr(
        pr,
        "load_runtime_config",
        lambda: {
            "enable_crewai_qa": False,
            "active_week": "W05",
            "qa_output_dir": "output/qa_reports/",
        },
    )
    called = {"n": 0}

    def fake_run_qa_agent(output_path=None):
        called["n"] += 1

    monkeypatch.setattr(pr, "run_qa_agent", fake_run_qa_agent)
    pr._maybe_run_crewai_qa()
    assert called["n"] == 0


def test_maybe_run_crewai_qa_uses_separate_artifact_name(monkeypatch):
    monkeypatch.setattr(
        pr,
        "load_runtime_config",
        lambda: {
            "enable_crewai_qa": True,
            "active_week": "W05",
            "qa_output_dir": "output/qa_reports/",
        },
    )
    seen = {}

    def fake_run_qa_agent(output_path=None):
        seen["path"] = output_path

    monkeypatch.setattr(pr, "run_qa_agent", fake_run_qa_agent)
    pr._maybe_run_crewai_qa()
    assert seen["path"] == "output/qa_reports/W05_CrewAI_QA.md"


def test_maybe_run_crewai_qa_soft_continue_on_error(monkeypatch, capsys):
    monkeypatch.setattr(
        pr,
        "load_runtime_config",
        lambda: {
            "enable_crewai_qa": True,
            "active_week": "W05",
            "qa_output_dir": "output/qa_reports/",
        },
    )

    def fake_run_qa_agent(output_path=None):
        raise RuntimeError("ollama down")

    monkeypatch.setattr(pr, "run_qa_agent", fake_run_qa_agent)
    pr._maybe_run_crewai_qa()

    captured = capsys.readouterr()
    assert "WARNING: CrewAI QA failed (soft continue):" in captured.err
