"""
Phase H.3b — Unit tests for tools/check_streaming_skills_drift.py.

Mocks subprocess.run via monkeypatch so no real `git ls-remote` calls happen
during tests. CI workflow run is the only place real network calls happen.
"""
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools import check_streaming_skills_drift as drift_mod


PINNED_SHA = "91d1871ef8c320be92bca955c8e42492a2778cb4"
DIFFERENT_SHA = "abc1234567890def1234567890abcdef12345678"


@pytest.fixture
def fake_vendor_sources(tmp_path, monkeypatch):
    """Point the module's VENDOR_SOURCES_PATH at a tmp file we control."""
    data = {
        "streaming-skills-plugin": {
            "upstream": "https://github.com/confluentinc/agent-skills",
            "repo": "confluentinc/agent-skills",
            "marketplace": "confluent-agent-skills",
            "plugin_name": "streaming-skills-plugin",
            "version": "1.0.0",
            "commit": PINNED_SHA,
            "installed_at": "2026-05-17",
            "kind": "claude-plugin",
            "license": "Apache-2.0",
            "drift_check": "tools/check_streaming_skills_drift.py"
        }
    }
    path = tmp_path / "vendor-sources.json"
    path.write_text(json.dumps(data, indent=2))
    monkeypatch.setattr(drift_mod, "VENDOR_SOURCES_PATH", path)
    return path


def _mock_subprocess_run(returncode: int, stdout: str = "", stderr: str = "", raise_exc=None):
    """Build a subprocess.run replacement returning a CompletedProcess-like object."""
    def _runner(*args, **kwargs):
        if raise_exc is not None:
            raise raise_exc
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)
    return _runner


def test_pin_matches_head_exits_zero(fake_vendor_sources, monkeypatch):
    """When ls-remote returns the same SHA as the pin, --check exits 0."""
    monkeypatch.setattr(
        subprocess,
        "run",
        _mock_subprocess_run(returncode=0, stdout=f"{PINNED_SHA}\tHEAD\n"),
    )
    exit_code = drift_mod.main(["--check"])
    assert exit_code == 0


def test_pin_mismatches_head_exits_one(fake_vendor_sources, monkeypatch, capsys):
    """When ls-remote returns a different SHA, --check exits 1 and prints drift report."""
    monkeypatch.setattr(
        subprocess,
        "run",
        _mock_subprocess_run(returncode=0, stdout=f"{DIFFERENT_SHA}\tHEAD\n"),
    )
    exit_code = drift_mod.main(["--check"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "drift detected" in captured.err.lower()
    assert PINNED_SHA in captured.err
    assert DIFFERENT_SHA in captured.err


def test_default_mode_does_not_exit_nonzero_on_drift(fake_vendor_sources, monkeypatch, capsys):
    """Default mode (no --check) prints summary but always exits 0."""
    monkeypatch.setattr(
        subprocess,
        "run",
        _mock_subprocess_run(returncode=0, stdout=f"{DIFFERENT_SHA}\tHEAD\n"),
    )
    exit_code = drift_mod.main([])  # no flags
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "DRIFT" in captured.out


def test_missing_entry_exits_two(tmp_path, monkeypatch):
    """Empty vendor-sources.json (no streaming-skills-plugin key) exits 2."""
    path = tmp_path / "vendor-sources.json"
    path.write_text("{}")
    monkeypatch.setattr(drift_mod, "VENDOR_SOURCES_PATH", path)
    with pytest.raises(SystemExit) as exc_info:
        drift_mod.main(["--check"])
    assert exc_info.value.code == 2


def test_malformed_json_exits_two(tmp_path, monkeypatch):
    """Malformed JSON exits 2 (config error)."""
    path = tmp_path / "vendor-sources.json"
    path.write_text("{not valid json")
    monkeypatch.setattr(drift_mod, "VENDOR_SOURCES_PATH", path)
    with pytest.raises(SystemExit) as exc_info:
        drift_mod.main(["--check"])
    assert exc_info.value.code == 2


def test_missing_commit_field_exits_two(tmp_path, monkeypatch):
    """Entry without commit field exits 2 (config error)."""
    path = tmp_path / "vendor-sources.json"
    path.write_text(json.dumps({"streaming-skills-plugin": {"version": "1.0.0"}}))
    monkeypatch.setattr(drift_mod, "VENDOR_SOURCES_PATH", path)
    with pytest.raises(SystemExit) as exc_info:
        drift_mod.main(["--check"])
    assert exc_info.value.code == 2


def test_git_unavailable_exits_three(fake_vendor_sources, monkeypatch):
    """When git command is not on PATH, --check exits 3."""
    monkeypatch.setattr(
        subprocess,
        "run",
        _mock_subprocess_run(returncode=0, raise_exc=FileNotFoundError("git not found")),
    )
    with pytest.raises(SystemExit) as exc_info:
        drift_mod.main(["--check"])
    assert exc_info.value.code == 3


def test_git_returns_empty_output_exits_three(fake_vendor_sources, monkeypatch):
    """When ls-remote returns empty output, --check exits 3."""
    monkeypatch.setattr(
        subprocess,
        "run",
        _mock_subprocess_run(returncode=0, stdout=""),
    )
    with pytest.raises(SystemExit) as exc_info:
        drift_mod.main(["--check"])
    assert exc_info.value.code == 3


def test_git_nonzero_returncode_exits_three(fake_vendor_sources, monkeypatch):
    """When ls-remote returncode != 0, --check exits 3."""
    monkeypatch.setattr(
        subprocess,
        "run",
        _mock_subprocess_run(returncode=128, stderr="remote not found"),
    )
    with pytest.raises(SystemExit) as exc_info:
        drift_mod.main(["--check"])
    assert exc_info.value.code == 3
