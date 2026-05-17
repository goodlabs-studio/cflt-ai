---
phase: H.4a-profile-family-schema-extension
plan: 01
subsystem: act-rail-profile-gating
tags: [profile-family, schema-extension, apply-engine, tool-overrides, fail-closed]

# Dependency graph
requires:
  - phase: 03C-act-rail-profile-gating
    provides: VALID_PROFILES set, PROFILE_TIER_ORDER, check_tool_permitted() tier cascade, load_profile() customer-overlay path
  - phase: G.2c-tool-classification-rename
    provides: tool_classification.json (54-tool kebab-case classification, unclassified_policy=deny)
provides:
  - VALID_FAMILIES = {"operator", "developer"} constant in apply_engine
  - family-aware load_profile() with back-compat default + per-family invariant validation
  - family-branched check_tool_permitted() (operator → tier cascade byte-identical; developer → tool_overrides dispatch)
  - Three operator profile JSONs with explicit "family": "operator" field
  - First developer-family fixture (test-dev-fixture.json) proving branch dispatch
  - Operator-permits snapshot (h4a_operator_permits.json) as regression guard for v1.0 behavior
affects: [H.4b, H.4c, H.3b]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Profile-family branching at check_tool_permitted() entry point (operator vs developer dispatch via load_profile().family)"
    - "Snapshot-based regression guard for all (profile × tool) decisions (one-liner regenerator embedded in test docstring)"
    - "Per-family invariant validation in _normalize_and_validate_profile() helper (pure-Python, no jsonschema dep)"
    - "Back-compat default injection with stderr surfacing (legacy fixtures load but get visibility on test runs)"

key-files:
  created:
    - tests/fixtures/profiles/test-dev-fixture.json
    - tests/snapshots/h4a_operator_permits.json
    - .planning/phases/H.4a-profile-family-schema-extension/H.4a-01-SUMMARY.md
  modified:
    - tools/apply_engine.py
    - tools/profiles/read-only.json
    - tools/profiles/engineer.json
    - tools/profiles/break-glass.json
    - tests/test_profile_gating.py

key-decisions:
  - "_normalize_and_validate_profile() implemented as a private module-level helper (not inside load_profile body) so it can be unit-tested directly if needed and so the customer-overlay path can call it without code duplication"
  - "Back-compat default uses sys.stderr.write() (no logging framework dep) — matches existing apply_engine.py style and surfaces in pytest output without separate handler config"
  - "Snapshot regenerator one-liner lives in TestOperatorBranchByteCompat docstring (not in plan file or external README) so it travels with the test that depends on it"
  - "Snapshot generated from live behavior post-Task 3 (not hand-rolled) so it captures the actual canonical decisions; 3 profiles × 54 tools = 162 booleans — read-only permits 10, engineer permits 44, break-glass permits 54"
  - "Customer-overlay path also runs _normalize_and_validate_profile() — applies family default to acme-bank engineer.json (which has no family field), preserving back-compat without forcing acme-bank fork to update"

patterns-established:
  - "Family-branched permission dispatch: load profile, read family, branch on family; future profile families slot in without rewriting check_tool_permitted()"
  - "Snapshot regression guard pattern (tests/snapshots/*.json): live-generated baseline, regenerated via one-liner in test docstring, drift in next PR forces visible-diff review"
  - "Per-family invariants enforced at load time (not at check time) — fail-closed before any permission decision can be made on a malformed profile"

requirements-completed: [PROFAM-01]

# Metrics
duration: 4min
completed: 2026-05-17
---

# Phase H.4a Plan 01: Profile-family schema extension Summary

**Family-aware load_profile() + family-branched check_tool_permitted() — operator branch byte-identical to v1.0, developer branch proven via fixture, 181/181 profile-gating tests pass.**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-05-17T17:22:19Z
- **Completed:** 2026-05-17T17:26:21Z
- **Tasks:** 5
- **Files modified:** 7 (3 new, 4 modified, plus this SUMMARY)

## Accomplishments

- `VALID_FAMILIES = {"operator", "developer"}` constant added to `tools/apply_engine.py` with docstring describing the family contract (D-08)
- `_normalize_and_validate_profile()` private helper: defaults absent family to "operator" (back-compat per D-02), rejects unknown family values (D-03), validates per-family invariants (D-07)
- `check_tool_permitted()` branches on family: operator → existing PROFILE_TIER_ORDER cascade (byte-identical to v1.0 Phase 3c); developer → `tool_overrides` map dispatch (fail-closed)
- Three operator profile JSONs gain explicit `"family": "operator"` between `description` and `allowed_operations` (D-01 placement)
- 4 new test classes (7 tests) in `tests/test_profile_gating.py`: TestFamilyRoundTrip (3), TestOperatorBranchByteCompat (1, snapshot-based, 162 decisions), TestDeveloperBranchDispatch (1, fixture-based), TestPerFamilyInvariants (2)
- `tests/fixtures/profiles/test-dev-fixture.json` (first developer-family fixture, test-only — VALID_PROFILES patched via monkeypatch in tests)
- `tests/snapshots/h4a_operator_permits.json` (3 profiles × 54 tools = 162 boolean decisions captured from live post-Task 3 behavior)

## Task Commits

Each task was committed atomically:

1. **Task 1: VALID_FAMILIES + family-aware load_profile()** — `e097d95` (feat)
2. **Task 2: Add family: "operator" to 3 profile JSONs** — `02db240` (feat)
3. **Task 3: Branch check_tool_permitted on family** — `ab86294` (feat)
4. **Task 4: Fixture + snapshot + 4 new test classes** — `735e95f` (test)

**Plan metadata commit:** Will be created after this SUMMARY + STATE/ROADMAP updates.

## Files Created/Modified

**Created:**
- `tests/fixtures/profiles/test-dev-fixture.json` — First developer-family fixture (test-only). Has family=developer, skill_blocklist=[], tool_overrides={produce-message, consume-messages, create-topics}. Used by TestDeveloperBranchDispatch.
- `tests/snapshots/h4a_operator_permits.json` — Snapshot of all (operator-profile × tool) → permit decisions. Baseline for TestOperatorBranchByteCompat regression guard.

**Modified:**
- `tools/apply_engine.py` — Added VALID_FAMILIES, _normalize_and_validate_profile() helper, family-aware load_profile(), family-branched check_tool_permitted(). Signature of check_tool_permitted unchanged.
- `tools/profiles/read-only.json` — Added `"family": "operator"` field.
- `tools/profiles/engineer.json` — Added `"family": "operator"` field.
- `tools/profiles/break-glass.json` — Added `"family": "operator"` field.
- `tests/test_profile_gating.py` — Extended import line with VALID_FAMILIES + PROFILES_DIR; appended 4 new test classes (174 → 181 tests).

## Decisions Made

- Customer-overlay profile (`canon/customer/acme-bank/profiles/engineer.json`) has no `family` field; runs through `_normalize_and_validate_profile()` which injects `family: "operator"` via the back-compat default. Customer fork stays unchanged — H.4c will explicitly add the field when acme-bank adopts the developer family.
- Snapshot generated from live post-Task 3 behavior rather than computed via a separate script. The plan's bash one-liner is the regenerator-of-record; it now lives verbatim in the TestOperatorBranchByteCompat docstring.
- `_normalize_and_validate_profile()` defined immediately above `load_profile()` (not at end of file) — keeps the contract next to its sole caller and follows Python convention for module-private helpers.

## Deviations from Plan

None — plan executed exactly as written. All 5 tasks completed in order with the exact acceptance criteria specified.

## Issues Encountered

- Full regression run (`pytest tests/`) surfaced 2 pre-existing failures unrelated to H.4a:
  1. `tests/test_check_canon_parity.py::TestCheckParity::test_no_drift_on_current_state` — DRIFT-1 for `module/cc-cluster-basic` missing from MODULE_TO_CANON_KEY mapping. Verified pre-existing via `git stash && pytest` (failed identically on HEAD without H.4a changes).
  2. `tests/test_manifest.py::TestManifestStructure::test_version_is_1_0_0` — MANIFEST.yaml version is 1.2.0 (fsi-dsp submodule bump), test still asserts 1.0.0. Verified pre-existing via the same stash check.

  Both are fsi-dsp drift, neither caused by the apply_engine refactor. Out of scope per Rule 4 (architectural / fsi-dsp manifest territory). Logged here for visibility; not fixed in this plan.

- All H.4a-relevant suites pass clean: `pytest tests/test_profile_gating.py` 181/181, `pytest tests/golden/` 539/539, `pytest tests/evals/run_skill_evals.py` 177/177.

## Pre-existing test issues

Documented above under Issues Encountered. Both predate Phase H.4a. Recommend filing as separate todo for the H.3b plan (fsi-dsp version-pin gate territory).

## User Setup Required

None — schema extension only, no external service config.

## Next Phase Readiness

**H.4b unblocked:**
- `VALID_FAMILIES` constant exists
- `check_tool_permitted()` developer branch is wired and tested
- `_normalize_and_validate_profile()` enforces developer-family invariants (tool_overrides + skill_blocklist, no allowed_operations)
- H.4b can author `tools/profiles/developer/sandbox.json` with `family: "developer"` and the engine will route it correctly without further surgery

**PROFAM-02 status:** Half-satisfied. Developer-branch dispatch proven via fixture. Full negative-space proof (operator profiles cannot invoke developer-tier-only tools and vice versa, with REAL profiles) requires H.4b's `developer-sandbox` profile + the H.4b negative-space test matrix.

**Snapshot baseline:** Captures the post-H.4a regression boundary. Any future change to tool_classification.json or the operator-branch logic that shifts permits will fail TestOperatorBranchByteCompat — regenerate via the docstring one-liner in a separate visible-diff PR.

## ROADMAP success criteria

1. ✓ Every existing profile has family="operator"; absence defaults to operator in load_profile (verified by TestFamilyRoundTrip)
2. ✓ check_tool_permitted branches on family — operator uses tier cascade, developer reads tool_overrides; both branches unit-tested
3. ✓ JSON Schema for profiles validates family field and rejects unknown values (implemented in Python per CONTEXT D-07; verified by TestFamilyRoundTrip.test_load_profile_rejects_unknown_family)
4. ✓ All existing operator-profile tests still pass — zero behavior change for operator family (verified by TestOperatorBranchByteCompat snapshot + 174 original profile_gating tests + 539 golden tests + 177 eval tests)

## Self-Check: PASSED

**File existence verified:**
- `tools/apply_engine.py` — FOUND (contains VALID_FAMILIES, _normalize_and_validate_profile, tool_overrides, family branching)
- `tools/profiles/read-only.json` — FOUND (contains `"family": "operator"`)
- `tools/profiles/engineer.json` — FOUND (contains `"family": "operator"`)
- `tools/profiles/break-glass.json` — FOUND (contains `"family": "operator"`)
- `tests/test_profile_gating.py` — FOUND (contains TestFamilyRoundTrip, TestOperatorBranchByteCompat, TestDeveloperBranchDispatch, TestPerFamilyInvariants)
- `tests/fixtures/profiles/test-dev-fixture.json` — FOUND (family=developer, tool_overrides present)
- `tests/snapshots/h4a_operator_permits.json` — FOUND (3 keys: read-only, engineer, break-glass; 54 tools each)

**Commits verified:**
- `e097d95` — Task 1 commit FOUND in git log
- `02db240` — Task 2 commit FOUND in git log
- `ab86294` — Task 3 commit FOUND in git log
- `735e95f` — Task 4 commit FOUND in git log

**Test verification:**
- `pytest tests/test_profile_gating.py` — 181/181 PASS
- `pytest tests/golden/` — 539/539 PASS
- `pytest tests/evals/run_skill_evals.py` — 177/177 PASS
- `pytest tests/` — 925/927 PASS (2 pre-existing failures unrelated to H.4a, documented above)

---
*Phase: H.4a-profile-family-schema-extension*
*Completed: 2026-05-17*
