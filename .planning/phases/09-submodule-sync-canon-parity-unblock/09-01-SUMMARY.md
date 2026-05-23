---
phase: 09-submodule-sync-canon-parity-unblock
plan: 01
subsystem: infra
tags: [submodule, fsi-dsp, manifest, canon-parity, linuxone-accelerator]

# Dependency graph
requires:
  - phase: 03A-act-rail-plan
    provides: "tools/check-canon-parity.py + MODULE_TO_CANON_KEY contract; tests/test_check_canon_parity.py drift gate"
  - phase: 00-foundation
    provides: "fsi-dsp submodule registration + MANIFEST.yaml stability test pattern (tests/test_manifest.py)"
provides:
  - "raw/repos/fsi-dsp submodule pointer at upstream main HEAD (5a86fd2)"
  - "LinuxONE accelerator visible on disk (accelerators/confluent-on-linuxone/, 5 layers: rbac, tls, schema-governance, audit, flink)"
  - "MANIFEST.yaml version delta 1.0.0 -> 1.1.0 reflected in test assertions"
  - "v2.0-MILESTONE-AUDIT tech-debt cleared (both pre-existing test failures resolved)"
affects: [10-accelerator-type-contract, 11-act-rail-dispatch, 12-wiki-ingest-linuxone]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Atomic submodule-bump + dependent-test-fix commit pattern (single commit, easier to revert)"
    - "Pre-bump test assertions track upstream MANIFEST version explicitly (1.0.0 -> 1.1.0) — version bumps surface as test-edit work, not silent drift"

key-files:
  created:
    - ".planning/phases/09-submodule-sync-canon-parity-unblock/deferred-items.md"
  modified:
    - "raw/repos/fsi-dsp (submodule pointer: 2989473 -> 5a86fd2)"
    - "tests/test_manifest.py (version assertion 1.0.0 -> 1.1.0, method renamed to test_version_is_1_1_0)"

key-decisions:
  - "Atomic commit pattern: submodule bump + dependent test fix in ONE commit (per CONTEXT.md — easier to revert if downstream regressions surface)"
  - "No edit required to tools/check-canon-parity.py: the bump alone removes module/cc-cluster-basic from MANIFEST (capability never reached upstream main), so the DRIFT-1 violation disappears naturally"
  - "Explicit fetch + checkout of origin/main instead of git submodule update --remote: .gitmodules has no branch= field set, --remote would be a no-op or chase wrong branch; explicit form is deterministic"
  - "Pre-existing test_wiki_citations failure deferred (not caused by Phase 09 changes; originates from bd7f967 observability wiki commit) — logged to deferred-items.md"

patterns-established:
  - "Submodule pointer bump as atomic commit alongside test-debt clearance — proven shape for future fsi-dsp sync phases"

requirements-completed: [SUBM-01, SUBM-02]

# Metrics
duration: 4min
completed: 2026-05-23
---

# Phase 09 Plan 01: Submodule sync + canon-parity unblock Summary

**Bumped fsi-dsp submodule from feat/module-cc-cluster-basic@2989473 to upstream main@5a86fd2 (LinuxONE accelerator + 30 commits ahead) and cleared the two v2.0-audit test failures (test_no_drift_on_current_state, test_version_is_1_0_0) in a single atomic commit.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-05-23T15:17:00Z
- **Completed:** 2026-05-23T15:21:00Z
- **Tasks:** 3
- **Files modified:** 2 (committed atomically) + 1 deferred-items.md (not in atomic commit)

## Accomplishments

- Submodule pointer advanced to upstream main HEAD `5a86fd2` (byte-equal to `git ls-remote origin main`)
- LinuxONE accelerator tier visible on disk: `raw/repos/fsi-dsp/accelerators/confluent-on-linuxone/` with all 5 layers (`01-rbac`, `02-tls`, `03-schema-governance`, `04-audit`, `05-flink`) — foundational for Phase 10
- `test_check_canon_parity::test_no_drift_on_current_state` — PASS (was FAIL; resolved by the bump alone — `module/cc-cluster-basic` no longer in MANIFEST)
- `test_manifest::test_version_is_1_1_0` — PASS (renamed from `test_version_is_1_0_0`; assertion updated to match upstream `1.1.0`)
- `tools/check-canon-parity.py` untouched (verified via `git diff` empty) — the bump alone cleared the drift
- Targeted test pair: 26/26 passing (was 24/26)
- Full suite: 960 passing; 1 pre-existing failure (`test_wiki_citations::test_no_raw_fsi_dsp_paths_in_sources`) deferred — confirmed not caused by Phase 09 (reproduced on pre-bump tree)

## Task Commits

Single atomic commit covering all three tasks (per plan requirement — bump + test fix as one revertable unit):

1. **Task 1: Bump submodule pointer to upstream main HEAD** — staged in `d6d62a0`
2. **Task 2: Fix the two v2.0-audit test failures** — staged in `d6d62a0`
3. **Task 3: Run full suite + commit atomically** — committed `d6d62a0` (fix(submodule): bump fsi-dsp to upstream main + clear v2.0-audit test debt)

**Commit hash:** `d6d62a0`
**Files in commit:** exactly `raw/repos/fsi-dsp` + `tests/test_manifest.py` (verified via `git log -1 --name-only`)

## Files Created/Modified

- `raw/repos/fsi-dsp` — submodule pointer bumped `2989473553bb0d3b8082df446fae2c6b3053ea89` → `5a86fd28935d4732f22ea139634987769777faf8`
- `tests/test_manifest.py` — `test_version_is_1_0_0` renamed to `test_version_is_1_1_0`; assertion updated from `"1.0.0"` to `"1.1.0"` with inline rationale comment
- `.planning/phases/09-submodule-sync-canon-parity-unblock/deferred-items.md` — logged the pre-existing `test_wiki_citations` failure (originates from `bd7f967`, not Phase 09)

## Decisions Made

- **Atomic commit pattern:** Submodule pointer bump + dependent test fix in a single commit. Easier to revert if downstream regressions surface; matches CONTEXT.md guidance.
- **No `tools/check-canon-parity.py` edit needed:** The DRIFT-1 violation (`module/cc-cluster-basic` has no entry in `MODULE_TO_CANON_KEY`) is resolved purely by the submodule bump — upstream main's MANIFEST never had that capability. Less code churn, less risk.
- **Explicit `fetch origin main` + `checkout` instead of `git submodule update --remote`:** `.gitmodules` has no `branch =` field; `--remote` would either no-op or chase the wrong default. Explicit form is deterministic and matches what the plan specifies.
- **Pre-existing `test_wiki_citations` failure deferred, not auto-fixed:** Per GSD SCOPE BOUNDARY rule, only auto-fix issues directly caused by the current task's changes. Reproduced the failure on the pre-bump tree via `git stash` to confirm it's not a regression. Logged to `deferred-items.md` for follow-up (likely Phase 12 wiki ingest or a separate hygiene PR).

## Deviations from Plan

None affecting the plan's atomic commit or test-fix work — plan executed exactly as written. One out-of-scope issue logged and deferred (see Issues Encountered).

## Issues Encountered

- **Pre-existing test failure surfaced during full-suite run:** `tests/test_wiki_citations.py::TestNoRawPaths::test_no_raw_fsi_dsp_paths_in_sources` flags 6 wiki articles (the observability expansion from commit `bd7f967`) that use raw `raw/repos/fsi-dsp/...` paths in their `sources:` frontmatter instead of `fsi-dsp://` ID form.
  - **Resolution:** Confirmed pre-existing via `git stash && pytest ...` reproduction on the pre-bump tree. Logged to `.planning/phases/09-submodule-sync-canon-parity-unblock/deferred-items.md`. Not blocking Phase 09: the two failures Phase 09 was scoped to clear are both green; the bump itself introduces zero new failures.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **Phase 10 (accelerator type contract):** READY. LinuxONE accelerator directory exists on disk at `raw/repos/fsi-dsp/accelerators/confluent-on-linuxone/` with all 5 layers. `tools/check-canon-parity.py` MODULE_TO_CANON_KEY can be extended for the new `type: accelerator` capabilities in Phase 10 without churning on stale local-feature-branch state.
- **Phase 11 (act rail dispatch):** Unblocked once Phase 10 publishes the type contract; submodule pointer is stable at upstream main.
- **Phase 12 (wiki ingest):** Unblocked. LinuxONE accelerator's DESIGN.md, KNOWN-GAPS.md, MIGRATION.md, RUNBOOK.md, ATTRIBUTION.md all visible on disk for ingest.
- **Carry-forward for non-Phase-09 work:** `test_wiki_citations` failure on 6 observability articles needs `fsi-dsp://` ID-form conversion — likely fits Phase 12 wiki ingest discipline or a separate hygiene PR.

## Self-Check: PASSED

- File `raw/repos/fsi-dsp` staged + committed: FOUND
- File `tests/test_manifest.py` edited + committed: FOUND
- File `.planning/phases/09-submodule-sync-canon-parity-unblock/09-01-SUMMARY.md` created: FOUND (this file)
- File `.planning/phases/09-submodule-sync-canon-parity-unblock/deferred-items.md` created: FOUND
- Commit `d6d62a0` exists: FOUND (verified `git log --oneline | grep d6d62a0`)
- Targeted tests `pytest tests/test_check_canon_parity.py tests/test_manifest.py` exit 0: VERIFIED (26 passed)
- Submodule SHA matches upstream: VERIFIED (`5a86fd28935d4732f22ea139634987769777faf8` byte-equal both sides)
- LinuxONE accelerator on disk: VERIFIED (`accelerators/confluent-on-linuxone/layers/{01-rbac,02-tls,03-schema-governance,04-audit,05-flink}` all present)

---
*Phase: 09-submodule-sync-canon-parity-unblock*
*Completed: 2026-05-23*
