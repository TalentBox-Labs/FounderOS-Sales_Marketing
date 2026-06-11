"""
Run each validator as a subprocess (same as production).

Requires: repository root layout, valid `data/runtime_config.json`, and content
that passes all gates for the configured `active_week`. If this fails after
changing week or content, fix artifacts or adjust config — do not skip without
documenting why.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from src.tools.pipeline_runner import VALIDATOR_MODULES, _run_subprocess_step


@pytest.mark.parametrize("validator_id", sorted(VALIDATOR_MODULES.keys()))
def test_validator_subprocess_passes(validator_id: str):
    result = _run_subprocess_step(validator_id)
    assert result.returncode == 0, (
        f"{validator_id} exit {result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    combined = (result.stdout or "") + (result.stderr or "")
    assert "FAIL" not in combined, f"{validator_id} reported FAIL:\n{combined}"
    assert "PASS" in combined, f"{validator_id} missing PASS in output:\n{combined}"


def test_run_subprocess_step_uses_sys_executable(monkeypatch):
    captured: dict = {}

    def fake_run(cmd, **_kwargs):
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="PASS\n", stderr="")

    monkeypatch.setattr("src.tools.pipeline_runner.subprocess.run", fake_run)
    _run_subprocess_step("draft_validator")
    assert captured["cmd"][0] == sys.executable
    assert captured["cmd"][1] == "-m"
    assert captured["cmd"][2] == "src.tools.draft_validator"
