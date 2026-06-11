import json
from pathlib import Path

from src.tools.runtime_paths import (
    REPO_ROOT,
    RUNTIME_CONFIG_PATH,
    load_canonical_runtime_config,
    load_runtime_config,
)


def test_repo_root_contains_src_and_data():
    assert (REPO_ROOT / "src").is_dir()
    assert (REPO_ROOT / "data").is_dir()


def test_runtime_config_loads():
    cfg = load_runtime_config()
    assert "active_week" in cfg
    assert RUNTIME_CONFIG_PATH.is_file()


def test_checklist_path_for_week():
    from src.tools.runtime_paths import checklist_path_for_week

    p = checklist_path_for_week("W05")
    assert p == REPO_ROOT / "input" / "W05" / "09_Publish_Checklist.md"
    assert isinstance(p, Path)


def test_load_runtime_config_env_override(monkeypatch, tmp_path):
    overlay = tmp_path / "overlay.json"
    overlay.write_text(
        json.dumps(
            {
                "active_week": "W99",
                "draft_path": "x/04_Draft.md",
                "research_path": "x/03_Research.md",
                "seo_plan_path": "x/02_SEO_Plan.md",
                "qa_output_dir": "output/qa_reports/staging/",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("WORKCREW_RUNTIME_CONFIG", str(overlay))
    cfg = load_runtime_config()
    assert cfg["active_week"] == "W99"

    monkeypatch.delenv("WORKCREW_RUNTIME_CONFIG", raising=False)
    canon = load_canonical_runtime_config()
    assert "active_week" in canon
