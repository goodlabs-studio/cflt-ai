---
phase: 00-foundation
plan: "05"
subsystem: wiki
tags: [wiki, citations, fsi-dsp, manifest, linuxone, ibm, mainframe, z/os, mq, kafka-connect]

# Dependency graph
requires:
  - phase: 00-02
    provides: MANIFEST.yaml v1 with stable fsi-dsp:// IDs for all assets
  - phase: 00-04
    provides: ADR-009 at raw/repos/fsi-dsp/docs/adr/009-linuxone-kafka-offload.md
provides:
  - All 10 wiki articles migrated from raw file paths to fsi-dsp:// MANIFEST.yaml IDs (CNTR-02)
  - wiki/concepts/linuxone-kafka-integration.md compiled from ADR-009 (WIKI-01)
  - wiki/_index.md and wiki/_graph.md updated with LinuxONE article
  - tests/test_wiki_citations.py with 12 tests validating no raw paths, citation resolution, and LinuxONE article
affects: [00-06, check-citations, wiki-validation, ci-parity]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "fsi-dsp:// URI scheme for stable wiki citation references (survives repo refactors)"
    - "pytest test classes for wiki citation enforcement (TestNoRawPaths, TestCitationResolution, TestLinuxOneArticle)"

key-files:
  created:
    - wiki/concepts/linuxone-kafka-integration.md
    - tests/test_wiki_citations.py
  modified:
    - wiki/concepts/sla-tiers.md
    - wiki/concepts/fsi-data-streaming-platform.md
    - wiki/concepts/schema-evolution-strategies.md
    - wiki/concepts/fsi-compliance.md
    - wiki/patterns/fsi-governance-automation.md
    - wiki/patterns/dr-cluster-linking.md
    - wiki/patterns/dr-mirrormaker2.md
    - wiki/patterns/dr-multi-region-cluster.md
    - wiki/patterns/topic-naming.md
    - wiki/synthesis/adr-index.md
    - wiki/_index.md
    - wiki/_graph.md

key-decisions:
  - "fsi-dsp:// URI scheme adopted as stable citation form — IDs are stable per MANIFEST.yaml contract, raw paths would break on fsi-dsp refactors"
  - "adr-index.md uses multi-line YAML list for sources (adr/001 through adr/009) rather than inline array — cleaner diff and easier future extension"
  - "TestCitationResolution strips fsi-dsp:// prefix and checks against manifest ID set — tests the contract, not the string format"

patterns-established:
  - "fsi-dsp:// citation pattern: all wiki articles cite fsi-dsp assets by MANIFEST.yaml ID, never by raw file path"
  - "Citation test pattern: pytest classes with fixture-based wiki traversal for ongoing enforcement of citation hygiene"

requirements-completed: [CNTR-02, WIKI-01]

# Metrics
duration: 2min
completed: 2026-04-28
---

# Phase 00 Plan 05: Wiki Citation Migration and LinuxONE Article Summary

**10 wiki articles migrated from raw file paths to stable fsi-dsp:// MANIFEST.yaml IDs, LinuxONE integration article compiled from ADR-009, and 12 citation validation tests written.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-04-28T18:43:00Z
- **Completed:** 2026-04-28T18:45:25Z
- **Tasks:** 2
- **Files modified:** 14 (10 migrated articles, 2 new files, 2 wiki meta files)

## Accomplishments

- Migrated all 10 wiki articles: sla-tiers, fsi-data-streaming-platform, schema-evolution-strategies, fsi-compliance, fsi-governance-automation, dr-cluster-linking, dr-mirrormaker2, dr-multi-region-cluster, topic-naming, adr-index — all sources frontmatter now uses fsi-dsp:// IDs
- Compiled wiki/concepts/linuxone-kafka-integration.md from ADR-009: covers bridge pattern (z/OS → MQ → MQ Source Connector on LinuxONE → Kafka), HiperSockets rationale, SLA tier fit, configuration specifics, and considerations
- Created tests/test_wiki_citations.py with 12 tests across TestNoRawPaths, TestCitationResolution, and TestLinuxOneArticle — all passing; enforces citation hygiene going forward

## Task Commits

1. **Task 1: Migrate wiki article sources to fsi-dsp:// IDs** — `349b533` (feat)
2. **Task 2: Compile LinuxONE article and create citation tests** — `4b09320` (feat)

**Plan metadata:** [pending final commit] (docs: complete plan)

## Files Created/Modified

- `wiki/concepts/linuxone-kafka-integration.md` — New article: LinuxONE as preferred compute for z/OS Kafka offload via IBM MQ Source Connector; compiled from ADR-009
- `tests/test_wiki_citations.py` — 12 citation validation tests: no raw paths, all IDs resolve against MANIFEST.yaml, LinuxONE article structure
- `wiki/concepts/sla-tiers.md` — sources: raw path → fsi-dsp://role/cp_topic
- `wiki/concepts/fsi-data-streaming-platform.md` — sources: raw path → fsi-dsp://scenario/cc-aws, fsi-dsp://module/topic
- `wiki/concepts/schema-evolution-strategies.md` — sources: raw path → fsi-dsp://adr/001, fsi-dsp://adr/002
- `wiki/concepts/fsi-compliance.md` — sources: raw path → fsi-dsp://script/validate-fips, fsi-dsp://adr/006
- `wiki/patterns/fsi-governance-automation.md` — sources: raw path → fsi-dsp://role/cp_topic, cp_schema, cp_rbac
- `wiki/patterns/dr-cluster-linking.md` — sources: raw path → fsi-dsp://adr/005, fsi-dsp://script/mirror-failover
- `wiki/patterns/dr-mirrormaker2.md` — sources: raw path → fsi-dsp://adr/005, fsi-dsp://script/mirror-failback
- `wiki/patterns/dr-multi-region-cluster.md` — sources: raw path → fsi-dsp://adr/008, fsi-dsp://script/fsi-dr
- `wiki/patterns/topic-naming.md` — sources: raw paths → fsi-dsp://adr/007, fsi-dsp://role/cp_topic
- `wiki/synthesis/adr-index.md` — sources: raw dir path → multi-line list fsi-dsp://adr/001 through adr/009
- `wiki/_index.md` — Added linuxone-kafka-integration entry under Concepts
- `wiki/_graph.md` — Added four backlinks for linuxone-kafka-integration

## Decisions Made

- fsi-dsp:// URI scheme adopted as stable citation form — IDs are stable per MANIFEST.yaml contract, raw paths would break on fsi-dsp refactors
- adr-index.md uses multi-line YAML list for sources (adr/001 through adr/009) — cleaner diff and easier future extension than inline array
- TestCitationResolution strips fsi-dsp:// prefix and checks against manifest ID set — tests the contract, not just the string format

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Plan 06 (check-citations.py) can now validate all fsi-dsp:// IDs against MANIFEST.yaml — all citations are in the stable ID form required by that script
- Citation enforcement tests in tests/test_wiki_citations.py provide ongoing regression coverage; runs in CI via `pytest tests/`
- LinuxONE article is wired into _index.md and _graph.md; Plan 06 link-checking will validate the new cross-links

---
*Phase: 00-foundation*
*Completed: 2026-04-28*
