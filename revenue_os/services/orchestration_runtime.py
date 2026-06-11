from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class OrchestrationError(RuntimeError):
    pass


@dataclass
class TaskRequest:
    name: str
    objective: str
    payload: dict[str, Any]


class AgentBackendAdapter:
    """Provider-agnostic adapter interface for orchestration agent backends."""

    name: str = "base"

    def is_configured(self) -> bool:
        return False

    def run_task(self, req: TaskRequest) -> dict[str, Any]:
        raise NotImplementedError()


class HermesAdapter(AgentBackendAdapter):
    """
    Hermes backend adapter.

    Expects an HTTP endpoint that accepts:
      {"task": "...", "objective": "...", "payload": {...}}
    """

    name = "hermes"

    def __init__(self) -> None:
        self.endpoint = os.getenv("HERMES_AGENT_URL", "").strip()
        self.api_key = os.getenv("HERMES_AGENT_API_KEY", "").strip()

    def is_configured(self) -> bool:
        return bool(self.endpoint)

    def run_task(self, req: TaskRequest) -> dict[str, Any]:
        if not self.endpoint:
            return {
                "provider": self.name,
                "mode": "fallback",
                "task": req.name,
                "status": "not_configured",
                "action": "Set HERMES_AGENT_URL to enable live execution.",
                "payload_preview": req.payload,
            }
        body = {
            "task": req.name,
            "objective": req.objective,
            "payload": req.payload,
        }
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        data = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(self.endpoint, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=45) as resp:
                raw = resp.read().decode("utf-8")
                try:
                    parsed = json.loads(raw) if raw else {}
                except json.JSONDecodeError:
                    parsed = {"raw": raw}
                return {
                    "provider": self.name,
                    "mode": "live",
                    "task": req.name,
                    "status": "ok",
                    "result": parsed,
                }
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise OrchestrationError(f"Hermes error ({e.code}): {body}") from e
        except Exception as e:
            raise OrchestrationError(f"Hermes call failed: {e}") from e


class OpenClawAdapter(AgentBackendAdapter):
    """
    OpenClaw backend adapter.

    Expects an HTTP endpoint that accepts:
      {"agent": "sales_marketing_orchestrator", "job": {...}}
    """

    name = "openclaw"

    def __init__(self) -> None:
        self.endpoint = os.getenv("OPENCLAW_AGENT_URL", "").strip()
        self.api_key = os.getenv("OPENCLAW_AGENT_API_KEY", "").strip()

    def is_configured(self) -> bool:
        return bool(self.endpoint)

    def run_task(self, req: TaskRequest) -> dict[str, Any]:
        if not self.endpoint:
            return {
                "provider": self.name,
                "mode": "fallback",
                "task": req.name,
                "status": "not_configured",
                "action": "Set OPENCLAW_AGENT_URL to enable live execution.",
                "payload_preview": req.payload,
            }
        body = {
            "agent": "sales_marketing_orchestrator",
            "job": {
                "task": req.name,
                "objective": req.objective,
                "payload": req.payload,
            },
        }
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        data = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(self.endpoint, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=45) as resp:
                raw = resp.read().decode("utf-8")
                try:
                    parsed = json.loads(raw) if raw else {}
                except json.JSONDecodeError:
                    parsed = {"raw": raw}
                return {
                    "provider": self.name,
                    "mode": "live",
                    "task": req.name,
                    "status": "ok",
                    "result": parsed,
                }
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise OrchestrationError(f"OpenClaw error ({e.code}): {body}") from e
        except Exception as e:
            raise OrchestrationError(f"OpenClaw call failed: {e}") from e


def get_backend(name: str) -> AgentBackendAdapter:
    key = (name or "").strip().lower()
    if key == "hermes":
        return HermesAdapter()
    if key == "openclaw":
        return OpenClawAdapter()
    raise ValueError("backend must be one of: hermes, openclaw")


def backend_status() -> dict[str, bool]:
    return {
        "hermes": HermesAdapter().is_configured(),
        "openclaw": OpenClawAdapter().is_configured(),
    }
