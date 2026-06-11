"""Integration: every tracker row has a week_runtime profile that passes gates."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_validate_all_tracker_weeks_exits_zero():
    r = subprocess.run(
        [sys.executable, "-m", "src.tools.validate_all_tracker_weeks"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr + r.stdout
