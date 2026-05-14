"""Unit tests for the Phase G.1 terraform-module executor in apply_engine.py.

These tests do NOT exercise real Terraform or Confluent Cloud — they
either route around the binary entirely (dispatcher tests) or substitute
a fake `terraform` shell script on PATH that records its argv and exits
with a configurable code. Real end-to-end verification (a topic actually
appears in CC) is manual via the FRANZ Apply page on a sandbox env.
"""

import os
import stat
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.apply_engine import (  # noqa: E402
    ExecutionResult,
    execute_artifact,
    execute_terraform_module,
)


# ---------------------------------------------------------------------------
# ExecutionResult dataclass
# ---------------------------------------------------------------------------


class TestExecutionResult:
    def test_minimal_construction(self):
        r = ExecutionResult(status="success", duration_seconds=2.5)
        assert r.status == "success"
        assert r.duration_seconds == 2.5
        assert r.per_phase == []
        assert r.outputs == {}

    def test_to_activity_log_string_is_status(self):
        r = ExecutionResult(status="failure", duration_seconds=1.0)
        assert r.to_activity_log_string() == "failure"


# ---------------------------------------------------------------------------
# Dispatcher (execute_artifact)
# ---------------------------------------------------------------------------


class TestExecuteArtifact:
    def test_unsupported_type_returns_skipped(self):
        artifact = {"id": "scenario/cc-gcp", "type": "scenario"}
        r = execute_artifact(artifact, {}, plan_slug="test-plan")
        assert r.status == "skipped"
        assert r.duration_seconds == 0.0
        assert "Phase G.2" in r.stderr_tail

    def test_missing_type_returns_skipped(self):
        r = execute_artifact({"id": "role/cp_topic"}, {}, plan_slug="t")
        assert r.status == "skipped"


# ---------------------------------------------------------------------------
# Terraform module executor — error paths (no fake terraform needed)
# ---------------------------------------------------------------------------


class TestExecuteTerraformModuleErrors:
    def test_missing_path_returns_failure(self):
        artifact = {"id": "module/topic", "type": "terraform-module"}
        r = execute_terraform_module(artifact, {}, plan_slug="t")
        assert r.status == "failure"
        assert "no 'path'" in r.stderr_tail

    def test_nonexistent_path_returns_failure(self):
        artifact = {
            "id": "module/topic",
            "type": "terraform-module",
            "path": "modules/does-not-exist",
        }
        r = execute_terraform_module(artifact, {}, plan_slug="t")
        assert r.status == "failure"
        assert "does not exist" in r.stderr_tail

    def test_terraform_binary_missing_returns_failure(self, monkeypatch, tmp_path):
        # Empty PATH so `terraform` can't be located.
        monkeypatch.setenv("PATH", str(tmp_path))
        artifact = {
            "id": "module/topic",
            "type": "terraform-module",
            "path": "modules/topic",
        }
        r = execute_terraform_module(artifact, {}, plan_slug="t-no-tf")
        assert r.status == "failure"
        assert "terraform" in r.stderr_tail.lower()


# ---------------------------------------------------------------------------
# Terraform module executor — happy path with fake terraform on PATH
# ---------------------------------------------------------------------------


def _install_fake_terraform(dir_: Path, exit_code: int = 0) -> Path:
    """Write an executable shim that records argv to argv.log and exits N."""
    log_file = dir_ / "argv.log"
    script = dir_ / "terraform"
    script.write_text(
        "#!/bin/sh\n"
        f'echo "argv: $@" >> "{log_file}"\n'
        # `terraform output -json` is parsed; emit an empty JSON object.
        'if [ "$1" = "output" ]; then echo "{}"; fi\n'
        f"exit {exit_code}\n"
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return log_file


class TestExecuteTerraformModuleHappyPath:
    def test_dry_run_runs_init_plan_no_apply(self, monkeypatch, tmp_path):
        log = _install_fake_terraform(tmp_path)
        monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
        artifact = {
            "id": "module/topic",
            "type": "terraform-module",
            "path": "modules/topic",
        }
        r = execute_terraform_module(
            artifact,
            {"domain": "franz", "entity": "smoke_test"},
            plan_slug="g1-dryrun",
            dry_run=True,
        )
        assert r.status == "dry-run", r.stderr_tail
        argv = log.read_text()
        assert "argv: init" in argv
        assert "argv: plan" in argv
        assert "argv: apply" not in argv

    def test_full_apply_runs_init_plan_apply(self, monkeypatch, tmp_path):
        log = _install_fake_terraform(tmp_path)
        monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
        artifact = {
            "id": "module/topic",
            "type": "terraform-module",
            "path": "modules/topic",
        }
        r = execute_terraform_module(
            artifact,
            {"domain": "franz", "entity": "smoke_test"},
            plan_slug="g1-apply",
            dry_run=False,
        )
        assert r.status == "success", r.stderr_tail
        argv = log.read_text()
        assert "argv: init" in argv
        assert "argv: plan" in argv
        assert "argv: apply" in argv
        # Phases captured in order
        phases = [p["phase"] for p in r.per_phase]
        assert phases[:3] == ["init", "plan", "apply"]

    def test_init_failure_stops_before_plan(self, monkeypatch, tmp_path):
        log = _install_fake_terraform(tmp_path, exit_code=1)
        monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
        artifact = {
            "id": "module/topic",
            "type": "terraform-module",
            "path": "modules/topic",
        }
        r = execute_terraform_module(artifact, {"domain": "x"}, plan_slug="g1-fail")
        assert r.status == "failure"
        argv = log.read_text()
        # init ran once; plan/apply must NOT have run.
        assert argv.count("argv: init") == 1
        assert "argv: plan" not in argv
        assert "argv: apply" not in argv

    def test_credentials_passed_through_as_tf_vars(
        self, monkeypatch, tmp_path, capsys
    ):
        _install_fake_terraform(tmp_path)
        monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
        monkeypatch.setenv("CONFLUENT_CLOUD_API_KEY", "key123")
        monkeypatch.setenv("CONFLUENT_CLOUD_API_SECRET", "secret456")
        # Make sure we start clean — no pre-existing TF_VAR
        monkeypatch.delenv("TF_VAR_confluent_cloud_api_key", raising=False)
        monkeypatch.delenv("TF_VAR_confluent_cloud_api_secret", raising=False)

        artifact = {
            "id": "module/topic",
            "type": "terraform-module",
            "path": "modules/topic",
        }
        # We can't easily inspect the child env from a fake shell shim, but
        # we can verify the mapping logic by importing it directly.
        from tools.apply_engine import _TF_VAR_PASSTHROUGH

        assert _TF_VAR_PASSTHROUGH == {
            "CONFLUENT_CLOUD_API_KEY": "TF_VAR_confluent_cloud_api_key",
            "CONFLUENT_CLOUD_API_SECRET": "TF_VAR_confluent_cloud_api_secret",
        }
        # And that a normal run doesn't crash when those env vars are set.
        r = execute_terraform_module(
            artifact, {"domain": "x"}, plan_slug="g1-creds", dry_run=True
        )
        assert r.status == "dry-run"


# ---------------------------------------------------------------------------
# Workspace rendering
# ---------------------------------------------------------------------------


class TestWorkspaceRendering:
    def test_invalid_tf_idents_are_skipped_in_tfvars(self, monkeypatch, tmp_path):
        _install_fake_terraform(tmp_path)
        monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
        artifact = {
            "id": "module/topic",
            "type": "terraform-module",
            "path": "modules/topic",
        }
        # 'topic.name' and '1foo' aren't valid TF identifiers; the renderer
        # must silently drop them rather than generating invalid HCL that
        # would tank the entire apply.
        args = {
            "domain": "franz",
            "topic.name": "should-not-appear",
            "1foo": "also-skipped",
            "entity": "smoke",
        }
        r = execute_terraform_module(
            artifact, args, plan_slug="g1-idents", dry_run=True
        )
        assert r.status == "dry-run", r.stderr_tail
        tfvars = (
            PROJECT_ROOT / "outputs" / "runs" / "g1-idents" / "franz.auto.tfvars"
        ).read_text()
        assert "domain" in tfvars
        assert "entity" in tfvars
        assert "topic.name" not in tfvars
        assert "1foo" not in tfvars
