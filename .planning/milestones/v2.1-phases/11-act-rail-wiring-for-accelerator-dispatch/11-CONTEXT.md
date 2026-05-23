# Phase 11: Act-rail wiring for accelerator dispatch — Context

**Gathered:** 2026-05-23
**Status:** Ready for planning
**Mode:** Auto-generated with locked decisions (autonomous run; integration points pre-mapped from existing G.1 terraform-module + G.2c canon-parity patterns)

<domain>
## Phase Boundary

Extend the `/dsp:plan` four-gate rail and the `/dsp:apply` executor to handle accelerator artifacts end-to-end:
1. Gate 1 (canon compliance) — 5-layer `MODULE_TO_CANON_KEY` entries for the accelerator layers (RBAC, TLS, schema-governance, audit, Flink)
2. `/dsp:apply` Step 7 executor — new `execute_accelerator()` function dispatched from `execute_artifact()`; walks `apply_sequence` layer-by-layer (build → `oc apply --dry-run=server` → `oc apply`)
3. Per-layer activity-log entries per ACTA-04 schema
4. Bidirectional canon-parity CI extension to cover `type: accelerator` entries
5. Profile gating: `read-only` refuses; `engineer` permits; `break-glass` requires two-step confirmation

After this phase, an operator can run `/dsp:plan create accelerator confluent-on-linuxone --layer 01-rbac` (and equivalents for the other 4 layers) and `/dsp:apply` against the resulting plan, with full canon-stack provenance and activity-log entries.

</domain>

<decisions>
## Implementation Decisions

### 5-layer MODULE_TO_CANON_KEY mapping (locked)

`MODULE_TO_CANON_KEY` in `tools/check-canon-parity.py` (lines 29-32 — currently 2 entries: `module/topic` → `topic_design`, `module/flink` → `flink_sql`).

**Extension shape:** Add 5 entries keyed by `accelerator/<id>:<layer>` composite to keep terraform-modules and accelerator-layers in the same flat map:

```python
MODULE_TO_CANON_KEY = {
    "module/topic": "topic_design",
    "module/flink": "flink_sql",
    "accelerator/confluent-on-linuxone:01-rbac": "fsi.security.mds-rbac",
    "accelerator/confluent-on-linuxone:02-tls": "fsi.security.tls-fips",
    "accelerator/confluent-on-linuxone:03-schema-governance": "fsi.schema.compatibility-full-transitive",
    "accelerator/confluent-on-linuxone:04-audit": "fsi.audit.events-retention",
    "accelerator/confluent-on-linuxone:05-flink": "fsi.flink.environment-mtls",
}
```

**Composite-key rationale:** Phase 11 uses composite `<artifact-id>:<layer-name>` keys (not nested dicts) to keep `check_parity()` walker simple and grep-friendly. Drift detection logic in `check-canon-parity.py` extends to also walk `apply_sequence` arrays from `type: accelerator` MANIFEST entries, comparing each layer's `canon_key` field against the composite-key map.

**Single source of truth still holds:** MANIFEST `canon_key` per-layer is canonical; cflt-ai's `MODULE_TO_CANON_KEY` mirror is enforced equal via the canon-parity CI gate (any divergence = `DRIFT-1` blocking violation).

### execute_accelerator() function (locked)

Add to `tools/apply_engine.py`. Signature mirrors `execute_terraform_module()`:

```python
def execute_accelerator(
    artifact: Dict,
    args: Dict[str, str],
    plan_slug: str,
    dry_run: bool = False,
    layer_filter: Optional[str] = None,  # NEW: optional per-layer execution; if None, walk full apply_sequence
) -> ExecutionResult:
    """Walk artifact.apply_sequence layer-by-layer.
    Per layer: kustomize build → oc apply --dry-run=server → oc apply (unless dry_run=True).
    Emits one ACTA-04 activity-log entry per layer.
    On any layer failure: halt sequence, emit blocked-outcome entry, return ExecutionResult(status="failed", failed_layer=...).
    """
```

Dispatch extension in `execute_artifact()`:
```python
elif artifact_type == "accelerator":
    return execute_accelerator(artifact, args, plan_slug, dry_run=dry_run,
                                layer_filter=args.get("layer"))
```

### Activity-log shape (locked — ACTA-04 already defined)

Per-layer entries reuse ACTA-04's 11-field schema. New field requirement:
- `layer_id` — the layer name (e.g., `01-rbac`); allows post-hoc filtering of per-layer outcomes for an accelerator apply

### Canon-parity CI extension (locked)

`tools/check-canon-parity.py` `check_parity()` currently iterates `terraform-module` entries (lines ~85-100). Extend to also iterate `accelerator` entries:
- For each `accelerator` entry, walk its `apply_sequence` list
- For each layer, compute composite key `<artifact-id>:<layer.layer>` and compare its `canon_key` against `MODULE_TO_CANON_KEY[composite]`
- Mismatch → drift string with `DRIFT-1: accelerator <id> layer <layer-name> declares canon_key '<X>' but MODULE_TO_CANON_KEY says '<Y>'`

Workflow `.github/workflows/canon-parity.yml` runs unchanged (already triggered on `raw/repos/fsi-dsp/**` and `canon/**` — accelerator changes hit both paths). No workflow YAML edits required.

### Profile gating (locked)

Profile gating lives in `tools/apply_engine.py` (existing G.2c precedent for terraform-module profile checks). Apply the same pattern:
- `read-only` profile: `execute_accelerator()` returns immediately with `status="refused"` and a clear activity-log entry
- `engineer` profile: permitted; walks the full apply_sequence
- `break-glass` profile: gated by the existing two-step confirmation pattern (CONFIRM APPLY → re-prompt with explicit operation enumeration)

Add accelerator entries to whatever profile JSON files exist for this gating (likely `tools/profiles/operator/*.json` per the v1.0 Phase 3c precedent).

### Test coverage (locked)

- **`/dsp:plan` golden act-harness**: 5 new cases (one per layer) — structurally-correct plans, provenance footer with canon-stack hash, MANIFEST ID reference
- **`/dsp:apply` per-layer dispatch**: 5 new tests asserting `execute_accelerator` walks layers in order, emits ACTA-04 entries, halts on dry-run failure
- **`MODULE_TO_CANON_KEY` parity**: 5 new tests asserting each layer's mapping; 1 negative test for unknown layer → `DRIFT-1`
- **Profile gating**: 3×5 = 15 tests (read-only refuses, engineer permits, break-glass two-step) for each of the 5 layers — but a parameterized test suite collapses this to ≤10 actual test methods

### Claude's Discretion

- Layer-filter CLI shape for `/dsp:plan create accelerator <id> --layer <name>`: implementation detail; planner picks based on existing CLI patterns
- Whether `execute_accelerator()` runs `kustomize` directly via subprocess or uses a wrapper helper — match the `execute_terraform_module()` subprocess pattern
- Exact location of profile gating JSON files (discover at planning time)

</decisions>

<code_context>
## Existing Code Insights

- **`tools/check-canon-parity.py`** (currently 2-entry MODULE_TO_CANON_KEY, lines 29-32). `check_parity()` walker iterates terraform-modules; needs extension to also walk accelerator apply_sequence arrays. Existing test coverage in `tests/test_check_canon_parity.py`.
- **`tools/apply_engine.py`** (lines 372-395 dispatcher). `execute_artifact()` currently only handles `terraform-module` + skipped fallback. `execute_terraform_module()` (line 396+) is the shape-mirror for the new accelerator executor. `ExecutionResult` dataclass already exists.
- **`raw/repos/fsi-dsp/MANIFEST.yaml`** post-Phase-10 contains the `accelerator/confluent-on-linuxone` entry with full apply_sequence + 5 canon_key per-layer fields.
- **`tools/check_manifest.py`** post-Phase-10 validates the new shape. Phase 11 doesn't modify the validator.
- **`.github/workflows/canon-parity.yml`** triggers on `raw/repos/fsi-dsp/**` (already covers accelerator MANIFEST entry changes via submodule pointer bumps) — no YAML edit needed; the script extension does the work.
- **G.1 terraform-module executor precedent**: `outputs/runs/<plan_slug>/` per-plan workspace; kustomize-based accelerator should use `outputs/runs/<plan_slug>/<layer-name>/` per-layer sub-directories for kustomize-build output capture (auditable per-layer artifacts).
- **G.2c profile-gating precedent**: `tools/profiles/operator/{read-only,engineer,break-glass}.json` (verify exact path during planning) — accelerator dispatch must integrate with this gate before any layer apply.

## Integration Map

```
/dsp:plan create accelerator <id> --layer <name>
   → reads MANIFEST entry by ID
   → gate 1 (canon compliance): MODULE_TO_CANON_KEY[<id>:<name>] ⊇ apply_sequence[layer].canon_key
   → gate 2-4: structural fsi-dsp coverage, schema, MCP state (existing logic, may be no-ops for accelerator)
   → emits plan with canon-stack provenance footer

/dsp:apply <plan>
   → profile gating (read-only refuse, engineer permit, break-glass two-step)
   → apply_engine.execute_artifact(artifact)
   → dispatches to execute_accelerator(artifact, args, plan_slug, dry_run=...)
      → for each layer in artifact.apply_sequence:
         → kustomize build {layer.path}
         → oc apply --dry-run=server -f -
         → if dry_run=False: oc apply -f -
         → emit ACTA-04 activity-log entry (operator, profile, plan_ref, layer_id, gate_results, execution_result, duration_seconds)
      → on any failure: halt, emit blocked-outcome, return ExecutionResult(status="failed", failed_layer=<name>)
```
</code_context>

<specifics>
## Specific Ideas

- **Mock `kustomize` and `oc` in tests** — these are cluster-dependent tools. Use `unittest.mock.patch('subprocess.run')` with realistic stdout/stderr returns. No live cluster in CI (KNOWN-GAPS G-01 from accelerator docs documents this constraint).
- **Layer-filter argument**: `--layer 01-rbac` operates on a single layer; absence walks the full sequence. Both shapes must work end-to-end.
- **Provenance footer**: Canon-stack hash MUST include the layer's `canon_key` in the hash input so the same plan operating on a different layer produces a different hash (auditable layer-of-record).

</specifics>

<deferred>
## Deferred Ideas

- **Live cluster validation** — explicit Phase 11 out-of-scope per ROADMAP; CI exercises kustomize-build + mocked apply only
- **GitOps apply mode** — backlog item G.2d; Phase 11 implements only direct apply
- **Composite scenario executor** (G.2b) — backlog item; the accelerator apply_sequence shape informs but doesn't implement composite scenarios

</deferred>
