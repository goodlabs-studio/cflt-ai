---
phase: G.2c-tool-classification-rename
plan: "01"
subsystem: testing
tags: [python, pytest, mcp-confluent, classification, tdd, regex, npm]

requires:
  - phase: 03C-act-rail-profile-gating
    provides: "tool_classification.json shape (version/tools/unclassified_policy), check_tool_permitted() runtime contract, parametrized test pattern over classification keys"
provides:
  - "tools/regenerate_tool_classification.py: dual-mode generator (default regenerate / --check drift / --dry-run offline) — single source of truth for tool_classification.json"
  - "D-05 verb-prefix rule encoded as Python tables (READ_ONLY_PREFIXES, ENGINEER_PREFIXES, BREAK_GLASS_PREFIXES) + OVERRIDES dict for produce-message and consume-messages"
  - "Bidirectional drift detection (D-08) — diff_classification() returns (missing_from_committed, extra_in_committed)"
  - "Static fixture tests/fixtures/mcp_confluent_tool_name_sample.js covering every verb branch + both overrides (16 tools, offline-runnable)"
  - "32 parametrized parser/classifier/builder/diff unit tests — all GREEN, run in <0.1s without network or npm"
affects: [G.2c-02-tool-classification-rewrite, G.2c-03-ci-drift-gate, G.2a-tool-call-executor]

tech-stack:
  added:
    - "argparse-based CLI with three operating modes"
    - "subprocess + tempfile.TemporaryDirectory for hermetic npm-install"
    - "regex parser tolerant of double/single quotes and whitespace"
  patterns:
    - "Generator-as-source-of-truth: JSON file is downstream artifact of code, not hand-edited"
    - "Pin-in-data: mcp_confluent_version lives in tool_classification.json so the file is self-describing (D-02)"
    - "JSON-comment workaround: tier_rule top-level string field stands in for D-05's 'comment block' (JSON has no comments)"
    - "Fail-loud-on-unknown-shape: classify_tier() raises ValueError per D-06 so CI blocks bump PRs until a human classifies new tools"

key-files:
  created:
    - "tools/regenerate_tool_classification.py"
    - "tests/test_regenerate_tool_classification.py"
    - "tests/fixtures/mcp_confluent_tool_name_sample.js"
  modified: []

key-decisions:
  - "--dry-run mode added under D-05 Claude's Discretion: enables unit tests to exercise parser/classifier chain offline against a static fixture without npm or network"
  - "tier_rule stored as top-level JSON string (D-05 specifies a 'comment block'; JSON has no comments — the field preserves human-readable intent visible on file open)"
  - "OVERRIDES checked before verb-prefix tables so produce-message/consume-messages cleanly bypass the rule rather than being post-corrected"
  - "Regex anchored on ToolName[...] = '...' with explicit uppercase-snake key shape and kebab-case value shape — narrow enough to ignore stray strings, tolerant enough to accept both quote styles tsc emits"
  - "tool_classification.json deliberately left untouched in this plan — the big-bang rewrite is G.2c-02's responsibility, keeping that diff small and reviewable"

patterns-established:
  - "Hermetic npm-install: subprocess invokes 'npm install --prefix <tempdir> --no-save --silent --no-fund --no-audit ...' so the script never depends on per-machine ~/.npm/_npx caches"
  - "Bidirectional drift contract: diff_classification returns (missing, extra) so the CI gate in G.2c-03 can render both sides of upstream change"
  - "Parametrized verb-prefix coverage: pytest.mark.parametrize over each verb in each tier prevents silent prefix drift"

requirements-completed: [ACTG-01]

duration: 3min
completed: 2026-05-15
---

# Phase G.2c Plan 01: Tool-classification rename — Generator + Tests Summary

**Dual-mode (regenerate / --check / --dry-run) Python generator + 32 unit tests that make `tool_classification.json` a reproducible, machine-verifiable artifact derived from a pinned `@confluentinc/mcp-confluent` package — without touching the JSON file itself.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-05-15T19:47:23Z
- **Completed:** 2026-05-15T19:50:19Z
- **Tasks:** 2 (TDD: RED scaffold + GREEN implementation)
- **Files created:** 3
- **Files modified:** 0 (apply_engine.py and tool_classification.json deliberately untouched)

## Accomplishments

- Generator script encodes D-05's verb-prefix rule as three Python tuples + an OVERRIDES dict — no regex in the classifier, so the policy is reviewable as code, not as data.
- Bidirectional drift checker (D-08) ready for the G.2c-03 CI workflow: returns both missing-from-committed and extra-in-committed so upstream removals are caught just as loudly as upstream additions.
- Static fixture covers all 14 verb prefixes plus both overrides in 16 tool entries — small enough to be hand-read in a PR, comprehensive enough that any verb-shape regression in mcp-confluent surfaces here first.
- `--dry-run` mode lets unit tests run offline in 0.04 seconds; CI doesn't need npm, the network, or Confluent Cloud credentials to validate the parser/classifier.
- ACTG-01 requirement (every tool classified by exact name) is now a property the generator enforces by construction — `unclassified_policy: "deny"` stays, but the live registry can no longer drift away from the committed JSON unobserved.

## Task Commits

Each task was committed atomically (TDD discipline — RED before GREEN):

1. **Task 1 (RED): Static fixture + failing unit tests** — `572a6b9` (test)
2. **Task 2 (GREEN): regenerate_tool_classification.py implementation** — `1a3837d` (feat)

**Plan metadata:** (final docs commit follows this SUMMARY) — `docs(G.2c-01): complete tool-classification-rename plan 01`

## Files Created/Modified

- `tools/regenerate_tool_classification.py` (333 LOC) — Dual-mode CLI: default regenerate, `--check` drift, `--dry-run` offline. Exports `parse_tool_name_js`, `classify_tier`, `build_classification`, `diff_classification` for direct import by tests and future tooling.
- `tests/test_regenerate_tool_classification.py` (252 LOC) — 32 parametrized tests covering parser quote styles, every verb-prefix branch, both explicit overrides, unknown-prefix ValueError contract, top-level JSON shape, sort order, version threading, and bidirectional diff cases.
- `tests/fixtures/mcp_confluent_tool_name_sample.js` (35 LOC) — Hand-crafted 16-tool excerpt mimicking the real `dist/confluent/tools/tool-name.js` shape. Static and intentional — never regenerated from npm so tests stay deterministic.

## Decisions Made

- **`--dry-run` mode is planner discretion under D-05.** Locked spec only mandates default-regenerate and `--check`. The dry-run path is necessary so unit tests can exercise the parse/classify/build chain offline; without it the GREEN test suite would require npm in CI for what is fundamentally pure-Python logic. Documented inline in the script docstring.
- **`tier_rule` as a JSON string field.** D-05 says "comment block at the top of tool_classification.json" — JSON has no comment syntax. The top-level `tier_rule` string preserves the semantic intent (rule visible to humans opening the file) without forking to JSON5 or stripping comments at load time.
- **OVERRIDES checked first.** Putting `if tool_name in OVERRIDES: return OVERRIDES[tool_name]` ahead of the prefix tables means produce-message/consume-messages take a clean fast path. The alternative — classify-then-post-correct — would obscure that these are explicit policy decisions, not edge-case fixups.
- **`tool_classification.json` left unchanged.** The plan's success criteria require `git diff --quiet tools/profiles/tool_classification.json` to exit 0. The big-bang rewrite is G.2c-02's responsibility; keeping that diff in a separate PR makes the rewrite reviewable side-by-side with the deletions of fictional snake_case entries.
- **Regex narrow enough to drop noise, tolerant enough to accept both quote styles.** `ToolName\s*\[\s*["']([A-Z][A-Z0-9_]*)["']\s*\]\s*=\s*["']([a-z][a-z0-9\-]*)["']` — uppercase-snake key shape and kebab-case value shape are explicit so the parser ignores stray template literals or comment fragments, but `["']` covers both quote forms tsc emits depending on configuration.

## Deviations from Plan

None — plan executed exactly as written. No bugs surfaced, no auto-fixes required, no checkpoint stops. The two TDD tasks both passed verification on first attempt:

- Task 1 RED: `pytest` failed with `ModuleNotFoundError: No module named 'tools.regenerate_tool_classification'` — the expected failure mode.
- Task 2 GREEN: All 32 tests pass; `--dry-run` end-to-end assertions all pass; `tool_classification.json` and `apply_engine.py` both unchanged from `HEAD~2`.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration. The generator's default (npm-install) mode requires Node.js on PATH at the time it's invoked in G.2c-02 and G.2c-03, but that is downstream of this plan.

## Next Phase Readiness

- **G.2c-02 (big-bang rewrite):** Run `python tools/regenerate_tool_classification.py --version 1.3.0` to overwrite `tool_classification.json` with the live 1.3.0 registry's 50 kebab-case tools. Then regenerate the hard-coded snake_case assertions in `tests/test_profile_gating.py` to match (per D-04). The generator is ready and the bidirectional-diff function exposes exactly what the new JSON must look like.
- **G.2c-03 (CI drift gate):** Add a GitHub Actions workflow that runs `python tools/regenerate_tool_classification.py --check` on PR + push-to-main. Exit code is already the only signal CI needs (0 = clean, 1 = drift); stderr already prints both directions of drift with regeneration instructions.
- **No blockers, no concerns.** The generator is fully self-contained, has no runtime dependencies beyond Python 3.9 stdlib (plus npm when not in --dry-run mode), and preserves the `load_tool_classification()` contract that `apply_engine.check_tool_permitted()` depends on.

## Self-Check: PASSED

- Files exist: tools/regenerate_tool_classification.py, tests/test_regenerate_tool_classification.py, tests/fixtures/mcp_confluent_tool_name_sample.js — all FOUND.
- Commits exist: 572a6b9, 1a3837d — both FOUND in `git log --oneline --all`.
- Untouched-file guarantees: `git diff --quiet tools/profiles/tool_classification.json` exits 0; `git diff --quiet tools/apply_engine.py` exits 0.

---
*Phase: G.2c-tool-classification-rename*
*Completed: 2026-05-15*
