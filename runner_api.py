"""
Local HTTP runner so n8n (or curl) can trigger the CMS OS pipeline.

ChatGPT-style snippets often POST {"week": "W10"} then only run main.py — that
does **not** switch weeks: main.py always follows data/runtime_config.json.
When ``week`` is set, this app runs ``runtime_apply`` first, then main.py.

Install: pip install -r requirements.txt -r requirements-api.txt
Run:    uvicorn runner_api:app --host 0.0.0.0 --port 8000

Dockerized n8n on Mac/Win: use http://host.docker.internal:8000/... not localhost.

Optional auth: set env RUNNER_API_KEY and send header
Authorization: Bearer <RUNNER_API_KEY>
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="WorkCrew CMS OS — pipeline runner")

PROJECT_ROOT = Path(__file__).resolve().parent
PIPELINE_TIMEOUT_SEC = int(os.environ.get("RUNNER_PIPELINE_TIMEOUT_SEC", "1800"))
TAIL_CHARS = int(os.environ.get("RUNNER_LOG_TAIL_CHARS", "4000"))


def _runner_api_key() -> str:
    """Read on each auth check so tests can monkeypatch ``RUNNER_API_KEY``."""
    return os.environ.get("RUNNER_API_KEY", "").strip()


class RunRequest(BaseModel):
    """``topic`` is echoed only; pipeline selection uses ``week`` + runtime files."""

    week: str | None = Field(
        default=None,
        description="If set (e.g. W10), copies data/week_runtime/WXX.json to runtime_config.json before the pipeline.",
    )
    topic: str | None = Field(
        default=None,
        description="Optional label for operators / n8n logs; not passed to validators.",
    )


def _require_auth(authorization: str | None) -> None:
    key = _runner_api_key()
    if not key:
        return
    expected = f"Bearer {key}"
    if (authorization or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _tail(text: str) -> str:
    if len(text) <= TAIL_CHARS:
        return text
    return text[-TAIL_CHARS:]


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=PIPELINE_TIMEOUT_SEC,
    )


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "project_root": str(PROJECT_ROOT),
        "python": sys.executable,
    }


@app.post("/run-pipeline")
def run_pipeline(
    request: RunRequest,
    authorization: str | None = Header(default=None),
) -> dict:
    """
    Optionally apply a week profile, then run the same entrypoint as ``python main.py``.
    """
    _require_auth(authorization)

    steps: list[dict] = []
    week = (request.week or "").strip().upper() or None

    if week:
        r = _run([sys.executable, "-m", "src.tools.runtime_apply", week])
        steps.append(
            {
                "step": "runtime_apply",
                "returncode": r.returncode,
                "stdout_tail": _tail(r.stdout or ""),
                "stderr_tail": _tail(r.stderr or ""),
            }
        )
        if r.returncode != 0:
            return {
                "status": "failed",
                "week": week,
                "topic": request.topic,
                "returncode": r.returncode,
                "steps": steps,
            }

    r = _run([sys.executable, "main.py"])
    steps.append(
        {
            "step": "main.py",
            "returncode": r.returncode,
            "stdout_tail": _tail(r.stdout or ""),
            "stderr_tail": _tail(r.stderr or ""),
        }
    )

    ok = r.returncode == 0
    return {
        "status": "success" if ok else "failed",
        "week": week,
        "topic": request.topic,
        "returncode": r.returncode,
        "steps": steps,
    }
