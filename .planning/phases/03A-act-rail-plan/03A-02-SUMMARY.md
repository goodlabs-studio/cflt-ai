---
phase: 03A-act-rail-plan
plan: 02
subsystem: infra
tags: [canon-parity, act-rail, fsi-dsp, github-actions, skill-file, parity-checker]

requires:
  - phase: 03A-01
    provides: tools/act_gates.py with run_gate_chain() and four-gate chain infrastructure

provides:
  - /dsp:plan skill file with 6-step gate chain invocation, overlay support, read-only Rules section
  - tools/check-canon-parity.py bidirectional drift detector (MODULE_TO_CANON_KEY mapping)
  - tests/test_check_canon_parity.py with 9 unit tests covering parity detection
  - .github/workflows/canon-parity.yml CI workflow blocking merges on canon<->fsi-dsp drift
  - tools/__init__.py updated to register check-canon-parity.py as underscore-importable alias

affects:
  - 03A-03 (golden harness — will invoke /dsp:plan skill)
  - any future phase adding new terraform-modules to fsi-dsp (must update MODULE_TO_CANON_KEY)

tech-stack:
  added: []
  patterns:
    - "MODULE_TO_CANON_KEY: explicit dict mapping terraform-module IDs to canon config keys — no heuristics"
    - "tools/__init__.py importlib registration pattern for hyphen-named modules"
    - "Both-repo CI coverage via submodule pointer: fsi-dsp MANIFEST changes trigger cflt-ai workflow via raw/repos/fsi-dsp/** path filter"
    - "/dsp:plan skill structure mirrors /review.md exactly (6 steps, flag parsing, activity log, provenance footer)"

key-files:
  created:
    - .claude/commands/dsp-plan.md
    - tools/check-canon-parity.py
    - tests/test_check_canon_parity.py
    - .github/workflows/canon-parity.yml
  modified:
    - tools/__init__.py

key-decisions:
  - "/dsp:plan Rules section explicitly names 'NEVER generate inline Terraform resource blocks' — enforces ACT-06 read-only constraint"
  - "MODULE_TO_CANON_KEY is explicit, not heuristic — each new terraform-module requires a conscious decision about which canon config key governs it"
  - "Both-repo CI coverage achieved via submodule pointer: no workflow duplication in fsi-dsp required, raw/repos/fsi-dsp/** path covers MANIFEST changes"
  - "Direction-2 drift (canon key with no module) is warning-only, not blocking — security/producer/consumer keys are cross-cutting and don't require a dedicated module per key"
  - "tools/__init__.py registration pattern (not rename) preserves the CLI entry point filename (check-canon-parity.py) while enabling Python import"

patterns-established:
  - "Skill file pattern: 6 steps (Parse, Load stack, Run gates, Select artifact, Produce plan, Emit log) — matches review.md structure"
  - "Parity checker pattern: check_parity(manifest_path, defaults_path) -> List[str] with empty-list-is-pass convention"
  - "CI workflow pattern: actions/checkout@v4 with submodules: true + pip install pyyaml + python tools/script.py"

requirements-completed: [ACT-04, ACT-06, ACT-08]

duration: 3min
completed: 2026-04-29
---

# Phase 03A Plan 02: /dsp:plan Skill + Canon Parity CI Summary

**/dsp:plan skill with 6-step gate chain, bidirectional canon<->fsi-dsp parity checker (exit 1 on drift), 9 unit tests green, CI workflow blocking merges via both-repo submodule trigger**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-04-29T01:08:59Z
- **Completed:** 2026-04-29T01:12:09Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Delivered `/dsp:plan` skill file with full 6-step structure, flag parsing (`--overlay`, `--gate-bypass`, `--dry-run`), `run_gate_chain()` invocation, `resolve_stack()`/`provenance_footer()` calls, and explicit read-only enforcement in Rules section (ACT-04, ACT-06)
- Built `check-canon-parity.py` with bidirectional drift detection: MANIFEST terraform-modules checked against canon defaults keys (blocking), canon infra keys checked for corresponding modules (warning), exit 1 on any blocking drift (ACT-08)
- 9 unit tests green covering no-drift on current state, missing canon key detection, empty MANIFEST, missing file handling, importability, and MODULE_TO_CANON_KEY integrity
- CI workflow triggers on `canon/**` and `raw/repos/fsi-dsp/**` paths — covers both repos without workflow duplication: cflt-ai canon changes fire directly, fsi-dsp MANIFEST changes fire via submodule pointer update (ACT-08)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create /dsp:plan skill file and canon parity checker with tests** - `72a05ce` (feat)
2. **Task 2: Create GitHub Actions canon-parity CI workflow** - `8ead974` (feat)

## Files Created/Modified

- `.claude/commands/dsp-plan.md` — /dsp:plan skill with Steps 1-6, overlay/gate-bypass flag parsing, read-only Rules section
- `tools/check-canon-parity.py` — bidirectional parity checker; `check_parity()` returns `List[str]` drift items; CLI with `--manifest-path`/`--defaults-path` overrides; exit 1 on drift
- `tests/test_check_canon_parity.py` — 9 unit tests: TestCheckParity (6 tests) + TestParityScript (3 tests)
- `.github/workflows/canon-parity.yml` — CI workflow blocking PRs on drift; submodules: true for MANIFEST access
- `tools/__init__.py` — added importlib registration for `tools.check_canon_parity` (check-canon-parity.py underscore alias)

## Decisions Made

- `/dsp:plan` Rules section explicitly prohibits inline Terraform and mcp-confluent write tools — enforces ACT-06 read-only constraint even when gates pass
- `MODULE_TO_CANON_KEY` mapping is explicit (not heuristic): each new terraform-module must be added to this dict with a conscious canon key assignment; unknown modules produce a DRIFT-1 blocking violation
- Both-repo CI coverage via submodule pointer: no workflow duplication in fsi-dsp, `raw/repos/fsi-dsp/**` path filter catches MANIFEST changes
- Direction-2 warnings (canon key without a module) are non-blocking — security, producer, consumer, etc. are cross-cutting and exempt from "must have a module" enforcement
- `tools/__init__.py` importlib pattern preserves CLI filename while enabling `from tools.check_canon_parity import check_parity` — consistent with existing `review_to_docx` registration

## Deviations from Plan

None — plan executed exactly as written. One minor note: the plan's verification command used `wf['on']` to assert CI paths, but PyYAML parses the `on` keyword as boolean `True`. The workflow YAML is structurally correct and GitHub Actions processes it correctly at runtime. The verification was run with the correct `wf[True]` key and passed.

## Issues Encountered

None. All verification passed on first run.

## Next Phase Readiness

- `/dsp:plan` skill is available for golden harness testing in 03A-03
- Parity CI will enforce drift prevention across both repos automatically
- MODULE_TO_CANON_KEY will need updating if new terraform-modules are added to fsi-dsp

---
*Phase: 03A-act-rail-plan*
*Completed: 2026-04-29*
