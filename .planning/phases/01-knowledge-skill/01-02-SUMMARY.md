---
phase: 01-knowledge-skill
plan: 02
subsystem: knowledge-skill
tags: [ask, recommend, triage-classifier, auto-stub, mode-routing]
dependency_graph:
  requires: []
  provides: [unified-ask-skill, thin-recommend-alias, auto-stub-queue-section]
  affects: [.claude/commands/ask.md, .claude/commands/wiki/recommend.md, wiki/_queue.md]
tech_stack:
  added: []
  patterns: [mode-routing, triage-classifier, auto-stub-dedup, decay-check]
key_files:
  created: []
  modified:
    - .claude/commands/ask.md
    - .claude/commands/wiki/recommend.md
    - wiki/_queue.md
decisions:
  - "Triage classifier uses four routes (wiki-only/wiki+MCP/deep/refuse) with explicit heuristics; --force-route bypasses it"
  - "Mode flag (ephemeral/report/reconsolidate) governs write behavior only — MCP routing is route-driven, not mode-driven"
  - "Auto-stub fires on ALL modes including ephemeral — coverage gaps are never lost"
  - "/wiki:recommend reduced to thin alias to eliminate duplicate logic; all knowledge flow goes through /ask"
metrics:
  duration: 109s
  completed_date: "2026-04-28"
  tasks_completed: 2
  files_modified: 3
---

# Phase 01 Plan 02: Unified /ask Skill with Mode Routing, Triage Classifier, and Auto-Stub Summary

**One-liner:** Consolidated /ask + /wiki:recommend into a unified skill with --mode flag (ephemeral/report/reconsolidate), Step 1.5 triage classifier (wiki-only/wiki+MCP/deep/refuse), decay check on article reads, and auto-stub coverage gap tracking in _queue.md.

## What Was Built

Three artifacts were modified to unify the knowledge skill layer:

**`.claude/commands/ask.md`** — Rewritten from a 5-step read-only query handler to a 6-step unified skill:
- Step 1: Parse `--mode` and `--force-route` flags from `$ARGUMENTS`
- Step 1.5: Triage classifier routes queries to wiki-only, wiki+MCP, deep, or refuse based on wiki hit count and query phrasing
- Step 2: Wiki search extended with decay check (WIKI-04) and auto-stub logic (WIKI-05)
- Step 3-4: Canon application and MCP validation unchanged; Step 4 skipped for wiki-only route
- Step 5: Mode-conditional output — ephemeral writes nothing, report saves to `outputs/reports/`, reconsolidate does report + wiki writeback

**`.claude/commands/wiki/recommend.md`** — Replaced 7-step full workflow with a 9-line alias that dispatches to `/ask --mode reconsolidate`. All logic lives in ask.md; recommend.md is now a thin indirection layer.

**`wiki/_queue.md`** — Added `## Auto-Stubs` section after `## Candidate Articles` with dedup comment format using `<!-- auto-stub: <slug> -->` markers.

## Deviations from Plan

None — plan executed exactly as written.

The pre-existing test failure in `tests/test_wiki_decay.py` (`AttributeError: module 'wiki_lint' has no attribute 'check_decay'`) was present before this plan's execution and is not caused by these changes. 57 other tests pass. This is logged as a deferred item from a prior phase.

## Known Stubs

None. All three modified files contain complete, wired functionality:
- ask.md has full mode routing and classifier logic
- recommend.md dispatches to ask.md correctly
- _queue.md Auto-Stubs section is empty by design (populated at runtime by /ask on wiki misses)

## Decisions Made

1. **Mode vs route separation:** Mode flag governs write behavior only. MCP routing is determined by the triage classifier (route), not the mode. This means `--mode ephemeral` can still call MCP if the classifier says wiki+MCP — ephemeral just means no file writes.

2. **Auto-stub fires on all modes:** Even ephemeral queries trigger the auto-stub append if wiki returns zero results. Coverage gaps are always tracked regardless of whether the user wants a persistent report.

3. **Thin alias pattern for recommend.md:** Rather than maintaining two parallel implementations, /wiki:recommend is now a 9-line dispatch alias. This eliminates drift between the two skills and ensures all enhancements to /ask flow automatically to /wiki:recommend.

4. **--force-route bypass:** The triage classifier is advisory. `--force-route wiki|mcp|deep` lets users override routing when the classifier's heuristics don't match their intent.

## Self-Check: PASSED

Files created/modified:
- `.claude/commands/ask.md` — FOUND (modified, 113 lines)
- `.claude/commands/wiki/recommend.md` — FOUND (modified, 9 lines)
- `wiki/_queue.md` — FOUND (modified, Auto-Stubs section appended)

Commits:
- `292abe4` — feat(01-02): rewrite ask.md with mode routing, triage classifier, and auto-stub
- `826b0bb` — feat(01-02): convert recommend.md to thin alias and add Auto-Stubs to _queue.md
