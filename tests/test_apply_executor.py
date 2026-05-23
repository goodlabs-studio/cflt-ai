"""Unit tests for the Phase G.1 terraform-module executor in apply_engine.py.

These tests do NOT exercise real Terraform or Confluent Cloud — they
either route around the binary entirely (dispatcher tests) or substitute
a fake `terraform` shell script on PATH that records its argv and exits
with a configurable code. Real end-to-end verification (a topic actually
appears in CC) is manual via the FRANZ Apply page on a sandbox env.

Phase 11.2 adds TestExecuteAccelerator — kustomize/oc dispatch coverage
for the new accelerator executor. Those tests patch subprocess.run
directly (no fake shell shim) and use the module-level `fake_binaries`
fixture to populate PATH so shutil.which() succeeds. The fixture is at
module scope (not nested inside TestExecuteAccelerator) so Plan 11-04's
TestAcceleratorProfileGating can reuse it without re-declaration.
"""

import os
import stat
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.apply_engine import (  # noqa: E402
    ExecutionResult,
    execute_artifact,
    execute_terraform_module,
)


# ---------------------------------------------------------------------------
# Shared accelerator fixtures (module-level for 11-04 reuse)
# ---------------------------------------------------------------------------


@pytest.fixture
def accelerator_artifact():
    """Canonical 5-layer LinuxONE accelerator MANIFEST entry (mirrors
    raw/repos/fsi-dsp/MANIFEST.yaml accelerator/confluent-on-linuxone)."""
    return {
        "id": "accelerator/confluent-on-linuxone",
        "type": "accelerator",
        "path": "accelerators/confluent-on-linuxone",
        "apply_sequence": [
            {
                "layer": "01-rbac",
                "path": "accelerators/confluent-on-linuxone/layers/01-rbac",
                "canon_key": "fsi.security.mds-rbac",
            },
            {
                "layer": "02-tls",
                "path": "accelerators/confluent-on-linuxone/layers/02-tls",
                "canon_key": "fsi.security.tls-fips",
            },
            {
                "layer": "03-schema-governance",
                "path": "accelerators/confluent-on-linuxone/layers/03-schema-governance",
                "canon_key": "fsi.schema.compatibility-full-transitive",
            },
            {
                "layer": "04-audit",
                "path": "accelerators/confluent-on-linuxone/layers/04-audit",
                "canon_key": "fsi.audit.events-retention",
            },
            {
                "layer": "05-flink",
                "path": "accelerators/confluent-on-linuxone/layers/05-flink",
                "canon_key": "fsi.flink.environment-mtls",
            },
        ],
    }


@pytest.fixture
def fake_binaries(tmp_path, monkeypatch):
    """Place dummy kustomize + oc binaries on PATH so shutil.which() resolves.

    Tests then patch tools.apply_engine.subprocess.run to control behavior.
    The binaries themselves are never executed in the test path — they only
    need to exist for the PATH check at the top of execute_accelerator() to
    pass. MODULE-level scope so Plan 11-04's TestAcceleratorProfileGating
    can reuse the same fixture without re-declaration.
    """
    for name in ("kustomize", "oc"):
        f = tmp_path / name
        f.write_text("#!/bin/sh\nexit 0\n")
        f.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path) + ":" + os.environ.get("PATH", ""))
    return tmp_path


@pytest.fixture
def apply_args():
    """Minimum args dict for _emit_layer_log to produce a well-formed entry."""
    return {
        "overlay": "base",
        "profile_name": "engineer",
        "operator": "test-operator",
        "plan_path": "outputs/plans/test-plan.md",
        "confirmation_status": "confirmed",
        "gate_results": [],
    }


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


# ---------------------------------------------------------------------------
# Accelerator executor (Phase 11.2) — mocked subprocess.run + activity-log
# ---------------------------------------------------------------------------
#
# Mocking strategy (CONTEXT.md): patch tools.apply_engine.subprocess.run to
# control returncode/stdout/stderr per phase. No live OpenShift cluster;
# fake_binaries fixture places dummy kustomize+oc on PATH so shutil.which()
# resolves; binaries are never actually invoked.


CANONICAL_LAYERS = [
    "01-rbac",
    "02-tls",
    "03-schema-governance",
    "04-audit",
    "05-flink",
]


class TestExecuteAccelerator:
    """Phase 11.2 — covers full-sequence success, dry-run-halt, layer-filter,
    per-layer ACTA-04 emission, binary-missing fail-closed, dispatcher routing."""

    def test_full_sequence_success(self, accelerator_artifact, fake_binaries, apply_args):
        """Test A: subprocess.run returns 0 for every call → 5 layers × 3 phases."""
        from tools.apply_engine import execute_accelerator
        ok = MagicMock(returncode=0, stdout="apiVersion: v1\nkind: Namespace\n", stderr="")
        with patch("tools.apply_engine.subprocess.run", return_value=ok), \
             patch("tools.apply_engine.emit_activity_log_apply"):
            result = execute_accelerator(accelerator_artifact, apply_args, "test-plan-A")
        assert result.status == "success", result.stderr_tail
        assert result.failed_layer is None
        # 3 phases (build, dry-run, apply) x 5 layers = 15 per_phase entries
        assert len(result.per_phase) == 15, [p["phase"] for p in result.per_phase]
        phases = " ".join(p["phase"] for p in result.per_phase)
        for layer in CANONICAL_LAYERS:
            assert layer in phases, f"missing layer {layer} from per_phase"

    def test_dry_run_server_failure_halts_at_02_tls(
        self, accelerator_artifact, fake_binaries, apply_args
    ):
        """Test B: oc dry-run for 02-tls returns 1 → halt before any 02-tls
        real apply and before any 03/04/05 layer phase.

        Call order per layer is: kustomize-build, oc-dry-run, oc-apply.
        Layer 01-rbac runs all 3 (calls 1-3). Layer 02-tls: call 4 = build (0),
        call 5 = dry-run (1 → halt). So we set side_effect to 4 zeros + one
        non-zero return.
        """
        from tools.apply_engine import execute_accelerator
        ok = MagicMock(returncode=0, stdout="x", stderr="")
        fail = MagicMock(returncode=1, stdout="", stderr="invalid manifest")
        side_effect = [ok, ok, ok, ok, fail]  # 01-rbac all 3 OK, 02-tls build OK, dry-run FAIL
        with patch("tools.apply_engine.subprocess.run", side_effect=side_effect), \
             patch("tools.apply_engine.emit_activity_log_apply"):
            result = execute_accelerator(accelerator_artifact, apply_args, "test-plan-B")
        assert result.status == "failure"
        assert result.failed_layer == "02-tls"
        phase_names = [p["phase"] for p in result.per_phase]
        # 01-rbac all three phases recorded
        assert "01-rbac:kustomize-build" in phase_names
        assert "01-rbac:oc-dry-run" in phase_names
        assert "01-rbac:oc-apply" in phase_names
        # 02-tls build + dry-run recorded; apply NOT (dry-run failed before real apply)
        assert "02-tls:kustomize-build" in phase_names
        assert "02-tls:oc-dry-run" in phase_names
        assert "02-tls:oc-apply" not in phase_names
        # 03/04/05 never touched
        for later in ("03-schema-governance", "04-audit", "05-flink"):
            for phase in ("kustomize-build", "oc-dry-run", "oc-apply"):
                assert f"{later}:{phase}" not in phase_names

    def test_layer_filter_runs_only_matching_layer(
        self, accelerator_artifact, fake_binaries, apply_args
    ):
        """Test C: layer_filter='03-schema-governance' → exactly 3 per_phase entries."""
        from tools.apply_engine import execute_accelerator
        ok = MagicMock(returncode=0, stdout="x", stderr="")
        with patch("tools.apply_engine.subprocess.run", return_value=ok), \
             patch("tools.apply_engine.emit_activity_log_apply"):
            result = execute_accelerator(
                accelerator_artifact, apply_args, "test-plan-C",
                layer_filter="03-schema-governance",
            )
        assert result.status == "success", result.stderr_tail
        assert len(result.per_phase) == 3, [p["phase"] for p in result.per_phase]
        for p in result.per_phase:
            assert p["phase"].startswith("03-schema-governance:"), p["phase"]

    def test_acta04_emission_per_layer(
        self, accelerator_artifact, fake_binaries, apply_args
    ):
        """Test D: full sequence emits exactly 5 emit_activity_log_apply calls,
        one per layer, each with layer_id kwarg matching the layer name in order."""
        from tools.apply_engine import execute_accelerator
        ok = MagicMock(returncode=0, stdout="x", stderr="")
        with patch("tools.apply_engine.subprocess.run", return_value=ok), \
             patch("tools.apply_engine.emit_activity_log_apply") as mock_emit:
            execute_accelerator(accelerator_artifact, apply_args, "test-plan-D")
        assert mock_emit.call_count == 5, [c.kwargs.get("layer_id") for c in mock_emit.call_args_list]
        layer_ids_in_order = [c.kwargs.get("layer_id") for c in mock_emit.call_args_list]
        assert layer_ids_in_order == CANONICAL_LAYERS, layer_ids_in_order

    def test_dry_run_flag_skips_real_apply(
        self, accelerator_artifact, fake_binaries, apply_args
    ):
        """Test E: dry_run=True → oc apply (real) never called. 2 phases × 5 layers."""
        from tools.apply_engine import execute_accelerator
        ok = MagicMock(returncode=0, stdout="x", stderr="")
        with patch("tools.apply_engine.subprocess.run", return_value=ok) as mock_run, \
             patch("tools.apply_engine.emit_activity_log_apply"):
            result = execute_accelerator(
                accelerator_artifact, apply_args, "test-plan-E", dry_run=True,
            )
        assert result.status == "dry-run", result.stderr_tail
        # 2 phases (build + dry-run) × 5 layers = 10 subprocess.run calls
        assert mock_run.call_count == 10, mock_run.call_count
        # per_phase mirrors the subprocess.run call count
        assert len(result.per_phase) == 10, [p["phase"] for p in result.per_phase]
        # No oc-apply phases recorded
        phase_names = [p["phase"] for p in result.per_phase]
        for p in phase_names:
            assert not p.endswith(":oc-apply"), p

    def test_missing_apply_sequence_returns_failure(self, fake_binaries):
        """Test F: artifact without apply_sequence → failure with clear stderr."""
        from tools.apply_engine import execute_accelerator
        bad = {"id": "accelerator/no-sequence", "type": "accelerator"}
        result = execute_accelerator(bad, {}, "p-F")
        assert result.status == "failure"
        assert "apply_sequence" in result.stderr_tail

    def test_empty_apply_sequence_returns_failure(self, fake_binaries):
        """Empty list is also a failure (no work to do is a misconfiguration)."""
        from tools.apply_engine import execute_accelerator
        bad = {"id": "accelerator/empty", "type": "accelerator", "apply_sequence": []}
        result = execute_accelerator(bad, {}, "p-F2")
        assert result.status == "failure"
        assert "apply_sequence" in result.stderr_tail

    def test_kustomize_binary_missing(
        self, accelerator_artifact, apply_args, monkeypatch, tmp_path
    ):
        """Test G: no kustomize on PATH → failure mentioning 'kustomize'."""
        from tools.apply_engine import execute_accelerator
        monkeypatch.setenv("PATH", str(tmp_path))  # empty dir, no binaries
        result = execute_accelerator(accelerator_artifact, apply_args, "p-G")
        assert result.status == "failure"
        assert "kustomize" in result.stderr_tail.lower()

    def test_oc_binary_missing(
        self, accelerator_artifact, apply_args, monkeypatch, tmp_path
    ):
        """Test H: kustomize present but oc missing → failure mentioning 'oc'."""
        from tools.apply_engine import execute_accelerator
        f = tmp_path / "kustomize"
        f.write_text("#!/bin/sh\nexit 0\n")
        f.chmod(0o755)
        monkeypatch.setenv("PATH", str(tmp_path))
        result = execute_accelerator(accelerator_artifact, apply_args, "p-H")
        assert result.status == "failure"
        # stderr_tail mentions oc explicitly (not generic 'binary missing')
        assert "oc" in result.stderr_tail.lower()
        # And does NOT mention kustomize (kustomize was found)
        assert "kustomize" not in result.stderr_tail.lower()

    def test_dispatcher_routes_accelerator_to_execute_accelerator(self):
        """Test I: execute_artifact(type='accelerator') routes to execute_accelerator
        and passes args['layer'] through as layer_filter."""
        artifact = {
            "id": "accelerator/test",
            "type": "accelerator",
            "apply_sequence": [{"layer": "x", "path": "p", "canon_key": "k"}],
        }
        with patch("tools.apply_engine.execute_accelerator") as mock_exec:
            mock_exec.return_value = ExecutionResult(status="success", duration_seconds=0.0)
            execute_artifact(artifact, {"layer": "x"}, plan_slug="dispatcher-test")
        mock_exec.assert_called_once()
        assert mock_exec.call_args.kwargs.get("layer_filter") == "x"

    def test_dispatcher_routes_accelerator_without_layer_arg(self):
        """layer arg absence → layer_filter=None (walks full sequence)."""
        artifact = {
            "id": "accelerator/test",
            "type": "accelerator",
            "apply_sequence": [{"layer": "x", "path": "p", "canon_key": "k"}],
        }
        with patch("tools.apply_engine.execute_accelerator") as mock_exec:
            mock_exec.return_value = ExecutionResult(status="success", duration_seconds=0.0)
            execute_artifact(artifact, {}, plan_slug="dispatcher-no-layer")
        mock_exec.assert_called_once()
        assert mock_exec.call_args.kwargs.get("layer_filter") is None

    def test_terraform_module_regression_still_skipped_for_scenario(self):
        """Test J: existing dispatcher behavior for type='scenario' unchanged."""
        artifact = {"id": "scenario/cc-gcp", "type": "scenario"}
        result = execute_artifact(artifact, {}, plan_slug="regression-J")
        assert result.status == "skipped"
        assert "Phase G.2" in result.stderr_tail

    def test_failed_kustomize_build_halts_at_first_layer(
        self, accelerator_artifact, fake_binaries, apply_args
    ):
        """Bonus: kustomize-build failure on 01-rbac halts before any oc invocation."""
        from tools.apply_engine import execute_accelerator
        fail = MagicMock(returncode=1, stdout="", stderr="kustomize error")
        with patch("tools.apply_engine.subprocess.run", return_value=fail) as mock_run, \
             patch("tools.apply_engine.emit_activity_log_apply"):
            result = execute_accelerator(accelerator_artifact, apply_args, "p-build-fail")
        assert result.status == "failure"
        assert result.failed_layer == "01-rbac"
        # Only one subprocess.run call — the kustomize build that failed
        assert mock_run.call_count == 1
        assert len(result.per_phase) == 1
        assert result.per_phase[0]["phase"] == "01-rbac:kustomize-build"

    def test_oc_apply_real_failure_halts_at_failing_layer(
        self, accelerator_artifact, fake_binaries, apply_args
    ):
        """oc apply (real) failure on 03-schema-governance halts before 04/05."""
        from tools.apply_engine import execute_accelerator
        ok = MagicMock(returncode=0, stdout="x", stderr="")
        fail = MagicMock(returncode=1, stdout="", stderr="apply rejected")
        # 01-rbac (3 ok) + 02-tls (3 ok) + 03-sg (build ok, dry-run ok, apply FAIL)
        side_effect = [ok] * 8 + [fail]
        with patch("tools.apply_engine.subprocess.run", side_effect=side_effect), \
             patch("tools.apply_engine.emit_activity_log_apply"):
            result = execute_accelerator(accelerator_artifact, apply_args, "p-apply-fail")
        assert result.status == "failure"
        assert result.failed_layer == "03-schema-governance"
        phase_names = [p["phase"] for p in result.per_phase]
        assert "03-schema-governance:oc-apply" in phase_names
        # 04 + 05 never touched
        for later in ("04-audit", "05-flink"):
            assert not any(p.startswith(f"{later}:") for p in phase_names)

    def test_layer_filter_no_match_returns_failure(
        self, accelerator_artifact, fake_binaries, apply_args
    ):
        """Unknown layer_filter → failure with clear stderr (vs silent no-op)."""
        from tools.apply_engine import execute_accelerator
        result = execute_accelerator(
            accelerator_artifact, apply_args, "p-bad-filter",
            layer_filter="99-nonexistent",
        )
        assert result.status == "failure"
        assert "99-nonexistent" in result.stderr_tail


# ---------------------------------------------------------------------------
# emit_activity_log_apply layer_id backward-compat
# ---------------------------------------------------------------------------


class TestEmitActivityLogLayerIdBackCompat:
    """Verify the new layer_id kwarg preserves byte-identical entry shape
    for terraform-module callers (omit layer_id → no **Layer:** field)."""

    def test_omitting_layer_id_produces_11_field_entry(self, tmp_path, monkeypatch):
        from tools.apply_engine import emit_activity_log_apply
        # Redirect activity log into tmp_path
        monkeypatch.setattr("tools.apply_engine.PROJECT_ROOT", tmp_path)
        emit_activity_log_apply(
            overlay="base",
            plan_path="outputs/plans/x.md",
            artifact_id="module/topic",
            profile_name="engineer",
            confirmation_status="confirmed",
            execution_result="success",
            duration_seconds=1.0,
            gate_results=[],
            operator="alice",
        )
        log_files = list((tmp_path / "wiki" / "activity").glob("*.md"))
        assert len(log_files) == 1
        content = log_files[0].read_text()
        assert "**Layer:**" not in content, "layer_id omitted should NOT emit **Layer:** field"
        assert "**Artifact:** module/topic" in content
        assert "**Plan:** outputs/plans/x.md" in content

    def test_layer_id_set_inserts_layer_field(self, tmp_path, monkeypatch):
        from tools.apply_engine import emit_activity_log_apply
        monkeypatch.setattr("tools.apply_engine.PROJECT_ROOT", tmp_path)
        emit_activity_log_apply(
            overlay="base",
            plan_path="outputs/plans/x.md",
            artifact_id="accelerator/confluent-on-linuxone",
            profile_name="engineer",
            confirmation_status="confirmed",
            execution_result="success",
            duration_seconds=1.0,
            gate_results=[],
            operator="alice",
            layer_id="02-tls",
        )
        log_files = list((tmp_path / "wiki" / "activity").glob("*.md"))
        assert len(log_files) == 1
        content = log_files[0].read_text()
        assert "**Layer:** 02-tls" in content
        # **Layer:** appears between **Artifact:** and **Plan:**
        artifact_idx = content.index("**Artifact:**")
        layer_idx = content.index("**Layer:**")
        plan_idx = content.index("**Plan:**")
        assert artifact_idx < layer_idx < plan_idx, content
