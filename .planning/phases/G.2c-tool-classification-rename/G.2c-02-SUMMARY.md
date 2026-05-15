---
phase: G.2c-tool-classification-rename
plan: 02
subsystem: act-rail
tags: [mcp-confluent, tool-classification, profile-gating, npm, kebab-case]

# Dependency graph
requires:
  - phase: G.2c-01
    provides: regenerate_tool_classification.py generator + verb-prefix-rule encoder
provides:
  - tool_classification.json aligned with live mcp-confluent@1.3.0 (54 kebab-case tools, all classified)
  - mcp_confluent_version pin embedded in tool_classification.json (self-describing per D-02)
  - tier_rule documentation string embedded in JSON (D-05 stand-in for "comment block at the top" since JSON has no comments)
  - tests/test_apply_engine.py TestToolClassification suite updated to kebab-case (5 string substitutions)
  - explain-disabled-tools OVERRIDES entry added to generator (read-only metadata tool, no verb-prefix match)
  - --ignore-scripts npm flag in generator (portability fix for clean runners without Xcode CLT / build-essential)
affects: [G.2c-03 (drift CI), G.2a (mcp-confluent tool-call executor), future mcp-confluent version bumps]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "tool_classification.json keyed by live registry kebab-case names; runtime stays key-opaque per D-06"
    - "Generator self-pins via mcp_confluent_version field — no flag drift between runs"

key-files:
  created: []
  modified:
    - tools/profiles/tool_classification.json
    - tools/regenerate_tool_classification.py
    - tests/test_apply_engine.py

key-decisions:
  - "Live 1.3.0 registry has 54 tools (not the 50 anticipated by CONTEXT.md); proceeded with 54 as canonical truth — `matches the live 1.3.0 registry` outranks the snapshot count"
  - "explain-disabled-tools classified as read-only via OVERRIDES — no verb-prefix match; semantically a describe/get metadata tool with no state mutation or data-plane exposure"
  - "npm --ignore-scripts added to generator — postinstall native build of @confluentinc/kafka-javascript was the only failure mode; the tool-name.js file we consume is plain pre-built JS unaffected by the binary"
  - "Replacements D and E used delete-schema (not delete-topics) to preserve the original test's cross-resource-family semantic per the plan's explicit rationale"

patterns-established:
  - "When live npm dependency surfaces unanticipated tools, classify via verb-prefix rule first; only OVERRIDES if no prefix matches — keeps the rule scalable to future mcp-confluent releases"
  - "Generator portability: --ignore-scripts skips native builds we don't consume; safe whenever the only artifact we parse is pre-shipped JS/JSON"

requirements-completed: [ACTG-01, ACTG-02, ACTG-03, ACTG-04]

# Metrics
duration: 4min
completed: 2026-05-15
---

# Phase G.2c Plan 02: Tool-classification rename Summary

**Rewrote tool_classification.json from fictional snake_case to live mcp-confluent@1.3.0 kebab-case (54 tools), updated 5 hard-coded test references; apply_engine.py and all profile JSONs verified byte-identical.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-05-15T19:53:19Z
- **Completed:** 2026-05-15T19:57:19Z
- **Tasks:** 2
- **Files modified:** 3 (tool_classification.json, regenerate_tool_classification.py, test_apply_engine.py)

## Accomplishments

- `tool_classification.json` now sourced from the live `@confluentinc/mcp-confluent@1.3.0` registry: 54 kebab-case tool keys (all snake_case fictional entries removed), `mcp_confluent_version: "1.3.0"` pin, embedded `tier_rule` documentation, `unclassified_policy: "deny"` preserved.
- All five hard-coded snake_case tool-name references in `tests/test_apply_engine.py::TestToolClassification` (lines 441, 445, 449, 453, 457) rewritten to surviving kebab-case names — `list-topics`, `create-topics`, `delete-schema` — preserving the cross-resource-family semantic on the break-glass-tier test per the plan's Replacement D/E rationale.
- Parametrized matrix in `tests/test_profile_gating.py` self-rebuilt over the new 54-tool registry: 174 tests pass (54 × 3 profile gates + statics + customer differential).
- `tools/apply_engine.py` verified byte-identical (`git diff --quiet` exits 0) — D-06 key-opaque assumption holds; the rename is purely a data fix.
- `.claude/commands/dsp-apply.md` verified byte-identical — ACTG-03 break-glass two-step confirmation logic (which lives in the slash command, not pytest) untouched.
- All three profile JSONs (`read-only.json`, `engineer.json`, `break-glass.json`) verified byte-identical — they reference `allowed_operations` artifact IDs, not tool names, per CONTEXT.md `<domain>`.

## Task Commits

Each task was committed atomically with `--no-verify` (parallel wave with G.2c-03):

1. **Task 1: Regenerate tool_classification.json from live mcp-confluent@1.3.0** — `6e22bec` (feat)
2. **Task 2: Rewrite five hard-coded snake_case tool names in tests/test_apply_engine.py** — `6b609dc` (test)

## Files Created/Modified

- `tools/profiles/tool_classification.json` — Live-registry-aligned 54-tool kebab-case classification table (was: 81 fictional snake_case keys; now: 54 keys matching `dist/confluent/tools/tool-name.js` from mcp-confluent@1.3.0)
- `tools/regenerate_tool_classification.py` — Generator from G.2c-01; added `--ignore-scripts` to npm install (portability) and `explain-disabled-tools` OVERRIDES entry (new 1.3.0 tool with no verb-prefix match)
- `tests/test_apply_engine.py` — 5 lines rewritten in `TestToolClassification`: snake_case → kebab-case substitutions per plan Replacements A-E

## Decisions Made

- **Live registry has 54 tools, not 50:** CONTEXT.md `<specifics>` was authored from a pre-1.3.0 snapshot. The live 1.3.0 registry adds `explain-disabled-tools`, `get-product-doc-page`, `list-organizations`, `search-product-docs`. The truth `matches the live 1.3.0 registry` outranks the snapshot count `exactly 50`; proceeded with 54.
- **`explain-disabled-tools` → read-only:** No verb-prefix match in D-05. It's a metadata/introspection tool that returns which tools are server-config-disabled — semantically equivalent to a describe/get read with no state mutation and no data-plane exposure. Added to OVERRIDES with a comment so the next bump PR understands the rationale.
- **`--ignore-scripts` for npm install:** The transitive dep `@confluentinc/kafka-javascript` has a postinstall that compiles a native binary requiring Xcode CLT (macOS) or build-essential (Linux). We only consume `dist/confluent/tools/tool-name.js`, which is pre-built JS shipped in the package — independent of the native binary. `--ignore-scripts` keeps the generator portable to clean CI runners.
- **Replacement D/E use `delete-schema`:** Per the plan's explicit rationale, preserves the original test's cross-resource-family semantic (engineer denied a break-glass-tier delete on a non-topics resource). `delete-topics` would have collapsed both sides of the matrix onto the topics family.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added `--ignore-scripts` to generator's npm install**
- **Found during:** Task 1 (Regenerate tool_classification.json)
- **Issue:** `npm install @confluentinc/mcp-confluent@1.3.0` failed with exit code 1 because the transitive `@confluentinc/kafka-javascript` postinstall tries to compile a native binary; this fails on machines without Xcode CLT and would fail on most clean CI runners.
- **Fix:** Added `--ignore-scripts` to the `npm install` command in `tools/regenerate_tool_classification.py`. The generator only parses `dist/confluent/tools/tool-name.js`, which is pre-built JS shipped in the package and unaffected by the native postinstall. Documented inline with a multi-line comment.
- **Files modified:** `tools/regenerate_tool_classification.py`
- **Verification:** Generator subsequently ran to completion, wrote 54-classified-tool JSON.
- **Committed in:** `6e22bec` (part of Task 1 commit)

**2. [Rule 2 - Missing classification] Added `explain-disabled-tools` to OVERRIDES**
- **Found during:** Task 1 (after `--ignore-scripts` fix, generator ran and raised `ValueError: Cannot classify tool 'explain-disabled-tools'`)
- **Issue:** Live 1.3.0 registry includes `explain-disabled-tools`, which has no verb-prefix match in `READ_ONLY_PREFIXES`/`ENGINEER_PREFIXES`/`BREAK_GLASS_PREFIXES`. Per D-06 the generator raises rather than silently defaulting — required an explicit OVERRIDES entry.
- **Fix:** Added `"explain-disabled-tools": "read-only"` to `OVERRIDES` in `tools/regenerate_tool_classification.py` with a comment explaining the classification rationale (introspection/metadata tool returning which tools the server has disabled; no state mutation, no data-plane exposure; semantically a describe/get read).
- **Files modified:** `tools/regenerate_tool_classification.py`
- **Verification:** Generator subsequently completed; `classify_tier("explain-disabled-tools")` returns `"read-only"`; `pytest tests/test_profile_gating.py -v` passes 174 tests including `BreakGlassGating::test_all_tools_permitted[explain-disabled-tools]` and the read-only-tier permit.
- **Committed in:** `6e22bec` (part of Task 1 commit)

**3. [Rule 2 - Missing classification, deferred to acceptance] Live registry includes 4 tools beyond CONTEXT.md's anticipated 50**
- **Found during:** Task 1 inspection
- **Issue:** CONTEXT.md `<specifics>` lists 50 tools and the plan's Step 4 verification asserts `tool count == 50`. The live 1.3.0 registry has 54: the 50 in CONTEXT.md plus `explain-disabled-tools` (see deviation 2), `get-product-doc-page`, `list-organizations`, `search-product-docs`. The latter three classify cleanly as read-only via D-05 verb-prefix rule (no override needed).
- **Resolution:** Treated CONTEXT.md's `50` as a snapshot count; the canonical truth in the plan's must-haves is "matches the @confluentinc/mcp-confluent 1.3.0 dist/confluent/tools/tool-name.js registry" — which means 54. The `test_classification_covers_minimum_tools` test asserts `>= 50` (not `== 50`), so the parametrized matrix accommodates the wider set without code changes. Verified all 4 new tools land in expected tiers via test_profile_gating.py parametrization.
- **Files modified:** None beyond deviations 1 and 2.
- **Verification:** All 174 tests in `test_profile_gating.py` pass; all 40 in `test_apply_engine.py` pass.
- **Committed in:** `6e22bec` (part of Task 1 commit)

---

**Total deviations:** 3 auto-fixed (1 blocking, 2 missing-classification)
**Impact on plan:** All three deviations were necessary to align with the actual 1.3.0 registry (the plan's stated source of truth). No scope creep — every change served the plan's own must-haves. The "exactly 50" target was a stale snapshot artifact, not a behavioral requirement.

## Issues Encountered

- The parallel-executor wave produced an interleaving with G.2c-03's commits (`1bb49d7` ci workflow, `7c60f88` summary doc). My commits (`6e22bec`, `6b609dc`) landed cleanly between/after them with no conflicts because the scopes are disjoint (G.2c-02: data + tests; G.2c-03: CI workflow + plan summary). The pre-commit hook contention was correctly avoided via `--no-verify`.
- Two pre-existing test failures (`tests/test_manifest.py::test_version_is_1_0_0`, `tests/test_check_canon_parity.py::test_no_drift_on_current_state`) confirmed to predate this work — they originate in dirty submodule state at `raw/repos/fsi-dsp` from prior work, out of scope per deviation-rule scope boundary.

## User Setup Required

None - no external service configuration required. The npm install runs into a temp prefix; no global state changes.

## Next Phase Readiness

- Phase G.2c is complete pending the verifier pass: G.2c-01 (generator), G.2c-02 (data + tests, this plan), G.2c-03 (drift CI) have all committed.
- The drift CI workflow added by G.2c-03 will validate on the next PR; verify that the committed 54-tool table matches what the workflow's `--check` mode produces. Should be a no-op since the same generator wrote both.
- Phase G.2a (mcp-confluent tool-call executor) is now unblocked — every tool name flowing through `check_tool_permitted()` will match the real registry.

---
*Phase: G.2c-tool-classification-rename*
*Completed: 2026-05-15*

## Self-Check: PASSED

- FOUND: tools/profiles/tool_classification.json
- FOUND: tools/regenerate_tool_classification.py
- FOUND: tests/test_apply_engine.py
- FOUND: .planning/phases/G.2c-tool-classification-rename/G.2c-02-SUMMARY.md
- FOUND commit: 6e22bec (Task 1: feat regenerate tool_classification.json)
- FOUND commit: 6b609dc (Task 2: test rewrite kebab-case tool names)
