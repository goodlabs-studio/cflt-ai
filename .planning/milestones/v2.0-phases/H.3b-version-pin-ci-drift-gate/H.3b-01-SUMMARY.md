---
phase: H.3b-version-pin-ci-drift-gate
plan: 01
subsystem: vendor-pin + CI drift gate
tags: [drift-gate, version-pin, ci, vendor-sources, streaming-skills-plugin, mirror-g2c]
requires:
  - tools/vendor-sources.json (extended by this plan with streaming-skills-plugin entry)
  - tools/check_streaming_skills_drift.py (new this plan)
  - .github/workflows/streaming-skills-drift.yml (new this plan)
  - tests/test_check_streaming_skills_drift.py (new this plan)
provides:
  - INST-01 (fully satisfied — install was H.3a, pin + CI gate is H.3b)
  - Bidirectional vendor-pin discipline (mirrors G.2c pattern for the second vendor source)
  - Runtime drift detection for streaming-skills-plugin
affects:
  - none (no engine changes, no canon changes, no profile changes)
tech-stack:
  added: []  # Python stdlib only — no new dependencies
  patterns:
    - "Drift-check generator with --check / --dry-run / --help CLI"
    - "GitHub Actions path-scoped workflow with defensive verb-step"
    - "subprocess.run mocked via monkeypatch in tests"
key-files:
  created:
    - tools/check_streaming_skills_drift.py
    - .github/workflows/streaming-skills-drift.yml
    - tests/test_check_streaming_skills_drift.py
  modified:
    - tools/vendor-sources.json
decisions:
  - "Single drift-check script per vendor source (not a unified generator) — matches G.2c posture"
  - "git ls-remote chosen over GitHub Releases API to avoid rate limits and auth"
  - "No Node.js step in workflow — only git is needed (vs G.2c which uses npm)"
  - "Default mode (no --check) always exits 0 to support local diagnosis; CI uses --check"
metrics:
  duration_minutes: ~10
  completed_date: "2026-05-17"
  tasks_completed: 5
  files_created: 3
  files_modified: 1
---

# Phase H.3b Plan 01: Version pin + CI drift gate Summary

Pinned `streaming-skills-plugin` at commit `91d1871e` in `tools/vendor-sources.json` and shipped a CI drift gate (generator + workflow + tests) that fails any PR which moves the plugin off the pinned commit without a matching bump — mirroring G.2c's `tool-classification-drift` pattern exactly, swapping `npm-install` for `git ls-remote` against `confluentinc/agent-skills`.

## What landed

- **`tools/vendor-sources.json`** — Extended with `streaming-skills-plugin` entry (kind: `claude-plugin`, commit pinned at `91d1871e`). The existing `confluent-agent-skills` entry is byte-identical.
- **`tools/check_streaming_skills_drift.py`** — Drift-check generator with `--check` / `--dry-run` / `--help`. Exit codes: 0 (no drift), 1 (drift), 2 (config error), 3 (transient error). Python stdlib only.
- **`.github/workflows/streaming-skills-drift.yml`** — CI workflow with `pull_request` + `push: main` triggers, path-scoped to the three relevant files. Mirrors G.2c shape minus the Node.js step.
- **`tests/test_check_streaming_skills_drift.py`** — 9 test cases covering all 4 exit codes via `monkeypatch` of `subprocess.run`.

## Requirements

- **INST-01:** Fully satisfied. Install was H.3a; pin + CI drift gate is H.3b. Bidirectional drift detection now in place for the runtime-installed plugin.

## ROADMAP success criteria (H.3b)

1. **tools/vendor-sources.json contains pinned streaming-skills-plugin version + commit** — Done; entry includes `version: "1.0.0"` and `commit: "91d1871ef8c320be92bca955c8e42492a2778cb4"`.
2. **`.github/workflows/streaming-skills-drift.yml` exists; fails on PR when upstream plugin manifest differs from pinned without matching update** — Done; workflow runs `python tools/check_streaming_skills_drift.py --check` and exits non-zero on drift, missing entry, or transient error.
3. **Drift-gate generator has `--check` mode that exits non-zero on drift (mirrors G.2c pattern)** — Done; CLI shape mirrors `tools/regenerate_tool_classification.py` (argparse, `--check`, `--dry-run`, default summary mode).

## Live drift check result

- Command: `python3 tools/check_streaming_skills_drift.py --check`
- Exit code: **0**
- Pinned commit: `91d1871ef8c320be92bca955c8e42492a2778cb4`
- Live HEAD: `91d1871ef8c320be92bca955c8e42492a2778cb4` (matches pin — upstream has not moved since H.3a install on 2026-05-17)
- Output: `OK: pinned=91d1871ef8c320be92bca955c8e42492a2778cb4 matches live HEAD`

The script demonstrably works against the real upstream. The CI workflow will exercise this same path on every PR that touches the pin file, the script, or the workflow itself.

## Regression results

- `pytest tests/test_check_streaming_skills_drift.py -v` — **9/9 PASS**
- `pytest tests/test_profile_gating.py tests/test_per_family_isolation.py tests/test_canon_overlay.py tests/test_check_streaming_skills_drift.py -v` — **228/228 PASS**
- `pytest tests/golden/ -v` — **539/539 PASS**
- `pytest tests/` (full suite) — **951 PASS, 2 FAIL** (both pre-existing, same as H.4a/H.4b/H.4c):
  - `tests/test_check_canon_parity.py::TestCheckParity::test_no_drift_on_current_state` (terraform-module mapping drift — unrelated)
  - `tests/test_manifest.py::TestManifestStructure::test_version_is_1_0_0` (manifest at 1.2.0 — unrelated)
- No new failures introduced by H.3b.

## Vendor-pin discipline now uniform across:

- **`confluent-agent-skills`** (kind: `wiki-source`) — H.1 vendored at SHA `91d1871e`, used by `/wiki:ingest`. Drift caught passively by wiki-lint.
- **`streaming-skills-plugin`** (kind: `claude-plugin`) — H.3a installed at SHA `91d1871e`, used by upstream-skill activations. Drift caught actively by the new H.3b CI gate.

Both pinned in `tools/vendor-sources.json`. Both gated on the same commit SHA (intentional — they point at the same upstream repo, packaged differently).

## Deviations from Plan

None — plan executed exactly as written. All 5 tasks landed in order with the prescribed commit shape (feat/test). Each task's acceptance criteria were verified before commit. The pin matches live HEAD on first run (best-case outcome — no drift to demonstrate yet, but the test suite proves the drift-detection path works via mock).

## Deferred

- **Auto-bump-PR generator** (Renovate-like) — would auto-create PRs that bump the pin when upstream moves. Not blocking; manual PR is fine for now.
- **Per-skill drift** (finer than commit-pin) — defer until the overlay article needs more protection.
- **Combined vendor-drift workflow** — merge `tool-classification-drift.yml` + `streaming-skills-drift.yml` once we have ≥3 vendor sources. Premature now (2 workflows, different toolchains).

## Commits

- `67f4ee8` — `feat(H.3b-01): extend vendor-sources.json with streaming-skills-plugin entry`
- `647880b` — `feat(H.3b-01): add check_streaming_skills_drift.py drift-check generator`
- `6a521d3` — `feat(H.3b-01): add streaming-skills-drift.yml CI workflow`
- `2087f2d` — `test(H.3b-01): add tests for check_streaming_skills_drift covering all exit codes`

## Self-Check: PASSED

Verified:
- `tools/vendor-sources.json` extended — FOUND
- `tools/check_streaming_skills_drift.py` created — FOUND (executable)
- `.github/workflows/streaming-skills-drift.yml` created — FOUND (valid YAML)
- `tests/test_check_streaming_skills_drift.py` created — FOUND (9 tests, all pass)
- Commits `67f4ee8`, `647880b`, `6a521d3`, `2087f2d` — all present in `git log`
- No spillover into `tools/regenerate_tool_classification.py`, `.github/workflows/tool-classification-drift.yml`, `tools/apply_engine.py`, `canon/`, or `tools/profiles/`
- Live drift check exits 0 against real upstream
