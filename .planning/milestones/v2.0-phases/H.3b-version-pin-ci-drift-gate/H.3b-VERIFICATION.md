---
phase: H.3b-version-pin-ci-drift-gate
verified: 2026-05-17T18:10:00Z
status: passed
score: 3/3 ROADMAP success criteria verified
requirements_completed: [INST-01]
---

# Phase H.3b: Version pin + CI drift gate — Verification Report

**Phase Goal:** Pin `streaming-skills-plugin` version + author CI drift gate. Mirrors v1.0 Phase G.2c pattern byte-for-byte where structurally possible. Closes INST-01 (H.3a was install; H.3b adds the pin and CI gate).

**Verified:** 2026-05-17 (autonomous execution self-check)
**Status:** passed
**Executor Self-Check:** PASSED

## Goal Achievement

| # | ROADMAP Success Criterion | Status | Evidence |
|---|---------------------------|--------|----------|
| 1 | `tools/vendor-sources.json` contains pinned `streaming-skills-plugin` version + commit | VERIFIED | New entry with `commit: 91d1871ef8c320be92bca955c8e42492a2778cb4`, `version: 1.0.0`, `kind: claude-plugin`; existing `confluent-agent-skills` entry unchanged |
| 2 | `.github/workflows/streaming-skills-drift.yml` exists; fails on PR when upstream plugin's commit differs from pinned without matching update | VERIFIED | Valid YAML; pull_request + push:main triggers; path-scoped to pin file + script + workflow itself; calls `python tools/check_streaming_skills_drift.py --check` |
| 3 | Drift-gate generator has `--check` mode that exits non-zero on drift (mirrors G.2c pattern) | VERIFIED | `tools/check_streaming_skills_drift.py` exit codes: 0=no drift, 1=drift, 2=config error, 3=transient/git error; CLI mirrors `tools/regenerate_tool_classification.py` shape |

**Score:** 3/3 verified

## Requirements

| ID | Status | Evidence |
|----|--------|----------|
| INST-01 | Complete (H.3a + H.3b) | Install (H.3a) + pin (H.3b) + CI drift gate (H.3b); bidirectional drift detection across both vendor entries |

## Live Drift Check

- `python3 tools/check_streaming_skills_drift.py --check` → exit 0 (pin matches live HEAD at execution time)
- Pinned commit: `91d1871ef8c320be92bca955c8e42492a2778cb4`

## Test Results

- `pytest tests/test_check_streaming_skills_drift.py -v`: 9/9 PASS
- `pytest tests/`: 951 PASS, 2 pre-existing failures persist (test_check_canon_parity, test_manifest)

## Gaps / Tech Debt

**Critical gaps:** None.

**Tech debt / deferred:**
- 2 pre-existing failures persist (same as H.4 sub-phases)
- Auto-bump-PR generator (Renovate-like) — not blocking
- Per-skill drift (finer than commit-pin) — defer
- Combined vendor-drift workflow (merge with tool-classification-drift) — premature

## Vendor-Pin Discipline Now Uniform

- `confluent-agent-skills` (kind: wiki-source) — H.1 vendored at SHA 91d1871e, drift detection via `tools/wiki-lint.py check_vendor_drift` (passive, non-fatal per H.1-03 D-09)
- `streaming-skills-plugin` (kind: claude-plugin) — H.3a installed at SHA 91d1871e, drift detection via H.3b new CI gate (active, blocks PR)

Both pinned in `tools/vendor-sources.json`.

## See Also

- `H.3b-01-SUMMARY.md` — Full execution record (5 commits, 9/9 new tests, no deviations)
- `H.3b-CONTEXT.md` — Decisions D-01 through D-09
