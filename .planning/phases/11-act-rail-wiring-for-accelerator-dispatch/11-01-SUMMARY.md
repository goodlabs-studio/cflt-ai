---
phase: 11-act-rail-wiring-for-accelerator-dispatch
plan: 01
subsystem: infra
tags: [canon-parity, accelerator, kustomize, fsi, ci, drift-detection]

# Dependency graph
requires:
  - phase: 10-accelerator-artifact-type-registration
    provides: "type: accelerator schema in MANIFEST.yaml with apply_sequence + per-layer canon_key fields; check_manifest.py validator"
provides:
  - "5 accelerator/confluent-on-linuxone:<layer> composite entries in MODULE_TO_CANON_KEY"
  - "5 dotted-path fsi.* canon keys in canon/industry/fsi/overrides.yaml"
  - "check_parity() walker extension that iterates accelerator apply_sequence and emits [DRIFT-1] on canon_key mismatch, unknown layer, or orphan canon-key reference"
  - "check_parity() optional fsi_overrides_path arg for test isolation"
  - "8 new tests (5 positive layer-mapping + 3 negative-space) + 2 fsi-overrides assertion tests"
affects:
  - 11-02 (executor: relies on composite-key map existing)
  - 11-03 (act-harness: 5 layer cases assume DRIFT-1 enforcement)
  - 11-04 (profile gating)
  - 12 (wiki ingest: documents accelerator layers as canon-tied)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Composite '<artifact-id>:<layer-name>' keys for capability-canon mapping (D-04)"
    - "Tri-source canon resolution: defaults.yaml + fsi/overrides.yaml unioned via optional fsi_overrides_path arg"
    - "Tempdir-isolated tests pass a non-existent fsi_overrides_path to avoid unioning production fsi keys"

key-files:
  created: []
  modified:
    - tools/check-canon-parity.py
    - tests/test_check_canon_parity.py
    - canon/industry/fsi/overrides.yaml

key-decisions:
  - "fsi.* keys placed in canon/industry/fsi/overrides.yaml (not canon/base/defaults.yaml) — keeps FSI-overlay-only keys out of the base canon; check_parity unions both into canon_keys"
  - "check_parity() signature extended with optional fsi_overrides_path arg (default = PROJECT_ROOT canon/industry/fsi/overrides.yaml) — production behavior unchanged, but tempdir tests can isolate fixtures from real fsi keys"
  - "Three distinct [DRIFT-1] shapes for accelerator: unknown composite, canon_key mismatch (names both sides), orphan canon-key reference — auditable CI output, unambiguous remediation path"
  - "CANON_INFRA_KEYS filters out composite keys (those containing ':') — keeps direction-2 WARN-2 reverse-lookup terraform-module-only; accelerator reverse direction is enforced by per-layer canon_key field on MANIFEST"
  - "test_module_to_canon_key_values_present_in_defaults updated to union defaults.yaml + fsi/overrides.yaml — single test catches missing canon definitions across both files"

patterns-established:
  - "Composite-key parity: `<artifact-id>:<layer-name>` → dotted-path canon key, walked via apply_sequence iteration alongside flat terraform-module entries"
  - "Tri-source canon union: defaults (base) ∪ fsi/overrides (industry) — explicit, test-injectable"
  - "Tempdir test isolation pattern: pass non-existent fsi_overrides_path to bypass production canon during synthetic-fixture tests"

requirements-completed: [MAN-04, MAN-05]

# Metrics
duration: 6min
completed: 2026-05-23
---

# Phase 11 Plan 01: Bidirectional canon parity for accelerator layers Summary

**MODULE_TO_CANON_KEY grew from 2 → 7 entries with 5 composite accelerator/confluent-on-linuxone:<layer> keys; check_parity() walker now traverses apply_sequence and emits [DRIFT-1] on three distinct failure modes; 19 tests pass against post-Phase-10 MANIFEST.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-05-23T17:00:30Z (approx)
- **Completed:** 2026-05-23T17:06:20Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- MODULE_TO_CANON_KEY now covers all 5 LinuxONE accelerator layers with explicit composite-key entries (RBAC, TLS, schema governance, audit, Flink)
- check_parity() walker iterates accelerator apply_sequence alongside existing terraform-module loop with zero regression to terraform-module behavior
- 5 fsi.* dotted-path canon keys landed in canon/industry/fsi/overrides.yaml with _source provenance back to the upstream MANIFEST
- Phase 11 success criteria 3 + 4 satisfied: unknown layer produces blocking DRIFT-1, bidirectional CI extended to accelerator entries (no workflow YAML edit needed — script extension does the work)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add 5 fsi.* dotted-path keys + extend MODULE_TO_CANON_KEY composite entries** — `dcc1bec` (feat)
2. **Task 2: Extend check_parity() to walk accelerator apply_sequence + 8 new tests** — `ece76b5` (feat)

**Plan metadata:** (pending — final commit ties SUMMARY + STATE + ROADMAP together)

## Files Created/Modified

- `tools/check-canon-parity.py` — MODULE_TO_CANON_KEY (2→7 entries); accelerator-walking block in check_parity(); optional fsi_overrides_path arg with PROJECT_ROOT default; CLI `--fsi-overrides-path` flag; expanded module docstring
- `tests/test_check_canon_parity.py` — +8 tests (5 TestAcceleratorParity + 3 TestAcceleratorNegativeSpace), +2 TestParityScript assertions for accelerator coverage; `_make_accelerator_manifest()` helper; existing tempdir tests updated to pass synthetic fsi_overrides_path for fixture isolation
- `canon/industry/fsi/overrides.yaml` — 5 new top-level dotted-path keys (fsi.security.mds-rbac, fsi.security.tls-fips, fsi.schema.compatibility-full-transitive, fsi.audit.events-retention, fsi.flink.environment-mtls) each with `_source: fsi-dsp://accelerator/confluent-on-linuxone/<layer>` provenance

## Decisions Made

- **fsi.* keys live in canon/industry/fsi/overrides.yaml, not defaults.yaml** — these are FSI-overlay-only; base canon (defaults.yaml) stays vendor-neutral. check_parity unions both files via the new fsi_overrides_path arg, so direction-1 resolution still works.
- **Composite-key shape unchanged from CONTEXT.md D-04 lock** — flat strings `<id>:<layer>`, no nested dicts. Keeps walker grep-friendly and the MODULE_TO_CANON_KEY dict shape uniform across terraform-module and accelerator entries.
- **Three distinct [DRIFT-1] error shapes** — unknown layer, canon_key mismatch (names both sides), orphan canon-key reference. Plan called for 2 (unknown + mismatch); orphan-reference was added because the existing terraform-module direction-1 emits the same shape and parity discipline says accelerator should mirror it.
- **CLI `--fsi-overrides-path` flag added** — symmetrical with `--defaults-path`. Future overlays (e.g., manufacturing, healthcare) slot in via the same arg.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] check_parity() unioning production fsi/overrides.yaml broke 3 existing tempdir tests**

- **Found during:** Task 2 (running full suite after walker landed)
- **Issue:** Plan assumed check_parity would read fsi/overrides.yaml via PROJECT_ROOT (Task 2 Step 1a). When implemented, the 3 existing tempdir-only tests (test_detects_missing_canon_key, test_detects_both_modules_missing_canon_keys, test_terraform_module_parity_unchanged) silently picked up the real production fsi keys (topic_design lives in both base + fsi overrides), causing expected DRIFT-1 violations to disappear because the canon_keys union resolved them. False negatives, not false positives — tests reported no drift when drift was the intended test signal.
- **Fix:** Added optional `fsi_overrides_path` parameter to `check_parity()` with PROJECT_ROOT default (production behavior unchanged). Updated 6 tempdir-based tests to pass `tmp / "no-overrides.yaml"` (non-existent path → silent skip via FileNotFoundError) so synthetic fixtures are the only canon source. Added CLI `--fsi-overrides-path` flag for symmetry.
- **Files modified:** tools/check-canon-parity.py (signature + FileNotFoundError silent skip), tests/test_check_canon_parity.py (6 callsites)
- **Verification:** All 19 tests pass; `python3 tools/check-canon-parity.py` (default args) still exits 0 against real MANIFEST.
- **Committed in:** ece76b5 (Task 2 commit)

**2. [Rule 2 - Missing critical] _make_accelerator_manifest helper insufficient for positive-path tests**

- **Found during:** Task 2 RED phase (positive tests failed with WARN-2 noise about missing terraform-modules)
- **Issue:** Plan's _make_accelerator_manifest produced a single-accelerator MANIFEST. The check_parity direction-2 reverse-lookup then fired WARN-2 for both module/topic and module/flink (since neither appeared in the synthetic capabilities), polluting the `assert drift == []` positive-path assertion.
- **Fix:** _run_layer_parity helper (the test-internal wrapper) now also includes module/topic + module/flink in the synthetic MANIFEST and topic_design + flink_sql in the synthetic defaults. Direction-2 reverse-lookup sees both terraform-modules present, no WARN-2 noise, positive-path tests get a clean `drift == []`.
- **Files modified:** tests/test_check_canon_parity.py (_run_layer_parity helper)
- **Verification:** All 5 TestAcceleratorParity tests pass with `drift == []`.
- **Committed in:** ece76b5 (Task 2 commit)

**3. [Rule 1 - Bug] test_module_to_canon_key_values_present_in_defaults regression after Task 1**

- **Found during:** Task 1 GREEN phase (after writing the new MODULE_TO_CANON_KEY entries, the existing test that asserts "every value is in defaults.yaml" failed because the new fsi.* values live in canon/industry/fsi/overrides.yaml, not defaults.yaml)
- **Issue:** The existing test was a snapshot of v1 invariants (when there were only 2 terraform-module entries, all canon keys were in defaults.yaml). Adding 5 accelerator entries with canon keys in overrides broke the invariant unconditionally.
- **Fix:** Updated the test to union defaults.yaml ∪ fsi/overrides.yaml and assert canon_key resolves in either. Reflects the production check_parity behavior; preserves the original test intent (no MODULE_TO_CANON_KEY orphan values).
- **Files modified:** tests/test_check_canon_parity.py
- **Verification:** Test passes; the union-based invariant now also covers future industry overlays.
- **Committed in:** dcc1bec (Task 1 commit)

---

**Total deviations:** 3 auto-fixed (2 Rule 1 bugs, 1 Rule 2 missing critical)
**Impact on plan:** All three deviations preserved the plan's intent — production behavior, test signal, and invariant scope — without expanding scope. The fsi_overrides_path parameter is a strict superset of the plan's "read both files" instruction (testable + CLI-exposed), so future overlays integrate without further engine changes.

## Issues Encountered

- None blocking. The 3 deviations above were all caught by the test suite during TDD GREEN cycles and resolved inline.
- Pre-existing test_wiki_citations failure (6 observability articles use raw paths in `sources:` field) carries forward from Phase 09; unrelated to Plan 11-01 work, documented in Phase 09 STATE/deferred-items.md.

## User Setup Required

None — pure code + canon changes, no external services involved.

## Next Phase Readiness

- 11-02 (`/dsp:apply` accelerator executor) can rely on the composite-key map already existing — no further check_canon_parity edits needed
- 11-03 (act-harness 5-layer cases) can build plans citing each composite canon-stack hash without parity drift
- 11-04 (profile gating) is independent of parity work
- CI gate `.github/workflows/canon-parity.yml` triggers on `raw/repos/fsi-dsp/**` and `canon/**` (unchanged) — any future PR that drifts the mirror map from upstream MANIFEST will fail this gate

---
*Phase: 11-act-rail-wiring-for-accelerator-dispatch*
*Completed: 2026-05-23*

## Self-Check: PASSED

- `tools/check-canon-parity.py` — FOUND
- `tests/test_check_canon_parity.py` — FOUND
- `canon/industry/fsi/overrides.yaml` — FOUND
- Commit `dcc1bec` (Task 1) — FOUND
- Commit `ece76b5` (Task 2) — FOUND
- `python3 tools/check-canon-parity.py` — exit 0
- `pytest tests/test_check_canon_parity.py -v` — 19/19 pass
- `pytest tests/` — 986 pass, 1 pre-existing failure (test_wiki_citations carry-forward from Phase 09)
