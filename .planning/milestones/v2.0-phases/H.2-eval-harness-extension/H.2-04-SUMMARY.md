---
phase: H.2-eval-harness-extension
plan: 04
subsystem: ci
tags: [github-actions, ci, eval-harness, structural-only, phase-exit-gate]

# Dependency graph
requires:
  - phase: H.2-01
    provides: tests/evals/run_skill_evals.py + test_runner_adapters.py (the targets of the workflow's pytest invocations)
  - phase: H.2-02
    provides: 4 wiki-skill evals.json files (40 cases, 2 trip-wires) — consumed by the runner the workflow invokes
  - phase: H.2-03
    provides: 3 thin-wrapper evals.json files (55 cases, 7 trip-wires) — consumed by the runner the workflow invokes
  - phase: G.2c-tool-classification-rename
    provides: tool-classification-drift.yml workflow shape — copied verbatim (paths-scoped pull_request + push:main, Python 3.12)
provides:
  - .github/workflows/skill-evals.yml — GitHub Actions workflow gating PRs at the 90%-per-skill threshold via pytest exit code
  - Three split pytest invocations in CI for triage clarity (runner gate, adapter regression, golden D-01 hybrid regression)
  - Phase H.2 exit: EVAL-01, EVAL-02, EVAL-03 all satisfied
affects: []

# Tech tracking
tech-stack:
  added: []  # no new dependencies introduced in CI (uses ubuntu-latest stock + pip install pytest pyyaml)
  patterns:
    - "Paths-scoped GitHub Actions trigger (pull_request + push:main) — fires only when tests/evals, tests/golden, wiki, .claude/commands, tools, or the workflow file itself changes"
    - "Three split pytest invocations as distinct workflow steps — failures in adapter-tests vs threshold-gate vs golden-regression surface separately in the GitHub UI"
    - "Threshold enforcement inside pytest (test_threshold_per_skill assertion), NOT as a separate workflow gate — D-06 lives in one tested code path"
    - "Zero secrets, zero model SDKs — D-04 structural-only lock surfaces as workflow shape (no env:, no secrets.)"

key-files:
  created:
    - .github/workflows/skill-evals.yml
  modified: []

key-decisions:
  - "Three pytest invocations split into distinct workflow steps (runner / adapters / golden) — failure-attribution in the GitHub UI is worth the marginal YAML"
  - "Path filter includes .github/workflows/skill-evals.yml itself so workflow tweaks get exercised in PR (consistent with tool-classification-drift.yml)"
  - "No --strict, no -x, no fail-fast — collect all failures so a single PR sees all bad skills at once"
  - "No live model API calls, no env: section, no secrets reference — D-04 structural-only is enforced architecturally in the runner and visible structurally in the workflow"

patterns-established:
  - "Phase H.2 exit pattern: structural verification commands chained via && for atomic pass/fail signal — 10 commands covering workflow validity, file presence, case counts, runner gates, regression gates, locks, trip-wires, and D-04 absence"

requirements-completed: [EVAL-03]

# Metrics
duration: 2min
completed: 2026-05-17
---

# Phase H.2 Plan 04: CI Workflow — Skill Evals Gate Summary

`.github/workflows/skill-evals.yml` lands as the phase-exit gate — runs the unified pytest harness on PRs (paths-scoped) and main pushes, fails CI via pytest exit code when any skill drops below 90% (D-06 enforced inside `test_threshold_per_skill`), and surfaces runner-regression vs threshold-gate vs golden-harness-regression as three distinct GitHub Actions steps for clean triage.

## Performance

- **Duration:** 2 min
- **Started:** 2026-05-17T16:03:56Z
- **Completed:** 2026-05-17T16:05:42Z
- **Tasks:** 2 (one authoring, one verification-only)
- **Files created:** 1
- **Files modified:** 0

## Workflow File Shape

The single artifact, `.github/workflows/skill-evals.yml`, has this structure:

| Step | Purpose |
|------|---------|
| 1. `actions/checkout@v4` | Standard repo checkout |
| 2. `actions/setup-python@v5` with `python-version: '3.12'` | Matches `tool-classification-drift.yml` toolchain |
| 3. `pip install pytest pyyaml` | Only harness deps — no model SDKs (D-04) |
| 4. `python -m pytest tests/evals/run_skill_evals.py -v` | Main D-06 90% threshold gate |
| 5. `python -m pytest tests/evals/test_runner_adapters.py -v` | Adapter regression gate (Plan 01) |
| 6. `python -m pytest tests/golden/ -v --tb=short` | D-01 hybrid regression gate (89 existing MD cases) |

Triggers:
- `pull_request` paths-scoped to `tests/evals/**, tests/golden/**, wiki/**, .claude/commands/**, tools/**, .github/workflows/skill-evals.yml`
- `push: branches: [main]` with the same paths filter

## Task Commits

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Author `.github/workflows/skill-evals.yml` | `d2d05f6` |
| 2 | Final phase-exit regression gate verification (no files modified) | (verification-only — no commit) |

## Verification Results (Task 2 — All 10 Commands PASS)

Run against the live tree on 2026-05-17:

| # | Command | Result |
|---|---------|--------|
| 1 | `python -c "import yaml; d = yaml.safe_load(open('.github/workflows/skill-evals.yml')); print(d['name'], '-', len(d['jobs']['evals']['steps']), 'steps')"` | `Skill Evals - 6 steps` |
| 2 | Per-skill case counts (≥10 floor) | wiki-ingest=10, wiki-validate=10, wiki-lint=10, wiki-recommend=10, review=20, dsp-plan=25, dsp-apply=10 — **ALL ≥10** |
| 3 | `pytest tests/evals/run_skill_evals.py::test_threshold_per_skill -v` | **PASS** (1 passed in 0.05s) |
| 4 | `pytest tests/evals/run_skill_evals.py::test_all_seven_new_skills_discovered -v` | **PASS** (RED→GREEN transition complete) |
| 5 | `pytest tests/evals/test_runner_adapters.py -v` | **PASS** (9 passed in 0.20s) |
| 6 | `pytest tests/golden/ -q --tb=no` | **PASS** (539 passed in 0.70s) |
| 7 | `git diff --quiet tools/apply_engine.py .claude/commands/dsp-apply.md` | **exit 0** — D-11 byte-identical |
| 8 | `git diff --stat v1.0..HEAD -- tests/golden/` | **empty** — zero modifications since v1.0 |
| 9 | All 9 trip-wire greps return expected counts | **9/9 confirmed** (see roll-up below) |
| 10 | `grep -rE "(subprocess\|requests\|anthropic\|openai\|httpx\|ANTHROPIC_API\|OPENAI_API)" tests/evals/ .github/workflows/skill-evals.yml` (minus fixtures + the docstring saying "never run a subprocess") | **0 substantive matches** — D-04 holds |

The single surface-level grep hit on line 7 of `tests/evals/test_runner_adapters.py` is the docstring asserting the D-04 lock ("never run a subprocess") — a meta-reference, not a usage.

Full chained verify (the plan's `<automated>` block) terminated with `PHASE-EXIT: OK`.

## RED→GREEN Transition Confirmed

`tests/evals/run_skill_evals.py::test_all_seven_new_skills_discovered` traced this trajectory:

| Plan | State | Why |
|------|-------|-----|
| H.2-01 | RED | Runner authored; zero evals.json files yet |
| H.2-02 | RED (partial green) | 4 of 7 skills landed (wiki-ingest, wiki-validate, wiki-lint, wiki-recommend) |
| H.2-03 | GREEN | All 7 skills landed (added review, dsp-plan, dsp-apply thin wrappers) |
| H.2-04 | GREEN (held) | CI workflow now wires this assertion into every PR check |

The RED-in-Plan-01 / GREEN-by-Plan-03 transition was a deliberate scaffolded coverage gate, documented in H.2-01-SUMMARY decisions #3. Plan 04 simply locks it into CI.

## Trip-Wire Roll-Up — All 9 H.1 Trip-Wires Encoded Verbatim

Each string is bytewise-verbatim from CONTEXT.md D-08, em-dashes (U+2014) and ASCII backticks preserved.

| # | H.1 trip-wire | Skill | File:Line | grep count |
|---|---------------|-------|-----------|------------|
| 5 | `avro-schema-source-directory` | `/wiki:ingest` | `tests/evals/wiki-ingest/evals.json:22` | 1 |
| 8 | `warpstream-config-overrides` | `/wiki:ingest` | `tests/evals/wiki-ingest/evals.json:33` | 1 |
| 2 | `cdc-tableflow-flink-decode-required` | `/review` | `tests/evals/review/evals.json:202` | 1 |
| 9 | `exactly-once-v2-warpstream-throughput-cost` | `/review` | `tests/evals/review/evals.json:213` | 1 |
| 6 | `schema-aware-console-producer-required` | `/review` | `tests/evals/review/evals.json:224` | 1 |
| 4 | `kafka-streams-4x-uncaught-exception-handler-import` | `/review` | `tests/evals/review/evals.json:235` | 1 |
| 1 | `tableflow-changelog-mode-immutability` | `/dsp:plan` | `tests/evals/dsp-plan/evals.json:274` | 1 |
| 3 | `oracle-xstream-source-limitations` | `/dsp:plan` | `tests/evals/dsp-plan/evals.json:285` | 1 |
| 7 | `warpstream-schema-registry-format-constraint` | `/dsp:plan` | `tests/evals/dsp-plan/evals.json:296` | 1 |

Total: 9 of 9 H.1 trip-wires encoded. EVAL-03 floor is ≥5 — exceeded by 4 (180% of floor).

Distribution per D-08: /review=4, /dsp:plan=3, /wiki:ingest=2, /dsp:apply=0 (D-08 explicit allocation). Sum = 9.

## Per-Skill Case Count Roll-Up (MD + JSON Combined)

| Skill | MD cases (existing) | JSON cases (new) | Total |
|-------|---------------------|------------------|-------|
| `/ask` | 32 | — | 32 |
| `/review` | 16 | 20 (16 case_refs + 4 trip-wires) | 36 |
| `/dsp:plan` | 22 | 25 (22 case_refs + 3 trip-wires) | 47 |
| `/dsp:apply` | 10 | 10 (10 case_refs, 0 trip-wires) | 20 |
| `/wiki:ingest` | — | 10 (8 happy/edge + 2 trip-wires) | 10 |
| `/wiki:validate` | — | 10 | 10 |
| `/wiki:lint` | — | 10 | 10 |
| `/wiki:recommend` | — | 10 | 10 |
| **TOTAL** | **80** | **95** | **175 cases** |

The runner discovers all 175 (plus a parametrized `test_case_well_formed` per case), totalling **177 runner tests** (175 parametrized + 1 threshold + 1 coverage). All 177 pass in 0.09s.

The existing `tests/golden/` harnesses (a parallel pytest tree, not duplicated by the new runner) contribute another 539 passing tests on their own runners — also exercised by step 6 of the workflow as the D-01 hybrid regression gate.

## Lock Status — All Three Phase-Level Locks Held

| Lock | Decision | Status |
|------|----------|--------|
| D-01 hybrid | `tests/golden/` byte-identical from milestone start (v1.0..HEAD) | **HELD** — `git diff --stat v1.0..HEAD -- tests/golden/` returns empty |
| D-04 structural-only | No subprocess/requests/anthropic/openai/httpx/model-SDK in tests/evals/ or skill-evals.yml | **HELD** — zero substantive matches (1 docstring meta-reference excluded) |
| D-11 byte-identical runtime | `tools/apply_engine.py` + `.claude/commands/dsp-apply.md` unchanged | **HELD** — `git diff --quiet` exits 0 |

## Phase H.2 Exit — All 5 ROADMAP Success Criteria Met

1. ✅ `evals/evals.json` exists for each of `/review`, `/wiki:ingest`, `/wiki:validate`, `/wiki:lint`, `/wiki:recommend`, `/dsp:plan`, `/dsp:apply` (Plans 02 + 03)
2. ✅ ≥10 cases per skill — actually 10/10/10/10/20/25/10 = **105 evals.json cases** across 7 files (Plans 02 + 03)
3. ✅ pytest-based runner at `tests/evals/run_skill_evals.py` reports pass rate per skill (Plan 01)
4. ✅ `.github/workflows/skill-evals.yml` gates PRs at 90% (THIS PLAN — via pytest exit code from `test_threshold_per_skill`)
5. ✅ ≥5 trip-wires encoded as `expectations[]` — actually **9 trip-wires** (Plans 02 + 03)

## Requirements Closed

- **EVAL-03 (this plan):** CI workflow gates PRs at the 90%-per-skill threshold. Failure path: pytest fails → workflow non-zero exit → PR blocked. Threshold logic centralized in `test_threshold_per_skill`, not duplicated in workflow YAML.
- **EVAL-01 (re-affirmed):** runner exists at `tests/evals/run_skill_evals.py`, exercised by step 4 of the workflow on every PR + main push.
- **EVAL-02 (re-affirmed):** all 7 named-skill evals.json files exist with ≥10 cases each, exercised structurally by step 4's parametrize and coverage gate.

## Deviations from Plan

None. Plan executed exactly as written. Task 1 created the workflow file with the verbatim content the plan specified; Task 2's 10 verification commands all returned expected output on first run.

## Deferred Work Surfacing

From CONTEXT.md `<deferred>` — nothing surfaced as worth promoting in this plan. The four deferred items remain deferred:

- **LLM-as-judge in CI** — still deferred per D-04/D-05. No real model-floor regressions surfaced during H.2 execution.
- **Per-skill threshold tuning** — D-06's 90% uniform held across all 7 skills with margin. No skill-specific tuning needed.
- **Coverage reporting (pytest-html etc.)** — `-v` flag's per-test output in GitHub Actions logs is sufficient for triage; no separate artifact justified yet.
- **Floor-model tiering on JSON cases** — D-07 keeps these floor-agnostic. No regressions surfaced to suggest tiering is needed.

## Issues Encountered

None. The plan's `<automated>` verify block passed on first run with no fixes required. The Task 2 verification surfaced one cosmetic note worth recording: PyYAML parses the YAML key `on:` as Python `True` (a known PyYAML behavior — `on/off` are YAML 1.1 booleans). The verification check accounted for this by accepting either key form. This is not a workflow bug — GitHub Actions parses YAML 1.2 where `on:` is a string key. No fix needed.

## User Setup Required

None — CI infrastructure. The workflow will fire automatically on the next PR or push to main that touches the paths-scoped trees. First fire will be when this very plan's commits hit a PR (or are merged to main, since the workflow file itself is in the path filter).

## Self-Check

- `.github/workflows/skill-evals.yml` — FOUND
- `tests/evals/wiki-ingest/evals.json` — FOUND (unchanged)
- `tests/evals/wiki-validate/evals.json` — FOUND (unchanged)
- `tests/evals/wiki-lint/evals.json` — FOUND (unchanged)
- `tests/evals/wiki-recommend/evals.json` — FOUND (unchanged)
- `tests/evals/review/evals.json` — FOUND (unchanged)
- `tests/evals/dsp-plan/evals.json` — FOUND (unchanged)
- `tests/evals/dsp-apply/evals.json` — FOUND (unchanged)
- Commit `d2d05f6` (Task 1) — FOUND in `git log`
- `pytest tests/evals/run_skill_evals.py -v` — 177 passed in 0.09s
- `pytest tests/golden/ -q --tb=no` — 539 passed in 0.70s
- `git diff --quiet tools/apply_engine.py .claude/commands/dsp-apply.md` — exit 0
- All 9 trip-wire grep counts — confirmed

## Self-Check: PASSED

---
*Phase: H.2-eval-harness-extension*
*Completed: 2026-05-17*
