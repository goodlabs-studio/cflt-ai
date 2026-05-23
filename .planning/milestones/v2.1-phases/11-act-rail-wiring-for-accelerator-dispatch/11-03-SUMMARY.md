---
phase: 11-act-rail-wiring-for-accelerator-dispatch
plan: 03
subsystem: act-rail
tags: [accelerator, dsp-plan, golden-harness, kustomize, linuxone, fsi, provenance]

# Dependency graph
requires:
  - phase: 11-act-rail-wiring-for-accelerator-dispatch
    plan: 01
    provides: "MODULE_TO_CANON_KEY composite-key entries + canon-parity walker — cross-plan integration test imports MODULE_TO_CANON_KEY to validate accelerator case canon_keys"
provides:
  - "/dsp:plan --layer <name> flag (skill-spec level)"
  - "Layer-aware provenance footer with canon_key in hash input (sha256-derived, no canon/stack.py change)"
  - "5 accelerator-* golden cases (one per kustomize layer of accelerator/confluent-on-linuxone)"
  - "TestAcceleratorCases (7 methods, 11 test points incl. parametrized layer iteration)"
  - "VALID_ARTIFACT_TYPES extended with accelerator/confluent-on-linuxone"
affects:
  - 11-02 (executor): reads "Apply Sequence" subsection from plan output to drive per-layer dispatch
  - 11-04 (profile gating): plan-rail emission unaffected, but the layer-aware provenance is gate-readable
  - 12 (wiki ingest): future activity-log entries cite layer-specific canon_key

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Layer-aware provenance hash: sha256(f'{stack_hash}:{canon_key}')[:12] — keeps canon/stack.py vendor-agnostic; layer-specific hashing lives at the skill-spec level"
    - "Cross-plan integration test pattern: importlib.util loading tools/check-canon-parity.py (hyphenated filename) to assert act-harness layer map aligns with parity walker's MODULE_TO_CANON_KEY"
    - "Layer→canon_key dict shared across plan-rail, executor, parity walker, golden harness — single source of truth replicated in 3 places (MANIFEST.yaml, MODULE_TO_CANON_KEY, ACCELERATOR_LAYER_TO_CANON_KEY) with cross-plan tests enforcing equality"

key-files:
  created:
    - tests/golden/act/cases/accelerator-rbac-100.md
    - tests/golden/act/cases/accelerator-tls-101.md
    - tests/golden/act/cases/accelerator-schema-governance-102.md
    - tests/golden/act/cases/accelerator-audit-103.md
    - tests/golden/act/cases/accelerator-flink-104.md
  modified:
    - .claude/commands/dsp-plan.md
    - tests/golden/act/test_golden_act.py

key-decisions:
  - "Layer-aware hash derivation handled at the skill-spec level (sha256 over '{stack_hash}:{canon_key}'), not by extending canon/stack.py — keeps canon module vendor-agnostic and avoids cross-cutting an unrelated module for a single artifact-type's needs"
  - "Cross-plan integration test (test_accelerator_canon_keys_align_with_module_to_canon_key) imports MODULE_TO_CANON_KEY via importlib.util to handle the hyphenated filename — catches divergence between act-harness and parity walker without duplicating the source-of-truth dict"
  - "VALID_ARTIFACT_TYPES extended with accelerator/confluent-on-linuxone (single artifact, not the 5 composite keys) — the parity walker handles per-layer canon_key cross-checks; the act-harness only needs to know the artifact ID is valid"
  - "TestAcceleratorCases reuses existing REQUIRED_FIELDS / load_case / CASES_DIR module-level constants (no duplication) — additive class within the existing test module"

patterns-established:
  - "Layer-scoped artifact invocation shape: /dsp:plan create <type> <id> --layer <name> — extensible to future artifact-types with multi-step apply_sequences"
  - "Per-artifact-type provenance hash variants: skill spec documents three footer shapes (non-accelerator, layer-scoped, full-sequence) — future multi-layer artifacts pattern-match this"
  - "Golden harness positive cases ALSO forbid 'resource \"confluent_' — defense-in-depth against inline-Terraform leakage even on positive paths (not just ACT-06 negative-space cases)"

requirements-completed: [MAN-02]

# Metrics
duration: 5min
completed: 2026-05-23
---

# Phase 11 Plan 03: /dsp:plan accelerator skill spec + 5-layer golden harness coverage Summary

**/dsp:plan gained --layer flag with layer-aware provenance hashing; 5 golden act-harness cases (one per LinuxONE kustomize layer) land at v1.0 90% threshold (actually 100%); cross-plan integration test enforces MODULE_TO_CANON_KEY parity with act-harness layer map.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-05-23T17:10Z (approx)
- **Completed:** 2026-05-23T17:14Z
- **Tasks:** 2 (RED → GREEN with TDD)
- **Files created:** 5 (case files)
- **Files modified:** 2 (skill spec + test runner)

## Accomplishments

- `/dsp:plan` skill spec extended end-to-end for accelerator artifacts: `--layer <name>` parsing (Step 1), accelerator artifact handling block (Step 4), layer-aware provenance footer (Step 5), Apply Sequence subsection (Step 5), and explicit accelerator rule (Rules)
- 5 golden cases (IDs 100-104) land in `tests/golden/act/cases/`, one per kustomize layer of `accelerator/confluent-on-linuxone`, each carrying the layer's canon_key in `required_claims` (RBAC, TLS, SR governance, audit, Flink)
- `TestAcceleratorCases` (7 methods, 11 test points via parametrization) joins the golden harness with zero regressions to the existing 30+ act cases
- Cross-plan integration test `test_accelerator_canon_keys_align_with_module_to_canon_key` imports `tools/check-canon-parity.py`'s `MODULE_TO_CANON_KEY` and asserts equality with `ACCELERATOR_LAYER_TO_CANON_KEY` — catches future drift between act-harness and parity walker
- Full golden act suite: 307/307 pass (was 266; +41 new test points). Full repo: 1033 pass (excluding pre-existing wiki_citations carry-forward)
- Phase 11 success criterion 1 satisfied: golden act-harness now contains ≥5 accelerator cases at v1.0 90% threshold (currently 100% — 41/41 accelerator-touching test points pass)

## Task Commits

Each task was committed atomically with `--no-verify` (parallel-execution discipline alongside 11-02):

1. **Task 1: Extend /dsp:plan skill spec for accelerator artifacts** — `f6e1cf8` (feat)
   - Step 1: `--layer <name>` flag parsing + Accelerator invocation shape doc
   - Step 4: Accelerator artifact handling block (apply_sequence, layer validation, Gate 1 MODULE_TO_CANON_KEY cross-check)
   - Step 5: Three provenance footer shapes (non-accelerator, layer-scoped, full-sequence) + Apply Sequence subsection
   - Rules: explicit accelerator rule

2. **Task 2 RED: TestAcceleratorCases golden harness assertions** — `06a7eea` (test)
   - 7 test methods + ACCELERATOR_LAYER_TO_CANON_KEY shared constant + VALID_ARTIFACT_TYPES extension

3. **Task 2 GREEN: 5 accelerator golden cases** — `fcdc23d` (test)
   - One per layer; each asserts artifact ID + layer name + canon_key + kustomize substrings; forbids inline Terraform + wrong-layer signal

**Plan metadata commit:** (pending — final commit ties SUMMARY + STATE + ROADMAP together)

## Files Created/Modified

### Created

- `tests/golden/act/cases/accelerator-rbac-100.md` — 01-rbac → fsi.security.mds-rbac
- `tests/golden/act/cases/accelerator-tls-101.md` — 02-tls → fsi.security.tls-fips
- `tests/golden/act/cases/accelerator-schema-governance-102.md` — 03-schema-governance → fsi.schema.compatibility-full-transitive
- `tests/golden/act/cases/accelerator-audit-103.md` — 04-audit → fsi.audit.events-retention
- `tests/golden/act/cases/accelerator-flink-104.md` — 05-flink → fsi.flink.environment-mtls

### Modified

- `.claude/commands/dsp-plan.md` — +71 lines / -2 lines
  - Step 1: `--layer <name>` flag + Accelerator invocation shape subsection
  - Step 4: Accelerator artifact handling block (apply_sequence read, --layer validation, Gate 1 canon_key cross-check, per-layer command derivation)
  - Step 5: Three provenance footer shapes documented; layer-aware hash derivation specified at skill-spec level (`sha256(f"{stack_hash}:{canon_key}")[:12]`); Apply Sequence subsection for 11-02's executor
  - Rules: explicit accelerator entry
- `tests/golden/act/test_golden_act.py` — +134 lines
  - `VALID_ARTIFACT_TYPES` extended with `"accelerator/confluent-on-linuxone"`
  - `ACCELERATOR_LAYER_TO_CANON_KEY` module-level constant (5 entries)
  - `TestAcceleratorCases` class with 7 methods (incl. one parametrized 5x for 11 total test points)

## (id, layer, canon_key) Mapping Table

| Case file | id | layer | canon_key |
|-----------|----|----|-----------|
| accelerator-rbac-100.md | accelerator-rbac-100 | 01-rbac | fsi.security.mds-rbac |
| accelerator-tls-101.md | accelerator-tls-101 | 02-tls | fsi.security.tls-fips |
| accelerator-schema-governance-102.md | accelerator-schema-governance-102 | 03-schema-governance | fsi.schema.compatibility-full-transitive |
| accelerator-audit-103.md | accelerator-audit-103 | 04-audit | fsi.audit.events-retention |
| accelerator-flink-104.md | accelerator-flink-104 | 05-flink | fsi.flink.environment-mtls |

## Decisions Made

- **Layer-aware hash derivation lives at the skill-spec level (`sha256(f'{stack_hash}:{canon_key}')[:12]`), NOT in canon/stack.py** — keeps the canon module vendor-agnostic; layer-specific hashing is a per-artifact-type concern, not a canon concern. The plan asked "did canon/stack.py need to change, or was it handled at the skill-spec level?" — handled at skill-spec level via documented formula.
- **Cross-plan integration test reuses `tools/check-canon-parity.py`'s MODULE_TO_CANON_KEY via importlib.util** — the hyphenated filename means standard `import` doesn't work; `importlib.util.spec_from_file_location` loads it. Catches divergence between act-harness and parity walker without duplicating the layer→canon_key dict.
- **VALID_ARTIFACT_TYPES extended with the single accelerator ID, not the 5 composite keys** — the parity walker (Plan 11-01) handles per-layer canon_key cross-checks; the act-harness only needs to validate `expected_artifact` is a recognized type. Composite keys belong in MODULE_TO_CANON_KEY, not VALID_ARTIFACT_TYPES.
- **TestAcceleratorCases reuses existing REQUIRED_FIELDS / load_case / CASES_DIR module-level constants** — no duplication. The existing harness pattern is "module-level constants + test classes that reuse them"; the accelerator class is additive.
- **Test file path: `tests/golden/act/test_golden_act.py` (NOT `test_act_golden.py` as the plan body referenced)** — discovered during execute; the existing runner was added to in-place rather than creating a duplicate. The plan's `<files>` frontmatter named the correct path; only the `<action>` body had the inverted name.

## Plan Body Naming Discrepancy

The plan's `<action>` body referenced `tests/golden/act/test_act_golden.py`, but the actual runner is `tests/golden/act/test_golden_act.py` (and is named correctly in the plan's `<files>` frontmatter). The plan's instruction to "find the existing runner" + "do NOT create a duplicate runner" was honored — `test_golden_act.py` was extended in-place. This is a documentation discrepancy only; no behavioral impact.

## Deviations from Plan

None — plan executed as written, with these clarifications:

- **REQUIRED_FIELDS constant reused, not duplicated** (as plan instructed: "If the existing harness uses a different test-class naming or REQUIRED_FIELDS module-level constant, integrate accordingly. Do NOT duplicate REQUIRED_FIELDS — import the existing constant.")
- **VALID_ARTIFACT_TYPES needed extension** to accept `accelerator/confluent-on-linuxone` (otherwise the existing `test_positive_case_has_valid_artifact[accelerator-*-NNN]` would have failed). This is implicit in the plan's "Existing 30+ act-skill cases continue to pass (regression-free)" must-have truth — the constant extension is the only way to make BOTH the new accelerator cases AND the existing positive-case validator coexist.
- **Cross-plan integration test added** (`test_accelerator_canon_keys_align_with_module_to_canon_key`) — not explicitly in the plan's test method list (the plan called for 4 methods; final delivered 7 methods incl. parametrization). This is a Rule 2 enhancement: without it, drift between act-harness and parity walker would be silent. The test is cheap (one importlib call, one dict-equality assertion), high-signal (catches a real future-drift bug class), and stays inside Plan 11-03's scope (validates the act-harness — Plan 11-01's MODULE_TO_CANON_KEY is the upstream source of truth being asserted against).

## Issues Encountered

- None blocking. The only friction was the plan body's `test_act_golden.py` vs actual `test_golden_act.py` filename — easily reconciled by inspecting the directory.
- Pre-existing test_wiki_citations carry-forward from Phase 09 (unrelated, documented in Phase 09 STATE/deferred-items.md).

## User Setup Required

None — pure skill-spec + test changes, no external services involved.

## Next Phase Readiness

- **11-02** (apply_engine.py `execute_accelerator()`): can read the plan-document "Apply Sequence" subsection (per skill-spec Step 5.6) to drive per-layer dispatch. The plan emission side and execution side were designed in tandem (CONTEXT.md locked decisions).
- **11-04** (profile gating): unaffected by skill-spec changes — profile gating reads from plan output independent of layer-scope; same gates fire whether the plan covers 1 layer or 5.
- **Provenance audit trail**: each layer-scoped plan produces a distinct hash (different `canon_key` → different `sha256` input). When 11-02 lands and operators run actual `/dsp:plan create accelerator confluent-on-linuxone --layer 01-rbac` vs `--layer 02-tls`, the activity log will surface 5 distinct hashes for 5 distinct plan emissions — auditable layer-of-record as required by CONTEXT.md "Specific Ideas".

## Known Stubs

None — all 5 case files contain substantive content (test goal, MANIFEST link, layer→canon_key annotation). The skill spec documents the layer-aware hash formula concretely (`sha256(f'{stack_hash}:{canon_key}')[:12]`); no TODO/FIXME/placeholder markers introduced.

---
*Phase: 11-act-rail-wiring-for-accelerator-dispatch*
*Completed: 2026-05-23*

## Self-Check: PASSED

- `.claude/commands/dsp-plan.md` — FOUND
- `tests/golden/act/test_golden_act.py` — FOUND
- `tests/golden/act/cases/accelerator-rbac-100.md` — FOUND
- `tests/golden/act/cases/accelerator-tls-101.md` — FOUND
- `tests/golden/act/cases/accelerator-schema-governance-102.md` — FOUND
- `tests/golden/act/cases/accelerator-audit-103.md` — FOUND
- `tests/golden/act/cases/accelerator-flink-104.md` — FOUND
- Commit `f6e1cf8` (Task 1) — FOUND
- Commit `06a7eea` (Task 2 RED) — FOUND
- Commit `fcdc23d` (Task 2 GREEN) — FOUND
- `pytest tests/golden/act/ -v` — 307/307 pass
- `pytest tests/` (excluding pre-existing wiki_citations) — 1033 pass
