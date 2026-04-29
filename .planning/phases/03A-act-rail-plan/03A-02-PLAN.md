---
phase: 03A-act-rail-plan
plan: 02
type: execute
wave: 2
depends_on: ["03A-01"]
files_modified:
  - .claude/commands/dsp-plan.md
  - tools/check-canon-parity.py
  - tests/test_check_canon_parity.py
  - .github/workflows/canon-parity.yml
autonomous: true
requirements:
  - ACT-04
  - ACT-06
  - ACT-08

must_haves:
  truths:
    - "/dsp:plan skill file exists with structured steps that never generate inline Terraform"
    - "Parity checker detects drift between MANIFEST capabilities and canon defaults keys"
    - "CI workflow runs parity check on PR and blocks on drift"
  artifacts:
    - path: ".claude/commands/dsp-plan.md"
      provides: "/dsp:plan skill with flag parsing, gate chain invocation, plan output, activity log"
      contains: "dsp:plan"
      min_lines: 80
    - path: "tools/check-canon-parity.py"
      provides: "Canon-to-fsi-dsp parity checker"
      exports: ["check_parity"]
      min_lines: 40
    - path: "tests/test_check_canon_parity.py"
      provides: "Unit tests for parity checker"
      min_lines: 40
    - path: ".github/workflows/canon-parity.yml"
      provides: "GitHub Actions CI for parity enforcement"
      contains: "check-canon-parity"
  key_links:
    - from: ".claude/commands/dsp-plan.md"
      to: "tools/act_gates.py"
      via: "Step 3 calls run_gate_chain()"
      pattern: "run_gate_chain"
    - from: "tools/check-canon-parity.py"
      to: "raw/repos/fsi-dsp/MANIFEST.yaml"
      via: "YAML load of capability IDs"
      pattern: "MANIFEST.yaml"
    - from: "tools/check-canon-parity.py"
      to: "canon/base/defaults.yaml"
      via: "YAML load of canon config keys"
      pattern: "defaults.yaml"
---

<objective>
Create the /dsp:plan skill file, build the canon-fsi-dsp parity checker, add unit tests for parity, and create the CI workflow that blocks merges on drift.

Purpose: Delivers the user-facing skill (ACT-04) and the CI parity enforcement (ACT-08) that keeps canon and fsi-dsp aligned.
Output: dsp-plan.md skill, check-canon-parity.py tool, unit tests, canon-parity.yml CI workflow.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/03A-act-rail-plan/03A-CONTEXT.md
@.planning/phases/03A-act-rail-plan/03A-RESEARCH.md
@.planning/phases/03A-act-rail-plan/03A-01-SUMMARY.md

<interfaces>
<!-- From Plan 01 outputs -->

From tools/act_gates.py (created in Plan 01):
```python
GATE_NAMES = ["canon_compliance", "fsi_dsp_coverage", "confluent_docs_schema", "mcp_confluent_state"]

def run_gate_chain(
    request: str,
    overlay: Optional[str] = None,
    bypass: Optional[List[str]] = None,
) -> List[Dict]:
    """Run the four-gate chain in fail-fast order. Returns list of GateResult dicts."""

# GateResult dict: {gate: str, status: pass|fail|skipped, detail: str, evidence: list}
```

From canon/stack.py:
```python
def resolve_stack(customer=None, engagement=None) -> Tuple[Dict, str]
def active_layers() -> List[str]
def provenance_footer() -> str
```

From .claude/commands/review.md (skill file pattern):
- Step 1: Parse arguments (--output, --overlay flags)
- Step 1.5: Load documents / config
- Steps 2-5: Core processing
- Step 6: Generate report, write file, emit activity log

From .github/workflows/manifest-citations.yml (CI pattern):
```yaml
on:
  pull_request:
    paths: [...]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: true
      - uses: actions/setup-python@v5
      - run: pip install pyyaml
      - run: python tools/check-xxx.py
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create /dsp:plan skill file and canon parity checker with tests</name>
  <files>.claude/commands/dsp-plan.md, tools/check-canon-parity.py, tests/test_check_canon_parity.py</files>
  <read_first>
    - .claude/commands/review.md (skill file pattern — step structure, flag parsing, activity log emission, provenance footer)
    - .claude/commands/ask.md (simpler skill pattern — flag parsing, route step, response structure)
    - tools/review-to-docx.py (PROJECT_ROOT pattern, get_manifest_version(), build_provenance())
    - canon/base/defaults.yaml (top-level keys: topic_design, schema_registry, producer, consumer, flink_sql, cluster_linking, security)
    - raw/repos/fsi-dsp/MANIFEST.yaml (capability types: terraform-module, ansible-role, scenario, adr, reference, script, observability)
    - tools/act_gates.py (from Plan 01 — verify run_gate_chain signature)
    - wiki/activity/README.md (activity log format if exists)
  </read_first>
  <action>
**1. Create .claude/commands/dsp-plan.md** (the /dsp:plan skill file per ACT-04):

Structure mirrors review.md exactly:

```markdown
# /dsp:plan -- FSI-DSP Infrastructure Plan

You are producing a read-only infrastructure plan that selects and validates
an existing fsi-dsp artifact through the four-gate validation chain.
You NEVER generate inline Terraform or invoke mcp-confluent write tools.

## Input
$ARGUMENTS

## Step 1: Parse arguments
- Extract `--overlay <name>` (customer overlay, e.g., "acme-bank")
- Extract `--dry-run` (default: true, plan-only mode)
- Extract `--gate-bypass <gate>` (repeatable; dev mode — skip named gates)
  Valid gate names: canon_compliance, fsi_dsp_coverage, confluent_docs_schema, mcp_confluent_state
- Remaining text is the natural language request string
- Validation:
  - If `--gate-bypass` names an unknown gate, stop: `Error: unknown gate: <name>. Valid: canon_compliance, fsi_dsp_coverage, confluent_docs_schema, mcp_confluent_state`
  - If `--overlay` specifies a customer with no `canon/customer/<name>/overrides.yaml`, stop: `Error: overlay not found: canon/customer/<name>/overrides.yaml`
  - If no request text, stop: `Error: no request specified`

## Step 2: Load canon stack
- Call `resolve_stack(customer=overlay)` from `canon/stack.py`
- Note the resolved config and stack hash for provenance

## Step 3: Run gate chain
- Import `run_gate_chain` from `tools/act_gates.py`
- Call `run_gate_chain(request, overlay, bypass_list)`
- If any gate returns status=fail:
  - Report which gate failed, its detail, and evidence
  - If gate 2 (fsi_dsp_coverage) failed: include "Suggested alternatives" from MANIFEST.yaml
  - Do NOT attempt to generate inline Terraform to work around the failure
  - Write the failure report to outputs/plans/ and skip to Step 6 (activity log)
- If all gates pass or are skipped: proceed to Step 4

## Step 4: Select artifact and build arguments
- Gate 2 result contains the matched artifact ID (e.g., "module/topic")
- Read the matched artifact's entry from MANIFEST.yaml for its path and description
- Based on the request, determine the arguments/variables the artifact needs
- CRITICAL (ACT-06): Never generate `resource "confluent_..."` blocks or any raw Terraform/Ansible
- If the request cannot be fully resolved to an existing artifact, return a "no matching artifact" response suggesting a PR proposal to fsi-dsp

## Step 5: Produce plan document
- Write to `outputs/plans/<slug>-plan-<YYYY-MM-DD>.md` (create directory if needed)
- Slug: lowercase, first 5 words of request, joined with hyphens
- Plan document sections:
  1. **Selected Artifact** — artifact ID, path, description from MANIFEST
  2. **Arguments** — derived variables/parameters for the artifact
  3. **Gate Results** — table of all gate results (gate | status | detail)
  4. **Canon Compliance** — active canon config relevant to this request
  5. **Provenance Footer** — `Canon stack: <layers> | Hash: <hash> | MANIFEST: <version> | Floor: <model> | Generated: <ISO-8601>`
    - Use provenance_footer() from canon/stack.py for canon part
    - Read MANIFEST version from raw/repos/fsi-dsp/MANIFEST.yaml

## Step 6: Emit activity log
- Append to `wiki/activity/YYYY-MM.md` (create if needed)
- Format:
  ## YYYY-MM-DDTHH:MM:SSZ
  **Skill:** /dsp:plan
  **Overlay:** {overlay name or "base"}
  **Input:** {request text}
  **Output:** {plan file path}
  **Canon stack:** {active_layers() output}
  **Gate results:** {comma-separated gate:status pairs}

## Rules
- NEVER generate inline Terraform resource blocks. If no artifact matches, say so and suggest a PR.
- NEVER invoke mcp-confluent create/update/delete tools. Read-only inspection only.
- Every invocation writes a plan file (even failures) and emits an activity log entry.
- Gate bypass requires explicit gate names — no blanket "skip all" supported.
- If MCP servers are unavailable, gates 3 and 4 can be bypassed with --gate-bypass.
```

**2. Create tools/check-canon-parity.py** (per ACT-08):

```python
#!/usr/bin/env python3
"""Check parity between canon/base/defaults.yaml keys and MANIFEST.yaml terraform-module capabilities.

Bidirectional drift detection:
- MANIFEST has terraform-module capability with no corresponding canon config category -> drift
- Canon has config category with no corresponding terraform-module -> drift (warning only)

Exit 0 = parity confirmed. Exit 1 = drift detected (blocks CI merge).
"""
```

- `PROJECT_ROOT = Path(__file__).resolve().parent.parent`
- `check_parity(manifest_path: Path, defaults_path: Path) -> List[str]` returns list of drift strings
- Mapping: terraform-module capabilities map to canon config categories:
  - `module/topic` -> `topic_design` (topics need topic_design canon config)
  - `module/flink` -> `flink_sql` (flink modules need flink_sql canon config)
- Check direction 1: each terraform-module in MANIFEST has a corresponding canon defaults key
- Check direction 2: each canon defaults top-level key that maps to infrastructure has a MANIFEST artifact (warning-level, not blocking — some keys like `security` are cross-cutting)
- `if __name__ == "__main__":` with argparse for optional --manifest-path and --defaults-path overrides, defaulting to standard project-relative paths
- Exit 0 on no drift, exit 1 on drift with stderr output

**3. Create tests/test_check_canon_parity.py:**

Follow tests/test_review_to_docx.py pattern:

```python
"""Unit tests for check-canon-parity.py (ACT-08)."""
```

Test class **TestCheckParity:**
- test_no_drift_on_current_state: run check_parity with real project files, expect empty list (current MANIFEST and defaults should be in parity)
- test_detects_missing_canon_key: create temp defaults.yaml missing topic_design, expect drift string mentioning "module/topic"
- test_parity_function_returns_list: result is always a list
- test_parity_with_empty_manifest: empty capabilities list returns no drift (no terraform-modules to check)

Test class **TestParityScript:**
- test_script_importable: `from tools.check_canon_parity import check_parity` works (underscore name, no hyphen registration needed)
  </action>
  <verify>
    <automated>python3 -c "from tools.check_canon_parity import check_parity; print('OK: parity importable')" && python3 -m pytest tests/test_check_canon_parity.py -v --tb=short -q && test -f .claude/commands/dsp-plan.md && echo "OK: skill file exists"</automated>
  </verify>
  <acceptance_criteria>
    - .claude/commands/dsp-plan.md exists with "## Step 1: Parse arguments" through "## Step 6: Emit activity log"
    - .claude/commands/dsp-plan.md contains "NEVER generate inline Terraform" in Rules section
    - .claude/commands/dsp-plan.md contains "--gate-bypass" flag documentation
    - .claude/commands/dsp-plan.md contains "run_gate_chain" reference in Step 3
    - .claude/commands/dsp-plan.md contains "outputs/plans/" as output path
    - .claude/commands/dsp-plan.md contains activity log emission in Step 6 referencing "wiki/activity/"
    - tools/check-canon-parity.py contains `def check_parity` function
    - tools/check-canon-parity.py contains `if __name__ == "__main__":` guard
    - tools/check-canon-parity.py contains `sys.exit(1)` for drift detection
    - tests/test_check_canon_parity.py passes: `python3 -m pytest tests/test_check_canon_parity.py -v` exits 0
    - `python3 tools/check-canon-parity.py` exits 0 (current state is in parity)
  </acceptance_criteria>
  <done>Skill file delivers /dsp:plan with full step structure (ACT-04). Parity checker detects drift bidirectionally (ACT-08). Skill enforces read-only constraint in Rules section (ACT-06). All parity tests green.</done>
</task>

<task type="auto">
  <name>Task 2: Create GitHub Actions canon-parity CI workflow</name>
  <files>.github/workflows/canon-parity.yml</files>
  <read_first>
    - .github/workflows/manifest-citations.yml (existing CI pattern — checkout with submodules, setup-python, pip install, run script)
    - tools/check-canon-parity.py (just created — verify script can run standalone)
  </read_first>
  <action>
Create .github/workflows/canon-parity.yml following the manifest-citations.yml pattern exactly:

```yaml
name: Canon Parity

on:
  pull_request:
    paths:
      - 'canon/**'
      - 'raw/repos/fsi-dsp/MANIFEST.yaml'
      - 'tools/check-canon-parity.py'

jobs:
  check-parity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: true

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install pyyaml

      - name: Check canon <-> fsi-dsp parity
        run: python tools/check-canon-parity.py
```

Key details:
- Triggers on changes to canon/, MANIFEST.yaml, or the parity script itself
- Uses submodules: true (fsi-dsp is a submodule)
- Installs pyyaml (only dependency)
- Script exit code 0/1 determines CI pass/fail
  </action>
  <verify>
    <automated>python3 -c "import yaml; wf=yaml.safe_load(open('.github/workflows/canon-parity.yml')); assert 'check-parity' in wf['jobs']; assert 'canon/**' in wf['on']['pull_request']['paths']; print('OK: CI workflow valid')"</automated>
  </verify>
  <acceptance_criteria>
    - .github/workflows/canon-parity.yml exists
    - Workflow name is "Canon Parity"
    - Triggers on pull_request with paths including 'canon/**' and 'raw/repos/fsi-dsp/MANIFEST.yaml'
    - Job uses actions/checkout@v4 with submodules: true
    - Job runs `python tools/check-canon-parity.py`
    - Job installs pyyaml dependency
  </acceptance_criteria>
  <done>CI workflow blocks merges on canon-fsi-dsp drift (ACT-08). Workflow structure matches existing manifest-citations.yml pattern.</done>
</task>

</tasks>

<verification>
- `test -f .claude/commands/dsp-plan.md` exits 0
- `python3 tools/check-canon-parity.py` exits 0
- `python3 -m pytest tests/test_check_canon_parity.py -v --tb=short` all green
- `test -f .github/workflows/canon-parity.yml` exits 0
</verification>

<success_criteria>
- /dsp:plan skill file exists with all 6 steps and read-only rules (ACT-04, ACT-06)
- Parity checker runs clean on current state (ACT-08)
- CI workflow triggers on canon/ and MANIFEST changes (ACT-08)
- Parity unit tests all pass
</success_criteria>

<output>
After completion, create `.planning/phases/03A-act-rail-plan/03A-02-SUMMARY.md`
</output>
