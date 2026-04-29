# /dsp:plan — FSI-DSP Infrastructure Plan

You are producing a read-only infrastructure plan that selects and validates
an existing fsi-dsp artifact through the four-gate validation chain.
You NEVER generate inline Terraform or invoke mcp-confluent write tools.

## Input

$ARGUMENTS

## Step 1: Parse arguments

Parse `$ARGUMENTS`:
- Extract `--overlay <name>` (customer overlay, e.g., "acme-bank")
- Extract `--dry-run` (default: true, plan-only mode)
- Extract `--gate-bypass <gate>` (repeatable; dev mode — skip named gates per ACT-03)
  Valid gate names: canon_compliance, fsi_dsp_coverage, confluent_docs_schema, mcp_confluent_state
- Remaining text after flags is the natural language request string
- Validation:
  - If `--gate-bypass` names an unknown gate, stop: `Error: unknown gate: <name>. Valid: canon_compliance, fsi_dsp_coverage, confluent_docs_schema, mcp_confluent_state`
  - If `--overlay` specifies a customer with no `canon/customer/<name>/overrides.yaml`, stop: `Error: overlay not found: canon/customer/<name>/overrides.yaml`
  - If no request text, stop: `Error: no request specified`

## Step 2: Load canon stack

- Call `resolve_stack(customer=overlay)` from `canon/stack.py`
- Note the resolved config and stack hash for provenance
- If `--overlay` is not provided, use base + FSI layers only

## Step 3: Run gate chain

- Import `run_gate_chain` from `tools/act_gates.py`
- Build bypass list from any `--gate-bypass` flags provided
- Call `run_gate_chain(request, overlay, bypass_list)`
- If any gate returns status=fail:
  - Report which gate failed, its detail, and evidence
  - If gate 2 (fsi_dsp_coverage) failed: include "Suggested alternatives" from MANIFEST.yaml
  - Do NOT attempt to generate inline Terraform to work around the failure
  - Write the failure report to `outputs/plans/<slug>-plan-<YYYY-MM-DD>.md` and skip to Step 6 (activity log)
- If all gates pass or are skipped: proceed to Step 4

## Step 4: Select artifact and build arguments

- Gate 2 result contains the matched artifact ID (e.g., "module/topic")
- Read the matched artifact's entry from `raw/repos/fsi-dsp/MANIFEST.yaml` for its path and description
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
     - Use `provenance_footer()` from `canon/stack.py` for the canon part
     - Read MANIFEST version from `raw/repos/fsi-dsp/MANIFEST.yaml`

## Step 6: Emit activity log

- Append to `wiki/activity/YYYY-MM.md` (create if needed)
- Format:
  ```
  ## YYYY-MM-DDTHH:MM:SSZ
  **Skill:** /dsp:plan
  **Overlay:** {overlay name or "base"}
  **Input:** {request text}
  **Output:** {plan file path}
  **Canon stack:** {active_layers() output}
  **Gate results:** {comma-separated gate:status pairs}
  ```

## Rules

- NEVER generate inline Terraform resource blocks. If no artifact matches, say so and suggest a PR.
- NEVER invoke mcp-confluent create/update/delete tools. Read-only inspection only.
- Every invocation writes a plan file (even failures) and emits an activity log entry.
- Gate bypass requires explicit gate names — no blanket "skip all" supported.
- If MCP servers are unavailable, gates 3 and 4 can be bypassed with --gate-bypass.
