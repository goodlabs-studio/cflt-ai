#!/usr/bin/env python3
"""
smt-alignment-gate.py — fail the build on SMTAlignmentError before the cluster does.

`cpuManagerPolicyOptions: full-pcpus-only` (manifests/05) allocates whole physical
cores. Under SMT-2 a physical core is 2 logical CPUs, so a **Guaranteed** pod
requesting an **odd whole number** of CPUs cannot be satisfied and is rejected at
admission with SMTAlignmentError.

That failure reads as a capacity problem, not an alignment one — you go add IFLs to
fix a config bug. This gate catches it in CI instead.

The precise rule (narrower than "Guaranteed pods need even cpu"):

    Guaranteed  + integer cpu    -> static CPU manager, exclusive cores.
                                    MUST be a multiple of threads-per-core.
    Guaranteed  + fractional cpu -> shared pool (e.g. 500m). No SMT constraint.
    Burstable   (req != lim)     -> shared pool. No SMT constraint.

Only the first case can fail. Control-plane pods (KRaft, Schema Registry, CMF) are
deliberately Burstable so they never claim a whole core away from an inference
TaskManager; brokers and Flink JM/TM are Guaranteed and even.

    python3 smt-alignment-gate.py ../manifests ../helm
    python3 smt-alignment-gate.py ../manifests --threads-per-core 1   # SMT disabled

Exit codes: 0 aligned | 1 misaligned | 2 bad input
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("[FAIL] pyyaml required: pip install pyyaml")


def cpu_to_millicores(value) -> int | None:
    """'4' -> 4000, 4 -> 4000, '500m' -> 500. None if unparseable."""
    if value is None:
        return None
    s = str(value).strip()
    try:
        if s.endswith("m"):
            return int(s[:-1])
        return int(float(s) * 1000)
    except ValueError:
        return None


def qos_of(block: dict) -> str:
    """Guaranteed iff requests == limits for BOTH cpu and memory."""
    rq, lm = block.get("requests") or {}, block.get("limits") or {}
    if not rq or not lm:
        return "Burstable"
    cpu_eq = cpu_to_millicores(rq.get("cpu")) == cpu_to_millicores(lm.get("cpu"))
    mem_eq = str(rq.get("memory")) == str(lm.get("memory"))
    return "Guaranteed" if (cpu_eq and mem_eq) else "Burstable"


def walk(node, path: str = ""):
    """Yield (path, qos, cpu_millicores) for every pod resource spec found.

    Two shapes matter:
      - k8s:  {requests: {cpu, memory}, limits: {cpu, memory}}
      - CFK FlinkApplication: {resource: {cpu, memory}} — a single spec, which CFK
        renders as requests == limits, i.e. always Guaranteed.
    """
    if isinstance(node, dict):
        if "requests" in node and "limits" in node:
            cpu = cpu_to_millicores((node.get("requests") or {}).get("cpu"))
            if cpu is not None:
                yield path or "<root>", qos_of(node), cpu

        for key, val in node.items():
            # jobManager.resource / taskManager.resource
            if key == "resource" and isinstance(val, dict) and "cpu" in val:
                cpu = cpu_to_millicores(val.get("cpu"))
                if cpu is not None:
                    yield f"{path}.{key}" if path else key, "Guaranteed", cpu
                continue
            yield from walk(val, f"{path}.{key}" if path else str(key))

    elif isinstance(node, list):
        for i, item in enumerate(node):
            yield from walk(item, f"{path}[{i}]")


def describe(doc: dict, fallback: str) -> str:
    kind = doc.get("kind")
    name = (doc.get("metadata") or {}).get("name")
    return f"{kind}/{name}" if kind and name else fallback


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("paths", nargs="+", type=Path,
                    help="directories or files containing k8s manifests / helm values")
    ap.add_argument("--threads-per-core", type=int, default=2,
                    help="SMT width. 2 on LinuxONE with SMT-2 (default); 1 if SMT is off.")
    args = ap.parse_args()

    tpc = args.threads_per_core
    if tpc < 1:
        sys.exit("[FAIL] --threads-per-core must be >= 1")

    files: list[Path] = []
    for p in args.paths:
        if p.is_dir():
            files += sorted(p.rglob("*.yaml")) + sorted(p.rglob("*.yml"))
        elif p.is_file():
            files.append(p)
        else:
            sys.exit(f"[FAIL] not found: {p}")

    if not files:
        sys.exit("[FAIL] no YAML files found")

    violations: list[str] = []
    checked = 0

    for f in files:
        try:
            docs = [d for d in yaml.safe_load_all(f.read_text()) if isinstance(d, dict)]
        except yaml.YAMLError as exc:
            sys.exit(f"[FAIL] {f}: {exc}")

        for doc in docs:
            owner = describe(doc, f.name)
            for path, qos, cpu_mc in walk(doc):
                checked += 1
                integral = cpu_mc % 1000 == 0
                cores = cpu_mc // 1000

                # Only Guaranteed + integer CPU reaches the static CPU manager.
                if qos != "Guaranteed" or not integral:
                    reason = "Burstable" if qos != "Guaranteed" else f"fractional ({cpu_mc}m)"
                    print(f"  [ ok ] {owner:<28} {path:<44} shared pool ({reason})")
                    continue

                if cores % tpc != 0:
                    violations.append(
                        f"{f}: {owner} at '{path}' is Guaranteed with cpu={cores}, "
                        f"not a multiple of threads-per-core={tpc}. "
                        f"Kubelet will reject this pod with SMTAlignmentError."
                    )
                    print(f"  [FAIL] {owner:<28} {path:<44} Guaranteed cpu={cores} (odd)")
                else:
                    print(f"  [ ok ] {owner:<28} {path:<44} Guaranteed cpu={cores} "
                          f"({cores // tpc} whole core{'s' if cores // tpc != 1 else ''})")

    print(f"\nChecked {checked} resource spec(s) across {len(files)} file(s), "
          f"threads-per-core={tpc}.")

    if violations:
        print("\nSMT alignment violations:\n")
        for v in violations:
            print(f"  - {v}")
        print(
            "\nFix by EITHER making the pod Burstable (requests != limits) so it draws from\n"
            "the shared pool — correct for control-plane pods like KRaft, Schema Registry,\n"
            "and CMF — OR raising cpu to a multiple of threads-per-core if it genuinely\n"
            f"needs exclusive cores. Do not lower --threads-per-core to {tpc - 1} to make\n"
            "this pass; that silently disables the pinning Option A depends on."
        )
        return 1

    print("[PASS] All Guaranteed integer-CPU pods align to whole physical cores.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
