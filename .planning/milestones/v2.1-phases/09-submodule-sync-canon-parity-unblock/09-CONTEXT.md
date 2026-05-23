# Phase 9: Submodule sync + canon-parity unblock — Context

**Gathered:** 2026-05-23
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — smart_discuss skipped per workflow §Sub-step 3 infrastructure-detection rule)

<domain>
## Phase Boundary

Bump the `raw/repos/fsi-dsp` submodule pointer from local `feat/module-cc-cluster-basic@2989473` to upstream `main` HEAD (currently `5a86fd2`, 23+ commits ahead including the LinuxONE accelerator + the 2989473 branch's own merge into main); resolve the two pre-existing test failures from the v2.0 audit (`test_check_canon_parity`, `test_manifest`); add a stale-submodule CI guard that enforces tracking of upstream `main` within an allowed drift window. After this phase, the submodule reflects the LinuxONE accelerator on disk and the v2.0 audit debt is cleared.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion

All implementation choices at Claude's discretion — this is pure infrastructure:
- Goal keywords are operational ("Bump", "resolve", "add ... guard")
- Success criteria are all technical (command runs, tests pass, workflow fails on drift, suite passes)
- No user-facing behavior described — operators run `git submodule update`, CI fails or passes; no UI, no skill output change

Use ROADMAP phase goal + success criteria + the established G.2c CI drift-gate pattern (`.github/workflows/streaming-skills-drift.yml`, `tools-classification-drift.yml`) as the reference shape.

</decisions>

<code_context>
## Existing Code Insights

Codebase context will be gathered during plan-phase research. Key reference points:

- **`tools/check_canon_parity.py`** + **`tests/test_check_canon_parity.py`** — the canon-parity test that currently fails; needs to pass at the bumped pointer
- **`tools/check_manifest.py`** + **`tests/test_manifest.py`** — the manifest test that currently fails; needs to pass at the bumped pointer
- **`.github/workflows/streaming-skills-drift.yml`** (H.3b) and **`.github/workflows/tool-classification-drift.yml`** (G.2c) — established CI drift-gate patterns to mirror for the new submodule-drift workflow
- **`raw/repos/fsi-dsp`** — the submodule itself; currently on `feat/module-cc-cluster-basic@2989473`, target is upstream `main@5a86fd2` (or HEAD at execution time)

</code_context>

<specifics>
## Specific Ideas

- **Drift window:** 14 days is the proposed default (per SUBM-03 success criterion); confirm this in plan-phase if a different cadence aligns better with FSI release-train expectations.
- **Bump shape:** Single commit that advances the submodule pointer + clears the 2 test failures atomically — easier to revert if downstream regressions surface during the suite run.
- **CI guard implementation:** Pure shell + `git ls-remote` (no Node.js, no API auth) mirrors the G.2c pattern; reuse the workflow shape directly.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. The G.2 carry-forward and `/dsp:scaffold` expansion items remain in the backlog parking lot (out of v2.1 scope).

</deferred>
