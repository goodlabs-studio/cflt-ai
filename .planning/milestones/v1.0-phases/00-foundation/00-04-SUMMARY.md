---
phase: 00-foundation
plan: "04"
subsystem: wiki-activity-log, fsi-dsp-adrs
tags: [wiki, activity-log, adr, linuxone, mainframe, fsi, kafka-offload]
dependency_graph:
  requires: ["00-02"]
  provides: ["wiki/activity/", "raw/repos/fsi-dsp/docs/adr/009-linuxone-kafka-offload.md"]
  affects: ["00-05"]
tech_stack:
  added: []
  patterns: ["append-only-log", "adr-backed-decision"]
key_files:
  created:
    - wiki/activity/README.md
    - wiki/activity/2026-04.md
    - raw/repos/fsi-dsp/docs/adr/009-linuxone-kafka-offload.md
  modified: []
decisions:
  - "Activity log uses overlay-scoped fields (Overlay + Canon stack) for full audit context per WIKI-02"
  - "ADR-009 status set to Accepted (not Proposed) — decision is already canonical in CLAUDE.md FSI overlay"
metrics:
  duration: "~8 minutes"
  completed: "2026-04-28"
  tasks: 2
  files: 3
---

# Phase 00 Plan 04: Activity Log + ADR-009 Summary

Wiki activity log infrastructure created and ADR-009 authored in fsi-dsp documenting IBM LinuxONE as preferred compute for z/OS Kafka offload via IBM MQ Source Connector bridge pattern.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Create wiki activity log directory and seed file | 38ed7d5 | wiki/activity/README.md, wiki/activity/2026-04.md |
| 2 | Author ADR-009 in fsi-dsp (submodule) | e58a909 (fsi-dsp), 4f4c199 (cflt-ai ptr) | raw/repos/fsi-dsp/docs/adr/009-linuxone-kafka-offload.md |

## What Was Built

### wiki/activity/ directory (WIKI-02)

- `wiki/activity/README.md`: Format specification for the append-only activity log. Defines the five-field entry schema (Skill, Overlay, Input, Output, Canon stack), retention rules (archive after 12 months, never delete), and append-only enforcement.
- `wiki/activity/2026-04.md`: Seed log with two entries documenting the Phase 0 work already performed: initial codebase mapping (`/gsd:map-codebase`, base overlay) and phase planning (`/gsd:plan-phase`, base + fsi overlay).

The `Overlay` and `Canon stack` fields provide per-entry provenance of which canon layers were active — the key WIKI-02 requirement for overlay-scoped path recording.

### ADR-009: LinuxONE for z/OS Kafka Offload (WIKI-01 prerequisite)

Full ADR authored in `raw/repos/fsi-dsp/docs/adr/009-linuxone-kafka-offload.md` with:

- **Status: Accepted** — decision is already canonical in CLAUDE.md FSI overlay; no further approval needed
- **Bridge pattern**: `z/OS Application -> IBM MQ Queue -> MQ Source Connector (LinuxONE) -> Kafka Topic`
- **Compute**: IBM LinuxONE Emperor 4 or Rockhopper III+ on RHEL 8.x/9.x or Ubuntu 22.04 LTS
- **Network**: HiperSockets for sub-millisecond z/OS-to-LinuxONE latency (no external network hop)
- **Security**: FIPS 140-2 native crypto; mTLS per ADR-006
- **DR**: Cluster Linking cross-region per ADR-005; Avro serialization per ADR-001
- **Consequences section**: Explicit easier/harder/mitigations for LinuxONE hardware lead times, s390x certification matrix, and MQ queue manager coordination

ADR-009 was pre-registered as `proposed` in MANIFEST.yaml (Plan 00-02); this plan authors the actual content and sets status to Accepted. Fulfills the MANIFEST.yaml `adr/009` entry created in Plan 00-02.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — no stubs. The activity log seed entries document real work that was done; ADR-009 is complete content.

## Self-Check: PASSED

- wiki/activity/README.md: FOUND
- wiki/activity/2026-04.md: FOUND
- raw/repos/fsi-dsp/docs/adr/009-linuxone-kafka-offload.md: FOUND
- Commits: 38ed7d5 (task 1), e58a909 (fsi-dsp task 2), 4f4c199 (submodule ptr): FOUND
