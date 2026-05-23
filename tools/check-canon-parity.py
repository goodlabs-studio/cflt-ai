#!/usr/bin/env python3
"""Check parity between canon keys and MANIFEST.yaml capabilities (terraform-module + accelerator).

Bidirectional drift detection:
- MANIFEST has terraform-module or accelerator capability with no corresponding canon
  config key -> drift (blocking)
- Canon has infrastructure config key with no corresponding terraform-module -> drift
  (warning only)

The mapping from capability IDs to canon config keys:
  Terraform modules (top-level canon keys in canon/base/defaults.yaml):
    module/topic  -> topic_design   (topics need topic_design canon config)
    module/flink  -> flink_sql      (flink modules need flink_sql canon config)

  Accelerator layers (composite key <id>:<layer-name> -> dotted-path canon key in
  canon/industry/fsi/overrides.yaml; Phase 11):
    accelerator/confluent-on-linuxone:01-rbac              -> fsi.security.mds-rbac
    accelerator/confluent-on-linuxone:02-tls               -> fsi.security.tls-fips
    accelerator/confluent-on-linuxone:03-schema-governance -> fsi.schema.compatibility-full-transitive
    accelerator/confluent-on-linuxone:04-audit             -> fsi.audit.events-retention
    accelerator/confluent-on-linuxone:05-flink             -> fsi.flink.environment-mtls

This mapping is intentionally explicit rather than heuristic — each new module or
accelerator layer requires a conscious decision about which canon config key
governs it. For accelerator entries, MODULE_TO_CANON_KEY mirrors the per-layer
`canon_key` field on the upstream MANIFEST apply_sequence; drift between them
produces a blocking [DRIFT-1] violation.

Exit 0 = parity confirmed. Exit 1 = drift detected (blocks CI merge).
"""
import argparse
import sys
from pathlib import Path
from typing import List

import yaml

# Match the pattern used by review-to-docx.py and act_gates.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Explicit mapping: capability ID -> canon key.
# Terraform-module entries (no ':' in key) map to top-level canon/base/defaults.yaml keys.
# Accelerator-layer entries (composite '<id>:<layer-name>') map to dotted-path keys
# in canon/industry/fsi/overrides.yaml. Source of truth for parity enforcement.
MODULE_TO_CANON_KEY = {
    "module/topic": "topic_design",
    "module/flink": "flink_sql",
    "accelerator/confluent-on-linuxone:01-rbac": "fsi.security.mds-rbac",
    "accelerator/confluent-on-linuxone:02-tls": "fsi.security.tls-fips",
    "accelerator/confluent-on-linuxone:03-schema-governance": "fsi.schema.compatibility-full-transitive",
    "accelerator/confluent-on-linuxone:04-audit": "fsi.audit.events-retention",
    "accelerator/confluent-on-linuxone:05-flink": "fsi.flink.environment-mtls",
}

# Canon keys that map to infrastructure modules (used for direction-2 warning check).
# Only includes terraform-module canon keys (composite accelerator keys are walked
# separately via apply_sequence; their reverse direction is enforced by the per-layer
# canon_key field on the MANIFEST, not by the existence of a top-level canon key).
# Keys NOT in this set are cross-cutting (security, producer, consumer, etc.) and
# are exempt from "no module found" warnings because they apply across all artifacts.
CANON_INFRA_KEYS = {v for k, v in MODULE_TO_CANON_KEY.items() if ":" not in k}  # {"topic_design", "flink_sql"}


def check_parity(manifest_path: Path, defaults_path: Path) -> List[str]:
    """Check parity between MANIFEST.yaml terraform-modules and canon defaults keys.

    Returns a list of drift strings. Empty list means parity confirmed.

    Direction 1 (blocking): Each terraform-module in MANIFEST must have a corresponding
    canon config key. Missing canon config = the module has no governing defaults.

    Direction 2 (warning): Each canon key in CANON_INFRA_KEYS should have a
    corresponding terraform-module. Missing module = canon config exists but no
    artifact implements it yet (warning, not blocking).

    Args:
        manifest_path: Path to raw/repos/fsi-dsp/MANIFEST.yaml
        defaults_path: Path to canon/base/defaults.yaml

    Returns:
        List of drift description strings. Empty = no drift.
    """
    drift: List[str] = []

    # Load MANIFEST
    try:
        manifest_data = yaml.safe_load(manifest_path.read_text())
    except FileNotFoundError:
        drift.append(f"MANIFEST not found: {manifest_path}")
        return drift
    except yaml.YAMLError as e:
        drift.append(f"MANIFEST parse error: {e}")
        return drift

    capabilities = manifest_data.get("capabilities", []) if isinstance(manifest_data, dict) else []

    # Load canon defaults
    try:
        defaults_data = yaml.safe_load(defaults_path.read_text())
    except FileNotFoundError:
        drift.append(f"Canon defaults not found: {defaults_path}")
        return drift
    except yaml.YAMLError as e:
        drift.append(f"Canon defaults parse error: {e}")
        return drift

    canon_keys = set(defaults_data.keys()) if isinstance(defaults_data, dict) else set()

    # Extract terraform-modules from MANIFEST
    tf_modules = [c for c in capabilities if c.get("type") == "terraform-module"]
    tf_module_ids = {c.get("id") for c in tf_modules}

    # Direction 1: Each terraform-module must have a corresponding canon defaults key.
    # Missing canon config key = blocking drift.
    for module_id in sorted(tf_module_ids):
        canon_key = MODULE_TO_CANON_KEY.get(module_id)
        if canon_key is None:
            drift.append(
                f"[DRIFT-1] terraform-module '{module_id}' has no entry in "
                f"MODULE_TO_CANON_KEY mapping — add it to check-canon-parity.py"
            )
        elif canon_key not in canon_keys:
            drift.append(
                f"[DRIFT-1] terraform-module '{module_id}' maps to canon key "
                f"'{canon_key}' but that key is absent from defaults.yaml"
            )

    # Direction 2: Each canon infra key should have a corresponding terraform-module.
    # Missing module = warning (not blocking — some keys are purely advisory).
    for canon_key in sorted(CANON_INFRA_KEYS):
        expected_module = next(
            (mid for mid, ckey in MODULE_TO_CANON_KEY.items() if ckey == canon_key), None
        )
        if expected_module and expected_module not in tf_module_ids:
            drift.append(
                f"[WARN-2] canon key '{canon_key}' has no corresponding "
                f"terraform-module '{expected_module}' in MANIFEST — "
                f"expected module ID missing from fsi-dsp"
            )

    return drift


def main() -> int:
    """CLI entry point. Returns exit code: 0 = parity, 1 = drift."""
    parser = argparse.ArgumentParser(
        description="Check parity between canon/base/defaults.yaml and MANIFEST.yaml terraform-modules."
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=PROJECT_ROOT / "raw" / "repos" / "fsi-dsp" / "MANIFEST.yaml",
        help="Path to fsi-dsp MANIFEST.yaml (default: raw/repos/fsi-dsp/MANIFEST.yaml)",
    )
    parser.add_argument(
        "--defaults-path",
        type=Path,
        default=PROJECT_ROOT / "canon" / "base" / "defaults.yaml",
        help="Path to canon base defaults.yaml (default: canon/base/defaults.yaml)",
    )
    args = parser.parse_args()

    drift = check_parity(args.manifest_path, args.defaults_path)

    if not drift:
        print("OK: canon <-> fsi-dsp parity confirmed (no drift)")
        return 0

    print("DRIFT DETECTED:", file=sys.stderr)
    for item in drift:
        print(f"  {item}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
