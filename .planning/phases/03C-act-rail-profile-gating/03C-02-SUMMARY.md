---
phase: 03C-act-rail-profile-gating
plan: "02"
subsystem: profile-gating
tags: [tool-classification, break-glass, override-logging, customer-overlay, dsp-apply]
dependency_graph:
  requires: [03C-01]
  provides: [check_tool_permitted, load_tool_classification, customer-overlay-load_profile, override_reason-logging, dsp-apply-break-glass-two-step]
  affects: [tools/apply_engine.py, .claude/commands/dsp-apply.md, tests/test_apply_engine.py]
tech_stack:
  added: []
  patterns: [tier-hierarchy-check, keyword-only-customer-param, dual-override-logging, two-step-break-glass-confirmation]
key_files:
  created: []
  modified:
    - tools/apply_engine.py
    - .claude/commands/dsp-apply.md
    - tests/test_apply_engine.py
decisions:
  - "check_tool_permitted() is a parallel function to check_profile_permits() — separate namespaces: MCP tool names vs fsi-dsp artifact IDs"
  - "customer param on load_profile() is keyword-only (*, customer) per RESEARCH.md Pitfall 2 — existing positional callers unaffected"
  - "override_reason uses Optional[str] = None default — backward compatible; None means omit the field from log/frontmatter"
  - "Break-glass two-step added as Step 6 Break-Glass Extension subsection — existing standard Step 6 flow preserved for other profiles"
metrics:
  duration: "~3 minutes"
  completed: "2026-04-29"
  tasks_completed: 2
  files_created: 0
  files_modified: 3
---

# Phase 03C Plan 02: Apply Engine Classification and Break-Glass Logging Summary

**One-liner:** apply_engine.py extended with classification-table-aware tool checking, customer overlay profile loading, and dual override_reason logging; dsp-apply.md updated with two-step break-glass confirmation flow.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Extend apply_engine.py with tool classification, customer overlay, and dual override logging | 6680683 | tools/apply_engine.py, tests/test_apply_engine.py |
| 2 | Update dsp-apply.md with two-step break-glass confirmation | a7d43f6 | .claude/commands/dsp-apply.md |

## What Was Built

**`tools/apply_engine.py` — tool classification and override logging extensions:**

- `PROFILE_TIER_ORDER = ["read-only", "engineer", "break-glass"]` — tier index for hierarchy comparison.
- `load_tool_classification()` — loads `tool_classification.json` with caching; returns dict with `tools` and `unclassified_policy`.
- `check_tool_permitted(profile_name, tool_name, customer=None)` — fail-closed MCP tool check using classification table. Unclassified tools return False. Tier check: `PROFILE_TIER_ORDER.index(profile) >= PROFILE_TIER_ORDER.index(required_tier)`.
- `load_profile(profile_name, *, customer=None)` — keyword-only `customer` param added. Checks `canon/customer/<name>/profiles/<profile>.json` first; falls back to base profile. All existing positional callers unaffected.
- `emit_activity_log_apply()` — `override_reason: Optional[str] = None` added. When not None, appends `**Override reason:** {override_reason}` line to activity log entry.
- `write_incident_article()` — `override_reason: Optional[str] = None` added. When not None, appends `override_reason: {value}` to YAML frontmatter and `Override reason: {value}` to Why section.

**`tests/test_apply_engine.py` — three new test classes (13 new tests, 40 total):**

- `TestToolClassification` — 7 tests covering: load_tool_classification() structure, read-only/engineer/break-glass tier matrix for specific tools, unclassified tool fail-closed.
- `TestCustomerOverlay` — 4 tests covering: acme-bank missing module/flink, acme-bank has role/cp_audit, nonexistent customer falls back to base, no-customer backward compat.
- `TestOverrideReasonLogging` — 2 tests covering: activity log contains override_reason text, incident article frontmatter contains `override_reason:` key.

**`.claude/commands/dsp-apply.md` — two-step break-glass confirmation:**

- New `### Step 6 Break-Glass Extension (when --profile break-glass)` subsection with Interaction 1 (reason collection) and Interaction 2 (full confirmation display).
- Empty/declined reason → `break-glass-reason-rejected` result, no proceed.
- BREAK-GLASS CONFIRMATION REQUIRED display block with artifact, profile, override reason, operator, and gate results.
- `CONFIRM BREAK-GLASS` option; cancel → `break-glass-cancelled`.
- Explicit dual logging requirement (ACTG-03) documented in Step 6 extension.
- Step 7 updated: stale "Phase 3c will classify" comment replaced with `check_tool_permitted()` and `tool_classification.json` reference.
- Steps 8 and 9 updated: `override_reason` parameter documented as break-glass-only field.

## Deviations from Plan

None — plan executed exactly as written.

## Verification Results

All plan verification commands passed:
- `pytest tests/test_apply_engine.py -x -q` — 40 passed (27 existing + 13 new)
- `grep "def check_tool_permitted" tools/apply_engine.py` — function exists
- `grep "CONFIRM BREAK-GLASS" .claude/commands/dsp-apply.md` — two-step flow present
- `grep -c "override_reason" tools/apply_engine.py` — 11 occurrences (both emit and write functions)
- No `str | None` union syntax in apply_engine.py (Python 3.9 compat)

## Known Stubs

None. All new functions are fully implemented. `check_tool_permitted()` is wired to `tool_classification.json`. Override reason flows end-to-end through both logging destinations. The Step 7 execution stub (`deferred-to-mcp-runtime`) is pre-existing and intentional (MCP execution wiring is Phase 3c Plan 3 scope).

## Self-Check: PASSED

- [x] `tools/apply_engine.py` — `PROFILE_TIER_ORDER`, `load_tool_classification`, `check_tool_permitted`, `customer` param on `load_profile`, `override_reason` on both emit and write functions
- [x] `tests/test_apply_engine.py` — `TestToolClassification`, `TestCustomerOverlay`, `TestOverrideReasonLogging` classes present
- [x] `.claude/commands/dsp-apply.md` — `BREAK-GLASS CONFIRMATION REQUIRED`, `CONFIRM BREAK-GLASS`, `Interaction 1`, `Interaction 2`, `break-glass-reason-rejected`, `check_tool_permitted` all present; no stale "Phase 3c will classify" reference
- [x] Commit 6680683 exists (Task 1)
- [x] Commit a7d43f6 exists (Task 2)
- [x] 40 tests pass
