---
phase: 03B-act-rail-apply
plan: 03
subsystem: testing
tags: [golden-harness, apply-rail, negative-space, profile-enforcement, acta-06]

requires:
  - phase: 03B-02
    provides: "apply engine implementation (apply_engine.py, dsp-apply.md skill)"
  - phase: 03B-01
    provides: "dsp-apply.md skill specification and gate chain integration"
  - phase: 03A-03
    provides: "golden act harness base (test_golden_act.py with 22 plan cases)"

provides:
  - "10 apply-specific golden cases (numbers 023-032) in tests/golden/act/cases/"
  - "TestGoldenApplyHarnessStructure class validating apply case structure"
  - "Apply-specific constants: APPLY_REQUIRED_FIELDS, VALID_PROFILES, VALID_CONFIRMATIONS, APPLY_CASES"
  - "script/* artifact types added to VALID_ARTIFACT_TYPES for DR failover coverage"

affects: [03C-per-tool-classification, phase-4-eval-gates]

tech-stack:
  added: []
  patterns:
    - "Apply cases use 4 extra frontmatter fields (skill, profile, confirmation, expected_incident) on top of base REQUIRED_FIELDS"
    - "Negative-space apply cases always include 'no matching artifact' in required_claims (consistent with plan harness)"
    - "APPLY_CASES filtered from ALL_CASES by skill field — no separate glob needed"
    - "Valid profile guard in test_apply_case_has_valid_profile skips unknown-profile negative-space cases"

key-files:
  created:
    - tests/golden/act/cases/apply-topic-engineer-023.md
    - tests/golden/act/cases/apply-schema-engineer-024.md
    - tests/golden/act/cases/apply-flink-engineer-025.md
    - tests/golden/act/cases/apply-rbac-engineer-026.md
    - tests/golden/act/cases/apply-dr-break-glass-027.md
    - tests/golden/act/cases/apply-readonly-blocked-028.md
    - tests/golden/act/cases/apply-bypass-confirmation-029.md
    - tests/golden/act/cases/apply-bypass-skip-030.md
    - tests/golden/act/cases/apply-unknown-profile-031.md
    - tests/golden/act/cases/apply-gate-drift-032.md
  modified:
    - tests/golden/act/test_golden_act.py

key-decisions:
  - "Apply negative-space cases include 'no matching artifact' in required_claims for consistency with plan harness pattern"
  - "script/* artifact types added to VALID_ARTIFACT_TYPES rather than creating a separate apply artifact type set"
  - "test_apply_case_has_valid_profile skips unknown-profile negative-space cases (admin profile rejection is the test point)"
  - "APPLY_CASES computed from ALL_CASES filtered by skill field, not a separate glob, maintaining single source of truth"

patterns-established:
  - "Apply cases extend base case format: 8 REQUIRED_FIELDS + 4 apply-specific fields = 12 total fields"
  - "Break-glass profile does not bypass confirmation — incident article is always written for break-glass applies"
  - "Gate drift negative-space case validates unconditional gate re-run at apply time (bypass=None enforcement)"

requirements-completed: [ACTA-06]

duration: 8min
completed: 2026-04-29
---

# Phase 03B Plan 03: Apply Golden Cases Summary

**10 apply-specific golden cases + TestGoldenApplyHarnessStructure validation class extending the act rail harness to 32 total cases covering profile enforcement, confirmation gate, and bypass prevention**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-29T13:12:00Z
- **Completed:** 2026-04-29T13:20:26Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments

- Authored 10 apply cases (023-032): 5 positive (topic/schema/flink/rbac via engineer + DR failover via break-glass) and 5 negative-space (read-only block, 2 bypass vectors, unknown profile, gate drift)
- Extended test runner with `TestGoldenApplyHarnessStructure` (10 test methods) validating apply-specific fields, profile enforcement, and bypass coverage
- Added `script/*` artifact types to `VALID_ARTIFACT_TYPES` to support DR failover/failback script artifacts
- Full test suite green: 675 tests passed (202 baseline + 64 new apply harness tests = 266 in act harness; all other test modules unchanged)

## Task Commits

1. **Task 1: Author 10 apply golden cases** - `4a7d4d6` (feat)
2. **Task 2: Extend test runner with apply-specific validation class** - `2a0e782` (feat)

## Files Created/Modified

- `tests/golden/act/cases/apply-topic-engineer-023.md` - Positive apply case: topic creation, engineer profile, confirms incident article written
- `tests/golden/act/cases/apply-schema-engineer-024.md` - Positive apply case: schema registry, engineer profile
- `tests/golden/act/cases/apply-flink-engineer-025.md` - Positive apply case: Flink deployment, engineer profile, haiku floor
- `tests/golden/act/cases/apply-rbac-engineer-026.md` - Positive apply case: RBAC role binding, engineer profile, haiku floor
- `tests/golden/act/cases/apply-dr-break-glass-027.md` - Positive apply case: DR failover, break-glass profile, confirms break-glass does not bypass confirmation
- `tests/golden/act/cases/apply-readonly-blocked-028.md` - Negative-space: read-only profile blocked at Step 2 before any gates run
- `tests/golden/act/cases/apply-bypass-confirmation-029.md` - Negative-space: ACTA-02 bypass vector (a) — "apply immediately without confirmation"
- `tests/golden/act/cases/apply-bypass-skip-030.md` - Negative-space: ACTA-02 bypass vector (b) — "just do it, skip all checks"
- `tests/golden/act/cases/apply-unknown-profile-031.md` - Negative-space: unknown profile "admin" rejected at Step 1 with valid profile list
- `tests/golden/act/cases/apply-gate-drift-032.md` - Negative-space: gate re-run at apply time detects state drift and blocks
- `tests/golden/act/test_golden_act.py` - Added VALID_ARTIFACT_TYPES script entries, APPLY_REQUIRED_FIELDS/VALID_PROFILES/VALID_CONFIRMATIONS/APPLY_CASES constants, TestGoldenApplyHarnessStructure class

## Decisions Made

- Apply negative-space cases include "no matching artifact" in `required_claims` to maintain consistency with the plan harness pattern (all negative-space cases claim no artifact was produced)
- `script/*` artifact types added directly to `VALID_ARTIFACT_TYPES` (not a separate apply-specific set) — the set is shared across all case types
- `test_apply_case_has_valid_profile` skips the valid-profile check for negative-space cases because testing rejection of an unknown profile name ("admin") IS the point of apply-unknown-profile-031
- `APPLY_CASES` filtered from `ALL_CASES` by `skill == "/dsp:apply"` — single source of truth, no separate glob

## Deviations from Plan

None - plan executed exactly as written.

Note: The pre-existing `TestNegativeSpaceCoverage.test_negative_cases_require_no_match_response` test was potentially a concern — it requires all negative-space cases to have "no matching artifact" in required_claims. This was resolved by designing all 5 apply negative-space cases to include this claim, which is semantically accurate (no artifact was applied in any of the blocked/refused scenarios).

## Issues Encountered

None.

## Next Phase Readiness

- Golden harness now covers the full act rail: 22 plan cases + 10 apply cases = 32 total
- Structural correctness >= 95% validated across all 32 cases (all 675 tests green)
- Phase 03B is now complete (plans 01, 02, 03 all done)
- Phase 03C (per-tool classification) can proceed with the apply rail proven structurally correct
- The golden harness framework is stable and extensible for Phase 03C per-tool test cases

---
*Phase: 03B-act-rail-apply*
*Completed: 2026-04-29*
