---
phase: 03B-act-rail-apply
plan: 01
subsystem: infra
tags: [apply-engine, policy-profiles, activity-log, incident-articles, least-privilege, acta]

# Dependency graph
requires:
  - phase: 03A-act-rail-plan
    provides: tools/act_gates.py, run_gate_chain(), canon/stack.py active_layers()
provides:
  - tools/profiles/read-only.json — empty allowed_operations, plan/inspect only
  - tools/profiles/engineer.json — standard non-destructive modules (topic, flink, schema, rbac, connect)
  - tools/profiles/break-glass.json — wildcard all operations including destructive
  - tools/apply_engine.py — load_profile, check_profile_permits, emit_activity_log_apply, write_incident_article
  - tests/test_apply_engine.py — 27 unit tests covering all four functions and bypass prevention
affects:
  - 03B-02 (dsp-apply skill uses these profiles and engine functions)
  - 03B-03 (golden harness tests apply skill which depends on engine)
  - 03C (per-tool classification builds on profile architecture)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "fail-closed profile enforcement: VALID_PROFILES set + ValueError on unknown"
    - "wildcard '*' permits all; empty list denies all; exact string match otherwise"
    - "activity log appended to wiki/activity/YYYY-MM.md with 11-field apply schema"
    - "incident article: YAML frontmatter (7 keys) + 4 body sections in wiki/incidents/"
    - "bypass prevention: source-level scan tests (no input(), skip_confirmation, bypass_confirmation)"

key-files:
  created:
    - tools/profiles/read-only.json
    - tools/profiles/engineer.json
    - tools/profiles/break-glass.json
    - tools/apply_engine.py
    - tests/test_apply_engine.py
  modified: []

key-decisions:
  - "Profile files live in tools/profiles/ colocated with act rail tooling; loaded by name at skill start"
  - "VALID_PROFILES explicit set (not filesystem scan) — unknown names fail immediately, fail-closed"
  - "Wildcard '*' in allowed_operations covers break-glass without per-tool enumeration at this phase"
  - "Activity log entries use 11-field schema (operator, profile, confirmation_status, execution_result, duration_seconds, gates, canon_stack, overlay, artifact, plan, skill)"
  - "Incident articles use YAML frontmatter for machine-readable provenance; four sections for human audit"

patterns-established:
  - "Profile enforcement pattern: load_profile() + check_profile_permits() before any gate chain invocation"
  - "Bypass prevention test pattern: source scan via PROJECT_ROOT path for forbidden strings"
  - "TDD RED-GREEN: tests committed before implementation (a1c31a8 test, b86bc08 feat)"

requirements-completed: [ACTA-02, ACTA-03, ACTA-04, ACTA-05]

# Metrics
duration: 2min
completed: 2026-04-29
---

# Phase 03B Plan 01: Apply Engine + Policy Profiles Summary

**Three JSON policy profiles (read-only/engineer/break-glass) and apply_engine.py with four exported functions enforcing least-privilege access control, activity log provenance, and wiki incident article generation.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-04-29T13:10:48Z
- **Completed:** 2026-04-29T13:12:59Z
- **Tasks:** 1 (TDD with RED + GREEN commits)
- **Files modified:** 5 created

## Accomplishments

- Three policy profile JSON files establish least-privilege tiers: read-only (empty ops), engineer (5 standard modules), break-glass (wildcard)
- apply_engine.py implements four core functions: load_profile, check_profile_permits, emit_activity_log_apply, write_incident_article
- 27 unit tests cover profile loading, enforcement, activity log creation/append, incident article structure, and bypass prevention
- Fail-closed design: unknown profile names raise ValueError before any gate chain runs
- Full test suite remains green (551 tests passed)

## Task Commits

TDD task with RED + GREEN commits:

1. **TDD RED: Test file + profile JSON files** - `a1c31a8` (test)
2. **TDD GREEN: apply_engine.py implementation** - `b86bc08` (feat)

**Plan metadata:** (docs commit — this summary)

_Note: TDD task with two commits (test RED → feat GREEN)_

## Files Created/Modified

- `tools/profiles/read-only.json` — Empty allowed_operations; plan/inspect only
- `tools/profiles/engineer.json` — Standard modules: module/topic, module/flink, role/cp_schema, role/cp_rbac, role/cp_connect
- `tools/profiles/break-glass.json` — Wildcard ["*"]; all operations including destructive
- `tools/apply_engine.py` — Four exported functions with CLI __main__ block; Python 3.9 compatible; no bypass patterns
- `tests/test_apply_engine.py` — 27 tests: TestProfileLoading, TestProfileFiles, TestProfileEnforcement, TestActivityLog, TestIncidentArticle, TestBypassPrevention

## Decisions Made

- VALID_PROFILES is an explicit Python set (not a filesystem scan) so unknown names fail immediately without touching the filesystem — stricter fail-closed enforcement
- Wildcard "*" in break-glass allowed_operations covers Phase 3b scope; per-tool enumeration deferred to Phase 3c where mcp-confluent tool classification lands
- Activity log entries use 11 fields matching the CONTEXT.md apply entry schema: all fields from ACTA-04 (operator, profile, confirmation_status, execution_result, duration_seconds) plus overlay, artifact, plan, gates, canon_stack, and skill
- Incident article YAML frontmatter uses 7 keys (artifact, operator, profile, outcome, canon_hash, plan_ref, timestamp) — minimal but complete provenance for audit trail
- Python 3.9 compatibility maintained: Optional[List[str]] from typing, no X|Y union syntax

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None — implementation matched plan specification directly.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Profile files and engine functions are ready for import by 03B-02 (dsp-apply skill file)
- `from tools.apply_engine import load_profile, check_profile_permits` import verified working
- activity log and incident article paths are PROJECT_ROOT-relative (monkeypatched cleanly in tests)
- wiki/incidents/ directory created and ready for apply-time article generation

---
*Phase: 03B-act-rail-apply*
*Completed: 2026-04-29*

## Self-Check: PASSED

- FOUND: tools/profiles/read-only.json
- FOUND: tools/profiles/engineer.json
- FOUND: tools/profiles/break-glass.json
- FOUND: tools/apply_engine.py
- FOUND: tests/test_apply_engine.py
- FOUND: .planning/phases/03B-act-rail-apply/03B-01-SUMMARY.md
- FOUND commit: a1c31a8 (test RED)
- FOUND commit: b86bc08 (feat GREEN)
- Module import: All 4 exports OK
- Test suite: 551 passed
