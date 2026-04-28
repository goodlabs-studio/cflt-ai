---
phase: 00-foundation
plan: "01"
subsystem: wiki-tooling
tags: [bug-fix, test-scaffold, wiki, hygiene]
dependency_graph:
  requires: []
  provides: [wiki-stats-clean, wiki-lint-anchor-aware, evaluate-full-paths, test-scaffold]
  affects: [wiki-tooling, ci]
tech_stack:
  added: [pytest]
  patterns: [regression-test-per-bugfix]
key_files:
  created:
    - tests/__init__.py
    - tests/conftest.py
    - tests/test_wiki_tools.py
  modified:
    - tools/wiki-stats.py
    - tools/wiki-lint.py
    - .claude/commands/wiki/evaluate.md
decisions:
  - "pytest chosen as test runner; already available in Flox venv via pip"
  - "Tests assert both source-level fix presence and runtime behavior (subprocess + regex import)"
metrics:
  duration: "~8 minutes"
  completed: "2026-04-28"
  tasks_completed: 2
  files_changed: 6
---

# Phase 00 Plan 01: Wiki Tooling Hygiene Fixes Summary

**One-liner:** Fixed three Python tool bugs (Unicode f-string crash, broken-link regex anchor handling, evaluate.md ellipsis paths) and built a pytest scaffold proving all fixes hold.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create test scaffold and regression tests | 23a88ef | tests/__init__.py, tests/conftest.py, tests/test_wiki_tools.py |
| 2 | Fix wiki-stats.py, wiki-lint.py, evaluate.md bugs | 98f2f12 | tools/wiki-stats.py, tools/wiki-lint.py, .claude/commands/wiki/evaluate.md |

## What Was Built

### HYG-01: wiki-stats.py Unicode syntax error (lines 57, 59, 75)
The three `print(f"\n{─*50}")` calls used U+2500 BOX DRAWINGS LIGHT HORIZONTAL as the repeated character — a valid-looking Unicode codepoint that Python rejects as a SyntaxError at runtime because `─` is not a valid Python identifier. Fixed by replacing with `'-' * 50` (ASCII hyphen string multiplication).

### HYG-02: wiki-lint.py broken-link regex
`re.findall(r"\[.*?\]\((wiki/[^)]+)\)", content)` matched the fragment identifier (`#section`) as part of the file path, causing valid links like `wiki/foo.md#anchor` to fail the path-exists check. Fixed by splitting the capture group: `(wiki/[^)#]+(?:#[^)]*)?)`  — base path captured without `#`, optional anchor appended separately.

### HYG-03: evaluate.md ellipsis paths
Two reference paths used `...` shorthand which Claude Code cannot resolve for `Read` tool calls:
- Before: `raw/repos/fsi-dsp/reference/java-producer/.../FsiProducer.java`
- After: `raw/repos/fsi-dsp/reference/java-producer/src/main/java/org/fsi/kafka/producer/FsiProducer.java`

Same fix applied to FsiConsumer.java.

### HYG-04: Flox environment
`manifest.toml` confirmed present and contains `pyyaml` in the `on-activate` pip install list. No changes needed.

### Test Scaffold (tests/)
7 regression tests covering all four hygiene items:
- `test_wiki_stats_no_syntax_error` — subprocess run, exit 0, "Articles:" in stdout
- `test_wiki_stats_no_unicode_box_drawing` — source-level assertion no U+2500
- `test_wiki_lint_anchor_regex` — regex behavior with plain, anchored, and external links
- `test_wiki_lint_source_has_anchor_regex` — source contains `(?:#[^)]*)?)`
- `test_evaluate_no_ellipsis_paths` — no `...` on fsi-dsp reference lines; full paths present
- `test_flox_manifest_exists` — `.flox/env/manifest.toml` on disk
- `test_flox_manifest_has_pyyaml_deps` — manifest contains `pyyaml`

All 7 tests pass green.

## Verification Results

```
python3 tools/wiki-stats.py   → exit 0, prints "Articles: 19"
python3 tools/wiki-lint.py    → exit 0, reports 1 unverified claim (expected, not a crash)
python3 -m pytest tests/test_wiki_tools.py -x -v → 7 passed in 0.06s
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

- tests/__init__.py: FOUND
- tests/conftest.py: FOUND
- tests/test_wiki_tools.py: FOUND
- tools/wiki-stats.py (fixed): FOUND
- tools/wiki-lint.py (fixed): FOUND
- .claude/commands/wiki/evaluate.md (fixed): FOUND
- Commit 23a88ef: FOUND
- Commit 98f2f12: FOUND
