"""Unified validation pipeline: config-driven steps, cwd-safe, same interpreter as parent."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from src.tools.runtime_paths import REPO_ROOT, load_runtime_config
from src.tools.tracker_updater import update_tracker
from src.qa_crew import QACrew

VALIDATOR_MODULES: dict[str, str] = {
    "research_mapper": "src.tools.research_mapper",
    "draft_validator": "src.tools.draft_validator",
    "structure_checker": "src.tools.structure_checker",
    "metadata_checker": "src.tools.metadata_checker",
    "publish_checklist_checker": "src.tools.publish_checklist_checker",
}

DEFAULT_VALIDATORS: list[str] = list(VALIDATOR_MODULES.keys())


def _validator_ids_from_config() -> list[str]:
    runtime = load_runtime_config()
    raw = runtime.get("validators")
    if not raw:
        return list(DEFAULT_VALIDATORS)
    out: list[str] = []
    for vid in raw:
        if vid not in VALIDATOR_MODULES:
            raise ValueError(
                f"Unknown validator id in runtime config: {vid!r}. "
                f"Allowed: {sorted(VALIDATOR_MODULES)}"
            )
        out.append(vid)
    return out


def _display_name(validator_id: str) -> str:
    return validator_id.replace("_", " ").title()


def _run_subprocess_step(validator_id: str) -> subprocess.CompletedProcess[str]:
    module = VALIDATOR_MODULES[validator_id]
    cmd = [sys.executable, "-m", module]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        check=False,
    )


def run_validation_pipeline() -> None:
    """Execute all validators from runtime config; raise on failure."""
    print("\nWORKCREW CMS OS VALIDATION STARTED\n")

    for validator_id in _validator_ids_from_config():
        name = _display_name(validator_id)
        print(f"\n=== Running: {name} ===")

        result = _run_subprocess_step(validator_id)

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        if result.returncode != 0:
            raise RuntimeError(
                f"Step failed (exit {result.returncode}): {name}\n"
                f"{result.stderr or result.stdout or ''}"
            )

        combined = (result.stdout or "") + (result.stderr or "")
        if "FAIL" in combined:
            raise RuntimeError(f"Gate reported FAIL: {name}")

        print(f"PASSED: {name}")

    print("\nALL VALIDATION GATES PASSED")


def run_pipeline() -> None:
    """Full pipeline: validators then tracker update for `active_week`."""
    print("\nWORKCREW CMS OS PIPELINE STARTED\n")
    run_validation_pipeline()
    _maybe_run_crewai_qa()
    update_tracker()
    cfg = load_runtime_config()
    week = cfg["active_week"]
    print(f"\n{week} is ready for human publish review (tracker updated).")


def _maybe_run_crewai_qa() -> None:
    """
    Optional Phase 2 QA artifact generation (soft-fail, non-blocking).

    Uses QACrew which resolves source file (final/draft) via crewai_qa_source config.
    """
    runtime = load_runtime_config()
    if not runtime.get("enable_crewai_qa"):
        return

    week = runtime.get("active_week")
    qa_dir = runtime.get("qa_output_dir", "output/qa_reports/")
    out_path = f"{qa_dir.rstrip('/')}/{week}_CrewAI_QA.md"

    try:
        crew = QACrew()
        crew.run_qa_agent(output_path=out_path)
    except Exception as e:  # soft-fail by design
        print(
            f"WARNING: CrewAI QA failed (soft continue): {e}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    run_pipeline()
