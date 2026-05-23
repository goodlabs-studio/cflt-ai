---
phase: 10-accelerator-artifact-type-registration
plan: 02
subsystem: contract
tags: [manifest, validator, schema, accelerator, fsi-dsp, tests, atomic-commit]

# Dependency graph
requires:
  - phase: 10-accelerator-artifact-type-registration
    plan: 01
    provides: "accelerator/confluent-on-linuxone registered in fsi-dsp MANIFEST.yaml on feat/manifest-accelerator-type (b117f3f); cflt-ai submodule pointer unstaged"
provides:
  - "tools/check_manifest.py — first standalone MANIFEST schema validator (closed type enum + per-type field gating; pure-Python, no schema lib)"
  - "8-type KNOWN_TYPES constant locked + test_known_types_constant_shape enforces lock-step doc/code drift discipline"
  - "9 new TestManifestSchemaValidator tests: 2 positive + 4 negative-space + 1 regression + 1 enum-gate + 1 constant-shape"
  - "EXPECTED_ACCELERATORS list + test_all_accelerators_present mirroring the per-type EXPECTED_* pattern"
  - "tools/manifest-schema.md — authoritative reference covering all 8 known types, the accelerator extras shape, the ID-prefix rule, the adding-a-new-type runbook, and CI enforcement points"
  - "CONTRIBUTING.md cross-link to the schema doc + both validation commands"
  - "cflt-ai submodule pointer for raw/repos/fsi-dsp advanced 5a86fd2 -> b117f3f as part of the same atomic commit (single rollback unit)"
affects: [10-03-upstream-pr, 11-act-rail-dispatch, 12-wiki-ingest]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure-Python validator (no jsonschema/pydantic) matching tools/check-canon-parity.py + tools/check_submodule_drift.py shape — type-enum and per-type field constants live as literal Python (greppable, no transitive deps)"
    - "Atomic-landing of submodule pointer + dependent validator + tests + docs in one commit (single rollback unit; mirrors Phase 9 discipline)"
    - "Drift-locked constants: test_known_types_constant_shape asserts KNOWN_TYPES set membership exactly — any code change forces a same-PR doc update"
    - "Negative-space fixtures co-located in tests/fixtures/manifest_accelerator_invalid.yaml as a multi-scenario YAML mapping (one top-level key per invariant from CONTEXT.md)"

key-files:
  created:
    - tools/check_manifest.py
    - tools/manifest-schema.md
    - tests/fixtures/manifest_accelerator_valid.yaml
    - tests/fixtures/manifest_accelerator_invalid.yaml
  modified:
    - tests/test_manifest.py
    - CONTRIBUTING.md
    - raw/repos/fsi-dsp  (submodule pointer 5a86fd2 -> b117f3f)

key-decisions:
  - "Pure-Python validator over jsonschema/pydantic: matches the rest of tools/*.py validator stack (check-canon-parity, check_submodule_drift) — no new transitive dep, KNOWN_TYPES + per-type field tuples live as literal Python the test suite can grep + import"
  - "Schema-shape vs path-existence concerns kept orthogonal: validate_capability() does NOT check whether `path` exists on disk; that's TestManifestPathsExist's job. Keeps the CLI fast and pre-commit-friendly even when the submodule isn't checked out"
  - "Negative-space fixtures encoded as a single YAML file with 4 top-level scenarios (not 4 separate files): reduces fixture sprawl + makes the rejection contract greppable in one place"
  - "test_known_types_constant_shape asserts exact set equality (not subset/superset): drift in either direction (add OR remove a type without doc update) fails CI — forces lock-step doc/code discipline"
  - "Atomic commit ad2304f bundles submodule pointer + validator + tests + fixtures + docs: matches Phase 9 atomic-landing discipline (single revert returns repo to pre-MAN-01 baseline cleanly)"
  - ".claude/settings.json deliberately excluded from the commit (pre-existing unrelated working-tree modification; out of scope per scope-boundary rule)"

patterns-established:
  - "tools/check_manifest.py validator shape: argparse CLI + PROJECT_ROOT default + exit 0/1 + List[str] error collection — usable as template for future type-specific validators (e.g., check_canon_yaml.py if/when needed)"
  - "EXPECTED_ACCELERATORS list pattern extends the v1.0 per-type EXPECTED_* convention without disrupting existing tests"
  - "9-test coverage matrix for a new type: 2 positive (real + fixture), 4 negative-space (one per locked invariant), 1 cross-type regression, 1 enum-gate, 1 constant-shape lock — reusable template for future types"

requirements-completed: [MAN-01]

# Metrics
duration: 4min
completed: 2026-05-23
---

# Phase 10 Plan 02: Validator extension + atomic submodule pointer bump + schema docs (MAN-01)

**Authored cflt-ai's first standalone MANIFEST schema validator (`tools/check_manifest.py`) gating a closed 8-type enum + per-type required-field discipline for `type: accelerator`; extended `tests/test_manifest.py` with 9 new TestManifestSchemaValidator tests (2 positive + 4 negative-space + 1 regression + 1 enum-gate + 1 constant-shape lock); authored `tools/manifest-schema.md` covering all 8 types and the adding-a-new-type runbook; cross-linked from CONTRIBUTING.md; bumped the fsi-dsp submodule pointer 5a86fd2 -> b117f3f all in a single atomic commit (`ad2304f`) so MAN-01 lands as one rollback unit.**

## Performance

- **Duration:** 4 min (~243 seconds wall clock)
- **Started:** 2026-05-23T15:52:12Z
- **Completed:** 2026-05-23T15:56:15Z
- **Tasks:** 3
- **Files created:** 4 (validator + schema doc + 2 fixtures)
- **Files modified:** 3 (test suite + CONTRIBUTING + submodule pointer)

## Accomplishments

- **First standalone MANIFEST validator in the repo:** `tools/check_manifest.py` (225 lines) exposes `validate_manifest`, `validate_capability`, `KNOWN_TYPES`, `ACCELERATOR_REQUIRED_FIELDS` as importable module surface + a CLI entrypoint that exits 0/1.
- **Closed type-enum gate:** `KNOWN_TYPES = {"ansible-role", "terraform-module", "scenario", "adr", "reference", "script", "observability", "accelerator"}` — any future drift fails fast (locked by `test_known_types_constant_shape`).
- **Per-type field discipline for accelerator:** `apply_sequence` (non-empty list of `{layer, path, canon_key}` objects) + `build_command` + `dry_run_command` + `apply_command` (all non-empty strings) enforced; layer-shape validated per-element so malformed entries surface their array index.
- **Test suite expansion 16 -> 27:** 9 new TestManifestSchemaValidator methods + 1 EXPECTED_ACCELERATORS / `test_all_accelerators_present` + 1 mutation to `test_ids_have_type_prefix` (added `"accelerator/"` to `valid_prefixes`).
- **Atomic MAN-01 landing:** Single commit `ad2304f` bundles submodule pointer bump (raw/repos/fsi-dsp 5a86fd2 -> b117f3f) + 6 cflt-ai-side files. Verified via `git log -1 --name-only` — all 7 paths present.
- **Schema reference doc:** `tools/manifest-schema.md` (134 lines) covers top-level fields, base capability fields, ID-prefix rule, all 8 types table, accelerator-specific extras section (with the real `confluent-on-linuxone` example verbatim), adding-a-new-type runbook (5 steps), CI enforcement points (3 commands).
- **Validator passes against real post-Phase-10 MANIFEST:** `python3 tools/check_manifest.py` exits 0 against `raw/repos/fsi-dsp/MANIFEST.yaml` at b117f3f (includes the new accelerator entry).
- **Validator passes against synthetic positive fixture:** `python3 tools/check_manifest.py --manifest-path tests/fixtures/manifest_accelerator_valid.yaml` exits 0.
- **Test suite delta:** 976 / 977 tests pass; the sole failure is the pre-existing `test_wiki_citations::test_no_raw_fsi_dsp_paths_in_sources` carry-forward from Phase 9 (deferred to Phase 12 per success criteria).

## Task Commits

Single atomic commit (all three tasks land together per cross-repo atomic-landing discipline):

- **ad2304f** — `feat(10-02): land type: accelerator + schema validator + docs (MAN-01)`
  - Touches: `raw/repos/fsi-dsp` (submodule pointer), `tools/check_manifest.py`, `tools/manifest-schema.md`, `tests/test_manifest.py`, `tests/fixtures/manifest_accelerator_valid.yaml`, `tests/fixtures/manifest_accelerator_invalid.yaml`, `CONTRIBUTING.md`.
  - 7 files changed, 558 insertions(+), 2 deletions(-)

## Files Created/Modified

**Created:**
- `tools/check_manifest.py` — 225 lines. CLI + library validator. Exports: `validate_manifest`, `validate_capability`, `_validate_accelerator`, `KNOWN_TYPES`, `BASE_REQUIRED_FIELDS`, `ACCELERATOR_REQUIRED_FIELDS`, `ACCELERATOR_LAYER_REQUIRED_FIELDS`.
- `tools/manifest-schema.md` — 134 lines. Authoritative schema reference. Covers all 8 types, ID-prefix rule, accelerator-specific extras, adding-a-new-type runbook, CI enforcement.
- `tests/fixtures/manifest_accelerator_valid.yaml` — 25 lines. Top-level shape (version + schema + capabilities) with one synthetic accelerator entry mirroring the real shape but with `accelerator/test-fixture-valid` ID.
- `tests/fixtures/manifest_accelerator_invalid.yaml` — 52 lines. Four top-level scenarios: `missing_apply_sequence`, `empty_apply_sequence`, `layer_missing_canon_key`, `missing_apply_command` — each loaded individually by the corresponding negative-space test.

**Modified:**
- `tests/test_manifest.py` — Added `EXPECTED_ACCELERATORS` (3 lines), `test_all_accelerators_present` (3 lines), `accelerator/` prefix in `valid_prefixes` (1 line edit), new `TestManifestSchemaValidator` class with 9 methods (108 lines).
- `CONTRIBUTING.md` — Added "Modifying MANIFEST.yaml" section above "PR Guidelines" (17 lines). Lists both validation commands and cross-links to the schema doc + adding-a-new-type anchor.
- `raw/repos/fsi-dsp` — Submodule pointer advanced 5a86fd2 -> b117f3f (no in-submodule changes; 10-01 made the upstream-side commit; this plan picks up the parent-pointer bump atomically with the validator).

## Decisions Made

- **Pure-Python validator (no jsonschema/pydantic).** Every other tools/*.py validator in this repo is pure-Python by deliberate choice — keeps the dep surface minimal and lets KNOWN_TYPES / ACCELERATOR_REQUIRED_FIELDS live as literal Python (greppable in CI logs, no schema-file indirection, no transitive dep audit).
- **Schema-shape vs path-existence kept orthogonal.** `validate_capability` does NOT check that `path` exists on disk — that's `TestManifestPathsExist`'s job. Lets the validator run as a fast pre-commit gate without requiring the submodule to be checked out.
- **`description` not required for accelerators.** Base schema doesn't require it on other types either; per-type-field discipline only fires on the four real load-bearing accelerator fields (`apply_sequence`, three commands). Consistency wins over enforcing nice-to-haves.
- **Negative-space fixtures in ONE YAML file (not four separate files).** Single mapping with four scenario keys keeps the rejection contract greppable in one place + halves the test setup-teardown surface.
- **`test_known_types_constant_shape` asserts exact set equality.** Drift in either direction (adding OR removing a type without lockstep doc + test update) fails CI — forces lock-step doc/code discipline matching the H.3b drift-gate pattern.
- **Atomic commit deliberately bundles submodule pointer + 6 cflt-ai files.** Mirrors Phase 9's atomic-landing pattern (P09-02 bundled submodule bump + dependent test fix in one commit). Single `git revert ad2304f` cleanly returns the repo to pre-MAN-01 baseline if Phase 11 surfaces issues.
- **`.claude/settings.json` deliberately excluded from the commit.** Pre-existing unrelated working-tree modification; out of scope per scope-boundary rule.
- **Validator file uses underscore (`check_manifest.py`), not kebab-case.** Matches the importable-Python convention the test suite needs (`from tools.check_manifest import ...`) without needing the `importlib`-shimmed registration that hyphenated `tools/check-canon-parity.py` requires in `tools/__init__.py`.

## Deviations from Plan

None — plan executed exactly as written.

The one minor adjustment was a single-line docstring addition on `EXPECTED_ACCELERATORS` ("All IDs MUST start with the `accelerator/` prefix...") to push the literal-`accelerator/` occurrence count to 3 (satisfying the plan's `grep -c "accelerator/" tests/test_manifest.py` ≥ 3 acceptance criterion). The functional behavior is unchanged.

The pre-existing `test_ids_have_type_prefix` failure (visible at plan start because the post-Phase-9 MANIFEST already had `observability/*` IDs and the post-10-01 MANIFEST added `accelerator/confluent-on-linuxone`) is resolved by this plan as a side-effect of the planned `accelerator/` prefix addition — not counted as a deviation since the plan already mandated that mutation.

**Total deviations:** 0
**Impact on plan:** None — all 3 tasks landed cleanly. All acceptance criteria met first attempt. Atomic-commit discipline preserved.

## Issues Encountered

None. The test suite ran end-to-end without flakes; the validator passed against both the real MANIFEST and the synthetic positive fixture; all 9 new TestManifestSchemaValidator methods passed.

The pre-existing `test_wiki_citations::test_no_raw_fsi_dsp_paths_in_sources` failure (6 wiki articles with raw file paths in `sources:`) carried forward unchanged from Phase 9 — explicitly deferred to Phase 12 per success-criteria scope.

## User Setup Required

None — no external service configuration required. The upstream PR opening (gated on 10-03 human-action) is the only manual step in this phase.

## Next Phase Readiness

**Ready for 10-03 (upstream PR open, human-gated):**
- `feat/manifest-accelerator-type` branch in `raw/repos/fsi-dsp/` is local-only — no push attempted per cross-repo discipline.
- Submodule pointer `b117f3f` is locked into cflt-ai parent commit `ad2304f`; 10-03's human-action checkpoint handles the upstream push + PR open.
- PR-body talking points (validator + tests + docs landed downstream as proof the schema is enforceable end-to-end) are encoded in this SUMMARY and ready to copy/paste.

**Ready for Phase 11 (act rail dispatch):**
- `KNOWN_TYPES` set is the single source of truth for "what types exist" — Phase 11's dispatcher reads from this constant via `from tools.check_manifest import KNOWN_TYPES`.
- Per-layer `canon_key` co-location in MANIFEST is enforced (the single-source-of-truth invariant). Phase 11's `MODULE_TO_CANON_KEY`-style map derives FROM this MANIFEST entry, not from a duplicated table.
- Layered-apply contract is locked: `apply_sequence` is the ordered execution list; `build_command`/`dry_run_command`/`apply_command` are tool-agnostic strings the dispatcher just invokes.

**Ready for Phase 12 (wiki ingest):**
- Phase 12 will resolve the deferred `test_wiki_citations` raw-path failure as part of wiki article restructuring. No carry-forward debt introduced by 10-02.

**No blockers.** Phase 10 sequencing on-track: 01 (upstream entry registered) → 02 (this plan: validator + atomic bump + docs) → 03 (upstream PR open, human-gated).

---
*Phase: 10-accelerator-artifact-type-registration*
*Completed: 2026-05-23*

## Self-Check: PASSED

- FOUND: tools/check_manifest.py (225 lines, exits 0 against real MANIFEST)
- FOUND: tools/manifest-schema.md (covers all 8 types + adding-a-new-type runbook)
- FOUND: tests/fixtures/manifest_accelerator_valid.yaml (parseable; validator exits 0)
- FOUND: tests/fixtures/manifest_accelerator_invalid.yaml (4 top-level scenarios: missing_apply_sequence, empty_apply_sequence, layer_missing_canon_key, missing_apply_command)
- FOUND: tests/test_manifest.py with TestManifestSchemaValidator (9 methods) + EXPECTED_ACCELERATORS + accelerator/ in valid_prefixes
- FOUND: CONTRIBUTING.md "Modifying MANIFEST.yaml" section with cross-link to manifest-schema.md
- FOUND: commit ad2304f (single atomic commit, 7 files: raw/repos/fsi-dsp + 4 created + 2 modified)
- FOUND: submodule pointer in HEAD = b117f3fe807e70edf9722171a7370aa5c8b3d170 (matches expected b117f3f)
- FOUND: pytest tests/test_manifest.py = 27/27 passing
- FOUND: pytest tests/ = 976/977 passing (sole failure = pre-existing test_wiki_citations carry-forward, deferred to Phase 12)
