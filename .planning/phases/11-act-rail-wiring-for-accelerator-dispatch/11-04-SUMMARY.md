---
phase: 11-act-rail-wiring-for-accelerator-dispatch
plan: 04
subsystem: act-rail
tags: [apply-engine, profile-gating, accelerator, fail-closed, fsi, executor, tdd]

# Dependency graph
requires:
  - phase: 11-act-rail-wiring-for-accelerator-dispatch
    plan: 02
    provides: "execute_accelerator() function with empty profile_name slot reserved for 11-04 (per-layer ACTA-04 emission + ExecutionResult.failed_layer + module-level fake_binaries fixture)"
provides:
  - "tools/profiles/engineer.json — allowed_operations gains accelerator/confluent-on-linuxone"
  - "tools/profiles/break-glass.json — allowed_operations gains accelerator/confluent-on-linuxone (two-step confirmation enforced upstream at /dsp:apply Step 6c)"
  - "execute_accelerator(profile_name: Optional[str] = None) — pre-flight profile gate inside the executor; returns status='refused' with single blocked-by-profile ACTA-04 entry when denied"
  - "execute_artifact() dispatcher threads profile_name=args.get('profile_name') to execute_accelerator()"
  - "TestAcceleratorProfileGating — 6 parameterized test methods covering 20 scenarios (5x3 + 3 + 2 standalone) plus full back-compat assertion for profile_name=None"
  - "status='refused' promoted from RESERVED to active in ExecutionResult docstring with semantics distinguishing it from 'skipped' (no executor) and 'failure' (executor errored)"
affects:
  - phase 12 (wiki ingest) — read-only operators will see refused entries for accelerator artifacts, completing the fail-closed inspection posture
  - .claude/commands/dsp-apply.md Step 6c — break-glass two-step confirmation UI remains the upstream gate; this plan deliberately does NOT re-implement it inside the executor

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pre-flight profile gate inside executor (additive Optional kwarg; profile_name=None bypasses for back-compat)"
    - "Single blocked-by-profile ACTA-04 entry on refused dispatch (vs per-layer entries on success/failure) — no layer_id field when no layer was iterated"
    - "ValueError from load_profile() caught and converted to status='refused' (never raises) — defensive against malformed callers"
    - "pytest.mark.parametrize on class-level LAYERS list to collapse 5x3 matrix into 3 methods + 1 negative-space parametrize"

key-files:
  created:
    - .planning/phases/11-act-rail-wiring-for-accelerator-dispatch/11-04-SUMMARY.md
  modified:
    - tools/profiles/engineer.json
    - tools/profiles/break-glass.json
    - tools/apply_engine.py
    - tests/test_apply_executor.py

key-decisions:
  - "Break-glass two-step confirmation is /dsp:apply Step 6c's responsibility, NOT execute_accelerator()'s. The executor trusts that the caller has already captured break-glass confirmation upstream. Separation of concerns: profile-level permission lives in profile JSON, interactive UI lives in the skill spec."
  - "profile_name=None default bypasses the gate entirely (back-compat with Plan 11-02's 17 tests that don't pass the kwarg). Caller is responsible for gating when None is supplied."
  - "Unknown profile names (e.g., 'nonexistent-profile') are caught (ValueError from load_profile) and converted to ExecutionResult(status='refused', ...) — never raise. Prevents malformed callers from crashing the executor mid-dispatch; surfaces the bad name in stderr_tail for diagnostics."
  - "Single blocked-by-profile ACTA-04 entry on refused dispatch (vs N per-layer entries on success). The refused entry has NO layer_id field — no layer was iterated, so layer_id=None preserves the activity-log invariant that layer_id is present iff a layer was visited."
  - "confirmation_status='blocked' on the refused entry mirrors the /dsp:apply Step 5 'blocked-by-profile' log shape — downstream activity-log readers (incident articles, audit pipelines) can filter on either confirmation_status='blocked' or execution_result='refused'."
  - "read-only.json was NOT modified. Empty allowed_operations list IS the correct fail-closed posture; adding an explicit denial would be redundant and could introduce drift."
  - "Removed redundant artifact_id assignment further down execute_accelerator (now set once at function top, before the gate)."

requirements-completed: [MAN-03]

# Metrics
duration: ~3min
completed: 2026-05-23
---

# Phase 11 Plan 04: Profile gating for accelerator dispatch Summary

**`execute_accelerator()` gains an additive `profile_name` kwarg that performs a pre-flight `check_profile_permits()` before any kustomize/oc invocation; read-only refuses, engineer permits, break-glass permits (two-step UI lives at /dsp:apply Step 6c) — 20 new parameterized test scenarios in 6 methods, all green, zero regressions.**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-05-23T17:18:39Z
- **Tasks:** 2 (Task 1: profile JSONs + docstring; Task 2: TDD RED -> GREEN pre-flight gate + test class)
- **Files modified:** 4 (tools/profiles/engineer.json, tools/profiles/break-glass.json, tools/apply_engine.py, tests/test_apply_executor.py)
- **Lines added/changed:** ~240 (+6 profile JSON, +12 docstring, +57 gate + dispatcher, +172 test class)

## Accomplishments

- All 3 operator profile JSONs configured correctly for accelerator dispatch:
  - `engineer.json` — appended `accelerator/confluent-on-linuxone`; description updated to mention FSI-hardened accelerators (LinuxONE)
  - `break-glass.json` — appended `accelerator/confluent-on-linuxone`; description updated to call out two-step confirmation
  - `read-only.json` — UNCHANGED (empty `allowed_operations: []` is the correct fail-closed posture)
- `execute_accelerator()` gains `profile_name: Optional[str] = None` parameter (additive — Plan 11-02's 17 tests continue to pass unchanged)
- Pre-flight profile gate runs BEFORE `apply_sequence` validation, kustomize/oc PATH check, or per-layer ACTA-04 emission
- On deny: emits exactly ONE `ACTA-04` activity-log entry with `confirmation_status="blocked"`, `execution_result="refused"`, and NO `layer_id` (no layer was iterated)
- `execute_artifact()` dispatcher threads `profile_name=args.get("profile_name")` through to `execute_accelerator()`
- `ExecutionResult.status` docstring promotes `"refused"` from RESERVED to active; documents the semantic distinction from `"skipped"` (no executor) and `"failure"` (executor errored)
- `TestAcceleratorProfileGating` class: 6 test methods, 20 parameterized scenarios (5×3 layer×profile matrix + 3 negative-space + 2 standalone), all passing
- Phase 11 success criterion 5 landed: `/dsp:apply` respects profile gating for accelerator artifacts; fail-closed for read-only AND for unknown accelerator IDs across all 3 profiles

## Task Commits

1. **Task 1: Profile JSONs + ExecutionResult.status docstring** — `a3e0a42` (feat)
2. **Task 2 RED: TestAcceleratorProfileGating (20 failing scenarios)** — `6225b47` (test)
3. **Task 2 GREEN: Pre-flight profile gate in execute_accelerator() + dispatcher passthrough** — `304f520` (feat)

## Files Created/Modified

- `tools/profiles/engineer.json` (+1 entry, description updated): allowed_operations gains `accelerator/confluent-on-linuxone`
- `tools/profiles/break-glass.json` (+1 entry, description updated): allowed_operations gains `accelerator/confluent-on-linuxone` (two-step confirmation enforced at /dsp:apply Step 6c, not at profile level)
- `tools/profiles/read-only.json` (UNCHANGED): empty `allowed_operations: []` denies all operations — verified by `test_read_only_refuses_every_layer` parameterized over all 5 layers
- `tools/apply_engine.py` (+57 lines):
  - `ExecutionResult.status` docstring: `"refused"` promoted from RESERVED to active with full semantics
  - `execute_artifact()` dispatcher: threads `profile_name=args.get("profile_name")` to `execute_accelerator()`
  - `execute_accelerator()`: signature gains `profile_name: Optional[str] = None` (between `dry_run` and `layer_filter`)
  - `execute_accelerator()`: pre-flight gate block (lines ~570-610) — loads profile via `load_profile()` with customer-overlay support; `check_profile_permits()` decision; emits single blocked-by-profile entry on deny; ValueError caught and converted to refused
  - Removed redundant `artifact_id = artifact.get("id", "")` further down (now set once at function top)
- `tests/test_apply_executor.py` (+172 lines, +1 class):
  - `TestAcceleratorProfileGating` — 6 test methods reusing module-level `accelerator_artifact`, `fake_binaries`, `apply_args` fixtures placed by Plan 11-02
  - `LAYERS` class constant + `ACCEL_ID` for parameterization
  - Methods: `test_read_only_refuses_every_layer` (5 scenarios), `test_engineer_permits_every_layer` (5), `test_break_glass_permits_every_layer` (5), `test_unknown_accelerator_id_refused_by_every_profile` (3), `test_profile_name_none_skips_preflight_gate` (standalone), `test_unknown_profile_name_refused` (standalone)

## Decisions Made

- **Break-glass two-step lives upstream, not in the executor.** Profile-level permission goes in `break-glass.json` (the artifact ID is permitted); interactive `CONFIRM BREAK-GLASS` two-step lives in `.claude/commands/dsp-apply.md` Step 6c (already covers ALL artifact types). The executor trusts that the caller has captured break-glass confirmation upstream — `test_break_glass_permits_every_layer` verifies the executor honors the profile-level permission and does NOT re-implement the two-step UI. Separation of concerns enforced.
- **`profile_name=None` skips the gate entirely.** Plan 11-02's 17 TestExecuteAccelerator + TestEmitActivityLogLayerIdBackCompat tests do not pass `profile_name`. Adding a default of `None` (skip gate) preserves byte-identical behavior for those callers. The `/dsp:apply` skill spec is responsible for always supplying `profile_name` in production; the None default is for unit-test convenience and back-compat only.
- **ValueError from `load_profile()` is caught.** An unknown profile name (e.g., `"nonexistent-profile"`) would normally raise — the gate catches and converts to `status="refused"` with the offending name in `stderr_tail`. This prevents malformed callers (or callers that pass a profile name from an unvalidated source) from crashing the executor mid-dispatch.
- **Single blocked-by-profile ACTA-04 entry, no `layer_id`.** When refused, no layer was iterated — emitting per-layer entries would be misleading. The single entry has `confirmation_status="blocked"` (mirrors `/dsp:apply` Step 5 log shape) and `execution_result="refused"`. Downstream activity-log readers can filter on either field.
- **`read-only.json` deliberately unchanged.** Empty `allowed_operations: []` is the canonical fail-closed posture; adding an explicit denial would be drift and would invite confusion ("why is this entry here if it's denied anyway?"). The negative-space test `test_unknown_accelerator_id_refused_by_every_profile[read-only]` proves the empty list denies the accelerator artifact too.
- **`confirmation_status="blocked"` on the refused entry** mirrors `/dsp:apply` Step 5's `execution_result="blocked-by-profile"` log shape (when the skill spec catches the gate upstream). This means downstream consumers (incident articles, audit reports) can grep for either `confirmation_status="blocked"` OR `execution_result="refused"` and capture both upstream-gated and executor-gated denials.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Removed redundant `artifact_id` assignment**

- **Found during:** Task 2 GREEN
- **Issue:** Plan 11-02 had `artifact_id = artifact.get("id", "")` at line ~609 (just before the apply_sequence iteration). The new pre-flight gate must set `artifact_id` BEFORE that (at the top of the function), so the original assignment became dead code.
- **Fix:** Removed the redundant reassignment, left a comment noting `artifact_id was already set at the top of the function (pre-flight gate)`.
- **Files modified:** `tools/apply_engine.py`
- **Commit:** `304f520`

### Additive Behavior Beyond Plan

The plan called for 6 test methods, 18 parametrized scenarios. Final count: **6 methods, 20 parametrized scenarios** (5+5+5+3 = 18 from parametrize + 2 standalone). Plan was 18 "scenarios" but pytest's parametrize convention counts standalone tests as 1 scenario each, so 18+2 = 20 by pytest's reckoning. Method count (6) matches the plan exactly and is well under the `≤10 actual test methods` CONTEXT.md cap.

### Documentation Tightening

- Plan called for a docstring update on `ExecutionResult.status` documenting `"refused"`. Task 1 implementation went beyond the bare minimum: the new docstring distinguishes "refused" from "skipped" (no executor exists for this type) and "failure" (executor ran but errored), and explicitly states that refused emits one ACTA-04 entry with `execution_result="refused"` and no `layer_id`. This makes the activity-log invariant grep-able in the docstring itself.
- `execute_accelerator()` docstring `Args:` section gains a new `profile_name:` paragraph (~10 lines) covering: when the gate fires, when it skips (None default), the deny path's ACTA-04 emission shape, and the ValueError-caught-as-refused defensive behavior. The plan called for the parameter to be added but didn't require the docstring expansion; it landed because the parameter's semantics are subtle and a single-line `:param profile_name:` would have under-documented them.

## Test Coverage Matrix

| Method | Scenarios | Assertion |
|---|---|---|
| `test_read_only_refuses_every_layer` | 5 (layer 01..05) | status=='refused', subprocess.run not called, exactly 1 ACTA-04 with execution_result='refused' and no layer_id, stderr_tail mentions profile + artifact_id |
| `test_engineer_permits_every_layer` | 5 (layer 01..05) | status=='success', layer iterated, ACTA-04 entry has the right layer_id |
| `test_break_glass_permits_every_layer` | 5 (layer 01..05) | status=='success' (profile-level permit honored; two-step UI is upstream) |
| `test_unknown_accelerator_id_refused_by_every_profile` | 3 (profile read-only / engineer / break-glass) | status=='refused' for accelerator/does-not-exist across all 3 profiles (fail-closed); subprocess.run not called |
| `test_profile_name_none_skips_preflight_gate` | 1 standalone | status=='success' when profile_name=None (back-compat with 11-02) |
| `test_unknown_profile_name_refused` | 1 standalone | status=='refused', stderr_tail contains 'nonexistent-profile'; does NOT raise ValueError |
| **Totals** | **20 scenarios, 6 methods** | **20/20 PASS — well under the ≤10 method cap** |

Full suite: **249/249 PASS** in `tests/test_apply_executor.py` + `tests/test_profile_gating.py` + `tests/test_check_canon_parity.py` (Phase 11 integration set).

Pre-existing failure unchanged: `tests/test_wiki_citations.py::TestNoRawPaths::test_no_raw_fsi_dsp_paths_in_sources` carries forward from Phase 09 (6 wiki articles still cite raw/repos/fsi-dsp paths in sources — out of Phase 11 scope, documented in 11-01 and 11-02 SUMMARIES).

## How break-glass two-step interacts with execute_accelerator()

**It doesn't — by design.**

- Profile-level permission (`accelerator/confluent-on-linuxone` in `break-glass.json`'s `allowed_operations`) — answers "is this artifact allowed under this profile?"
- Interactive two-step confirmation — lives at `.claude/commands/dsp-apply.md` Step 6c (`CONFIRM BREAK-GLASS` → re-prompt with explicit operation enumeration). Already covers ALL artifact types.

`execute_accelerator()`'s pre-flight gate uses `check_profile_permits()` only — it permits the artifact under break-glass and proceeds. The two-step UI must have already happened upstream in `/dsp:apply` before the executor is even called. `test_break_glass_permits_every_layer` documents and enforces this contract: when called directly (skipping the upstream two-step), the executor permits break-glass operations — because the executor is not the two-step gate.

If we were to bake the two-step into the executor, it would (a) couple the executor to interactive prompt rendering (out of scope), (b) duplicate the gate (Step 6c already enforces it for all artifact types), and (c) make the executor untestable without a TTY mock. Separation of concerns wins.

## Phase 11 Closure

All 4 plans landed; all 4 requirements (MAN-02, MAN-03, MAN-04, MAN-05) verified:

| Plan | Requirement | Status | Commit landmarks |
|---|---|---|---|
| 11-01 | Canon-parity script extension + 5 composite layer canon-key entries | DONE | (per 11-01 SUMMARY) |
| 11-02 | execute_accelerator() executor + per-layer ACTA-04 emission + ExecutionResult.failed_layer | DONE | 8d4a461, c4f9bb7 |
| 11-03 | Golden act-harness — 5 layer cases + provenance footer | DONE | (per 11-03 SUMMARY) |
| 11-04 | Profile gating — 3 profile JSONs + execute_accelerator() pre-flight gate | DONE | a3e0a42, 6225b47, 304f520 |

`/dsp:apply` against accelerator artifacts is now dispatchable end-to-end with profile gating, per-layer ACTA-04 entries, canon-parity drift detection, and golden-act coverage. Live cluster validation remains explicit Phase 11 out-of-scope (per ROADMAP); CI exercises kustomize-build + mocked oc apply.

## Issues Encountered

- None blocking. TDD RED → GREEN clean: all 20 scenarios failed with the expected `TypeError: execute_accelerator() got an unexpected keyword argument 'profile_name'` during RED, all 20 turned GREEN after the Task 2 implementation, zero rework.
- The redundant `artifact_id` assignment (auto-fixed under Rule 1) was a minor cleanup, not a blocker.
- Pre-existing `test_wiki_citations` failure unchanged from Phase 09; explicitly out of this plan's scope (carry-forward, documented in 11-01 and 11-02 SUMMARIES).

## User Setup Required

None — pure code + test + profile-JSON changes. No external services, no new credentials, no migration scripts.

## Next Phase Readiness

Phase 11 is complete. Phase 12 (wiki ingest — accelerator layers documented as canon-tied) can proceed with the full Phase 11 surface area: end-to-end `/dsp:plan` + `/dsp:apply` dispatch for the LinuxONE accelerator, with canon-parity CI enforcement, golden act-harness coverage, and fail-closed profile gating.

The `accelerator/confluent-on-linuxone` artifact ID is now safe for production operator runs in `engineer` and `break-glass` profiles (the latter gated by the existing two-step UI), and is correctly refused in `read-only` and against unknown artifact IDs across all 3 profiles.

---
*Phase: 11-act-rail-wiring-for-accelerator-dispatch*
*Completed: 2026-05-23*

## Self-Check: PASSED

- `tools/profiles/engineer.json` — FOUND
- `tools/profiles/break-glass.json` — FOUND
- `tools/profiles/read-only.json` — FOUND (unchanged, as planned)
- `tools/apply_engine.py` — FOUND
- `tests/test_apply_executor.py` — FOUND
- `.planning/phases/11-act-rail-wiring-for-accelerator-dispatch/11-04-SUMMARY.md` — FOUND
- Commit `a3e0a42` (Task 1: profile JSONs + docstring) — FOUND
- Commit `6225b47` (Task 2 RED: 20 failing scenarios) — FOUND
- Commit `304f520` (Task 2 GREEN: pre-flight gate + dispatcher passthrough) — FOUND
- `pytest tests/test_apply_executor.py::TestAcceleratorProfileGating` — 20/20 PASS
- `pytest tests/test_apply_executor.py tests/test_profile_gating.py tests/test_check_canon_parity.py` — 249/249 PASS
- `pytest tests/` — 1064 pass, 1 pre-existing carry-forward (test_wiki_citations from Phase 09, out of scope)
