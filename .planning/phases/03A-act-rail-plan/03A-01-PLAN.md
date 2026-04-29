---
phase: 03A-act-rail-plan
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - .mcp.json
  - tools/act_gates.py
  - tests/test_act_gates.py
autonomous: true
requirements:
  - ACT-01
  - ACT-02
  - ACT-03
  - ACT-06

must_haves:
  truths:
    - "Terraform MCP server entry exists in .mcp.json alongside existing MCP servers"
    - "run_gate_chain() executes four gates in fail-fast order and returns structured results"
    - "Each gate can be bypassed by name via bypass list, returning status=skipped"
    - "Gate chain never invokes mcp-confluent write tools — read-only inspection only"
  artifacts:
    - path: ".mcp.json"
      provides: "Terraform MCP server entry"
      contains: "terraform"
    - path: "tools/act_gates.py"
      provides: "Four-gate chain with run_gate_chain() orchestrator"
      exports: ["gate1_canon_compliance", "gate2_fsi_dsp_coverage", "gate3_confluent_docs_schema", "gate4_mcp_confluent_state", "run_gate_chain", "GATE_NAMES"]
      min_lines: 120
    - path: "tests/test_act_gates.py"
      provides: "Unit tests for gate chain functions"
      min_lines: 80
  key_links:
    - from: "tools/act_gates.py"
      to: "canon/stack.py"
      via: "resolve_stack() import for gate 1 canon compliance"
      pattern: "from canon.stack import resolve_stack"
    - from: "tools/act_gates.py"
      to: "raw/repos/fsi-dsp/MANIFEST.yaml"
      via: "YAML load for gate 2 artifact matching"
      pattern: "yaml.safe_load"
---

<objective>
Wire Terraform MCP into .mcp.json, build the four-gate validation chain module (tools/act_gates.py), and create unit tests proving gate isolation, fail-fast, and bypass behavior.

Purpose: Establishes the core gate chain abstraction that all downstream act rail work (skill file, harness, phases 3b/3c) composes on top of. This is the single new architectural primitive in Phase 3a.
Output: .mcp.json with terraform entry, tools/act_gates.py with 4 gates + orchestrator, tests/test_act_gates.py with unit coverage.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/03A-act-rail-plan/03A-CONTEXT.md
@.planning/phases/03A-act-rail-plan/03A-RESEARCH.md

<interfaces>
<!-- Key types and contracts the executor needs. -->

From canon/stack.py:
```python
def resolve_stack(
    layers: Optional[List[str]] = None,
    customer: Optional[str] = None,
    engagement: Optional[str] = None,
) -> Tuple[Dict, str]:
    """Returns (merged_config_dict, sha256_hex_hash)."""

def active_layers() -> List[str]:
    """Return list of layers that have config files present."""

def provenance_footer() -> str:
    """Generate a provenance footer string for artifact embedding."""
```

From canon/base/defaults.yaml (top-level keys):
```
topic_design, schema_registry, producer, consumer, flink_sql, cluster_linking, security
```

From raw/repos/fsi-dsp/MANIFEST.yaml (capability structure):
```yaml
capabilities:
  - id: "module/topic"        # type: terraform-module
  - id: "module/flink"        # type: terraform-module
  - id: "role/cp_topic"       # type: ansible-role
  # ... 9 roles, 2 modules, 6 scenarios, 9 ADRs, 10 references, 7 scripts, 7 observability
```

From .mcp.json (existing structure):
```json
{
  "mcpServers": {
    "context7": { "command": "npx", "args": ["-y", "@upstash/context7-mcp"] },
    "confluent-docs": { ... },
    "mcp-confluent": { ... }
  }
}
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Wire Terraform MCP and build four-gate chain module</name>
  <files>.mcp.json, tools/act_gates.py</files>
  <read_first>
    - .mcp.json (current MCP server entries — must preserve all existing entries)
    - canon/stack.py (resolve_stack signature and import path)
    - canon/base/defaults.yaml (top-level keys for gate 1 compliance checking)
    - raw/repos/fsi-dsp/MANIFEST.yaml (capability structure for gate 2 matching)
    - tools/review-to-docx.py (PROJECT_ROOT pattern, sys.path.insert, argparse guard)
  </read_first>
  <behavior>
    - gate1_canon_compliance: request mentioning "acks=0" with base canon returns status=fail with evidence citing producer.acks=all
    - gate1_canon_compliance: request mentioning "topic with DR" with base canon returns status=pass
    - gate2_fsi_dsp_coverage: request "create a topic" matches module/topic from MANIFEST
    - gate2_fsi_dsp_coverage: request "provision MongoDB" returns status=fail with no matching artifact
    - gate3_confluent_docs_schema: returns status=pass (stub — real validation requires MCP call)
    - gate4_mcp_confluent_state: returns status=pass (stub — real validation requires live cluster)
    - run_gate_chain with no bypass: returns list of 4 GateResult dicts
    - run_gate_chain with bypass=["mcp_confluent_state"]: gate 4 returns status=skipped
    - run_gate_chain fail-fast: gate 1 failure stops chain, only 1 result returned
    - GATE_NAMES list contains exactly 4 entries in order
  </behavior>
  <action>
1. Add Terraform MCP entry to .mcp.json (per ACT-01). Add `"terraform"` key alongside existing entries:
```json
"terraform": {
  "command": "npx",
  "args": ["-y", "@hashicorp/terraform-mcp-server"]
}
```
Preserve all three existing entries (context7, confluent-docs, mcp-confluent) exactly as-is.

2. Create tools/act_gates.py with:
- `PROJECT_ROOT = Path(__file__).resolve().parent.parent` and `sys.path.insert(0, str(PROJECT_ROOT))` (matches review-to-docx.py pattern)
- Use `from typing import Optional, List, Dict` (Python 3.9 compat — no X|Y union syntax per STATE.md decision)
- `GATE_NAMES = ["canon_compliance", "fsi_dsp_coverage", "confluent_docs_schema", "mcp_confluent_state"]`
- `GateResult` type alias: `Dict` with keys gate(str), status(str: pass|fail|skipped), detail(str), evidence(list)

Gate functions (each takes request: str, overlay: Optional[str] = None) -> Dict:

**gate1_canon_compliance(request, overlay):**
- Call `resolve_stack(customer=overlay)` to get active config
- Parse request for config-relevant keywords (acks, compression, auto.commit, etc.)
- If request contradicts canon config values, return fail with evidence listing the canon default
- If request aligns or is neutral, return pass

**gate2_fsi_dsp_coverage(request, overlay):**
- Load MANIFEST.yaml from `PROJECT_ROOT / "raw" / "repos" / "fsi-dsp" / "MANIFEST.yaml"`
- Match request keywords against capability descriptions and names
- Prefer terraform-module type for "create/provision" requests, ansible-role for "configure/deploy" requests
- If matched: return pass with evidence containing matched artifact ID
- If no match: return fail with detail "no matching artifact" and evidence listing closest alternatives

**gate3_confluent_docs_schema(request, overlay):**
- Stub implementation: return pass with detail "schema validation deferred to MCP runtime"
- This gate validates at skill runtime via confluent-docs MCP; unit tests verify the stub returns correct structure

**gate4_mcp_confluent_state(request, overlay):**
- Stub implementation: return pass with detail "cluster state check deferred to MCP runtime"
- This gate validates at skill runtime via mcp-confluent; unit tests verify the stub returns correct structure

**run_gate_chain(request, overlay=None, bypass=None):**
- Iterate gates in GATE_NAMES order
- If gate_name in bypass list: append skipped result, continue
- Call gate function; append result
- If result status == "fail": break (fail-fast, per CONTEXT.md decision)
- Return list of GateResult dicts

**Important constraints (ACT-06):**
- No gate function may generate Terraform resource blocks
- Gate 4 reads cluster state only — never calls create/update/delete tools
- Add module docstring: "Read-only gate chain for /dsp:plan act rail. Never generates inline Terraform or invokes write tools."
- Include `if __name__ == "__main__":` guard for CLI testing (matches tools/ convention)
  </action>
  <verify>
    <automated>python3 -c "from tools.act_gates import run_gate_chain, GATE_NAMES; assert len(GATE_NAMES) == 4; print('OK: act_gates importable')" && python3 -c "import json; d=json.load(open('.mcp.json')); assert 'terraform' in d['mcpServers']; assert 'context7' in d['mcpServers']; print('OK: .mcp.json valid')"</automated>
  </verify>
  <acceptance_criteria>
    - .mcp.json contains key "terraform" under mcpServers with command "npx" and args containing "@hashicorp/terraform-mcp-server"
    - .mcp.json still contains keys "context7", "confluent-docs", "mcp-confluent" (no existing entries removed)
    - tools/act_gates.py exports GATE_NAMES with exactly ["canon_compliance", "fsi_dsp_coverage", "confluent_docs_schema", "mcp_confluent_state"]
    - tools/act_gates.py contains `from canon.stack import resolve_stack`
    - tools/act_gates.py contains `yaml.safe_load` for MANIFEST loading
    - tools/act_gates.py contains `if __name__ == "__main__":` guard
    - tools/act_gates.py docstring contains "Never generates inline Terraform"
    - run_gate_chain function accepts (request, overlay, bypass) parameters
    - Each gate function returns dict with keys: gate, status, detail, evidence
  </acceptance_criteria>
  <done>Terraform MCP wired in .mcp.json. Four-gate chain module importable with all 4 gate functions + orchestrator. No write-tool invocations anywhere in module.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Unit tests for gate chain — isolation, fail-fast, bypass</name>
  <files>tests/test_act_gates.py</files>
  <read_first>
    - tools/act_gates.py (just created — read to verify actual function signatures)
    - tests/test_review_to_docx.py (existing test pattern — PROJECT_ROOT, imports, class structure)
    - tests/conftest.py (shared fixtures)
  </read_first>
  <behavior>
    - test_gate_names_count: GATE_NAMES has exactly 4 entries
    - test_gate_names_order: GATE_NAMES is ["canon_compliance", "fsi_dsp_coverage", "confluent_docs_schema", "mcp_confluent_state"]
    - test_gate1_pass_on_compliant_request: "create a topic with DR and replication factor 3" returns pass
    - test_gate1_fail_on_noncompliant_request: "create topic with acks=0" returns fail with evidence mentioning "acks"
    - test_gate2_pass_matches_manifest_artifact: "create a topic" matches module/topic
    - test_gate2_fail_no_matching_artifact: "provision a MongoDB cluster" returns fail
    - test_gate3_stub_returns_pass: always returns pass with correct structure
    - test_gate4_stub_returns_pass: always returns pass with correct structure
    - test_run_gate_chain_all_pass: returns 4 results all with status pass
    - test_run_gate_chain_bypass_returns_skipped: bypass=["mcp_confluent_state"] -> gate 4 status=skipped
    - test_run_gate_chain_fail_fast: gate 1 fail -> only 1 result returned
    - test_gate_result_structure: every result has keys gate, status, detail, evidence
    - test_gate2_prefers_terraform_module: "create topic" matches module/topic not role/cp_topic
  </behavior>
  <action>
Create tests/test_act_gates.py following the established test pattern (see tests/test_review_to_docx.py):

```python
"""Unit tests for act_gates.py gate chain (ACT-02, ACT-03, ACT-06)."""
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.act_gates import (
    gate1_canon_compliance,
    gate2_fsi_dsp_coverage,
    gate3_confluent_docs_schema,
    gate4_mcp_confluent_state,
    run_gate_chain,
    GATE_NAMES,
)

GATE_RESULT_KEYS = {"gate", "status", "detail", "evidence"}
```

Test classes:

**TestGateNames:** test count == 4, test order matches GATE_NAMES constant

**TestGateResultStructure:** parametrize across all 4 gate functions with a neutral request, assert each returns dict with GATE_RESULT_KEYS, assert status is one of pass|fail|skipped

**TestGate1CanonCompliance:**
- Compliant request ("create a topic with replication factor 3 and DR") -> status=pass
- Non-compliant request ("set acks=0 for maximum throughput") -> status=fail, "acks" in str(evidence)

**TestGate2FsiDspCoverage:**
- "create a topic for trade events" -> status=pass, "module/topic" in str(evidence)
- "provision a MongoDB Atlas cluster" -> status=fail, "no matching artifact" in detail
- "create a topic" prefers module/topic (terraform-module) over role/cp_topic (ansible-role)

**TestGate3Stub:** returns pass with correct gate name
**TestGate4Stub:** returns pass with correct gate name

**TestRunGateChain:**
- All pass: compliant request, no bypass -> len(results) >= 1, all status in (pass, skipped)
- Bypass: bypass=["mcp_confluent_state"] -> last result has status=skipped, gate=mcp_confluent_state
- Fail-fast: non-compliant request triggering gate 1 fail -> len(results) == 1, results[0]["status"] == "fail"
- Multiple bypass: bypass=["confluent_docs_schema", "mcp_confluent_state"] -> those gates return skipped

**TestReadOnlyConstraint (ACT-06):**
- Read act_gates.py source text, assert no occurrence of "create_topic", "delete_topic", "update_topic" (mcp-confluent write tool names)
- Assert source contains "Never generates inline Terraform" in docstring
  </action>
  <verify>
    <automated>python3 -m pytest tests/test_act_gates.py -v --tb=short -q</automated>
  </verify>
  <acceptance_criteria>
    - tests/test_act_gates.py contains class TestGateNames with test_gate_names_count and test_gate_names_order
    - tests/test_act_gates.py contains class TestRunGateChain with test methods for all_pass, bypass, and fail_fast
    - tests/test_act_gates.py contains class TestReadOnlyConstraint checking ACT-06
    - All tests pass: `python3 -m pytest tests/test_act_gates.py -v --tb=short` exits 0
    - At least 12 test functions total in the file
  </acceptance_criteria>
  <done>Unit tests prove gate chain isolation (each gate testable independently per ACT-03), fail-fast behavior, bypass returning skipped, and read-only constraint (ACT-06). All tests green.</done>
</task>

</tasks>

<verification>
- `python3 -c "import json; d=json.load(open('.mcp.json')); assert 'terraform' in d['mcpServers']"` exits 0
- `python3 -c "from tools.act_gates import run_gate_chain, GATE_NAMES"` exits 0
- `python3 -m pytest tests/test_act_gates.py -v --tb=short -q` all green
</verification>

<success_criteria>
- Terraform MCP entry present in .mcp.json (ACT-01)
- Four-gate chain importable and unit-tested (ACT-02, ACT-03)
- Read-only constraint enforced by test (ACT-06)
- Gate bypass works per-name, not blanket (ACT-03)
</success_criteria>

<output>
After completion, create `.planning/phases/03A-act-rail-plan/03A-01-SUMMARY.md`
</output>
