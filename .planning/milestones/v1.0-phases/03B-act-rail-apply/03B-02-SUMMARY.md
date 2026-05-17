---
phase: 03B-act-rail-apply
plan: "02"
subsystem: infra
tags: [dsp-apply, act-rail, policy-profile, human-confirmation, provenance, incident-log]

# Dependency graph
requires:
  - phase: 03A-act-rail-plan
    provides: dsp-plan skill file step structure, act_gates.py run_gate_chain, canon/stack.py provenance
  - phase: 03B-01
    provides: apply_engine.py with load_profile/check_profile_permits/emit_activity_log_apply/write_incident_article, profile JSON files

provides:
  - /dsp:apply Claude Code custom command with 9-step apply structure
  - Mandatory human confirmation (CONFIRM APPLY / CANCEL) at Step 6
  - Profile enforcement before gate chain (read-only blocked at Step 2)
  - Gate re-run at apply time without bypass (unconditional drift detection)
  - Step 7 stub for Phase 3c MCP runtime wiring
  - Activity log and incident article emission on every invocation path

affects:
  - 03B-03 (golden harness apply cases build on this skill file)
  - 03C (Step 7 execution stub replaced with real MCP invocation)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "/dsp:apply skill mirrors /dsp:plan step numbering but adds profile check (Step 2) and confirmation (Step 6)"
    - "Early exit pattern: profile block at Step 2 exits before any MCP calls; gate failure at Step 4 exits before confirmation"
    - "Stub execution pattern (Step 7): emit structured result with deferred-to-mcp-runtime, same pattern as Phase 3a gate stubs"
    - "Activity log on every exit path including rejected, blocked-by-profile, gate-failure, and deferred-to-mcp-runtime"
    - "Incident articles written only when Step 7 is reached (execution attempted), not on early exits"

key-files:
  created:
    - .claude/commands/dsp-apply.md
  modified: []

key-decisions:
  - "Verified skill file contains no gate-bypass flag — apply-time gate re-run is unconditional per ACTA architecture"
  - "Profile enforcement happens at Step 2 (before Step 4 gate chain) — fail-closed pattern prevents MCP calls for wrong-profile invocations"
  - "Bypass attempt language ('apply immediately', 'skip confirmation') triggers explicit refusal with activity log entry"
  - "Step 7 stub emits deferred-to-mcp-runtime — real MCP wiring deferred to Phase 3c per RESEARCH.md open question resolution"

patterns-established:
  - "Pattern: skill file drives UX (AskUserQuestion confirmation); apply_engine.py receives confirmation_status as parameter — engine never prompts"
  - "Pattern: gate-bypass excluded from apply skill; flag present in plan skill for dev mode only"
  - "Pattern: incident articles gated on Step 7 reach — profile blocks and rejections are activity log only events"

requirements-completed: [ACTA-01]

# Metrics
duration: 2min
completed: 2026-04-29
---

# Phase 03B Plan 02: /dsp:apply Skill File Summary

**/dsp:apply Claude Code custom command with 9-step apply structure enforcing profile check before gate re-run, mandatory CONFIRM APPLY confirmation, and provenance logging on every exit path**

## Performance

- **Duration:** 2 min
- **Started:** 2026-04-29T13:10:46Z
- **Completed:** 2026-04-29T13:12:25Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Created `.claude/commands/dsp-apply.md` (161 lines) with complete 9-step structure
- Step 2 fail-closed: read-only profile blocked before any MCP calls, activity log entry emitted
- Step 4 gate re-run unconditional: no bypass flag, catches state drift between plan and apply time
- Step 6 mandatory: CONFIRM APPLY / CANCEL options; bypass attempts explicitly refused and logged
- Step 7 stub: `deferred-to-mcp-runtime` structured result, ready for Phase 3c MCP wiring
- All 15 acceptance criteria verified with automated Python check

## Task Commits

Each task was committed atomically:

1. **Task 1: Create /dsp:apply skill file with 9-step structure** - `30693c8` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `.claude/commands/dsp-apply.md` - /dsp:apply Claude Code custom command with 9-step apply structure, profile enforcement, gate re-run, human confirmation, execution stub, and provenance logging

## Decisions Made

- Gate-bypass excluded from apply skill: unlike `/dsp:plan` (which has `--gate-bypass` for dev-mode testing), `/dsp:apply` explicitly omits the flag. The acceptance criteria check verifies the string `--gate-bypass` is absent from the file. Documentation of the absence uses "gate-bypass" without the flag prefix to satisfy the constraint.
- Step 7 as stub: execution deferred to Phase 3c per RESEARCH.md recommendation — confirmed by CONTEXT.md deferred section listing "per-tool classification" as Phase 3c work
- Bypass refusal pattern: explicit rejection of "apply immediately", "skip confirmation", "just do it" with activity log entry — covers ACTA-02 bypass vector (c): crafted prompt injection

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed --gate-bypass string presence in documentation text**
- **Found during:** Task 1 (verification script run)
- **Issue:** File initially documented "There is NO `--gate-bypass` flag" which made the literal string `--gate-bypass` appear in the file, causing the acceptance criteria check (`'--gate-bypass' not in t`) to fail
- **Fix:** Rewrote both references to say "Gate bypass is not available at apply time" and "There is NO gate-bypass flag" — preserving the semantic intent without the flag literal
- **Files modified:** .claude/commands/dsp-apply.md
- **Verification:** Automated check passed after fix: `ALL CHECKS PASSED`
- **Committed in:** 30693c8 (Task 1 commit, amended before final commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug in documentation pattern)
**Impact on plan:** Acceptance criteria constraint clarified — the intent is to not expose the flag as valid syntax, not to never mention gate bypass as a concept. Fix preserves security constraint while enabling documentation.

## Issues Encountered

None beyond the deviation documented above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `/dsp:apply` skill is complete and invocable as a Claude Code custom command
- All references to `apply_engine.py` functions are in place; Plan 01 (apply_engine.py + profile files) is the dependency
- Plan 03 (golden harness apply cases) can extend `tests/golden/act/` referencing this skill file's structure
- Phase 3c can replace the Step 7 stub with real MCP execution once per-tool classification is complete

## Known Stubs

- **Step 7 execution stub** — `.claude/commands/dsp-apply.md`, Step 7 section
  - `execution_result = "deferred-to-mcp-runtime"`, `duration_seconds = 0.0`
  - Intentional: Phase 3c wires real MCP invocation per-tool. The confirmation, profile, and provenance infrastructure are the Phase 3b deliverables.

## Self-Check: PASSED

- FOUND: `.claude/commands/dsp-apply.md`
- FOUND: `.planning/phases/03B-act-rail-apply/03B-02-SUMMARY.md`
- FOUND: commit `30693c8`

---
*Phase: 03B-act-rail-apply*
*Completed: 2026-04-29*
