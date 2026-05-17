---
phase: H.2-eval-harness-extension
plan: 03
subsystem: testing
tags: [eval-harness, thin-wrapper, trip-wire, agent-skills-schema, hybrid-format]

# Dependency graph
requires:
  - phase: H.2-01
    provides: tests/evals/run_skill_evals.py runner with load_json_cases() adapter — consumes the JSON files authored here
  - phase: H.1-wiki-ingest-agent-skills
    provides: 7 H.1 trip-wires consumed here as verbatim expectations[] strings (4 for /review, 3 for /dsp:plan; the other 2 went to /wiki:ingest in H.2-02)
  - phase: 02-review-skill
    provides: 16 existing /review MD cases (case_ref targets)
  - phase: 03A-act-rail-plan
    provides: 22 /dsp:plan + 10 /dsp:apply existing MD cases (case_ref targets, discriminated by `skill: /dsp:apply` frontmatter)
provides:
  - tests/evals/review/evals.json — 20 cases (16 case_refs + 4 trip-wire cases) for /review skill
  - tests/evals/dsp-plan/evals.json — 25 cases (22 case_refs + 3 trip-wire cases) for /dsp:plan skill
  - tests/evals/dsp-apply/evals.json — 10 cases (10 case_refs, zero trip-wires per D-08) for /dsp:apply skill
  - 7 H.1 trip-wire expectation strings encoded bytewise-verbatim (em-dashes U+2014 preserved)
affects: [H.2-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Thin-wrapper JSON shape: case_ref field references existing MD case stems by filename; runner already accepts the additive field via load_json_cases() (no runner changes needed)"
    - "Trip-wire expectation strings encoded bytewise-verbatim — em-dash (U+2014) and ASCII backticks preserved as grep-targets"
    - "Skill-discrimination by frontmatter on /dsp:plan vs /dsp:apply (filter via grep on `^skill: /dsp:apply`) — same data source, two evals.json wrappers"

key-files:
  created:
    - tests/evals/review/evals.json
    - tests/evals/dsp-plan/evals.json
    - tests/evals/dsp-apply/evals.json
  modified: []

key-decisions:
  - "Boilerplate prompt + boilerplate expectations[] across the case_ref wrapper cases — each case's discriminating power comes from the MD case it references, NOT the wrapper-level fields; this keeps the JSON files mechanically generatable from the MD case enumeration"
  - "Trip-wire cases author concrete prompts (architecture deck, runbook, snippet, code sample) rather than reference MD cases — these are the verbatim-string-presence assertions H.1 trip-wire articles depend on"
  - "ACT-06 no-inline-Terraform constraint surfaced in every wrapper case's expectations to prevent a stealth regression where a future runtime change starts emitting `resource \"confluent_*` blocks"

patterns-established:
  - "Per-skill evals.json thin-wrapper convention: wrapper cases include `case_ref` (the MD stem), `files` (the MD case path), and boilerplate prompt/expectations; standalone trip-wire cases include `prompt` + `expected_output` + verbatim trip-wire string in expectations[]"
  - "Combined H.2-02 + H.2-03 trip-wire distribution honored per D-08: /review=4, /dsp:plan=3, /dsp:apply=0, /wiki:ingest=2 — total 9 of 9 H.1 trip-wires encoded (well above EVAL-03's >=5 floor)"

requirements-completed: [EVAL-02, EVAL-03]

# Metrics
duration: 3min
completed: 2026-05-17
---

# Phase H.2 Plan 03: Eval harness extension — thin wrappers for /review, /dsp:plan, /dsp:apply Summary

Authored 3 thin-wrapper `evals.json` files completing EVAL-02 coverage for the remaining 3/7 named skills and encoding 7 of the 9 H.1 trip-wires as bytewise-verbatim `expectations[]` strings. Combined with H.2-02 (which landed in parallel), the runner's `test_all_seven_new_skills_discovered` gate transitioned RED→GREEN — all 7 required skills (`/review`, `/wiki:ingest`, `/wiki:validate`, `/wiki:lint`, `/wiki:recommend`, `/dsp:plan`, `/dsp:apply`) now have evals.json coverage at the 10-case floor.

## Tasks Completed

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Author tests/evals/review/evals.json (16 case_refs + 4 trip-wires) | c94f1d6 | tests/evals/review/evals.json |
| 2 | Author tests/evals/dsp-plan/evals.json (22 case_refs + 3 trip-wires) | 04d6913 | tests/evals/dsp-plan/evals.json |
| 3 | Author tests/evals/dsp-apply/evals.json (10 case_refs, 0 trip-wires) | a2c96e9 | tests/evals/dsp-apply/evals.json |

## Per-file Case Counts

| File | Target | Actual | Wrapper cases (case_refs) | Trip-wire cases | Notes |
| ---- | ------ | ------ | ------------------------- | --------------- | ----- |
| `tests/evals/review/evals.json` | 20 | 20 | 16 (ids 1..16) | 4 (ids 17..20) | All 16 stems verified resolve to `tests/golden/review/cases/*.md` |
| `tests/evals/dsp-plan/evals.json` | 25 | 25 | 22 (ids 1..22) | 3 (ids 23..25) | All 22 stems verified to have NO `^skill: /dsp:apply` frontmatter |
| `tests/evals/dsp-apply/evals.json` | 10 | 10 | 10 (ids 1..10) | 0 (D-08 distribution) | All 10 stems verified to HAVE `^skill: /dsp:apply` frontmatter |

## Trip-wire Expectation Strings Landed (7 total)

Each string is bytewise-verbatim from CONTEXT.md D-08 specifics — em-dashes (U+2014) preserved.

**`tests/evals/review/evals.json` (4 strings):**

| H.1 trip-wire # | Article | File:Line | Verbatim string (excerpt) |
| --------------- | ------- | --------- | ------------------------- |
| #2 (Tableflow-on-CDC) | `wiki/concepts/cdc-tableflow-flink-decode-required.md` | `tests/evals/review/evals.json:202` | `Flags Tableflow-on-CDC-source-topic claims as a violation — citing the Flink decode pattern as the required mitigation` |
| #9 (EOS-WarpStream) | `wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md` | `tests/evals/review/evals.json:213` | `Flags exactly-once-v2 on WarpStream claims as a throughput-cost violation — citing the 'EOS enables idempotent producers internally' fact` |
| #6 (schema-aware-producer) | `wiki/concepts/schema-aware-console-producer-required.md` | `tests/evals/review/evals.json:224` | `Flags kafka-console-producer usage in verification snippets as a Schema-Registry-incompatible tool — recommends kafka-avro-console-producer` |
| #4 (KS 4.x import) | `wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md` | `tests/evals/review/evals.json:235` | `Flags ` `` `StreamsUncaughtExceptionHandler` `` ` cited as a nested class under ` `` `KafkaStreams` `` ` — corrects to org.apache.kafka.streams.errors import (KS 4.x rename)` |

**`tests/evals/dsp-plan/evals.json` (3 strings):**

| H.1 trip-wire # | Article | File:Line | Verbatim string (excerpt) |
| --------------- | ------- | --------- | ------------------------- |
| #1 (Tableflow-changelog-immutability) | `wiki/concepts/tableflow-changelog-mode-immutability.md` | `tests/evals/dsp-plan/evals.json:274` | `Refuses to plan a Tableflow changelog mode change on an already-materialized topic — directs to delete+recreate per immutability rule` |
| #3 (OracleXStream after.state.only) | `wiki/concepts/oracle-xstream-source-limitations.md` | `tests/evals/dsp-plan/evals.json:285` | ``Refuses to plan OracleXStreamSource with `after.state.only=true` — that config is not supported by Oracle XStream`` |
| #7 (WarpStream SR format) | `wiki/concepts/warpstream-schema-registry-format-constraint.md` | `tests/evals/dsp-plan/evals.json:296` | `Refuses to plan JSON Schema registration against WarpStream's built-in Schema Registry — accepts Avro or Protobuf only` |

## case_ref Resolution Audit

All 48 case_refs resolve to existing MD cases with correct skill attribution:

- **16 /review case_refs** → all files exist under `tests/golden/review/cases/`
- **22 /dsp:plan case_refs** → all files exist under `tests/golden/act/cases/`, none have `^skill: /dsp:apply` frontmatter (correct discrimination)
- **10 /dsp:apply case_refs** → all files exist under `tests/golden/act/cases/`, all have `^skill: /dsp:apply` frontmatter (correct discrimination)

## D-11 Lock Held

`git diff --quiet tools/apply_engine.py .claude/commands/dsp-apply.md` exits 0 — both files byte-identical pre/post. The eval harness is testing infrastructure, NOT a runtime change.

## D-01 Hybrid Lock Held

`git diff --quiet tests/golden/` exits 0 — zero modifications to existing 89 MD cases.

## Runner Gates

After all three tasks landed (alongside H.2-02's 4 wiki-skill files):

- `python -m pytest tests/evals/run_skill_evals.py::test_threshold_per_skill -v` → PASS
- `python -m pytest tests/evals/run_skill_evals.py::test_all_seven_new_skills_discovered -v` → PASS (RED→GREEN transition)
- Full runner: 177 tests pass in 0.10s
- `python -m pytest tests/golden/ -q --tb=no` → 539 passed in 0.71s (existing harnesses unaffected)

## Combined H.2-02 + H.2-03 Trip-wire Coverage

Distribution per D-08:

| Skill | Trip-wires | Plan |
| ----- | ---------- | ---- |
| /review | 4 | H.2-03 |
| /dsp:plan | 3 | H.2-03 |
| /dsp:apply | 0 | (D-08 distribution) |
| /wiki:ingest | 2 | H.2-02 |
| **Total** | **9 of 9 H.1 trip-wires** | EVAL-03 floor (>=5) exceeded by 4 |

## Deviations from Plan

None. Plan executed exactly as written. The three files landed at expected case counts (20/25/10), all 7 trip-wire strings appear bytewise-verbatim with em-dashes preserved, and both locked file sets (D-01 golden cases, D-11 runtime files) remained byte-identical.

## Self-Check: PASSED

- tests/evals/review/evals.json: FOUND
- tests/evals/dsp-plan/evals.json: FOUND
- tests/evals/dsp-apply/evals.json: FOUND
- Commit c94f1d6: FOUND
- Commit 04d6913: FOUND
- Commit a2c96e9: FOUND
- D-11 lock: HELD
- D-01 lock: HELD
- Runner test_threshold_per_skill: PASS
- Runner test_all_seven_new_skills_discovered: PASS (RED→GREEN)
