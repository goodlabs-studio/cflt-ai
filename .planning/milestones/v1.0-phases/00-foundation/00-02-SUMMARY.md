---
phase: 00-foundation
plan: "02"
subsystem: infra
tags: [manifest, flox, fsi-dsp, yaml, python311, asset-inventory]

requires: []
provides:
  - "MANIFEST.yaml v1 with 50 stable IDs covering all fsi-dsp asset types"
  - "fsi-dsp Flox environment manifest targeting 4 architectures"
affects: [00-03, 00-04, 00-05, wiki-citations, ci-parity]

tech-stack:
  added: [pyyaml, pytest, ansible-lint, yamllint, flox-1.11.0]
  patterns:
    - "MANIFEST.yaml type-prefixed IDs: role/, module/, scenario/, adr/, reference/, script/, observability/"
    - "Flox manifest modeled after cflt-ai pattern with 4-architecture systems array"

key-files:
  created:
    - raw/repos/fsi-dsp/MANIFEST.yaml
    - raw/repos/fsi-dsp/.flox/env/manifest.toml
  modified: []

key-decisions:
  - "MANIFEST.yaml IDs embed type prefix (role/cp_topic, not cp_topic) to prevent cross-type collisions — Pitfall 2 from research"
  - "ADR-009 (LinuxONE) included in MANIFEST.yaml as status:proposed so citation infrastructure is ready before ADR is authored in plan 00-05"
  - "fsi-dsp Flox manifest pins python311 explicitly to match CI rather than generic python3"
  - "Systems array copied verbatim from cflt-ai manifest to guarantee CI parity on x86_64-linux runners"

patterns-established:
  - "Stable ID contract: fsi-dsp publishes IDs in MANIFEST.yaml; cflt-ai cites via fsi-dsp://{id}; CI enforces both sides"
  - "Flox manifest pattern: schema-version 1.11.0, uv-based venv in on-activate, 4-architecture systems array"

requirements-completed: [CNTR-01, HYG-05]

duration: 8min
completed: "2026-04-28"
---

# Phase 00 Plan 02: MANIFEST.yaml v1 + fsi-dsp Flox Manifest Summary

**MANIFEST.yaml v1 with 50 type-prefixed stable IDs (9 roles, 2 modules, 6 scenarios, 9 ADRs, 10 references, 7 scripts, 7 observability) plus fsi-dsp Flox manifest targeting all 4 architectures with Python 3.11**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-28T18:01:16Z
- **Completed:** 2026-04-28T18:09:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- MANIFEST.yaml v1 published in fsi-dsp with 50 capabilities covering every existing asset — the stable ID contract between cflt-ai and fsi-dsp is now live
- fsi-dsp Flox manifest created with Python 3.11, uv, pyyaml, pytest, ansible-lint, yamllint across all 4 target architectures
- ADR-009 (LinuxONE) pre-registered in MANIFEST.yaml as `status: proposed` so wiki citation infrastructure is ready before the ADR is authored in plan 00-05

## Task Commits

Each task was committed atomically inside the fsi-dsp submodule, with cflt-ai submodule pointer advanced:

1. **Task 1: Author MANIFEST.yaml v1** - `b579f25` (feat) — inside fsi-dsp
2. **Task 2: Create fsi-dsp Flox manifest** - `532eb7d` (chore) — inside fsi-dsp
3. **Submodule pointer update** - `0f54c43` (feat) — cflt-ai

## Files Created/Modified

- `raw/repos/fsi-dsp/MANIFEST.yaml` - 50 stable asset IDs, schema fsi-dsp/manifest/v1, version 1.0.0
- `raw/repos/fsi-dsp/.flox/env/manifest.toml` - Flox env with Python 3.11, 4 architectures, testing tools

## Decisions Made

- Type prefix embedded in ID (`role/cp_topic` not `cp_topic`) to prevent cross-type ID collisions per Pitfall 2 from research
- ADR-009 pre-registered as `status: proposed` — enables citation resolution CI to be wired without blocking on ADR authoring
- Python 3.11 pinned explicitly (not generic `python3`) to match fsi-dsp CI
- Systems array copied from cflt-ai manifest verbatim to guarantee GitHub Actions CI works on `x86_64-linux`

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

Submodule commit workflow: `git add raw/repos/fsi-dsp/FILE` from cflt-ai is rejected ("Pathspec is in submodule"). Files must be committed inside the submodule first, then the submodule pointer updated in cflt-ai. Handled correctly — committed inside `raw/repos/fsi-dsp/` then advanced submodule ref in cflt-ai.

## Next Phase Readiness

- MANIFEST.yaml stable IDs unblock: wiki citation migration (plan 00-03), CI parity workflows (plan 00-04)
- fsi-dsp Flox manifest unblocks: clean-clone verification in CI
- ADR-009 placeholder in MANIFEST.yaml unblocks: LinuxONE wiki ingest (plan 00-05) once ADR is authored

---
*Phase: 00-foundation*
*Completed: 2026-04-28*
