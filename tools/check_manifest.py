#!/usr/bin/env python3
"""Check MANIFEST.yaml schema validity.

Validates that every capability entry in raw/repos/fsi-dsp/MANIFEST.yaml
conforms to the fsi-dsp/manifest/v1 schema:
  - Top-level: `version`, `schema` ('fsi-dsp/manifest/v1'), `capabilities` (list).
  - Base capability fields (id, type, name, path) required on every entry.
  - `type` must be one of KNOWN_TYPES (closed enum — drift forces a doc+code update).
  - Type-specific required fields enforced (e.g. `accelerator` -> apply_sequence + 3 commands).

Pure-Python implementation: no jsonschema/pydantic dep. Matches the shape of
tools/check-canon-parity.py and tools/check_submodule_drift.py — each new validator
in this repo intentionally avoids a schema library so the type-enum and per-type
field constants live as literal Python (greppable, unit-testable, no transitive deps).

Exit 0 = valid. Exit 1 = schema errors detected (blocks CI merge).

Usage:
  python3 tools/check_manifest.py                                  # default: real MANIFEST
  python3 tools/check_manifest.py --manifest-path path/to/file.yaml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

# Mirror the pattern used by check-canon-parity.py and check_submodule_drift.py.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Closed enum of every type the v1 schema currently knows about.
# Sourced from the live raw/repos/fsi-dsp/MANIFEST.yaml usage (v1.1.0 as of Phase 10).
# Adding a new type requires:
#   1) Land the upstream fsi-dsp entry first.
#   2) Add the type string here.
#   3) Add a row to tools/manifest-schema.md.
#   4) Update tests/test_manifest.py EXPECTED_* lists + valid_prefixes set.
# The KNOWN_TYPES set is locked by test_known_types_constant_shape — any drift
# fails CI until the doc + tests are updated in lock-step.
KNOWN_TYPES = {
    "ansible-role",
    "terraform-module",
    "scenario",
    "adr",
    "reference",
    "script",
    "observability",
    "accelerator",   # Added in cflt-ai v2.1 Phase 10 (MAN-01).
}

# Base fields required on EVERY capability entry, regardless of type.
BASE_REQUIRED_FIELDS = ("id", "type", "name", "path")

# Accelerator-specific schema (locked in 10-CONTEXT.md):
#   apply_sequence: non-empty list of {layer, path, canon_key} objects.
#   build_command / dry_run_command / apply_command: non-empty strings.
# Per-layer canon_key co-locates the layer->canon mapping with the artifact
# (single source of truth — downstream MODULE_TO_CANON_KEY readers derive from this,
# not a duplicated table; matches the G.2c cleanup pattern).
ACCELERATOR_REQUIRED_FIELDS = (
    "apply_sequence",
    "build_command",
    "dry_run_command",
    "apply_command",
)
ACCELERATOR_LAYER_REQUIRED_FIELDS = ("layer", "path", "canon_key")


def validate_capability(cap: Dict[str, Any]) -> List[str]:
    """Validate a single capability entry. Returns a list of error strings (empty = valid).

    The validator covers shape only — path-existence-on-disk is intentionally
    out of scope (that's TestManifestPathsExist in tests/test_manifest.py). Keeping
    schema-shape and existence-on-disk orthogonal lets this script run as a fast
    pre-commit/CI gate without requiring the submodule to be checked out.
    """
    errors: List[str] = []
    cap_id = cap.get("id", "<unknown>")

    # Base fields.
    for field in BASE_REQUIRED_FIELDS:
        if field not in cap:
            errors.append(f"[{cap_id}] missing required base field '{field}'")

    # Type enum gate. None (= type field absent) is already flagged above.
    cap_type = cap.get("type")
    if cap_type is not None and cap_type not in KNOWN_TYPES:
        errors.append(
            f"[{cap_id}] unknown type '{cap_type}' -- must be one of: "
            f"{sorted(KNOWN_TYPES)}. To add a new type, register it in "
            f"tools/check_manifest.py KNOWN_TYPES and document in tools/manifest-schema.md."
        )

    # Type-specific gating. Other existing types have no extra schema beyond the
    # base required fields, so no per-type validator is needed for them today.
    if cap_type == "accelerator":
        errors.extend(_validate_accelerator(cap_id, cap))

    return errors


def _validate_accelerator(cap_id: str, cap: Dict[str, Any]) -> List[str]:
    """Validate accelerator-specific schema. See ACCELERATOR_REQUIRED_FIELDS.

    The four required extras lock the artifact-tool-agnostic contract:
    apply_sequence (ordered list of layers, each with its own canon_key)
    + 3 explicit command strings so non-kustomize accelerators (Helm, Terraform)
    can reuse the schema without an enum-of-tools field.
    """
    errors: List[str] = []

    for field in ACCELERATOR_REQUIRED_FIELDS:
        if field not in cap:
            errors.append(f"[{cap_id}] accelerator missing required field '{field}'")

    # apply_sequence must be a non-empty list of layer objects, each with the
    # three required layer fields.
    seq = cap.get("apply_sequence")
    if seq is not None:
        if not isinstance(seq, list):
            errors.append(
                f"[{cap_id}] apply_sequence must be a list, got {type(seq).__name__}"
            )
        elif len(seq) == 0:
            errors.append(
                f"[{cap_id}] apply_sequence is empty (must declare at least one layer)"
            )
        else:
            for i, layer in enumerate(seq):
                if not isinstance(layer, dict):
                    errors.append(
                        f"[{cap_id}] apply_sequence[{i}] must be an object, "
                        f"got {type(layer).__name__}"
                    )
                    continue
                for field in ACCELERATOR_LAYER_REQUIRED_FIELDS:
                    if field not in layer:
                        errors.append(
                            f"[{cap_id}] apply_sequence[{i}] missing '{field}'"
                        )

    # Commands must be non-empty strings (presence already flagged above).
    for cmd in ("build_command", "dry_run_command", "apply_command"):
        val = cap.get(cmd)
        if val is not None and (not isinstance(val, str) or not val.strip()):
            errors.append(f"[{cap_id}] {cmd} must be a non-empty string")

    return errors


def validate_manifest(manifest_path: Path) -> List[str]:
    """Validate an entire MANIFEST.yaml file. Returns a list of error strings.

    Empty list = manifest is schema-valid. Caller is responsible for translating
    a non-empty list into an exit code (main() does this for the CLI surface).
    """
    errors: List[str] = []
    try:
        data = yaml.safe_load(manifest_path.read_text())
    except FileNotFoundError:
        return [f"MANIFEST not found: {manifest_path}"]
    except yaml.YAMLError as e:
        return [f"MANIFEST parse error: {e}"]

    if not isinstance(data, dict):
        return [
            f"MANIFEST must be a mapping at top level, got {type(data).__name__}"
        ]

    if data.get("schema") != "fsi-dsp/manifest/v1":
        errors.append(
            f"MANIFEST schema field must be 'fsi-dsp/manifest/v1', "
            f"got {data.get('schema')!r}"
        )

    caps = data.get("capabilities", [])
    if not isinstance(caps, list):
        return errors + [
            f"capabilities must be a list, got {type(caps).__name__}"
        ]

    for cap in caps:
        if not isinstance(cap, dict):
            errors.append(
                f"capability must be an object, got {type(cap).__name__}"
            )
            continue
        errors.extend(validate_capability(cap))

    return errors


def main() -> int:
    """CLI entry point. Returns exit code: 0 = valid, 1 = schema errors."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate MANIFEST.yaml schema (type enum + per-type required fields). "
            "Exit 0 valid, 1 schema errors detected."
        )
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=PROJECT_ROOT / "raw" / "repos" / "fsi-dsp" / "MANIFEST.yaml",
        help="Path to fsi-dsp MANIFEST.yaml (default: raw/repos/fsi-dsp/MANIFEST.yaml)",
    )
    args = parser.parse_args()

    errors = validate_manifest(args.manifest_path)

    if not errors:
        print(f"OK: MANIFEST schema valid ({args.manifest_path})")
        return 0

    print("SCHEMA ERRORS:", file=sys.stderr)
    for err in errors:
        print(f"  {err}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
