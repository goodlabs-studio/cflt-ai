---
phase: 02-review-skill
plan: 01
subsystem: skills
tags: [review, claim-extraction, premise-challenge, multi-doc, docx-output, activity-log, canon-overlay]

# Dependency graph
requires:
  - phase: 01-knowledge-skill
    provides: /ask skill flag-parsing pattern (--mode, --force-route), auto-stub logic, activity log format
  - phase: 00-foundation
    provides: canon/stack.py (resolve_stack, active_layers, provenance_footer), wiki/activity/ format, canon overlay layers

provides:
  - Rewritten /review skill (.claude/commands/review.md) with 8-step structured process
  - Structured YAML claim extraction schema (id, source_file, source_section, category, text)
  - Step 2.5 premise-challenge with overlay awareness and severity rating
  - Multi-document corpus labeling with source-slug-N ID convention
  - --output (md|docx|both) and --overlay flag parsing
  - review-to-docx.py invocation contract for docx output
  - Activity log emission per invocation (wiki/activity/YYYY-MM.md)
  - Auto-stub on wiki miss for claims (wiki/_queue.md)

affects: [02-02-docx-converter, 02-03-golden-harness]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "YAML intermediate output before table rendering (reproducibility anchor for REVW-01)"
    - "Source-slug-N claim ID convention for multi-doc deduplication"
    - "Premise-challenge with Critical/Moderate/Minor severity before claim validation"
    - "Overlay-resolved canon config for compliance checking when --overlay is active"
    - "Activity log emission after every skill invocation (mandatory, no silent runs)"

key-files:
  created: []
  modified:
    - .claude/commands/review.md

key-decisions:
  - "YAML claim block is mandatory before table rendering — cannot skip Step 2 YAML for direct table output"
  - "Multi-doc claim IDs use source-slug prefix (deck-1, runbook-2) to prevent collision on merge"
  - "Premise-challenge runs between claim extraction and wiki cross-reference (Step 2.5, not end of process)"
  - "Auto-stub fires on claim-level wiki misses (not just query-level as in /ask)"
  - "/review is always report mode — no ephemeral output variant"

patterns-established:
  - "Flag parsing pattern: --flag-name value extraction before remaining tokens treated as inputs (mirrors ask.md Step 1)"
  - "Activity log emission: append to wiki/activity/YYYY-MM.md after every invocation, never skip"
  - "Overlay error guard: check canon/customer/<name>/overrides.yaml existence before loading, stop on miss"

requirements-completed: [REVW-01, REVW-02, REVW-04]

# Metrics
duration: 1min
completed: 2026-04-28
---

# Phase 2 Plan 01: /review Skill Rewrite Summary

**8-step /review skill with YAML claim extraction, premise-challenge (Step 2.5), multi-doc corpus support, --output/--overlay flags, and mandatory activity log emission**

## Performance

- **Duration:** 1 min
- **Started:** 2026-04-28T21:18:24Z
- **Completed:** 2026-04-28T21:19:39Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Rewrote .claude/commands/review.md from 6-step to 8-step process (110 lines to 247 lines)
- Added Step 1 (argument parsing) with --output and --overlay flag support, error guards for missing files and unknown flag values
- Added Step 1.5 (document loading) with multi-file corpus labeling by basename
- Rewrote Step 2 (claim extraction) with YAML intermediate block required before table rendering — five numbered categories: config_value, behavior_assertion, architecture_choice, metric_sla, comparison
- Added Step 2.5 (premise-challenge) with FSI SLA tier awareness and Critical/Moderate/Minor severity rating
- Extended Step 3 with auto-stub on claim-level wiki miss (appends to wiki/_queue.md)
- Extended Step 5 with overlay-aware compliance checking and Overlay Override column
- Rewrote Step 6 (report generation) with Premise Challenge section, provenance_footer() call, review-to-docx.py invocation for docx output, and activity log emission

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite review.md with structured claim extraction, premise-challenge, multi-doc, flag parsing, and activity log emission** - `f8350de` (feat)

**Plan metadata:** (see final commit below)

## Files Created/Modified
- `.claude/commands/review.md` - Complete 8-step /review skill rewrite; replaces 6-step version

## Decisions Made
- YAML claim block is mandatory and must appear before table rendering — this is the reproducibility anchor for REVW-01 (claim extraction determinism >= 95%)
- Multi-doc claim IDs use source-slug prefix convention (deck-1, runbook-2) to prevent collision when claims from multiple documents are merged into a single validation table
- Premise-challenge (Step 2.5) runs after claim extraction but before wiki cross-reference — not as a post-processing step — so overlay conflicts can inform the validation pass
- Auto-stub fires on claim-level wiki misses in /review (consistent with /ask's query-level auto-stub; coverage gaps never lost)
- /review is always report mode — no ephemeral variant; every invocation writes a file

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan 02 (docx converter, tools/review-to-docx.py) can implement against the invocation contract in Step 6: `python3 tools/review-to-docx.py outputs/reports/<slug>-review-<YYYY-MM-DD>.md`
- Plan 03 (golden harness) can implement against the YAML claim schema defined in Step 2 and the report section structure defined in Step 6
- Both downstream plans have unambiguous output contracts from this plan

---
*Phase: 02-review-skill*
*Completed: 2026-04-28*
