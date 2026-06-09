#!/usr/bin/env python3
"""
Apply engine for /dsp:apply act rail. Enforces least-privilege policy profiles,
emits provenance activity log entries, and creates wiki incident articles.

Requirements: ACTA-01 (apply gate chain), ACTA-02 (bypass prevention),
              ACTA-03 (profile enforcement), ACTA-04 (activity log),
              ACTA-05 (incident articles)
"""
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import sys

# Add project root to path for canon.stack import (matches act_gates.py pattern)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from canon.stack import active_layers, _layer_roots  # noqa: E402 (after sys.path.insert)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROFILES_DIR = PROJECT_ROOT / "tools" / "profiles"

# Explicit set of valid profile names — fail-closed: unrecognized names raise ValueError
# H.4b: developer/sandbox added as first developer-family profile. Slash in name denotes
# nested directory on disk: tools/profiles/developer/sandbox.json (see _profile_path).
VALID_PROFILES = {"read-only", "engineer", "break-glass", "developer/sandbox"}

# Tier order for hierarchy comparison: read-only < engineer < break-glass
PROFILE_TIER_ORDER = ["read-only", "engineer", "break-glass"]

# Profile families (H.4a):
#   - "operator" — tier cascade (read-only < engineer < break-glass) via PROFILE_TIER_ORDER.
#                  Profile JSON MUST have "allowed_operations" list. Tool permission via
#                  check_tool_permitted() consults tool_classification.json (G.2c).
#   - "developer" — per-profile tool_overrides map. Profile JSON MUST have
#                   "tool_overrides" dict AND "skill_blocklist" list (may be empty).
#                   NO allowed_operations field (operator-only). Authored in H.4b.
# Unknown family value → ValueError. Missing family field → defaults to "operator" for
# back-compat with pre-H.4a external profiles; log the default-application.
VALID_FAMILIES = {"operator", "developer"}


# ---------------------------------------------------------------------------
# Tool Classification (ACTG-01)
# ---------------------------------------------------------------------------

_tool_classification_cache = None


def load_tool_classification() -> Dict:
    """Load tool_classification.json. Cached after first load."""
    global _tool_classification_cache
    if _tool_classification_cache is None:
        path = PROFILES_DIR / "tool_classification.json"
        _tool_classification_cache = json.loads(path.read_text())
    return _tool_classification_cache


def check_tool_permitted(profile_name: str, tool_name: str, customer: Optional[str] = None) -> bool:
    """Check whether profile_name permits invoking tool_name.

    Branches on profile family (H.4a):
      - operator family: uses tier hierarchy (read-only < engineer < break-glass) +
        tool_classification.json tier map. Identical to v1.0 Phase 3c behavior.
      - developer family: reads `tool_overrides` map from the profile JSON.
        Tool is permitted if present in the map; denied otherwise (fail-closed).

    Returns False (fail-closed) when:
      - tool_name is not in classification table (operator branch)
      - tool_name is not in tool_overrides map (developer branch)
      - profile_name is not in VALID_PROFILES (caller error — raises via load_profile)

    Args:
        profile_name: One of VALID_PROFILES.
        tool_name:    Exact mcp-confluent tool name.
        customer:     Optional customer overlay name (keyword-only — see load_profile).

    Returns:
        True if permitted; False otherwise (fail-closed).

    Raises:
        ValueError: If profile family is unknown (defensive — load_profile validates first).
    """
    profile = load_profile(profile_name, customer=customer)
    family = profile["family"]  # always present after H.4a load (defaulted or explicit)

    if family == "operator":
        # v1.0 Phase 3c branch — byte-identical to pre-H.4a behavior.
        classification = load_tool_classification()
        tools = classification.get("tools", {})

        if tool_name not in tools:
            return False

        required_tier = tools[tool_name]
        profile_idx = PROFILE_TIER_ORDER.index(profile_name)
        required_idx = PROFILE_TIER_ORDER.index(required_tier)
        return profile_idx >= required_idx

    elif family == "developer":
        # H.4a developer-branch — per-profile tool_overrides dispatch.
        # Tools listed in the map are permitted; anything else is denied (fail-closed).
        # The map's value-strings (developer-sandbox, developer-restricted, etc.) are
        # informational at H.4a; H.4b's developer-sandbox profile pins the value set.
        overrides = profile.get("tool_overrides", {})
        return tool_name in overrides

    else:
        # Defensive — load_profile validates family before we get here, but if a
        # third party calls load_profile with a malformed profile and the validation
        # is bypassed, raise rather than silently permit.
        raise ValueError(f"Unknown profile family {family!r} for profile {profile_name!r}")


def check_skill_permitted(
    profile_name: str,
    skill_name: str,
    customer: Optional[str] = None,
) -> bool:
    """Check whether profile_name permits invoking skill_name (H.4b).

    Consults the profile's `skill_blocklist` (developer family) or returns True
    unconditionally (operator family, which has no blocklist field).

    Use this at any cflt-ai skill entry-point (e.g., /dsp:apply) to gate access
    based on the active profile. Currently wired into H.4b's negative-space test
    matrix only — production callers in /dsp:apply etc. follow in subsequent phases.

    Args:
        profile_name: One of VALID_PROFILES.
        skill_name:   Skill identifier (e.g., 'dsp-apply', 'wiki-validate').
        customer:     Optional customer overlay name (keyword-only).

    Returns:
        False if skill_name is in the profile's skill_blocklist, True otherwise.
        Operator profiles (no blocklist field) return True for every skill.

    Raises:
        ValueError: If profile_name is not in VALID_PROFILES (via load_profile).
    """
    profile = load_profile(profile_name, customer=customer)
    blocklist = profile.get("skill_blocklist", [])
    return skill_name not in blocklist


# ---------------------------------------------------------------------------
# Profile Loading (ACTA-03 + H.4a family schema)
# ---------------------------------------------------------------------------

def _normalize_and_validate_profile(profile_data: Dict, profile_name: str) -> Dict:
    """Inject family default + validate per-family invariants (H.4a D-02, D-03, D-07)."""
    # D-02: Missing family field defaults to "operator" for back-compat with pre-H.4a
    # external/customer fixtures. Surface the default-application via stderr so test
    # runs make legacy shapes visible.
    if "family" not in profile_data:
        sys.stderr.write(
            f"[apply_engine] profile {profile_name!r} missing 'family' field; "
            f"defaulting to 'operator' (pre-H.4a shape)\n"
        )
        profile_data["family"] = "operator"

    # D-03: Unknown family value is a hard error (fail-closed).
    family = profile_data["family"]
    if family not in VALID_FAMILIES:
        raise ValueError(
            f"Profile {profile_name!r} has unknown family {family!r} — "
            f"must be one of {sorted(VALID_FAMILIES)}"
        )

    # D-07: Per-family invariants.
    if family == "operator":
        allowed_ops = profile_data.get("allowed_operations")
        if not isinstance(allowed_ops, list):
            raise ValueError(
                f"Operator profile {profile_name!r} is missing required "
                f"'allowed_operations' list"
            )
    elif family == "developer":
        # D-06: Developer profiles MUST have tool_overrides (dict) AND skill_blocklist (list).
        # They MUST NOT have allowed_operations (operator-only).
        tool_overrides = profile_data.get("tool_overrides")
        if not isinstance(tool_overrides, dict):
            raise ValueError(
                f"Developer profile {profile_name!r} is missing required "
                f"'tool_overrides' dict"
            )
        skill_blocklist = profile_data.get("skill_blocklist")
        if not isinstance(skill_blocklist, list):
            raise ValueError(
                f"Developer profile {profile_name!r} is missing required "
                f"'skill_blocklist' list (may be empty)"
            )
        if "allowed_operations" in profile_data:
            raise ValueError(
                f"Developer profile {profile_name!r} must NOT have "
                f"'allowed_operations' field (operator-only)"
            )

    return profile_data


def _profile_path(profiles_root: Path, profile_name: str) -> Path:
    """Resolve profile_name (possibly slash-separated) to filesystem path under profiles_root.

    Slashes in profile_name denote nested directories under profiles_root. Pathlib's
    `__truediv__` already accepts slash-containing strings as relative paths, so e.g.
    `profiles_root / "developer/sandbox.json"` resolves to
    `profiles_root / "developer" / "sandbox.json"`. No additional split logic needed.

    H.4b: introduced so load_profile() can route "developer/sandbox" to the on-disk
    nested layout while preserving v1.0 callers ("engineer" → engineer.json).
    """
    return profiles_root / (profile_name + ".json")


def load_profile(profile_name: str, *, customer: Optional[str] = None) -> Dict:
    """Load a policy profile by name from PROFILES_DIR.

    Profile names must be one of the VALID_PROFILES set. Unknown names raise
    ValueError immediately (fail-closed — never silently degrades to permissive mode).

    If customer is provided, checks canon/customer/<name>/profiles/<profile>.json first,
    falling back to the base profile in PROFILES_DIR if the customer overlay is absent.

    After loading, the profile is run through _normalize_and_validate_profile() which
    injects family="operator" default when absent (H.4a back-compat) and validates
    per-family invariants (operator → allowed_operations; developer → tool_overrides +
    skill_blocklist, no allowed_operations).

    Args:
        profile_name: Name of the profile to load (e.g., "engineer").
        customer:     Optional customer name for overlay resolution (keyword-only).

    Returns:
        Dict with keys: name (str), description (str), family (str), and either
        allowed_operations (list, operator family) or tool_overrides (dict) +
        skill_blocklist (list) for the developer family.

    Raises:
        ValueError: If profile_name is not in VALID_PROFILES, is empty, has an unknown
                    family value, or violates per-family invariants.
    """
    if not profile_name:
        raise ValueError(f"Unknown profile: {profile_name!r} — must be one of {VALID_PROFILES}")

    if profile_name not in VALID_PROFILES:
        raise ValueError(
            f"Unknown profile: {profile_name!r} — must be one of {sorted(VALID_PROFILES)}"
        )

    # Check customer overlay first (ACTG-04)
    # H.4b: customer overlay also routes through _profile_path so customer-side
    # developer/sandbox.json overrides work (H.4c will exercise this path).
    # Silos: search every canon root (repo + CFLT_CANON_EXTERNAL_PATH) so a client's
    # profiles can live in their private overlay repo, never in the shared tree.
    if customer:
        for root in _layer_roots():
            customer_profile = _profile_path(
                root / "customer" / customer / "profiles",
                profile_name,
            )
            if customer_profile.exists():
                return _normalize_and_validate_profile(
                    json.loads(customer_profile.read_text()), profile_name
                )

    # Fall back to base profile (H.4b: slash-separated names resolve to nested dirs)
    profile_path = _profile_path(PROFILES_DIR, profile_name)
    profile_data = json.loads(profile_path.read_text())
    return _normalize_and_validate_profile(profile_data, profile_name)


# ---------------------------------------------------------------------------
# Profile Enforcement (ACTA-03)
# ---------------------------------------------------------------------------

def check_profile_permits(profile: Dict, artifact_id: str) -> bool:
    """Check whether a policy profile permits a given artifact operation.

    Wildcard "*" in allowed_operations permits all artifact IDs.
    Empty allowed_operations list denies all operations (read-only semantics).
    Exact string match required for non-wildcard entries.

    Args:
        profile:     Profile dict as returned by load_profile().
        artifact_id: The fsi-dsp artifact ID to check (e.g., "module/topic").

    Returns:
        True if the operation is permitted; False otherwise.
    """
    allowed: List[str] = profile.get("allowed_operations", [])

    if "*" in allowed:
        return True

    return artifact_id in allowed


# ---------------------------------------------------------------------------
# Execution (Phase G.1 — terraform-module executor)
# ---------------------------------------------------------------------------
#
# Step 7 of /dsp-apply previously emitted a "deferred-to-mcp-runtime" stub.
# Phase G.1 replaces that for `terraform-module` artifacts: render the args
# as tfvars, run terraform plan + apply inside an isolated workspace, and
# return a structured ExecutionResult. State persists per-plan-slug so
# re-applies are idempotent updates rather than duplicate creations.
#
# Scope:
#   - Supports artifact.type == "terraform-module" only.
#     (module/topic, module/flink, and a future module/cc-cluster-basic.)
#   - Other artifact types (scenario/*, role/*, script/*) still fall back
#     to the stub. Composite-sequence + non-terraform execution is Phase G.2+.
#   - Credentials: maps CONFLUENT_CLOUD_API_KEY / _API_SECRET (set by FRANZ
#     from its managed mcp.env) into TF_VAR_* so the Confluent provider
#     picks them up automatically. Operator's user-mode TFE auth is not
#     used in G.1.
#   - State: lives under outputs/runs/<plan-slug>/.terraform/, local backend.
#     Remote backend for FSI overlays is Phase G.2.

FSI_DSP_ROOT = PROJECT_ROOT / "raw" / "repos" / "fsi-dsp"

# Credentials FRANZ injects from {userData}/mcp.env. The Confluent
# Terraform provider auto-discovers cloud_api_key / cloud_api_secret from
# variables of those names, so we shim via TF_VAR_*.
_TF_VAR_PASSTHROUGH = {
    "CONFLUENT_CLOUD_API_KEY": "TF_VAR_confluent_cloud_api_key",
    "CONFLUENT_CLOUD_API_SECRET": "TF_VAR_confluent_cloud_api_secret",
}


@dataclass
class ExecutionResult:
    """Structured outcome of an artifact execution.

    Single source of truth for what /dsp:apply Step 7 produces. Fields map
    1:1 to the activity-log and incident-article schemas downstream.

    `status` is the compact label embedded in activity log entries; treat
    these as a closed set:
      - "success"  — every phase completed; resources are in the desired state
      - "failure"  — execution attempted and at least one phase errored;
                     no rollback was attempted (see partial state in stdout)
      - "dry-run"  — plan phase only (no apply); used when the operator's
                     overlay or profile blocks state mutations
      - "skipped"  — artifact type isn't supported by any executor in this
                     version (e.g. scenario/* in G.1); equivalent to the
                     historical "deferred-to-mcp-runtime" stub
      - "refused"  — profile gating denied the operation BEFORE any execution
                     attempt (Phase 11.4 — accelerator + read-only profile).
                     Distinct from "skipped" (no executor exists for this
                     artifact type) and "failure" (executor ran but errored).
                     Emits exactly one ACTA-04 entry with
                     execution_result="refused" and no layer_id.

    `failed_layer` is populated only by the accelerator executor when an
    apply_sequence layer aborts the walk (kustomize / oc dry-run / oc apply
    non-zero exit). None for every other executor and on success.
    """

    status: str
    duration_seconds: float
    stdout_tail: str = ""
    stderr_tail: str = ""
    per_phase: List[Dict[str, str]] = field(default_factory=list)
    outputs: Dict[str, str] = field(default_factory=dict)
    failed_layer: Optional[str] = None

    def to_activity_log_string(self) -> str:
        """Compact form for emit_activity_log_apply()'s execution_result field."""
        return self.status


def execute_artifact(
    artifact: Dict,
    args: Dict[str, str],
    plan_slug: str,
    dry_run: bool = False,
) -> ExecutionResult:
    """Dispatch on artifact.type and execute. Returns ExecutionResult.

    Supported types:
      - "terraform-module" → execute_terraform_module (Phase G.1)
      - "accelerator"      → execute_accelerator (Phase 11.2 — LinuxONE
                             5-layer kustomize/oc dispatch). args.get("layer")
                             is passed through as layer_filter for single-layer
                             execution; absence walks the full apply_sequence.

    For unsupported types, returns status="skipped" (G.1 backstop until
    G.2 adds mcp-confluent tool-call sequences for scenario/* etc.).
    """
    artifact_type = artifact.get("type", "")
    if artifact_type == "terraform-module":
        return execute_terraform_module(artifact, args, plan_slug, dry_run=dry_run)
    elif artifact_type == "accelerator":
        return execute_accelerator(
            artifact, args, plan_slug, dry_run=dry_run,
            profile_name=args.get("profile_name"),
            layer_filter=args.get("layer"),
        )
    return ExecutionResult(
        status="skipped",
        duration_seconds=0.0,
        stderr_tail=(
            f"artifact.type='{artifact_type}' has no executor in this version; "
            "Phase G.2 will add support."
        ),
    )


def execute_terraform_module(
    artifact: Dict,
    args: Dict[str, str],
    plan_slug: str,
    dry_run: bool = False,
) -> ExecutionResult:
    """Run terraform plan + apply against a fsi-dsp terraform-module artifact.

    Workspace layout:
        outputs/runs/<plan_slug>/
          main.tf            — wraps the fsi-dsp module by absolute path
          franz.auto.tfvars  — rendered from `args`
          .terraform/        — provider plugins (created by `terraform init`)
          terraform.tfstate  — local state (lives next to main.tf)
    """
    started = time.monotonic()
    per_phase: List[Dict[str, str]] = []

    module_path = artifact.get("path", "")
    if not module_path:
        return ExecutionResult(
            status="failure",
            duration_seconds=0.0,
            stderr_tail=f"artifact {artifact.get('id')!r} has no 'path'",
        )
    module_abs = (FSI_DSP_ROOT / module_path).resolve()
    if not module_abs.is_dir():
        return ExecutionResult(
            status="failure",
            duration_seconds=0.0,
            stderr_tail=f"module path does not exist: {module_abs}",
        )

    workspace = PROJECT_ROOT / "outputs" / "runs" / plan_slug
    workspace.mkdir(parents=True, exist_ok=True)
    _render_root_module(workspace, module_abs, args)

    env = os.environ.copy()
    for src, dst in _TF_VAR_PASSTHROUGH.items():
        if src in env and dst not in env:
            env[dst] = env[src]

    tf = shutil.which("terraform")
    if not tf:
        return ExecutionResult(
            status="failure",
            duration_seconds=time.monotonic() - started,
            stderr_tail="`terraform` not on PATH — install Terraform >= 1.6",
        )

    stdout_chunks: List[str] = []
    stderr_chunks: List[str] = []

    def _run(phase: str, cmd: List[str]) -> int:
        proc = subprocess.run(
            cmd,
            cwd=workspace,
            env=env,
            capture_output=True,
            text=True,
            timeout=900,  # 15 min cap per phase — enough for slow provider init
        )
        stdout_chunks.append(f"=== {phase} stdout ===\n{proc.stdout}")
        stderr_chunks.append(f"=== {phase} stderr ===\n{proc.stderr}")
        per_phase.append({"phase": phase, "exit_code": str(proc.returncode)})
        return proc.returncode

    if _run("init", [tf, "init", "-input=false", "-no-color"]) != 0:
        return _finalize("failure", started, stdout_chunks, stderr_chunks, per_phase)

    if _run("plan", [tf, "plan", "-input=false", "-no-color", "-out=franz.tfplan"]) != 0:
        return _finalize("failure", started, stdout_chunks, stderr_chunks, per_phase)

    if dry_run:
        return _finalize("dry-run", started, stdout_chunks, stderr_chunks, per_phase)

    if _run("apply", [tf, "apply", "-input=false", "-no-color", "franz.tfplan"]) != 0:
        return _finalize("failure", started, stdout_chunks, stderr_chunks, per_phase)

    outputs: Dict[str, str] = {}
    out_proc = subprocess.run(
        [tf, "output", "-json"],
        cwd=workspace,
        env=env,
        capture_output=True,
        text=True,
    )
    if out_proc.returncode == 0:
        try:
            for k, v in json.loads(out_proc.stdout).items():
                # `value` is the unwrapped output; stringify for compactness.
                outputs[k] = str(v.get("value", "")) if isinstance(v, dict) else str(v)
        except json.JSONDecodeError:
            pass

    result = _finalize("success", started, stdout_chunks, stderr_chunks, per_phase)
    result.outputs = outputs
    return result


def execute_accelerator(
    artifact: Dict,
    args: Dict[str, str],
    plan_slug: str,
    dry_run: bool = False,
    profile_name: Optional[str] = None,
    layer_filter: Optional[str] = None,
) -> ExecutionResult:
    """Walk an accelerator artifact's apply_sequence layer-by-layer (Phase 11.2).

    For each layer in `artifact["apply_sequence"]` (or just the single matching
    layer when `layer_filter` is set):

      1. `kustomize build {layer.path}` — captures rendered manifest on stdout
      2. `oc apply --dry-run=server -f -` — server-side validation
      3. `oc apply -f -` — only when dry_run=False AND dry-run passed

    Halts on any non-zero exit before subsequent layers (and before the real
    apply within the failing layer). ExecutionResult.failed_layer is set to
    the layer name on failure; None on success.

    Per-layer ACTA-04 emission: this executor calls emit_activity_log_apply()
    once per layer with the new `layer_id` kwarg (one entry per layer, not one
    summary entry). This DEVIATES from execute_terraform_module's contract
    (where the /dsp:apply Step 8 caller emits a single summary entry) because
    only execute_accelerator knows about the layer iteration. CONTEXT.md D-03
    locked this as the intended shape ("Reuse ACTA-04 11-field schema + new
    layer_id field. One entry per layer.").

    Mocking note: tests patch `tools.apply_engine.subprocess.run` and
    `tools.apply_engine.emit_activity_log_apply` to exercise without a live
    cluster or kustomize/oc binaries. PATH must still contain placeholder
    binaries so shutil.which() succeeds — see fake_binaries fixture in
    tests/test_apply_executor.py.

    Args:
        artifact:     MANIFEST entry dict; must contain id, path, apply_sequence list.
        args:         Plan args dict; must contain at least 'overlay', 'profile_name',
                      'operator', 'plan_path' for per-layer activity-log emission.
                      Optional 'gate_results' (list), 'override_reason' (str),
                      'confirmation_source' (str), 'confirmation_status' (str).
        plan_slug:    Workspace key (per-plan + per-layer subdirectory isolation).
        dry_run:      If True, run kustomize+oc-dry-run only, skip real oc-apply.
        profile_name: Phase 11.4 pre-flight gate. When supplied, the executor
                      loads the named profile and calls check_profile_permits()
                      BEFORE any subprocess invocation or per-layer ACTA-04
                      emission. On deny: emits a single blocked-by-profile
                      ACTA-04 entry (execution_result="refused", no layer_id)
                      and returns ExecutionResult(status="refused", ...).
                      When None (default): the gate is SKIPPED — back-compat
                      with Plan 11-02 tests that don't supply the kwarg.
                      Unknown profile names are caught (ValueError from
                      load_profile) and converted to status="refused" with
                      the offending name in stderr_tail (no raise).
        layer_filter: If set, run only the matching layer; absent walks full sequence.

    Returns:
        ExecutionResult with status in {"success", "failure", "dry-run", "refused"}.
        failed_layer is None on success/dry-run/refused; set to the layer name
        only on per-layer execution failure.
    """
    started = time.monotonic()
    per_phase: List[Dict[str, str]] = []
    stdout_chunks: List[str] = []
    stderr_chunks: List[str] = []

    # ---------------------------------------------------------------------
    # Phase 11.4 pre-flight profile gate. Runs BEFORE apply_sequence
    # validation so refused operations never produce per-layer ACTA-04
    # entries or touch kustomize/oc. Skipped when profile_name=None
    # (back-compat with Plan 11-02 callers).
    # ---------------------------------------------------------------------
    artifact_id = artifact.get("id", "")
    if profile_name is not None:
        try:
            profile = load_profile(profile_name, customer=args.get("overlay"))
        except (ValueError, FileNotFoundError, OSError) as exc:
            return ExecutionResult(
                status="refused",
                duration_seconds=0.0,
                stderr_tail=f"Unknown or unreadable profile {profile_name!r}: {exc}",
            )
        if not check_profile_permits(profile, artifact_id):
            # Single ACTA-04 entry (blocked-by-profile) — no layer_id,
            # no per-layer entries. confirmation_status="blocked" mirrors
            # the /dsp:apply Step 5 "blocked-by-profile" log shape.
            emit_activity_log_apply(
                overlay=args.get("overlay", "base"),
                plan_path=args.get("plan_path", ""),
                artifact_id=artifact_id,
                profile_name=profile_name,
                confirmation_status="blocked",
                execution_result="refused",
                duration_seconds=0.0,
                gate_results=args.get("gate_results", []) or [],
                operator=args.get("operator", "unknown"),
            )
            return ExecutionResult(
                status="refused",
                duration_seconds=0.0,
                stderr_tail=(
                    f"Profile {profile_name!r} does not permit operation on "
                    f"{artifact_id!r}"
                ),
            )

    apply_sequence = artifact.get("apply_sequence", [])
    if not apply_sequence:
        return ExecutionResult(
            status="failure",
            duration_seconds=0.0,
            stderr_tail=(
                f"artifact {artifact.get('id')!r} has no 'apply_sequence' "
                "or it is empty"
            ),
        )

    if layer_filter:
        apply_sequence = [
            layer for layer in apply_sequence
            if layer.get("layer") == layer_filter
        ]
        if not apply_sequence:
            return ExecutionResult(
                status="failure",
                duration_seconds=0.0,
                stderr_tail=(
                    f"layer_filter {layer_filter!r} matched no layer in "
                    "apply_sequence"
                ),
            )

    kustomize_bin = shutil.which("kustomize")
    if not kustomize_bin:
        return ExecutionResult(
            status="failure",
            duration_seconds=round(time.monotonic() - started, 1),
            stderr_tail="`kustomize` not on PATH — install kustomize >= 5.0",
        )
    oc_bin = shutil.which("oc")
    if not oc_bin:
        return ExecutionResult(
            status="failure",
            duration_seconds=round(time.monotonic() - started, 1),
            stderr_tail="`oc` not on PATH — install OpenShift CLI",
        )

    # artifact_id was already set at the top of the function (pre-flight gate)
    for layer_entry in apply_sequence:
        layer_name = layer_entry.get("layer", "")
        layer_path = layer_entry.get("path", "")
        layer_abs = (FSI_DSP_ROOT / layer_path).resolve()

        workspace = PROJECT_ROOT / "outputs" / "runs" / plan_slug / layer_name
        workspace.mkdir(parents=True, exist_ok=True)

        # Phase 1: kustomize build {layer.path} — capture rendered manifest
        build_proc = subprocess.run(
            [kustomize_bin, "build", str(layer_abs)],
            capture_output=True, text=True, timeout=300,
        )
        per_phase.append({
            "phase": f"{layer_name}:kustomize-build",
            "exit_code": str(build_proc.returncode),
        })
        stdout_chunks.append(
            f"=== {layer_name}:kustomize-build stdout ===\n{build_proc.stdout[:2048]}"
        )
        stderr_chunks.append(
            f"=== {layer_name}:kustomize-build stderr ===\n{build_proc.stderr}"
        )
        if build_proc.returncode != 0:
            _emit_layer_log(
                args, artifact_id, layer_name, "failure",
                time.monotonic() - started,
            )
            return _finalize_accelerator(
                "failure", started, stdout_chunks, stderr_chunks, per_phase,
                failed_layer=layer_name,
            )
        kustomize_output = build_proc.stdout

        # Phase 2: oc apply --dry-run=server (always runs)
        dryrun_proc = subprocess.run(
            [oc_bin, "apply", "--dry-run=server", "-f", "-"],
            input=kustomize_output,
            capture_output=True, text=True, timeout=300,
        )
        per_phase.append({
            "phase": f"{layer_name}:oc-dry-run",
            "exit_code": str(dryrun_proc.returncode),
        })
        stdout_chunks.append(
            f"=== {layer_name}:oc-dry-run stdout ===\n{dryrun_proc.stdout}"
        )
        stderr_chunks.append(
            f"=== {layer_name}:oc-dry-run stderr ===\n{dryrun_proc.stderr}"
        )
        if dryrun_proc.returncode != 0:
            # Halt sequence BEFORE any real apply runs for this layer.
            _emit_layer_log(
                args, artifact_id, layer_name, "failure",
                time.monotonic() - started,
            )
            return _finalize_accelerator(
                "failure", started, stdout_chunks, stderr_chunks, per_phase,
                failed_layer=layer_name,
            )

        # Phase 3: oc apply (real) — skipped when dry_run=True
        if dry_run:
            _emit_layer_log(
                args, artifact_id, layer_name, "dry-run",
                time.monotonic() - started,
            )
            continue

        apply_proc = subprocess.run(
            [oc_bin, "apply", "-f", "-"],
            input=kustomize_output,
            capture_output=True, text=True, timeout=600,
        )
        per_phase.append({
            "phase": f"{layer_name}:oc-apply",
            "exit_code": str(apply_proc.returncode),
        })
        stdout_chunks.append(
            f"=== {layer_name}:oc-apply stdout ===\n{apply_proc.stdout}"
        )
        stderr_chunks.append(
            f"=== {layer_name}:oc-apply stderr ===\n{apply_proc.stderr}"
        )
        if apply_proc.returncode != 0:
            _emit_layer_log(
                args, artifact_id, layer_name, "failure",
                time.monotonic() - started,
            )
            return _finalize_accelerator(
                "failure", started, stdout_chunks, stderr_chunks, per_phase,
                failed_layer=layer_name,
            )

        _emit_layer_log(
            args, artifact_id, layer_name, "success",
            time.monotonic() - started,
        )

    final_status = "dry-run" if dry_run else "success"
    return _finalize_accelerator(
        final_status, started, stdout_chunks, stderr_chunks, per_phase,
        failed_layer=None,
    )


def _emit_layer_log(
    args: Dict[str, str],
    artifact_id: str,
    layer_name: str,
    execution_result: str,
    duration_seconds: float,
) -> None:
    """Per-layer ACTA-04 emission for execute_accelerator (Phase 11.2 D-03).

    Thin wrapper that calls emit_activity_log_apply() with the new layer_id
    kwarg. Pulls overlay/profile/operator/plan_path from args dict (with safe
    defaults — these should always be populated by the /dsp:apply caller but
    we don't want a missing field to crash the executor mid-walk).
    """
    emit_activity_log_apply(
        overlay=args.get("overlay", "base"),
        plan_path=args.get("plan_path", ""),
        artifact_id=artifact_id,
        profile_name=args.get("profile_name", ""),
        confirmation_status=args.get("confirmation_status", "confirmed"),
        execution_result=execution_result,
        duration_seconds=duration_seconds,
        gate_results=args.get("gate_results", []) or [],
        operator=args.get("operator", ""),
        override_reason=args.get("override_reason"),
        confirmation_source=args.get("confirmation_source"),
        layer_id=layer_name,
    )


def _finalize_accelerator(
    status: str,
    started: float,
    stdout_chunks: List[str],
    stderr_chunks: List[str],
    per_phase: List[Dict[str, str]],
    failed_layer: Optional[str],
) -> ExecutionResult:
    """Mirror of _finalize() that threads failed_layer into the result."""
    tail = lambda chunks, n: ("\n".join(chunks))[-n:]
    return ExecutionResult(
        status=status,
        duration_seconds=round(time.monotonic() - started, 1),
        stdout_tail=tail(stdout_chunks, 4096),
        stderr_tail=tail(stderr_chunks, 4096),
        per_phase=per_phase,
        failed_layer=failed_layer,
    )


def _render_root_module(
    workspace: Path,
    module_abs: Path,
    args: Dict[str, str],
) -> None:
    """Write a tiny root module that sources `module_abs` and a tfvars file."""
    root_tf = workspace / "main.tf"
    root_tf.write_text(
        "# Auto-generated by FRANZ /dsp-apply Step 7 — do not edit by hand.\n"
        "# Source module is the fsi-dsp artifact referenced by the active plan.\n"
        "\n"
        "terraform {\n"
        '  required_version = ">= 1.6"\n'
        "}\n"
        "\n"
        'module "target" {\n'
        f'  source = "{module_abs}"\n'
        + "".join(f'  {k} = var.{k}\n' for k in args.keys() if _is_valid_tf_ident(k))
        + "}\n"
    )

    variables_tf = workspace / "variables.tf"
    variables_tf.write_text(
        "\n".join(
            f'variable "{k}" {{ type = string }}'
            for k in args.keys() if _is_valid_tf_ident(k)
        )
        + "\n"
    )

    tfvars = workspace / "franz.auto.tfvars"
    tfvars.write_text(
        "\n".join(
            f'{k} = "{_tf_escape(v)}"'
            for k, v in args.items() if _is_valid_tf_ident(k)
        )
        + "\n"
    )


def _is_valid_tf_ident(name: str) -> bool:
    """Terraform variable identifiers: letter, then letters/digits/underscores."""
    if not name or not name[0].isalpha():
        return False
    return all(c.isalnum() or c == "_" for c in name)


def _tf_escape(value: str) -> str:
    """Minimal escape for HCL double-quoted strings — backslash + double-quote."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _finalize(
    status: str,
    started: float,
    stdout_chunks: List[str],
    stderr_chunks: List[str],
    per_phase: List[Dict[str, str]],
) -> ExecutionResult:
    """Tail outputs to keep activity-log entries bounded."""
    tail = lambda chunks, n: ("\n".join(chunks))[-n:]
    return ExecutionResult(
        status=status,
        duration_seconds=round(time.monotonic() - started, 1),
        stdout_tail=tail(stdout_chunks, 4096),
        stderr_tail=tail(stderr_chunks, 4096),
        per_phase=per_phase,
    )


# ---------------------------------------------------------------------------
# Activity Log (ACTA-04)
# ---------------------------------------------------------------------------

def emit_activity_log_apply(
    overlay: str,
    plan_path: str,
    artifact_id: str,
    profile_name: str,
    confirmation_status: str,
    execution_result: str,
    duration_seconds: float,
    gate_results: List[Dict],
    operator: str,
    override_reason: Optional[str] = None,
    confirmation_source: Optional[str] = None,
    layer_id: Optional[str] = None,
) -> None:
    """Append a /dsp:apply entry to the overlay-scoped activity log.

    Writes to wiki/activity/YYYY-MM.md relative to PROJECT_ROOT. Creates the
    file with a header if it does not exist. Appends to the existing file if it
    does exist. Activity log is append-only — never modifies existing entries.

    Args:
        overlay:             Customer overlay name (e.g., "base", "acme-bank").
        plan_path:           Path to the plan file that was applied.
        artifact_id:         fsi-dsp artifact ID that was applied.
        profile_name:        Policy profile name used for this apply.
        confirmation_status: Human confirmation outcome ("confirmed" or "rejected").
        execution_result:    Execution outcome ("success", "failure", "dry-run").
        duration_seconds:    Wall-clock seconds from confirmation to execution complete.
        gate_results:        List of gate result dicts from run_gate_chain().
        operator:            Operator identifier (user/service account name).
        override_reason:     Break-glass override reason (ACTG-03); omit for non-break-glass.
        confirmation_source: How confirmation was captured — "interactive" (in-chat
                             AskUserQuestion) or "pre-confirmed" (orchestrator UI modal,
                             e.g. FRANZ). Distinguishes UI-modal confirmations from
                             chat-based ones in audits.
        layer_id:            Accelerator-only (Phase 11.2 D-03): the layer name from
                             apply_sequence for per-layer ACTA-04 entries. When non-None,
                             the entry includes a **Layer:** field between **Artifact:**
                             and **Plan:**. Terraform-module callers omit this kwarg
                             and get the byte-identical pre-11 11-field entry shape
                             (back-compat preserved).
    """
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    month_key = now.strftime("%Y-%m")

    # Build gate summary for log entry (compact form)
    gate_summary = ", ".join(
        f"{r['gate']}={r['status']}" for r in gate_results
    ) if gate_results else "no gates recorded"

    # Build canon stack reference
    try:
        layers = active_layers()
        canon_stack = " + ".join(layers) if layers else "base"
    except Exception:
        canon_stack = overlay or "base"

    # Compose the activity log entry
    entry_lines = [
        f"## {timestamp}",
        f"**Skill:** /dsp:apply",
        f"**Operator:** {operator}",
        f"**Overlay:** {overlay}",
        f"**Profile:** {profile_name}",
        f"**Artifact:** {artifact_id}",
        *(
            [f"**Layer:** {layer_id}"]
            if layer_id
            else []
        ),
        f"**Plan:** {plan_path}",
        f"**Confirmation status:** {confirmation_status}",
        *(
            [f"**Confirmation source:** {confirmation_source}"]
            if confirmation_source
            else []
        ),
        f"**Execution result:** {execution_result}",
        f"**Duration seconds:** {duration_seconds:.1f}",
        f"**Gates:** {gate_summary}",
        f"**Canon stack:** {canon_stack}",
    ]
    if override_reason is not None:
        entry_lines.append(f"**Override reason:** {override_reason}")
    entry_lines.append("")
    entry = "\n".join(entry_lines)

    # Resolve log file path
    activity_dir = PROJECT_ROOT / "wiki" / "activity"
    activity_dir.mkdir(parents=True, exist_ok=True)
    log_file = activity_dir / f"{month_key}.md"

    if not log_file.exists():
        # Create with header
        header = f"# Activity Log — {month_key}\n\n"
        log_file.write_text(header + entry)
    else:
        # Append to existing file
        existing = log_file.read_text()
        # Ensure there's a blank line separator before appending
        separator = "\n" if existing.endswith("\n") else "\n\n"
        log_file.write_text(existing + separator + entry)


# ---------------------------------------------------------------------------
# Incident Article (ACTA-05)
# ---------------------------------------------------------------------------

def write_incident_article(
    slug: str,
    artifact_id: str,
    operator: str,
    profile_name: str,
    outcome: str,
    canon_hash: str,
    plan_path: str,
    gate_results: List[Dict],
    execution_result: str,
    override_reason: Optional[str] = None,
) -> Path:
    """Write a wiki incident article for a /dsp:apply execution.

    Creates wiki/incidents/<slug>-<YYYY-MM-DD>.md relative to PROJECT_ROOT.
    Creates the incidents directory if it does not exist.

    Each apply operation creates one incident article as a trackable audit record
    (ACTA-05). The article contains YAML frontmatter and four required sections.

    Args:
        slug:             URL-safe slug for the incident (e.g., "trade-topic-create").
        artifact_id:      fsi-dsp artifact ID that was applied.
        operator:         Operator identifier.
        profile_name:     Policy profile used.
        outcome:          High-level outcome ("success", "failure", "rejected").
        canon_hash:       16-char SHA-256 hash of the active canon stack.
        plan_path:        Path to the source plan file.
        gate_results:     List of gate result dicts from run_gate_chain().
        execution_result: Detailed execution result string.
        override_reason:  Break-glass override reason (ACTG-03); omit for non-break-glass.

    Returns:
        Path to the created incident article.
    """
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Build file name: <slug>-<YYYY-MM-DD>.md
    filename = f"{slug}-{date_str}.md"
    incidents_dir = PROJECT_ROOT / "wiki" / "incidents"
    incidents_dir.mkdir(parents=True, exist_ok=True)
    article_path = incidents_dir / filename

    # Build YAML frontmatter (7 required keys + optional override_reason for break-glass)
    frontmatter_lines = [
        "---",
        f"artifact: {artifact_id}",
        f"operator: {operator}",
        f"profile: {profile_name}",
        f"outcome: {outcome}",
        f"canon_hash: {canon_hash}",
        f"plan_ref: {plan_path}",
        f"timestamp: {timestamp}",
    ]
    if override_reason is not None:
        frontmatter_lines.append(f"override_reason: {override_reason}")
    frontmatter_lines += ["---", ""]

    # Build gate results markdown table
    if gate_results:
        table_header = "| Gate | Status | Detail |"
        table_sep = "| --- | --- | --- |"
        table_rows = [
            f"| {r.get('gate', '')} | {r.get('status', '')} | {r.get('detail', '')} |"
            for r in gate_results
        ]
        gate_table = "\n".join([table_header, table_sep] + table_rows)
    else:
        gate_table = "| Gate | Status | Detail |\n| --- | --- | --- |\n| (no gates recorded) | - | - |"

    # Build canon provenance
    try:
        layers = active_layers()
        canon_stack = " + ".join(layers) if layers else "base"
    except Exception:
        canon_stack = "base"

    # Compose article body
    body_sections = [
        f"# Incident: {slug}",
        "",
        "## What Changed",
        "",
        f"Applied `{artifact_id}` via profile `{profile_name}`.",
        f"Execution result: `{execution_result}`.",
        "",
        "## Why",
        "",
        f"See plan: `{plan_path}`",
    ]
    if override_reason is not None:
        body_sections.append(f"Override reason: {override_reason}")
    body_sections += [
        "",
        "## Gate Results",
        "",
        gate_table,
        "",
        "## Provenance",
        "",
        f"Canon stack: {canon_stack}",
        f"Canon hash: `{canon_hash}`",
        f"Operator: {operator}",
        f"Timestamp: {timestamp}",
        "",
    ]

    article_content = "\n".join(frontmatter_lines + body_sections)
    article_path.write_text(article_content)
    return article_path


# ---------------------------------------------------------------------------
# CLI entry point (matches tools/ convention)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Apply engine for /dsp:apply: load profiles and check permissions."
    )
    subparsers = parser.add_subparsers(dest="command")

    # check-profile subcommand
    check_parser = subparsers.add_parser("check-profile", help="Check if profile permits an operation")
    check_parser.add_argument("profile", help="Profile name (read-only, engineer, break-glass)")
    check_parser.add_argument("artifact_id", help="Artifact ID to check (e.g., module/topic)")

    # show-profile subcommand
    show_parser = subparsers.add_parser("show-profile", help="Show profile details")
    show_parser.add_argument("profile", help="Profile name")

    args = parser.parse_args()

    if args.command == "check-profile":
        try:
            profile = load_profile(args.profile)
            permitted = check_profile_permits(profile, args.artifact_id)
            status = "PERMITTED" if permitted else "DENIED"
            print(f"[{status}] {args.profile} -> {args.artifact_id}")
        except ValueError as exc:
            print(f"[ERROR] {exc}")
            sys.exit(1)
    elif args.command == "show-profile":
        try:
            profile = load_profile(args.profile)
            print(json.dumps(profile, indent=2))
        except ValueError as exc:
            print(f"[ERROR] {exc}")
            sys.exit(1)
    else:
        parser.print_help()
