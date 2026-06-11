"""HTTP runner for n8n — requires ``pip install -r requirements-api.txt``."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from runner_api import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_returns_ok(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "project_root" in data
    assert "python" in data


def test_run_pipeline_no_week_only_main_py(client: TestClient) -> None:
    ok = subprocess.CompletedProcess(
        ["python", "main.py"], returncode=0, stdout="done\n", stderr=""
    )
    with patch("runner_api._run", return_value=ok) as m:
        r = client.post("/run-pipeline", json={})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"
    assert body["week"] is None
    assert body["returncode"] == 0
    assert len(m.call_args_list) == 1
    assert m.call_args_list[0][0][0][-1] == "main.py"


def test_run_pipeline_with_week_runs_apply_then_main(client: TestClient) -> None:
    apply_ok = subprocess.CompletedProcess(
        [], returncode=0, stdout="Applied\n", stderr=""
    )
    main_ok = subprocess.CompletedProcess(
        [], returncode=0, stdout="ALL VALIDATION GATES PASSED\n", stderr=""
    )
    with patch("runner_api._run", side_effect=[apply_ok, main_ok]) as m:
        r = client.post("/run-pipeline", json={"week": "w10", "topic": "t"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"
    assert body["week"] == "W10"
    assert body["topic"] == "t"
    assert len(m.call_args_list) == 2
    first_cmd = m.call_args_list[0][0][0]
    assert first_cmd[-1] == "W10"
    assert "src.tools.runtime_apply" in first_cmd
    assert m.call_args_list[1][0][0][-1] == "main.py"


def test_run_pipeline_stops_when_runtime_apply_fails(client: TestClient) -> None:
    fail = subprocess.CompletedProcess([], returncode=1, stdout="", stderr="no profile")
    with patch("runner_api._run", return_value=fail):
        r = client.post("/run-pipeline", json={"week": "ZZ99"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "failed"
    assert body["returncode"] == 1
    assert len(body["steps"]) == 1


def test_run_pipeline_requires_bearer_when_env_set(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RUNNER_API_KEY", "test-secret-token")
    r = client.post("/run-pipeline", json={})
    assert r.status_code == 401

    ok = MagicMock()
    ok.returncode = 0
    ok.stdout = ""
    ok.stderr = ""
    with patch("runner_api._run", return_value=ok):
        r2 = client.post(
            "/run-pipeline",
            json={},
            headers={"Authorization": "Bearer test-secret-token"},
        )
    assert r2.status_code == 200
    assert r2.json()["status"] == "success"
