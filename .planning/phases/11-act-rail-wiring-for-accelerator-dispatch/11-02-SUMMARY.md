---
phase: 11-act-rail-wiring-for-accelerator-dispatch
plan: 02
subsystem: act-rail
tags: [apply-engine, accelerator, kustomize, oc, acta-04, fsi, executor, tdd]

# Dependency graph
requires:
  - phase: 11-act-rail-wiring-for-accelerator-dispatch
    plan: 01
    provides: "5 composite accelerator/confluent-on-linuxone:<layer> entries in MODULE_TO_CANON_KEY + canon_key fields on apply_sequence layers (post-Phase-10 MANIFEST shape)"
provides:
  - "execute_accelerator(artifact, args, plan_slug, dry_run=False, layer_filter=None) in tools/apply_engine.py"
  - "ExecutionResult.failed_layer: Optional[str] = None field for accelerator halt diagnostics"
  - "emit_activity_log_apply(layer_id=...) kwarg — additive 12th field; back-compat preserved for terraform-module callers"
  - "execute_artifact() dispatcher branch: elif artifact_type == 'accelerator' → execute_accelerator(..., layer_filter=args.get('layer'))"
  - "TestExecuteAccelerator (15 tests) + TestEmitActivityLogLayerIdBackCompat (2 tests) — full kustomize/oc mocked coverage"
  - "Module-level fake_binaries fixture in tests/test_apply_executor.py — reusable by Plan 11-04 TestAcceleratorProfileGating"
affects:
  - 11-04 (profile gating — sits on top of execute_accelerator; will add profile_name=None param additively)
  - 11-03 (act-harness — golden cases reference layer_id field this plan introduces)
  - 12 (wiki ingest — accelerator layers documented as canon-tied)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-layer ACTA-04 emission inside the executor (D-03 deviation from terraform-module's caller-emits pattern)"
    - "subprocess.run side_effect list for deterministic per-phase exit-code control in tests"
    - "Module-level pytest fixture (vs class-nested) for cross-plan fixture reuse"
    - "shutil.which() PATH check with fake-binary fixture — separates 'binary present' check from 'binary behavior' (which is patched at subprocess.run layer)"

key-files:
  created: []
  modified:
    - tools/apply_engine.py
    - tests/test_apply_executor.py

key-decisions:
  - "Per-layer activity-log emission lives INSIDE execute_accelerator() (via _emit_layer_log helper), not in /dsp:apply Step 8 caller — only the executor knows about layer iteration. This deviates from terraform-module's caller-emits-summary pattern; CONTEXT.md D-03 locked the per-layer-entry shape so this was the only viable home."
  - "Dry-run halt = early return with ExecutionResult(status='failure', failed_layer=<name>) — NOT a flag-and-continue pattern. Mirror of execute_terraform_module's init-failure early-return at line 463."
  - "Three halt points within a layer (build / dry-run / apply) all share the same early-return path: emit failure log entry, then _finalize_accelerator with failed_layer set."
  - "fake_binaries fixture at MODULE level (not class level) per plan-checker observation — Plan 11-04 will reuse without re-declaration."
  - "ExecutionResult.failed_layer default = None preserves byte-identical shape for terraform-module callers (back-compat)."
  - "emit_activity_log_apply layer_id kwarg defaults to None; when omitted, **Layer:** field is NOT inserted (back-compat assertion in TestEmitActivityLogLayerIdBackCompat)."
  - "11-04 will additively add profile_name=None to execute_accelerator signature (per key_context note) — 11-02 leaves that slot empty so 11-04 lands cleanly."

requirements-completed: [MAN-03]

# Metrics
duration: ~7min
completed: 2026-05-23
---

# Phase 11 Plan 02: Apply-engine accelerator executor Summary

**`execute_accelerator()` walks 5 LinuxONE layers via kustomize-build → oc dry-run → oc apply, emits per-layer ACTA-04 entries with the new `layer_id` field, halts cleanly on any non-zero exit with `failed_layer` populated — 17 new tests, zero regressions.**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-05-23T (parallel with 11-03)
- **Tasks:** 2
- **Files modified:** 2
- **Lines added:** 282 (apply_engine.py) + 388 (test_apply_executor.py) = 670

## Accomplishments

- `tools/apply_engine.py` gains `execute_accelerator()` mirroring `execute_terraform_module()` shape with three additions: `layer_filter` parameter, per-layer ACTA-04 emission, `failed_layer` field on ExecutionResult
- Dispatcher routes `type=="accelerator"` to the new executor with `layer_filter=args.get("layer")` passthrough
- `emit_activity_log_apply()` gains optional `layer_id` kwarg; when None, entry is byte-identical to pre-Phase-11 11-field shape (terraform-module callers unaffected)
- `tests/test_apply_executor.py` test count grew 12 → 29 (15 new TestExecuteAccelerator + 2 new TestEmitActivityLogLayerIdBackCompat)
- Module-level `fake_binaries`, `accelerator_artifact`, `apply_args` fixtures are reusable by Plan 11-04's TestAcceleratorProfileGating (per plan-checker observation)
- Phase 11 success criterion 2 enabler landed: `/dsp:apply` can now dispatch accelerator artifacts end-to-end (profile gating from 11-04 sits on top of this)

## Task Commits

1. **Task 1: execute_accelerator() + dispatcher + ExecutionResult.failed_layer + emit_activity_log_apply.layer_id** — `8d4a461` (feat)
2. **Task 2: TestExecuteAccelerator + TestEmitActivityLogLayerIdBackCompat (17 new tests)** — `c4f9bb7` (test)

## Files Created/Modified

- `tools/apply_engine.py` (+282 lines):
  - `ExecutionResult` dataclass gains `failed_layer: Optional[str] = None`; docstring updated to document the new field and the reserved `"refused"` status for Plan 11-04
  - `execute_artifact()` dispatcher gains `elif artifact_type == "accelerator"` branch; docstring expanded
  - NEW: `execute_accelerator()` (~150 lines) — walks `apply_sequence` layer-by-layer with kustomize+oc dispatch, halt-on-failure, per-layer logging
  - NEW: `_emit_layer_log()` helper — thin wrapper around `emit_activity_log_apply()` with `layer_id` populated
  - NEW: `_finalize_accelerator()` helper — `_finalize()` mirror that threads `failed_layer` into the returned ExecutionResult
  - `emit_activity_log_apply()` gains `layer_id: Optional[str] = None` kwarg + entry-assembly conditional that inserts `**Layer:** {layer_id}` between `**Artifact:**` and `**Plan:**` when non-None
- `tests/test_apply_executor.py` (+388 lines):
  - Module-level fixtures: `accelerator_artifact` (5-layer dict mirroring MANIFEST.yaml), `fake_binaries` (PATH shim for shutil.which), `apply_args` (overlay/profile/operator/plan_path)
  - `TestExecuteAccelerator` class with 15 tests covering full-sequence success, dry-run-halt, layer-filter, ACTA-04 emission per layer, dry-run flag, missing/empty apply_sequence, kustomize+oc binary-missing, dispatcher routing (with + without layer arg), terraform-module regression, build-failure halt, apply-failure halt, bad layer_filter
  - `TestEmitActivityLogLayerIdBackCompat` class with 2 tests asserting layer_id=None preserves pre-11 entry shape and layer_id="02-tls" inserts **Layer:** field in the correct position

## Decisions Made

- **Per-layer ACTA-04 emission lives inside the executor.** CONTEXT.md D-03 specified one entry per layer (not one summary entry). Since `/dsp:apply` Step 8's single emit call has no visibility into layer iteration, the executor itself must emit. Deviation from `execute_terraform_module`'s caller-emits-summary pattern; documented in the new executor's docstring.
- **Dry-run halt = early return.** Pattern matches `execute_terraform_module`'s init-failure early-return at line 463. Three potential halt points within a layer (build / dry-run / apply) all share the same return path: emit failure log, `_finalize_accelerator` with `failed_layer=layer_name`.
- **Module-level fixtures vs class-nested.** Per plan-checker observation, `fake_binaries` (and the other two shared fixtures) sit at module scope so Plan 11-04's TestAcceleratorProfileGating can use them without re-declaration. The shared fixture set also reduces noise in Test definitions.
- **layer_id kwarg position in entry.** Inserted between `**Artifact:**` and `**Plan:**` so the layer name appears alongside the artifact identifier (rather than at the end as an afterthought). Back-compat preserved: omitting layer_id produces zero textual diff against pre-11 entries.
- **`failed_layer` default = None.** Allows terraform-module and other executors to construct ExecutionResult without specifying the field; only accelerator failures populate it.
- **11-04 placeholder slot.** Plan 11-04 will additively add `profile_name=None` to `execute_accelerator()` signature for profile pre-flight gating. 11-02 leaves that slot empty (the field doesn't exist on the signature yet) so 11-04 lands cleanly without conflict.

## Deviations from Plan

### Auto-fixed Issues

None — plan executed as written. All deviations were anticipated and documented in the plan itself:

- The "per-layer emission inside executor" deviation from terraform-module pattern was called out in the plan's Task 1 Step 3 docstring guidance.
- The fake_binaries module-level scope was specified in the `<key_context>` block of the executor prompt.

### Additive Behavior Beyond Plan

The plan called for 10 tests (A–J); landed 15 in TestExecuteAccelerator + 2 in TestEmitActivityLogLayerIdBackCompat = 17 total. Extras (still within plan scope, just more granular):

- `test_empty_apply_sequence_returns_failure` — split from F (plan combined empty + missing apply_sequence; I covered both explicitly)
- `test_dispatcher_routes_accelerator_without_layer_arg` — split from I (verifies `layer_filter=None` passthrough when args lacks 'layer' key)
- `test_failed_kustomize_build_halts_at_first_layer` — bonus halt-mode coverage (plan focused on dry-run-halt but apply_engine has three halt points; this asserts build-failure halts too)
- `test_oc_apply_real_failure_halts_at_failing_layer` — bonus halt-mode (third halt point: real apply non-zero)
- `test_layer_filter_no_match_returns_failure` — bonus: unknown layer_filter returns failure (not silent no-op)

Plus the new `TestEmitActivityLogLayerIdBackCompat` class with 2 tests — the plan asked for the kwarg + entry-assembly change but did not require explicit back-compat assertions. Adding them prevents accidental regression if a future plan reorders entry_lines.

## Test Coverage Matrix

| Concern | Test method | Outcome |
|---|---|---|
| Full sequence success (5 layers × 3 phases = 15 per_phase) | test_full_sequence_success | PASS |
| Dry-run halt at 02-tls before subsequent layers/apply | test_dry_run_server_failure_halts_at_02_tls | PASS |
| layer_filter operation (single layer, 3 phases) | test_layer_filter_runs_only_matching_layer | PASS |
| ACTA-04 emission count (5) + layer_id order | test_acta04_emission_per_layer | PASS |
| dry_run=True skips real oc apply (10 subprocess calls) | test_dry_run_flag_skips_real_apply | PASS |
| Missing apply_sequence → failure | test_missing_apply_sequence_returns_failure | PASS |
| Empty apply_sequence → failure | test_empty_apply_sequence_returns_failure | PASS |
| kustomize binary missing | test_kustomize_binary_missing | PASS |
| oc binary missing (kustomize present) | test_oc_binary_missing | PASS |
| Dispatcher routes accelerator + layer arg | test_dispatcher_routes_accelerator_to_execute_accelerator | PASS |
| Dispatcher routes accelerator without layer arg | test_dispatcher_routes_accelerator_without_layer_arg | PASS |
| Terraform-module regression (scenario type still skipped) | test_terraform_module_regression_still_skipped_for_scenario | PASS |
| kustomize-build failure halts at layer 1 | test_failed_kustomize_build_halts_at_first_layer | PASS |
| oc apply real failure halts at failing layer | test_oc_apply_real_failure_halts_at_failing_layer | PASS |
| Unknown layer_filter → failure | test_layer_filter_no_match_returns_failure | PASS |
| Omitting layer_id produces pre-11 11-field entry | test_omitting_layer_id_produces_11_field_entry | PASS |
| layer_id="02-tls" inserts **Layer:** in correct position | test_layer_id_set_inserts_layer_field | PASS |

**Total: 17 new tests, all green. Full pytest tests/test_apply_executor.py: 29/29 PASS.**

## Issues Encountered

- None blocking. TDD GREEN on first run — implementation in Task 1 aligned with test expectations in Task 2 with zero rework.
- Pre-existing `test_wiki_citations` failure carries forward from Phase 09 (documented in 11-01 SUMMARY); not in this plan's scope.
- Two tests in `tests/golden/act/test_golden_act.py::TestAcceleratorCases` are RED — they're Plan 11-03's territory (golden act-harness, running in parallel) and will turn GREEN when 11-03 lands its 5 layer cases.

## User Setup Required

None — pure code + test changes, no external services or credentials involved.

## Next Phase Readiness

- **11-04 (profile gating)** can layer profile_name=None onto execute_accelerator's signature additively. The signature placeholder is intentionally empty so 11-04 lands without conflict. The module-level `fake_binaries`, `accelerator_artifact`, and `apply_args` fixtures are ready for direct reuse by TestAcceleratorProfileGating.
- **11-03 (act-harness)** can reference `layer_id` field in golden cases — the field is now wired through emit_activity_log_apply.
- **Phase 12** can consume `execute_accelerator` directly via dispatcher; the LinuxONE accelerator is now dispatchable end-to-end (modulo live cluster, which is explicit Phase 11 out-of-scope per ROADMAP).

---
*Phase: 11-act-rail-wiring-for-accelerator-dispatch*
*Completed: 2026-05-23*

## Self-Check: PASSED

- `tools/apply_engine.py` — FOUND
- `tests/test_apply_executor.py` — FOUND
- `.planning/phases/11-act-rail-wiring-for-accelerator-dispatch/11-02-SUMMARY.md` — FOUND
- Commit `8d4a461` (Task 1: execute_accelerator + dispatcher + layer_id) — FOUND
- Commit `c4f9bb7` (Task 2: TestExecuteAccelerator + back-compat) — FOUND
- `pytest tests/test_apply_executor.py -v` — 29/29 pass
- `pytest tests/` — 1036 pass, 3 pre-existing/parallel failures (test_wiki_citations from Phase 09; TestAcceleratorCases from Plan 11-03 running in parallel)
