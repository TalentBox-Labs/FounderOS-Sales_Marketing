"""Crew wiring: LLM env and contract banner (no live LLM calls)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import src.crew as crew_mod


def test_build_crew_llm_respects_env(monkeypatch):
    monkeypatch.setenv("WORKCREW_CREWAI_MODEL", "ollama/test-model")
    monkeypatch.setenv("WORKCREW_OLLAMA_BASE_URL", "http://example:11434")
    monkeypatch.setenv("WORKCREW_CREWAI_TEMPERATURE", "0.2")
    llm = crew_mod.build_crew_llm()
    assert llm.model == "test-model"
    assert llm.api_base == "http://example:11434"
    assert llm.temperature == 0.2


def test_run_qa_agent_contract_banner_on_bad_output(tmp_path, monkeypatch):
    monkeypatch.chdir(crew_mod.BASE_DIR)
    monkeypatch.setattr(
        crew_mod,
        "load_runtime_config",
        lambda: {
            "final_path": "input/W99/05_Final.md",
            "draft_path": "input/W99/04_Draft.md",
            "crewai_qa_source": "draft",
        },
    )
    monkeypatch.setattr(
        crew_mod,
        "get_active_content",
        lambda: {
            "content_id": "W99",
            "draft_path": "input/W99/04_Draft.md",
            "qa_output_path": str(tmp_path / "out.md"),
            "title": "T",
            "current_step": "Draft",
            "next_step": "QA",
        },
    )
    monkeypatch.setattr(crew_mod, "read_file", lambda _p: "# hello\n")

    def fake_load_yaml(path: str) -> dict:
        if "agents" in path:
            return {"qa_agent": {"role": "r", "goal": "g", "backstory": "b"}}
        return {
            "qa_review_task": {
                "description": "d",
                "expected_output": "e",
            }
        }

    monkeypatch.setattr(crew_mod, "load_yaml", fake_load_yaml)

    bad_markdown = "not a valid qa report"
    fake_crew = MagicMock()
    fake_crew.kickoff.return_value = bad_markdown

    fake_agent = MagicMock()
    fake_task = MagicMock()

    with patch("src.crew.Agent", return_value=fake_agent):
        with patch("src.crew.Task", return_value=fake_task):
            with patch("src.crew.Crew", return_value=fake_crew):
                out = crew_mod.run_qa_agent()

    assert "CREWAI_QA_CONTRACT_VIOLATION" in out
    saved = (tmp_path / "out.md").read_text(encoding="utf-8")
    assert "CREWAI_QA_CONTRACT_VIOLATION" in saved
    assert bad_markdown in saved
