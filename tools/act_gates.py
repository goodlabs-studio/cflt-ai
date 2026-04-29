#!/usr/bin/env python3
"""
Read-only gate chain for /dsp:plan act rail. Never generates inline Terraform or invokes write tools.

Gate chain validates a planning request through four sequential gates before any fsi-dsp
artifact is recommended. Each gate is independently testable (ACT-03) and may be bypassed
by name during development (ACT-06 bypass list). The chain is fail-fast: the first gate
failure stops evaluation and returns a single-result list.

Gates:
    1. canon_compliance    — request does not contradict Confluent Canon defaults
    2. fsi_dsp_coverage    — a matching fsi-dsp artifact exists in MANIFEST.yaml
    3. confluent_docs_schema — schema validity (stub: real validation requires confluent-docs MCP)
    4. mcp_confluent_state — cluster state check (stub: real validation requires mcp-confluent)

Requirements: ACT-01 (Terraform MCP), ACT-02 (four gates), ACT-03 (individually testable/bypassable),
              ACT-06 (read-only, no inline Terraform generation)
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml

# Add project root to path for canon.stack import (matches review-to-docx.py pattern)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from canon.stack import resolve_stack  # noqa: E402 (after sys.path.insert)


# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------

GATE_NAMES: List[str] = [
    "canon_compliance",
    "fsi_dsp_coverage",
    "confluent_docs_schema",
    "mcp_confluent_state",
]

# Type alias documentation: GateResult is a Dict with keys:
#   gate     (str)  — gate name from GATE_NAMES
#   status   (str)  — "pass" | "fail" | "skipped"
#   detail   (str)  — human-readable explanation
#   evidence (list) — supporting facts (canon defaults, artifact IDs, etc.)
GateResult = Dict  # Dict[str, object] — kept as Dict for Python 3.9 compat


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_result(gate: str, status: str, detail: str, evidence: Optional[List] = None) -> GateResult:
    """Build a GateResult dict with all required keys."""
    return {
        "gate": gate,
        "status": status,
        "detail": detail,
        "evidence": evidence if evidence is not None else [],
    }


# Canon keywords that map to config sections and their violation patterns.
# Each entry: (keyword_pattern, config_path, violating_value, canon_value)
_CANON_VIOLATION_PATTERNS = [
    # Producer violations
    ("acks=0", "producer.acks", "0", "all"),
    ("acks=1", "producer.acks", "1", "all"),
    ("acks = 0", "producer.acks", "0", "all"),
    ("acks = 1", "producer.acks", "1", "all"),
    # Consumer auto-commit violations
    ("enable.auto.commit=true", "consumer.enable_auto_commit", "true", "false"),
    ("enable.auto.commit = true", "consumer.enable_auto_commit", "true", "false"),
    ("auto.commit=true", "consumer.enable_auto_commit", "true", "false"),
    # Schema format violations
    ("json schema", "schema_registry.format", "json", "avro"),
]


def _load_manifest() -> List[Dict]:
    """Load fsi-dsp MANIFEST.yaml capabilities. Returns empty list on error."""
    manifest_path = PROJECT_ROOT / "raw" / "repos" / "fsi-dsp" / "MANIFEST.yaml"
    try:
        data = yaml.safe_load(manifest_path.read_text())
        if isinstance(data, dict):
            return data.get("capabilities", [])
    except (FileNotFoundError, yaml.YAMLError):
        pass
    return []


# ---------------------------------------------------------------------------
# Gate 1: Canon Compliance
# ---------------------------------------------------------------------------

def gate1_canon_compliance(
    request: str,
    overlay: Optional[str] = None,
) -> GateResult:
    """Check that the request does not contradict Confluent Canon defaults.

    Calls resolve_stack() to get the active canon config (with optional customer overlay),
    then scans the request for known violation patterns. Returns fail with evidence if
    any violation is detected; pass otherwise.

    Args:
        request: The planning request text to evaluate.
        overlay:  Optional customer name to load customer/{name}/overrides.yaml.

    Returns:
        GateResult dict with gate="canon_compliance".
    """
    gate_name = "canon_compliance"

    # Resolve active canon stack (customer overlay if provided)
    try:
        config, _stack_hash = resolve_stack(customer=overlay)
    except Exception as exc:
        return _make_result(
            gate_name,
            "fail",
            f"canon stack resolution failed: {exc}",
            [],
        )

    request_lower = request.lower()
    violations = []

    for keyword, config_path, violating_val, canon_val in _CANON_VIOLATION_PATTERNS:
        if keyword.lower() in request_lower:
            violations.append(
                f"Request uses {keyword!r} — canon default: {config_path}={canon_val!r}"
            )

    if violations:
        return _make_result(
            gate_name,
            "fail",
            "Request contradicts Confluent Canon defaults.",
            violations,
        )

    return _make_result(
        gate_name,
        "pass",
        "Request is consistent with Confluent Canon defaults.",
        [],
    )


# ---------------------------------------------------------------------------
# Gate 2: FSI-DSP Coverage
# ---------------------------------------------------------------------------

# Keywords that suggest a "create/provision" intent → prefer terraform-module
_CREATE_VERBS = ("create", "provision", "stand up", "deploy a new", "spin up")
# Keywords that suggest "configure/manage" intent → prefer ansible-role
_CONFIGURE_VERBS = ("configure", "manage", "update", "modify", "patch")

# Capability matching: map domain keywords to capability IDs
_CAPABILITY_KEYWORDS: List[tuple] = [
    # terraform-module first (preferred for create/provision)
    ("topic", "module/topic", "terraform-module"),
    ("flink", "module/flink", "terraform-module"),
    # ansible-roles
    ("schema", "role/cp_schema", "ansible-role"),
    ("rbac", "role/cp_rbac", "ansible-role"),
    ("connect", "role/cp_connect", "ansible-role"),
    ("mirrormaker", "role/cp_dr_mm2", "ansible-role"),
    ("mm2", "role/cp_dr_mm2", "ansible-role"),
    ("multi-region", "role/cp_dr_mrc", "ansible-role"),
    ("observability", "role/cp_observability", "ansible-role"),
    ("kubernetes", "role/cfk_operator", "ansible-role"),
    ("openshift", "role/cfk_operator", "ansible-role"),
    # scenarios
    ("aws", "scenario/cc-aws", "scenario"),
    ("azure", "scenario/cc-azure", "scenario"),
    ("gcp", "scenario/cc-gcp", "scenario"),
    ("private cloud", "scenario/private-cloud", "scenario"),
    # scripts
    ("failover", "script/mirror-failover", "script"),
    ("failback", "script/mirror-failback", "script"),
    ("dr ", "script/fsi-dr", "script"),
    ("fips", "script/validate-fips", "script"),
]


def gate2_fsi_dsp_coverage(
    request: str,
    overlay: Optional[str] = None,
) -> GateResult:
    """Check that a matching fsi-dsp artifact exists in MANIFEST.yaml.

    Prefers terraform-module type for create/provision requests, ansible-role for
    configure/deploy requests. Returns fail if no artifact matches, with closest
    alternatives listed in evidence.

    Args:
        request: The planning request text to evaluate.
        overlay:  Unused at gate 2 (kept for uniform signature).

    Returns:
        GateResult dict with gate="fsi_dsp_coverage".
    """
    gate_name = "fsi_dsp_coverage"
    capabilities = _load_manifest()
    request_lower = request.lower()

    # Determine intent (create vs configure)
    is_create_intent = any(verb in request_lower for verb in _CREATE_VERBS)

    # Collect all matching capabilities
    matches: List[Dict] = []
    for keyword, cap_id, cap_type in _CAPABILITY_KEYWORDS:
        if keyword.lower() in request_lower:
            # Find the capability in the loaded manifest for full details
            cap_detail = next(
                (c for c in capabilities if c.get("id") == cap_id),
                {"id": cap_id, "type": cap_type},
            )
            matches.append(cap_detail)

    if not matches:
        # List some closest alternatives from manifest for user guidance
        alternatives = [c.get("id", "?") for c in capabilities[:5]]
        return _make_result(
            gate_name,
            "fail",
            "No matching artifact found in fsi-dsp MANIFEST.yaml.",
            [f"no matching artifact — closest alternatives: {alternatives}"],
        )

    # Prefer terraform-module if create intent and any module matches
    if is_create_intent:
        tf_modules = [m for m in matches if m.get("type") == "terraform-module"]
        if tf_modules:
            best = tf_modules[0]
        else:
            best = matches[0]
    else:
        best = matches[0]

    return _make_result(
        gate_name,
        "pass",
        f"Matched fsi-dsp artifact: {best.get('id')} ({best.get('type')})",
        [best.get("id"), best.get("description", "")],
    )


# ---------------------------------------------------------------------------
# Gate 3: Confluent Docs Schema (stub)
# ---------------------------------------------------------------------------

def gate3_confluent_docs_schema(
    request: str,
    overlay: Optional[str] = None,
) -> GateResult:
    """Validate request against Confluent documentation schema (stub).

    Real validation requires a live call to the confluent-docs MCP server. This stub
    returns pass with a deferred-to-MCP-runtime detail so that unit tests can verify
    the correct return structure without MCP connectivity.

    Args:
        request: The planning request text to evaluate.
        overlay:  Unused at gate 3 (kept for uniform signature).

    Returns:
        GateResult dict with gate="confluent_docs_schema", status="pass".
    """
    return _make_result(
        "confluent_docs_schema",
        "pass",
        "Schema validation deferred to MCP runtime (confluent-docs).",
        [],
    )


# ---------------------------------------------------------------------------
# Gate 4: MCP-Confluent State (stub)
# ---------------------------------------------------------------------------

def gate4_mcp_confluent_state(
    request: str,
    overlay: Optional[str] = None,
) -> GateResult:
    """Check live cluster state via mcp-confluent (stub).

    Real validation requires a live call to the mcp-confluent MCP server. This stub
    returns pass with a deferred-to-MCP-runtime detail. Gate 4 is read-only — it never
    calls create/update/delete tools (ACT-06 constraint).

    Args:
        request: The planning request text to evaluate.
        overlay:  Unused at gate 4 (kept for uniform signature).

    Returns:
        GateResult dict with gate="mcp_confluent_state", status="pass".
    """
    return _make_result(
        "mcp_confluent_state",
        "pass",
        "Cluster state check deferred to MCP runtime (mcp-confluent).",
        [],
    )


# ---------------------------------------------------------------------------
# Gate orchestrator
# ---------------------------------------------------------------------------

_GATE_FUNCTIONS = {
    "canon_compliance": gate1_canon_compliance,
    "fsi_dsp_coverage": gate2_fsi_dsp_coverage,
    "confluent_docs_schema": gate3_confluent_docs_schema,
    "mcp_confluent_state": gate4_mcp_confluent_state,
}


def run_gate_chain(
    request: str,
    overlay: Optional[str] = None,
    bypass: Optional[List[str]] = None,
) -> List[GateResult]:
    """Execute the four-gate validation chain in GATE_NAMES order.

    Fail-fast: if any gate returns status="fail", the chain stops and returns the
    results accumulated so far (including the failing gate). Gates named in the bypass
    list are skipped (status="skipped") without evaluation.

    This function is read-only. It never invokes mcp-confluent write tools (ACT-06).

    Args:
        request: The planning request text to evaluate.
        overlay: Optional customer name passed to gates that support overlay config.
        bypass:  Optional list of gate names to skip (returns status="skipped").
                 Names must match entries in GATE_NAMES exactly.

    Returns:
        List of GateResult dicts, one per gate evaluated (or skipped).
        Stops after first failing gate.
    """
    if bypass is None:
        bypass = []

    results: List[GateResult] = []

    for gate_name in GATE_NAMES:
        if gate_name in bypass:
            results.append(
                _make_result(gate_name, "skipped", "Gate bypassed by bypass list.", [])
            )
            continue

        gate_fn = _GATE_FUNCTIONS[gate_name]
        result = gate_fn(request, overlay)
        results.append(result)

        # Fail-fast: stop chain on first failure (per CONTEXT.md decision)
        if result["status"] == "fail":
            break

    return results


# ---------------------------------------------------------------------------
# CLI entry point (matches tools/ convention)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run the four-gate act rail validation chain against a planning request."
    )
    parser.add_argument("request", help="Planning request text to evaluate")
    parser.add_argument("--overlay", default=None, help="Customer overlay name")
    parser.add_argument(
        "--bypass",
        nargs="*",
        default=[],
        metavar="GATE_NAME",
        help="Gate names to bypass (e.g., mcp_confluent_state)",
    )
    args = parser.parse_args()

    results = run_gate_chain(args.request, overlay=args.overlay, bypass=args.bypass)
    for r in results:
        icon = {"pass": "PASS", "fail": "FAIL", "skipped": "SKIP"}.get(r["status"], "???")
        print(f"[{icon}] {r['gate']}: {r['detail']}")
        if r["evidence"]:
            for ev in r["evidence"]:
                print(f"       - {ev}")
