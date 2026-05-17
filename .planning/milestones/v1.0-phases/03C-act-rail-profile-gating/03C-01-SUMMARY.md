---
phase: 03C-act-rail-profile-gating
plan: "01"
subsystem: profile-gating
tags: [tool-classification, profile-gating, break-glass, customer-overlay, acme-bank]
dependency_graph:
  requires: []
  provides: [tool_classification.json, acme-bank-engineer-overlay, adr-003]
  affects: [tools/apply_engine.py, tests/test_profile_gating.py]
tech_stack:
  added: []
  patterns: [explicit-tool-enumeration, customer-profile-overlay, fail-closed-unclassified]
key_files:
  created:
    - tools/profiles/tool_classification.json
    - canon/customer/acme-bank/profiles/engineer.json
    - canon/customer/acme-bank/adrs/adr-003.md
  modified:
    - tools/profiles/break-glass.json
    - tests/test_apply_engine.py
decisions:
  - "81 mcp-confluent tools explicitly classified into three tiers (37 read-only, 25 engineer, 19 break-glass) — all by exact name per ACTG-01"
  - "break-glass wildcard '*' replaced with explicit artifact operation list: module/topic, module/flink, role/cp_schema, role/cp_rbac, role/cp_connect, script/fsi-dr, scenario/cc-aws"
  - "acme-bank engineer overlay is a complete profile document (not a partial diff) per RESEARCH.md Pitfall 4 — load_profile() returns entire file"
  - "unclassified_policy set to deny — fail-closed per Phase 3b VALID_PROFILES pattern"
metrics:
  duration: "~8 minutes"
  completed: "2026-04-29"
  tasks_completed: 2
  files_created: 3
  files_modified: 2
---

# Phase 03C Plan 01: Tool Classification Table and Customer Profile Overlay Summary

**One-liner:** 81 mcp-confluent tools classified by explicit name into three tiers, break-glass wildcard eliminated, and acme-bank differential engineer profile created with module/flink removed and role/cp_audit added.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create tool_classification.json and update profile JSONs | 99569bb | tools/profiles/tool_classification.json, tools/profiles/break-glass.json |
| 2 | Create acme-bank engineer overlay and ADR-003 | 343a875 | canon/customer/acme-bank/profiles/engineer.json, canon/customer/acme-bank/adrs/adr-003.md, tests/test_apply_engine.py |

## What Was Built

**`tools/profiles/tool_classification.json`** — 81 entries mapping every mcp-confluent tool name to a profile tier string ("read-only", "engineer", or "break-glass"). Tier hierarchy: read-only < engineer < break-glass. `unclassified_policy: "deny"` ensures fail-closed behavior for any future unclassified tools. This is the single source of truth for per-tool permission checks in apply_engine.py.

**`tools/profiles/break-glass.json`** — Wildcard `"*"` in `allowed_operations` replaced with explicit list: `["module/topic", "module/flink", "role/cp_schema", "role/cp_rbac", "role/cp_connect", "script/fsi-dr", "scenario/cc-aws"]`. Satisfies ACTG-01 "by name, not regex" requirement.

**`canon/customer/acme-bank/profiles/engineer.json`** — Complete engineer profile document for acme-bank customer overlay. Key differentials vs base engineer: `module/flink` removed (multi-tenant Flink contention risk), `role/cp_audit` added (SOX compliance requirement). `customer_overrides` metadata block documents the diff with ADR reference.

**`canon/customer/acme-bank/adrs/adr-003.md`** — ADR documenting Flink prohibition and audit role addition. Status: Accepted. Follows adr-002.md pattern (Context / Decision / Consequences sections).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated two test_apply_engine.py tests asserting old wildcard behavior**
- **Found during:** Task 2 regression test run
- **Issue:** `test_load_break_glass_contains_wildcard` asserted `allowed_operations == ["*"]`; `test_break_glass_permits_all` asserted that `"anything/at/all"` was permitted via wildcard — both were correct assertions for Phase 3b behavior but became failures after the Phase 3c wildcard removal.
- **Fix:** Updated `test_load_break_glass_contains_wildcard` to assert no wildcard and explicit operations present. Updated `test_break_glass_permits_all` to assert explicit operations pass and unknown operation fails (new desired behavior).
- **Files modified:** `tests/test_apply_engine.py`
- **Commit:** 343a875

## Verification Results

All plan verification commands passed:
- `tool_classification.json`: 81 tools classified (>= 50 threshold)
- `break-glass.json`: no wildcard in `allowed_operations`
- `acme-bank/profiles/engineer.json`: `module/flink` absent, `role/cp_audit` present
- `adr-003.md`: exists, contains "Accepted" status
- `pytest tests/test_apply_engine.py`: 27 passed, 0 failed

## Known Stubs

None. All artifacts are fully wired data (JSON classification table, complete profile docs, ADR). No placeholder values flow to UI or downstream enforcement logic.

## Self-Check: PASSED

- [x] `tools/profiles/tool_classification.json` exists
- [x] `tools/profiles/break-glass.json` updated
- [x] `canon/customer/acme-bank/profiles/engineer.json` exists
- [x] `canon/customer/acme-bank/adrs/adr-003.md` exists
- [x] Commit 99569bb exists in git log
- [x] Commit 343a875 exists in git log
- [x] 27 existing tests pass
