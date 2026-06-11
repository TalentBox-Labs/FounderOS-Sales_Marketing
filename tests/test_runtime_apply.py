from pathlib import Path

import pytest

import src.tools.runtime_apply as ra


def test_list_profiles_includes_known_weeks():
    names = ra._list_profiles()
    for w in ("W01", "W02", "W03", "W04", "W05"):
        assert w in names


def test_apply_profile_missing_week(tmp_path, monkeypatch):
    monkeypatch.setattr(ra, "PROFILES_DIR", tmp_path)
    monkeypatch.setattr(ra, "RUNTIME_CONFIG_PATH", tmp_path / "runtime_config.json")
    with pytest.raises(FileNotFoundError):
        ra.apply_profile("W99")
