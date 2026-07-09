#!/usr/bin/env python3
"""
nnpa-coverage-gate.py — fail the build if any hot-path op falls back to CPU.

This is the single most important gate in the pipeline. Any op in the model graph
that isn't NNPA-eligible executes on the IFLs *with no error raised*: the job runs,
the p99 SLO quietly dies, and the Telum thesis is disproven by a benchmark that
looks like it succeeded.

zDLC (built on onnx-mlir) emits a compile-time report of which ops lowered to
zDNN/NNPA vs. which remained on CPU. We parse it, and fail CI if any op on the
declared hot path is CPU-resident.

Usage:
    zdlc --EmitLib --march=z16 --nnpa-report=coverage.json model.onnx
    python3 nnpa-coverage-gate.py coverage.json --hot-path-ops hot_path.txt

    # emits the coverage hash used to tag the job image (see manifests/12)
    python3 nnpa-coverage-gate.py coverage.json --print-hash

Exit codes:
    0  all hot-path ops NNPA-resident
    1  one or more hot-path ops fell back to CPU  (fail the build)
    2  bad input / unparseable report              (fail the build — never skip)

Note on Telum generation: INT8 lowering is only available on Telum II (z17 /
machine type 9175). On z16 (3931/3932) the accelerator consumes DLFLOAT16 only,
so an INT8-quantized graph will silently fall back here. --march must match the
target machine reported by ansible/00-platform-validate.yml.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

# Ops that, if CPU-resident, mean the model isn't really running on the
# accelerator. Tree traversal (TreeEnsemble*) is NOT NNPA math — if you see it
# here, run the model through Hummingbird to compile trees into tensor ops first.
TREE_OPS = {"TreeEnsembleClassifier", "TreeEnsembleRegressor", "SVMClassifier"}


def load_report(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        sys.exit(f"[FAIL] coverage report not found: {path}\n"
                 "       Did zDLC run with --nnpa-report? Never skip this gate.")
    except json.JSONDecodeError as exc:
        sys.exit(f"[FAIL] coverage report is not valid JSON: {exc}")


def extract_ops(report: dict) -> list[dict]:
    """zDLC report shape: {"ops": [{"name":..., "op_type":..., "device":"NNPA"|"CPU"}]}"""
    ops = report.get("ops")
    if not isinstance(ops, list) or not ops:
        sys.exit("[FAIL] coverage report has no 'ops' array — cannot attest coverage.")
    return ops


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report", type=Path, help="zDLC --nnpa-report JSON")
    ap.add_argument("--hot-path-ops", type=Path,
                    help="newline-delimited op names that MUST be NNPA-resident. "
                         "If omitted, ALL ops are treated as hot path.")
    ap.add_argument("--print-hash", action="store_true",
                    help="print the coverage hash (tag the job image with it) and exit")
    args = ap.parse_args()

    report = load_report(args.report)
    ops = extract_ops(report)

    if args.print_hash:
        # Deterministic attestation of *this* compiled model's op placement.
        # manifests/12 tags the image with it; observability/ labels the inference
        # metrics with it. That join is what makes "which build regressed?" answerable.
        digest = hashlib.sha256(
            json.dumps(ops, sort_keys=True).encode()
        ).hexdigest()[:7]
        print(digest)
        return 0

    if args.hot_path_ops:
        hot = {ln.strip() for ln in args.hot_path_ops.read_text().splitlines()
               if ln.strip() and not ln.startswith("#")}
    else:
        hot = {op.get("name", "") for op in ops}

    cpu_resident = [op for op in ops if op.get("device", "").upper() != "NNPA"]
    hot_fallbacks = [op for op in cpu_resident if op.get("name") in hot]
    trees = [op for op in cpu_resident if op.get("op_type") in TREE_OPS]

    total = len(ops)
    nnpa = total - len(cpu_resident)
    print(f"NNPA coverage: {nnpa}/{total} ops ({nnpa / total:.1%})")

    if trees:
        print("\n[FAIL] Tree-ensemble ops are executing on CPU:")
        for op in trees:
            print(f"  - {op.get('name')} ({op.get('op_type')})")
        print("       Tree traversal is not NNPA math. Compile the GBM through "
              "Hummingbird into tensor ops, then re-export to ONNX.")

    if hot_fallbacks:
        print("\n[FAIL] Hot-path ops fell back to CPU (silent latency killer):")
        for op in hot_fallbacks:
            print(f"  - {op.get('name')} ({op.get('op_type')}) -> {op.get('device')}")
        print("\n       Any of these will run on the IFLs with NO error raised at "
              "runtime. Fix the graph or re-declare the hot path — do not waive.")
        return 1

    if cpu_resident:
        # Cold-path fallback is tolerable; make it visible rather than silent.
        print(f"\n[warn] {len(cpu_resident)} non-hot-path op(s) on CPU:")
        for op in cpu_resident:
            print(f"  - {op.get('name')} ({op.get('op_type')})")

    print("\n[PASS] All hot-path ops are NNPA-resident.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
