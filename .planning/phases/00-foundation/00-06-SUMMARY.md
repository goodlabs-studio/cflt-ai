---
phase: 00-foundation
plan: "06"
subsystem: ci-enforcement
tags: [ci, manifest, citations, stability, parity]
dependency_graph:
  requires: ["00-02", "00-05"]
  provides: [CNTR-03, CNTR-04, CNTR-05]
  affects: [cflt-ai-ci, fsi-dsp-ci, wiki-citations, manifest-contract]
tech_stack:
  added: [check-citations.py, check-manifest-stability.py, manifest-citations.yml, manifest-stability.yml]
  patterns: [CI-enforcement, submodule-commit-pattern, pytest-fixtures]
key_files:
  created:
    - .github/workflows/manifest-citations.yml
    - tools/check-citations.py
    - raw/repos/fsi-dsp/.github/workflows/manifest-stability.yml
    - raw/repos/fsi-dsp/scripts/check-manifest-stability.py
    - tests/test_manifest.py
  modified: []
decisions:
  - "fsi-dsp scripts committed inside submodule then parent pointer updated"
  - "check-citations.py exits 0 with 28 citations resolved against 50 MANIFEST.yaml IDs"
  - "check-manifest-stability.py allows ID removal only on major version bump (1.x -> 2.x)"
metrics:
  duration_minutes: 10
  completed_date: "2026-04-28"
  tasks_completed: 3
  files_created: 5
---

# Phase 00 Plan 06: CI Parity Enforcement Summary

CI enforcement for the MANIFEST.yaml contract between cflt-ai and fsi-dsp. cflt-ai blocks PRs where wiki citations reference non-existent MANIFEST.yaml IDs; fsi-dsp blocks PRs that remove stable IDs without a major version bump.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | cflt-ai citation check workflow and script (CNTR-05) | 425027a | tools/check-citations.py, .github/workflows/manifest-citations.yml |
| 2 | fsi-dsp ID stability workflow and script (CNTR-04) | 85e3133 (parent), 5721f9a (submodule) | raw/repos/fsi-dsp/scripts/check-manifest-stability.py, raw/repos/fsi-dsp/.github/workflows/manifest-stability.yml |
| 3 | MANIFEST.yaml completeness tests | 8720705 | tests/test_manifest.py |

## Verification Results

1. `python3 tools/check-citations.py` exits 0 — 28 citations resolved, 50 IDs in MANIFEST.yaml
2. `python3 -m pytest tests/test_manifest.py -v` — 17/17 passed
3. `.github/workflows/manifest-citations.yml` — valid YAML, triggers on wiki/**, submodules: true
4. `raw/repos/fsi-dsp/.github/workflows/manifest-stability.yml` — valid YAML, fetch-depth: 0, python 3.11
5. `raw/repos/fsi-dsp/scripts/check-manifest-stability.py` — compiles, contains get_ids and is_major_bump

## Decisions Made

- fsi-dsp scripts committed inside submodule repo first, then parent pointer updated — required by git submodule mechanics
- check-citations.py strips `fsi-dsp://` prefix to get bare ID for MANIFEST.yaml lookup
- check-manifest-stability.py uses `GITHUB_BASE_REF` env var, falls back to `main` for local testing
- ID removal allowed only on major version bump (e.g., 1.0.0 → 2.0.0); minor/patch bumps are blocked

## Deviations from Plan

None — plan executed exactly as written. Submodule commit pattern is standard git mechanics, not a deviation.

## Known Stubs

None. All CI scripts are fully functional. Tests verify real file existence and script logic.

## Self-Check: PASSED

- tools/check-citations.py: FOUND
- .github/workflows/manifest-citations.yml: FOUND
- raw/repos/fsi-dsp/scripts/check-manifest-stability.py: FOUND
- raw/repos/fsi-dsp/.github/workflows/manifest-stability.yml: FOUND
- tests/test_manifest.py: FOUND
- Commits: 425027a (task 1), 85e3133 (task 2), 8720705 (task 3): all FOUND
