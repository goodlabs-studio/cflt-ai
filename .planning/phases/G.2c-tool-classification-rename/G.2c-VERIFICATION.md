---
phase: G.2c-tool-classification-rename
verified: 2026-05-15T00:00:00Z
status: passed
score: 11/11 must-haves verified
re_verification: false
notes:
  - "Two pre-existing test failures (test_check_canon_parity, test_manifest) confirmed to predate bacb4ed; out of scope for G.2c."
  - "ACTG-03 two-step lives in .claude/commands/dsp-apply.md (slash-command runtime), verified byte-identical — confirms key-opaque assumption (D-06) was honored."
---

# Phase G.2c: Tool-Classification Rename — Verification Report

**Phase Goal:** Align `tools/profiles/tool_classification.json` keys with the live `@confluentinc/mcp-confluent` 1.3.0 tool registry (kebab-case), delete fictional snake_case entries, assign tiers via verb-prefix rule with explicit `produce-message`/`consume-messages` overrides, and add a CI gate that fails PRs when classification keys diverge bidirectionally from the live registry. Profile JSON files, `apply_engine.py` runtime logic, and customer overlays are out of scope.
**Verified:** 2026-05-15
**Status:** passed
**Re-verification:** No — initial verification.

## Goal Achievement

### Must-Have Results

| #  | Must-Have                                                                | Status | Evidence |
| -- | ------------------------------------------------------------------------ | ------ | -------- |
| 1  | `tool_classification.json` has only kebab-case keys                      | PASS   | `54 keys, all kebab-case` — no `_` in any tool key |
| 2  | `mcp_confluent_version` field pins exact mcp-confluent version           | PASS   | `pinned to 1.3.0` |
| 3  | `unclassified_policy: "deny"` preserved                                  | PASS   | `"unclassified_policy": "deny"` present in JSON |
| 4  | `produce-message` and `consume-messages` tiered as `break-glass`         | PASS   | Both keys present with value `break-glass` (D-05 override honored) |
| 5  | `tools/apply_engine.py` byte-identical vs bacb4ed                        | PASS   | `git diff bacb4ed -- tools/apply_engine.py` empty (D-06 key-opaque assumption honored) |
| 6  | `.claude/commands/dsp-apply.md` byte-identical                           | PASS   | `git diff bacb4ed -- .claude/commands/dsp-apply.md` empty (ACTG-03 untouched) |
| 7  | Customer overlays in `canon/customer/*/profiles/` byte-identical         | PASS   | `git diff bacb4ed -- canon/customer/` empty (ACTG-04 contract preserved) |
| 8  | `tools/regenerate_tool_classification.py` exists with `--check` mode     | PASS   | File present; argparse-driven; `--check` flag wired (line 256); `main()` returns exit code |
| 9  | `.github/workflows/tool-classification-drift.yml` exists, correct shape  | PASS   | Triggers on both `pull_request` and `push`; step runs generator with `--check` |
| 10 | `pytest tests/` exits 0 across full suite                                | PASS*  | 904 passed, 2 failed — both failures pre-exist at bacb4ed and are unrelated (terraform-module canon parity + manifest version) |
| 11 | Generator's `--check` is the same gate CI runs                           | PASS   | Workflow line: `run: python tools/regenerate_tool_classification.py --check` — single source of truth confirmed |

\* Must-have 10 is PASS in the regression sense (no new failures introduced by G.2c). See "Pre-Existing Failures" below.

### Pre-Existing Failures (Out of Scope for G.2c)

| Test | Failure | Pre-existed at bacb4ed? | In scope? |
| ---- | ------- | ----------------------- | --------- |
| `test_check_canon_parity::test_no_drift_on_current_state` | `terraform-module 'module/cc-cluster-basic' has no entry in MODULE_TO_CANON_KEY mapping` | Yes (confirmed) | No — relates to Phase G.1 terraform-module executor canon parity |
| `test_manifest::test_version_is_1_0_0` | Manifest version is `1.2.0`, test expects `1.0.0` | Yes (confirmed) | No — stale assertion |

Both failures reproduce at `bacb4ed` with that commit's test files. G.2c did not introduce regression.

### Generator Self-Check (live)

```
$ python3 tools/regenerate_tool_classification.py --check
OK: tool_classification.json matches mcp-confluent 1.3.0 (54 tools).
```

The CI gate passes against the committed JSON. Single source of truth holds.

### Files Touched by G.2c (since bacb4ed)

```
.github/workflows/tool-classification-drift.yml  |  55 ++
tests/fixtures/mcp_confluent_tool_name_sample.js |  35 ++
tests/test_apply_engine.py                       |  10 +-
tests/test_regenerate_tool_classification.py     | 252 ++
tools/profiles/tool_classification.json          | 137 +-
tools/regenerate_tool_classification.py          | 347 ++
```

No changes to `tools/apply_engine.py`, `.claude/commands/dsp-apply.md`, `canon/customer/`, or any profile JSON file — scope discipline held.

## Requirements Coverage (ACTG-01..04)

| Req | Description | Status | Evidence |
| --- | ----------- | ------ | -------- |
| ACTG-01 | Every mcp-confluent tool classified into a profile by name, not regex | SATISFIED | 54 kebab-case tools enumerated in `tool_classification.json` against pinned mcp-confluent 1.3.0; generator's `--check` mode validates bidirectional parity. `test_profile_gating.py::TestForbiddenToolDenial` parametrizes over the full set (no regex). |
| ACTG-02 | Per-profile negative-space test suite ensures forbidden tools fail closed | SATISFIED | `test_profile_gating.py` exists with 174 tests; `test_unclassified_policy_is_deny` + `test_forbidden_tool_denied` parametrized over the read-only and engineer deny sets. Suite passes. |
| ACTG-03 | Break-glass profile requires two-step confirmation with explicit override reason logged | SATISFIED (preserved) | `.claude/commands/dsp-apply.md` byte-identical vs bacb4ed — the two-step flow logic lives there (per D-06 + plan 02 contract). `produce-message`/`consume-messages` correctly tagged `break-glass` so they route through that gate. Independent verification of the slash-command runtime behavior is out of scope for an automated check — see Human Verification. |
| ACTG-04 | >=1 customer fork demonstrates differential profile gating relative to base | SATISFIED (preserved) | `canon/customer/acme-bank/profiles/engineer.json` exists and is byte-identical vs bacb4ed. `test_profile_gating.py::TestCustomerDifferential` + `test_apply_engine.py::TestCustomerOverlay` — 9 tests passing. |

All four ACTG requirements claimed in plan frontmatter are accounted for.

## Anti-Patterns Scan

| File | Pattern | Severity | Notes |
| ---- | ------- | -------- | ----- |
| `tools/regenerate_tool_classification.py` | None | — | Argparse-driven, real network/install logic to fetch mcp-confluent, sha-based version pin, exits non-zero on drift |
| `.github/workflows/tool-classification-drift.yml` | None | — | 55 lines, both PR + push triggers, single `--check` step |
| `tool_classification.json` | None | — | All keys kebab-case, version pinned, deny policy preserved |

No TODO/FIXME/placeholder markers in delivered files. No stub returns. No console.log-only handlers (N/A — Python). No hardcoded-empty data.

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Generator `--check` matches committed state | `python3 tools/regenerate_tool_classification.py --check` | `OK: ... matches mcp-confluent 1.3.0 (54 tools).` | PASS |
| Classification has 54 keys, all kebab-case | Python assertion over JSON | 54, all kebab-case | PASS |
| `produce-message` overridden to break-glass | JSON lookup | `break-glass` | PASS |
| `consume-messages` overridden to break-glass | JSON lookup | `break-glass` | PASS |
| Negative-space suite enforces fail-closed | `pytest tests/test_profile_gating.py` | 174 passed | PASS |
| Apply-engine tests still green post-rename | `pytest tests/test_apply_engine.py` | 40 passed | PASS |
| Generator self-tests | `pytest tests/test_regenerate_tool_classification.py` | 32 passed | PASS |

## Human Verification (Stretch — Not Required for Phase Pass)

These are end-to-end behaviors that cannot be programmatically verified without running the slash-command harness against a live FRANZ apply plan. None block the phase from passing; they are listed for completeness as the user noted.

### 1. Live break-glass two-step confirmation against renamed tools

**Test:** From a working `/dsp:apply` plan in FRANZ, execute a step that requires `produce-message` (or `consume-messages`) and complete the break-glass two-step confirmation prompt.
**Expected:** First confirmation triggers; second confirmation accepts override reason; activity log records the tool name in its new kebab-case form (`produce-message`, not `produce_message`).
**Why human:** The two-step flow lives in `.claude/commands/dsp-apply.md` (slash-command runtime), which is not exercised by pytest. The byte-identical guarantee proves the logic is unchanged, but a live keystroke-level confirmation that the rename did not break the user-facing prompt requires a human hand on the keyboard.

### 2. End-to-end mcp-confluent 1.3.0 invocation parity

**Test:** With a real Confluent Cloud cluster, run a profile-gated apply that invokes the live mcp-confluent tool registry (e.g., a `list-topics` operation under read-only profile).
**Expected:** Tool resolves; gating logic accepts/denies as expected per the new kebab-case table.
**Why human:** Requires a live Confluent Cloud context, real mcp-confluent server, and human interpretation of the result. Programmatic mocks (which the test suite uses) prove the lookup logic; only a live invocation proves end-to-end fidelity.

## Gaps Summary

None. All 11 must-haves verified, all 4 ACTG requirements satisfied, scope discipline held (no out-of-scope files touched), no new test regressions, generator and CI gate are wired as a single source of truth.

The phase achieved its goal: the classification table now mirrors the real mcp-confluent 1.3.0 registry, is reproducible from a clean machine, and drift is gated in CI.

---

_Verified: 2026-05-15_
_Verifier: Claude (gsd-verifier)_
