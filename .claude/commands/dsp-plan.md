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
- Extract `--layer <name>` (optional — only valid when the matched artifact is `type: accelerator`)
- Remaining text after flags is the natural language request string
- Validation:
  - If `--gate-bypass` names an unknown gate, stop: `Error: unknown gate: <name>. Valid: canon_compliance, fsi_dsp_coverage, confluent_docs_schema, mcp_confluent_state`
  - If `--overlay` specifies a customer with no `canon/customer/<name>/overrides.yaml`, stop: `Error: overlay not found: canon/customer/<name>/overrides.yaml`
  - If no request text, stop: `Error: no request specified`

### Accelerator invocation shape

In addition to the natural-language request shape, `/dsp:plan` accepts an
explicit accelerator invocation:

```
/dsp:plan create accelerator <id> --layer <name>
```

Treat `create accelerator <id>` as a natural-language request equivalent to
"create accelerator <id>". Step 2's gate chain matches this to the
`accelerator/<id>` MANIFEST entry; `--layer <name>` scopes Step 4 selection
to a single kustomize layer from the artifact's `apply_sequence`.

The `--layer <name>` flag is rejected (Step 4 error) when the matched
artifact's `type` is anything other than `accelerator`.

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

### Accelerator artifact handling

If the matched artifact's `type` is `accelerator`:

- Read its `apply_sequence` list from MANIFEST.yaml
- If `--layer <name>` was supplied in Step 1:
  - Scope the plan to that single layer: select the matching entry from `apply_sequence`
  - **Validation:** if `<name>` is NOT present in `[l.layer for l in apply_sequence]`, stop with:
    `Error: layer '<name>' not in accelerator '<id>' apply_sequence`
  - The plan document's "Selected Artifact" section records the layer name AND its `canon_key`
- If `--layer` was NOT supplied:
  - The plan covers all layers in `apply_sequence`
  - The plan document's "Apply Sequence" subsection lists each layer with its `canon_key`
- **Gate 1 (canon compliance) validation:** for each in-scope layer, verify
  `MODULE_TO_CANON_KEY['<id>:<layer>']` equals the layer's `canon_key` field
  from MANIFEST. Mismatch = `DRIFT-1` blocking violation (delegated to
  `tools/check-canon-parity.py`'s `check_parity()` walker from Plan 11-01).
- **Per-layer arguments:** derive `build_command`, `dry_run_command`, and
  `apply_command` for the in-scope layer(s) from the artifact-level commands
  (substitute the layer's `path` for `overlays/prod` when scoping a single layer).

If `--layer <name>` was supplied but the matched artifact's `type` is NOT
`accelerator`, stop with: `Error: --layer flag only valid for type: accelerator artifacts`.

## Step 5: Produce plan document

- Write to `outputs/plans/<slug>-plan-<YYYY-MM-DD>.md` (create directory if needed)
- Slug: lowercase, first 5 words of request, joined with hyphens
- Plan document sections:
  1. **Selected Artifact** — artifact ID, path, description from MANIFEST
     - For `type: accelerator` artifacts with `--layer` scope, also include
       the layer name and its `canon_key`
  2. **Arguments** — derived variables/parameters for the artifact
  3. **Gate Results** — table of all gate results (gate | status | detail)
  4. **Canon Compliance** — active canon config relevant to this request
  5. **Provenance Footer** —

     For non-accelerator artifacts (existing behavior):
     `Canon stack: <layers> | Hash: <hash> | MANIFEST: <version> | Floor: <model> | Generated: <ISO-8601>`

     For accelerator artifacts with `--layer` scope:
     `Canon stack: <layers> | Layer: <layer-name> | Canon key: <canon_key> | Hash: <hash-including-canon_key> | MANIFEST: <version> | Floor: <model> | Generated: <ISO-8601>`

     For accelerator artifacts WITHOUT `--layer` scope (full apply_sequence):
     `Canon stack: <layers> | Apply sequence: <comma-separated layer names> | Hash: <hash-including-all-canon_keys> | MANIFEST: <version> | Floor: <model> | Generated: <ISO-8601>`

     **Layer-aware hash input (required for auditable layer-of-record):**
     - Start with `provenance_footer()` from `canon/stack.py` for the base canon part
     - For layer-scoped accelerator plans, derive the final hash as
       `sha256(f"{stack_hash}:{canon_key}").hexdigest()[:12]` — this ensures
       the same plan operating on a different layer produces a different hash
     - For full-sequence accelerator plans, derive the final hash as
       `sha256(f"{stack_hash}:" + ",".join(canon_keys_in_order)).hexdigest()[:12]`
     - Read MANIFEST version from `raw/repos/fsi-dsp/MANIFEST.yaml`
  6. **Apply Sequence** (accelerator artifacts only) —
     Layer list with each layer's: layer name, path, `canon_key`, and the
     per-layer `build_command` / `dry_run_command` / `apply_command` derived
     from the artifact-level commands. Plan 11-02's `execute_accelerator()`
     reads this section to dispatch the kustomize sequence layer-by-layer.

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
- For `type: accelerator` artifacts, `--layer <name>` scopes the plan to a single
  kustomize layer. Without `--layer`, the plan covers all layers in sequence.
  The four-gate chain validates each in-scope layer's `canon_key` against
  `MODULE_TO_CANON_KEY` (Plan 11-01); mismatch = `DRIFT-1` blocking violation.
