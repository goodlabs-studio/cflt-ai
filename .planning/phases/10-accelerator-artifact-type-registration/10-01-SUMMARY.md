---
phase: 10-accelerator-artifact-type-registration
plan: 01
subsystem: contract
tags: [manifest, fsi-dsp, accelerator, kustomize, linuxone, schema-contract]

# Dependency graph
requires:
  - phase: 09-submodule-sync-canon-parity-unblock
    provides: "submodule pinned at upstream main (5a86fd2) with accelerators/confluent-on-linuxone/ on disk; manifest stability check passing at v1.1.0"
provides:
  - "type: accelerator registered in raw/repos/fsi-dsp/MANIFEST.yaml (id accelerator/confluent-on-linuxone) on feat/manifest-accelerator-type branch inside the submodule"
  - "Schema additions: apply_sequence (ordered list of {layer, path, canon_key}), build_command, dry_run_command, apply_command — reusable across future Helm/Terraform accelerators"
  - "Per-layer canon_key (single source of truth) for the 5 hardening layers: mds-rbac, tls-fips, compatibility-full-transitive, events-retention, environment-mtls"
  - "cflt-ai parent working tree shows raw/repos/fsi-dsp pointer advanced 5a86fd2 → b117f3f (unstaged, deliberately handed off to 10-02)"
affects: [10-02-validator-extension, 10-03-upstream-pr, 11-act-rail-dispatch, 12-wiki-ingest]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-layer canon_key co-location: MANIFEST entry IS the layer→canon map (downstream consumers read this, not a duplicated table — anti-pattern fix derived from G.2c cleanup)"
    - "Explicit build/dry_run/apply commands per artifact: keeps the schema tool-agnostic (kustomize today, helm/terraform tomorrow without cflt-ai changes)"
    - "Append-only schema extension at v1.1.0: 1 added / 0 removed per CNTR-04; no major version bump"

key-files:
  created: []
  modified:
    - raw/repos/fsi-dsp/MANIFEST.yaml

key-decisions:
  - "Inserted accelerator block as a new top-level section after the final observability entry (line ~374) rather than alphabetical interleave — matches upstream's existing section-comment convention for artifact-type grouping"
  - "Did NOT edit raw/repos/fsi-dsp/CLAUDE.md per plan Step 3 — file is auto-generated and has no curated schema-contract section; schema docs land in cflt-ai's CONTRIBUTING.md / tools/manifest-schema.md in 10-02 Task 4 and in the upstream PR body in 10-03"
  - "Single-file, single-commit inside submodule (b117f3f) — atomic rollback unit; parent-pointer bump deferred to 10-02's atomic cflt-ai commit with validator extension"

patterns-established:
  - "type: accelerator schema shape: id (accelerator/{name}), type accelerator, path, description, apply_sequence list, build_command, dry_run_command, apply_command — locked verbatim from CONTEXT.md <decisions>"
  - "Submodule feature branching: feat/{topic} branched from origin/main, single-file commit, parent-pointer left unstaged for downstream cflt-ai-side atomic commit to pick up"

requirements-completed: [MAN-01]

# Metrics
duration: 3min
completed: 2026-05-23
---

# Phase 10 Plan 01: Accelerator artifact-type registration in upstream fsi-dsp MANIFEST.yaml

**Registered `type: accelerator` as a first-class MANIFEST.yaml capability with a 5-layer `apply_sequence` schema (RBAC → TLS → SR → audit → Flink), per-layer `canon_key` co-location, and explicit kustomize build/dry-run/apply commands — committed inside the fsi-dsp submodule on `feat/manifest-accelerator-type` (b117f3f); cflt-ai parent pointer ready for 10-02 to atomically bump.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-05-23T15:46:42Z
- **Completed:** 2026-05-23T15:49:18Z
- **Tasks:** 1
- **Files modified:** 1 (inside submodule)

## Accomplishments

- First-ever `type: accelerator` entry registered in upstream fsi-dsp MANIFEST.yaml (`accelerator/confluent-on-linuxone`)
- `apply_sequence` schema landed with all 5 layers + verbatim canon_keys + verbatim layer paths matching on-disk shape
- `build_command` / `dry_run_command` / `apply_command` schema fields landed as explicit strings — Helm/Terraform accelerators reuse the schema unchanged in future phases
- fsi-dsp submodule branched (`feat/manifest-accelerator-type`) with a single, clean, reviewable commit ready for upstream PR (gated on 10-03 human-action)
- cflt-ai parent-tree shows pointer advance `5a86fd2 → b117f3f` (unstaged — deliberate handoff to 10-02)
- Manifest stability check passes inside submodule: 56 IDs, +1 added, 0 removed, version unchanged at 1.1.0 (additive change per CNTR-04)

## Task Commits

Inside `raw/repos/fsi-dsp/` (submodule, branch `feat/manifest-accelerator-type`):

1. **Task 1: Register accelerator capability in raw/repos/fsi-dsp/MANIFEST.yaml on a feature branch** — `b117f3f` (feat)

**Parent-pointer bump:** Deferred to 10-02 (atomic with validator extension)

## Files Created/Modified

- `raw/repos/fsi-dsp/MANIFEST.yaml` — appended new "Accelerators (1)" section after the final observability entry; added 28 lines: section-comment + accelerator/confluent-on-linuxone entry with apply_sequence (5 layers × 3 keys = 15 sub-entries) + 3 command strings

## Decisions Made

- **Insertion position:** Appended as a new "Accelerators (1)" section after `observability/metrics-mapping` (line 374), not interleaved alphabetically. Matches upstream's existing section-comment convention (Ansible Roles (9), Terraform Modules (2), Scenarios (6), ADRs (10), References (10), Scripts (7), Observability (7), Accelerators (1)) — preserves the "browse by artifact type" reading order operators already use.
- **CLAUDE.md untouched:** Plan Step 3 explicitly verified during planning that fsi-dsp/CLAUDE.md is auto-generated (Tech Stack / Conventions / Architecture sections come from upstream tooling, no curated schema-contract section). Schema documentation lands in cflt-ai's CONTRIBUTING.md / tools/manifest-schema.md in 10-02 Task 4 and in the upstream PR body in 10-03 — no rot in the auto-generated file.
- **Description text from CONTEXT.md verbatim:** "Confluent Platform on IBM LinuxONE — FSI-hardened RBAC + mTLS + SR governance + audit + Flink layers via Kustomize Components over Mondics's upstream base" matches DESIGN.md's first-paragraph framing of the accelerator; no light alignment needed.
- **No parent-pointer commit in this plan:** Parent-pointer bump is 10-02's atomic operation per the cross_repo_warning. cflt-ai's `git status` correctly shows `modified: raw/repos/fsi-dsp (new commits)` — left unstaged.

## Deviations from Plan

None — plan executed exactly as written.

The locked CONTEXT.md `<decisions>` block was copied verbatim into MANIFEST.yaml. All 5 canon_keys, 5 layer paths, and 3 command strings match the plan spec character-for-character.

---

**Total deviations:** 0
**Impact on plan:** None — single-task plan landed cleanly on first attempt. All success criteria met without auto-fix needed.

## Issues Encountered

None. The submodule was already on `5a86fd2` (detached HEAD from Phase 9), `git fetch origin` was a no-op (already up to date), and `git checkout -b feat/manifest-accelerator-type` from that HEAD landed the branch on the same commit `origin/main` points to — diff vs origin/main shows only the single MANIFEST.yaml change.

## User Setup Required

None — no external service configuration required for this plan. The upstream PR opening (gated on 10-03 human-action) is the only manual step in this phase.

## Next Phase Readiness

**Ready for 10-02:**
- `raw/repos/fsi-dsp/MANIFEST.yaml` on `feat/manifest-accelerator-type` has the locked schema shape — cflt-ai's validator extension can be developed against the on-disk shape and tested against fixtures derived from this entry.
- Parent-pointer diff (`5a86fd2 → b117f3f`) is unstaged in cflt-ai's working tree — 10-02 picks it up alongside the validator commit in a single atomic cflt-ai-side commit.
- `tools/check_manifest.py` (or `check-manifest.py`) needs:
  - Add `"accelerator"` to the type enum
  - Add `accelerator/` to test_ids_have_type_prefix (existing test enforces id-prefix convention)
  - Add apply_sequence required-field + shape validation for `type: accelerator`
  - Add `{build,dry_run,apply}_command` required-string validation for `type: accelerator`

**Ready for 10-03 (gated on 10-02):**
- `feat/manifest-accelerator-type` branch is local-only — no push attempted per cross_repo_warning. 10-03's human-action checkpoint handles upstream push + PR open.

**No blockers.** Phase 10 sequencing on-track: 01 (this plan) → 02 (validator + parent-pointer atomic commit) → 03 (upstream PR open, human-gated).

---
*Phase: 10-accelerator-artifact-type-registration*
*Completed: 2026-05-23*

## Self-Check: PASSED

- FOUND: raw/repos/fsi-dsp/MANIFEST.yaml (modified)
- FOUND: submodule commit b117f3f on feat/manifest-accelerator-type
- FOUND: accelerator/confluent-on-linuxone entry with 5 apply_sequence layers
- FOUND: All 5 canon_keys verbatim
- FOUND: All 3 command strings present
- FOUND: MANIFEST version unchanged at "1.1.0"
- FOUND: cflt-ai parent pointer advance (5a86fd2 → b117f3f) visible in `git diff raw/repos/fsi-dsp`
- FOUND: manifest stability check passes (+1 added, 0 removed)
