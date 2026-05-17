---
phase: H.2-eval-harness-extension
plan: 04
type: execute
wave: 3
depends_on: [H.2-01, H.2-02, H.2-03]
files_modified:
  - .github/workflows/skill-evals.yml
autonomous: true
requirements: [EVAL-03]
requirements_addressed: [EVAL-03]

must_haves:
  truths:
    - "`.github/workflows/skill-evals.yml` exists and runs the harness on pull_request and push to main"
    - "Workflow triggers are paths-scoped to tests/evals/**, tests/golden/**, wiki/**, .claude/commands/**, tools/**"
    - "Workflow fails the PR (non-zero exit) when any skill drops below 90% pass rate — enforcement happens inside pytest, not as a separate CI gate"
    - "Existing tests/golden/ harnesses continue to pass — final regression gate"
    - "All 9 H.1 trip-wires are encoded across the 7 JSON files (4 in /review, 3 in /dsp:plan, 2 in /wiki:ingest) — well above EVAL-03 ≥5 floor"
    - "tools/apply_engine.py and .claude/commands/dsp-apply.md remain byte-identical from milestone start (D-11)"
  artifacts:
    - path: ".github/workflows/skill-evals.yml"
      provides: "GitHub Actions workflow that runs the unified eval harness on PR and main pushes"
      contains: ["pull_request", "tests/evals", "python -m pytest"]
  key_links:
    - from: ".github/workflows/skill-evals.yml"
      to: "tests/evals/run_skill_evals.py"
      via: "pytest invocation — `python -m pytest tests/evals/run_skill_evals.py -v`"
      pattern: "pytest tests/evals/run_skill_evals.py"
    - from: ".github/workflows/skill-evals.yml"
      to: "tests/evals/*/evals.json"
      via: "paths-scoped trigger — workflow fires when any eval file changes"
      pattern: "tests/evals/\\*\\*"
---

<objective>
Land the CI workflow that runs the unified eval harness on every PR and main-branch push. The 90% per-skill threshold is enforced inside `test_threshold_per_skill()` (Plan 01) — so CI fails because pytest fails, NOT via a separate gate logic in the workflow YAML (D-06/D-09 lock).

Mirrors the existing `.github/workflows/tool-classification-drift.yml` shape from G.2c: paths-scoped triggers + setup-python 3.12 + a single pytest run.

After this plan: EVAL-03 is fully satisfied. All 9 H.1 trip-wires are encoded across the 7 evals.json files (4 + 3 + 2 = 9, well above the ≥5 floor). The phase exit criteria from ROADMAP.md success criteria are met:
1. ✅ evals/evals.json exists for each of /review, /wiki:ingest, /wiki:validate, /wiki:lint, /wiki:recommend, /dsp:plan, /dsp:apply (Plans 02 + 03)
2. ✅ ≥10 cases per skill (Plans 02 + 03)
3. ✅ pytest-based runner at tests/evals/run_skill_evals.py reports pass rate per skill (Plan 01)
4. ✅ .github/workflows/skill-evals.yml gates PRs at 90% (THIS PLAN)
5. ✅ ≥5 trip-wires encoded as expectations[] (actually 9 — Plans 02 + 03)

Output: `.github/workflows/skill-evals.yml` only. No changes to runner, no changes to evals.json files, no changes to runtime.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/H.2-eval-harness-extension/H.2-CONTEXT.md
@.planning/phases/H.2-eval-harness-extension/H.2-01-PLAN.md
@.planning/phases/H.2-eval-harness-extension/H.2-02-PLAN.md
@.planning/phases/H.2-eval-harness-extension/H.2-03-PLAN.md
@.github/workflows/tool-classification-drift.yml
@.github/workflows/canon-parity.yml
@.github/workflows/wiki-lint.yml

<interfaces>
<!-- CI workflow skeleton from CONTEXT.md `<specifics>` D-09 — copy verbatim shape: -->
name: Skill Evals
on:
  pull_request:
    paths: [tests/evals/**, tests/golden/**, wiki/**, .claude/commands/**, tools/**]
  push:
    branches: [main]
jobs:
  evals:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install pytest pyyaml
      - run: python -m pytest tests/evals/run_skill_evals.py -v

<!-- Existing tool-classification-drift.yml exemplar (already vetted by FSI CI conventions) -->
- actions/checkout@v4
- actions/setup-python@v5 with python-version: '3.12'
- pull_request + push:main trigger pattern (paths-scoped)
- Single bash step that returns exit 0/1 to gate the workflow
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Author .github/workflows/skill-evals.yml mirroring the tool-classification-drift.yml shape with paths-scoped pull_request + push:main triggers</name>
  <files>.github/workflows/skill-evals.yml</files>
  <read_first>
    - .github/workflows/skill-evals.yml (will not exist — confirm and create)
    - .planning/phases/H.2-eval-harness-extension/H.2-CONTEXT.md (D-09 CI workflow spec)
    - .github/workflows/tool-classification-drift.yml (FSI-vetted exemplar shape from G.2c — Python 3.12, pull_request + push:main, paths-scoped, single shell step)
    - .github/workflows/canon-parity.yml (second exemplar — also dual-trigger)
    - .github/workflows/wiki-lint.yml (third exemplar — Python-based pytest run)
    - tests/evals/run_skill_evals.py (the runner the workflow invokes)
  </read_first>
  <action>
    Create `.github/workflows/skill-evals.yml` mirroring CONTEXT.md D-09 + existing tool-classification-drift.yml conventions. Concrete file content:

    ```yaml
    name: Skill Evals

    # Phase H.2 (EVAL-03): unified eval harness gate.
    #
    # Runs tests/evals/run_skill_evals.py which:
    #   1. Discovers cases from tests/golden/*/cases/*.md   (89 existing MD cases — D-01 hybrid)
    #   2. Discovers cases from tests/evals/*/evals.json    (40 new JSON cases — Plans 02+03)
    #   3. Enforces >= 90% pass rate per skill              (D-06 threshold)
    #
    # CI fails the PR when:
    #   - any skill drops below 90% (test_threshold_per_skill assertion)
    #   - any case file is malformed (test_case_well_formed parametrize)
    #   - any of the 7 named skills is missing from tests/evals/ (test_all_seven_new_skills_discovered)
    #
    # Threshold enforcement is INSIDE pytest, not as a separate CI gate — keeps the
    # workflow YAML minimal and centralizes the rule in one tested code path.
    #
    # Triggers are paths-scoped per D-09 — workflow fires only when relevant trees change.

    on:
      pull_request:
        paths:
          - 'tests/evals/**'
          - 'tests/golden/**'
          - 'wiki/**'
          - '.claude/commands/**'
          - 'tools/**'
          - '.github/workflows/skill-evals.yml'
      push:
        branches:
          - main
        paths:
          - 'tests/evals/**'
          - 'tests/golden/**'
          - 'wiki/**'
          - '.claude/commands/**'
          - 'tools/**'
          - '.github/workflows/skill-evals.yml'

    jobs:
      evals:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4

          - name: Setup Python
            # Python 3.12 matches the existing tool-classification-drift.yml and
            # canon-parity.yml workflows — single toolchain across FSI CI.
            uses: actions/setup-python@v5
            with:
              python-version: '3.12'

          - name: Install harness dependencies
            # pytest for the runner, pyyaml for parsing the MD case frontmatter
            # (per tests/evals/run_skill_evals.py imports). No model SDKs — D-04 structural-only.
            run: pip install pytest pyyaml

          - name: Run unified skill eval harness
            # Exit code:
            #   0 = all skills >= 90% pass rate AND all 7 named skills discovered AND all cases well-formed
            #   non-zero = at least one threshold failure, malformed case, or missing skill
            #
            # The -v flag surfaces per-test results in the GitHub Actions log so
            # a developer can see exactly which skill / case failed without re-running.
            run: python -m pytest tests/evals/run_skill_evals.py -v

          - name: Run runner adapter unit tests
            # Catches regressions in the adapters themselves (load_md_cases, load_json_cases)
            # before they cascade into false-positive threshold failures.
            run: python -m pytest tests/evals/test_runner_adapters.py -v

          - name: Regression gate — existing tests/golden/ harnesses
            # D-01 hybrid lock: the 89 existing MD cases MUST keep working.
            # If anyone modifies tests/golden/{ask,review,act}/cases/ in a way
            # that breaks the original harnesses, fail here so the breakage is
            # surfaced separately from the new eval harness.
            run: python -m pytest tests/golden/ -v --tb=short
    ```

    Key choices (carry these forward as YAML comments inline):

    1. **Path scoping** is intentionally narrow per D-09. Tests/evals + tests/golden + wiki + .claude/commands + tools are the only trees that can affect eval outcomes. Trigger fires on the workflow file itself too (last entry) so workflow tweaks get exercised in PR.

    2. **Python 3.12 fixed** — matches G.2c's tool-classification-drift.yml. Don't introduce a second Python version in this milestone.

    3. **No Node.js step** — unlike tool-classification-drift.yml, this workflow doesn't need npm because the runner is pure Python and the eval JSON files are static (no generator).

    4. **Three pytest invocations** instead of one:
       - `tests/evals/run_skill_evals.py` — the main harness gate (D-06 threshold).
       - `tests/evals/test_runner_adapters.py` — unit tests for the runner itself (catches adapter regressions).
       - `tests/golden/` — D-01 regression gate, surfaced separately so adapter and threshold failures don't mask underlying MD-harness breakage.

       Splitting into three steps means: a failure in step 2 (runner regression) is visually distinct in the GitHub UI from a failure in step 3 (regression in the original 89-case suite). Aids triage.

    5. **No `--strict` or `-x` flag** on the main run — collect all failures, not just the first, so a single PR can see all bad skills at once.

    6. **No live model API calls anywhere** — D-04 structural-only lock. No `ANTHROPIC_API_KEY`, no `OPENAI_API_KEY`, no secrets section. This is enforced architecturally (no SDK imports in the runner) and reflected in the workflow having zero secret references.

    7. **No `--check` flag-style drift-detection** — unlike tool-classification-drift.yml, this is not a drift gate. It's a behavioral regression gate.

    Encoding constraints:
    - YAML uses lowercase booleans (`true`/`false`).
    - All keys in lower_with_underscores or quoted as needed (e.g., `python-version` is GH Actions convention with hyphen).
    - File ends with newline.
    - No trailing whitespace.
  </action>
  <verify>
    <automated>test -f .github/workflows/skill-evals.yml && python -c "import yaml; d = yaml.safe_load(open('.github/workflows/skill-evals.yml')); assert d['name'] == 'Skill Evals'; assert True in d['on'] or 'pull_request' in d['on'] or 'on' in d, 'on key missing'; assert 'evals' in d['jobs'], 'evals job missing'; steps = d['jobs']['evals']['steps']; assert any('checkout' in str(s.get('uses', '')) for s in steps), 'checkout step missing'; assert any('setup-python' in str(s.get('uses', '')) for s in steps), 'setup-python step missing'; assert any('pytest tests/evals/run_skill_evals.py' in str(s.get('run', '')) for s in steps), 'main harness invocation missing'; assert any('pytest tests/golden' in str(s.get('run', '')) for s in steps), 'regression gate invocation missing'; print('OK', len(steps), 'steps')" && grep -c "python-version: '3.12'" .github/workflows/skill-evals.yml && grep -c "tests/evals/\\*\\*" .github/workflows/skill-evals.yml && grep -cE "(ANTHROPIC|OPENAI|secrets\\.)" .github/workflows/skill-evals.yml</automated>
  </verify>
  <done>
    - `.github/workflows/skill-evals.yml` exists and parses as valid YAML.
    - `name == "Skill Evals"`.
    - Triggers on both `pull_request` AND `push: branches: [main]`, both paths-scoped to the same 5 directories (tests/evals/**, tests/golden/**, wiki/**, .claude/commands/**, tools/**) plus the workflow file itself.
    - Uses `actions/checkout@v4` + `actions/setup-python@v5` with `python-version: '3.12'`.
    - Installs only `pytest pyyaml` — no model SDKs (D-04).
    - Runs three pytest invocations: `tests/evals/run_skill_evals.py`, `tests/evals/test_runner_adapters.py`, `tests/golden/`.
    - The grep for `ANTHROPIC|OPENAI|secrets\.` returns 0 — no live model invocation possible.
    - The grep for `tests/evals/\*\*` returns 2 (once in pull_request paths, once in push paths).
  </done>
</task>

<task type="auto">
  <name>Task 2: Final phase-exit regression gate verification — confirm all phase success criteria are met against the live tree</name>
  <files>(no files modified — verification-only task)</files>
  <read_first>
    - .github/workflows/skill-evals.yml (just authored in Task 1)
    - tests/evals/run_skill_evals.py (Plan 01)
    - tests/evals/test_runner_adapters.py (Plan 01)
    - tests/evals/wiki-ingest/evals.json, tests/evals/wiki-validate/evals.json, tests/evals/wiki-lint/evals.json, tests/evals/wiki-recommend/evals.json (Plan 02)
    - tests/evals/review/evals.json, tests/evals/dsp-plan/evals.json, tests/evals/dsp-apply/evals.json (Plan 03)
    - .planning/phases/H.2-eval-harness-extension/H.2-CONTEXT.md (locked decisions to re-verify)
    - .planning/ROADMAP.md (phase H.2 success criteria)
    - .planning/REQUIREMENTS.md (EVAL-01, EVAL-02, EVAL-03)
  </read_first>
  <action>
    Run the verification commands below and confirm every one passes. This task does NOT modify any files — it is the final phase-exit gate.

    If any command fails, the failing artifact must be fixed in its originating plan (Plan 01 for runner, Plan 02/03 for JSON files, Task 1 of this plan for workflow), then re-verified.

    1. **Workflow file is valid YAML and structurally correct:**
       ```bash
       python -c "import yaml; d = yaml.safe_load(open('.github/workflows/skill-evals.yml')); print(d['name'], '-', len(d['jobs']['evals']['steps']), 'steps')"
       ```

    2. **All 7 named-skill evals.json files exist with ≥10 cases each:**
       ```bash
       for s in wiki-ingest wiki-validate wiki-lint wiki-recommend review dsp-plan dsp-apply; do
         count=$(python -c "import json; print(len(json.load(open(f'tests/evals/$s/evals.json'))['evals']))")
         echo "$s: $count cases"
         [ "$count" -ge 10 ] || { echo "FAIL: $s has fewer than 10 cases"; exit 1; }
       done
       ```

    3. **Per-skill threshold gate passes:**
       ```bash
       python -m pytest tests/evals/run_skill_evals.py::test_threshold_per_skill -v
       ```

    4. **Coverage gate passes — all 7 named skills discovered:**
       ```bash
       python -m pytest tests/evals/run_skill_evals.py::test_all_seven_new_skills_discovered -v
       ```

    5. **All adapter unit tests pass:**
       ```bash
       python -m pytest tests/evals/test_runner_adapters.py -v
       ```

    6. **Existing golden harnesses still pass (D-01 regression gate):**
       ```bash
       python -m pytest tests/golden/ -v --tb=short
       ```

    7. **D-11 byte-identical lock honored:**
       ```bash
       git diff --quiet tools/apply_engine.py .claude/commands/dsp-apply.md && echo "D-11: OK"
       ```

    8. **D-01 lock: zero modifications to tests/golden/ during this phase:**
       ```bash
       # Compare against the milestone-start commit (v1.0 tag = milestone-end of v1.0 = milestone-start of v2.0)
       git diff --stat v1.0..HEAD -- tests/golden/ | tail -1
       # Expected: empty (zero modifications) OR only summary lines indicating no files changed
       ```

    9. **All 9 H.1 trip-wires encoded as expectations[] strings across the 7 evals.json files:**

       Verbatim per CONTEXT.md D-08 — each trip-wire string MUST appear exactly once in the file it was assigned to:

       ```bash
       # /wiki:ingest — 2 trip-wires (D-08: #5, #8)
       grep -c "When ingesting an article that proposes Avro schemas under" tests/evals/wiki-ingest/evals.json   # expect 1
       grep -c "When ingesting an article that proposes WarpStream" tests/evals/wiki-ingest/evals.json           # expect 1

       # /review — 4 trip-wires (D-08: #2, #9, #6, #4)
       grep -c "Flags Tableflow-on-CDC-source-topic claims as a violation" tests/evals/review/evals.json        # expect 1
       grep -c "Flags exactly-once-v2 on WarpStream claims as a throughput-cost violation" tests/evals/review/evals.json  # expect 1
       grep -c "Flags kafka-console-producer usage in verification snippets" tests/evals/review/evals.json      # expect 1
       grep -cE "StreamsUncaughtExceptionHandler.{1,5}cited as a nested class" tests/evals/review/evals.json    # expect 1

       # /dsp:plan — 3 trip-wires (D-08: #1, #3, #7)
       grep -c "Refuses to plan a Tableflow changelog mode change on an already-materialized topic" tests/evals/dsp-plan/evals.json  # expect 1
       grep -c "Refuses to plan OracleXStreamSource with" tests/evals/dsp-plan/evals.json                       # expect 1
       grep -c "Refuses to plan JSON Schema registration against WarpStream" tests/evals/dsp-plan/evals.json    # expect 1

       # /dsp:apply — 0 trip-wires (D-08 distribution gives this skill none)
       grep -cE "(Refuses to plan|Flags|When ingesting)" tests/evals/dsp-apply/evals.json                       # expect 0
       ```

       Sum: 2 + 4 + 3 + 0 = 9 trip-wires encoded. EVAL-03 requires ≥5. Met with margin.

    10. **No live model invocation anywhere in tests/evals/ or .github/workflows/skill-evals.yml (D-04):**
        ```bash
        grep -rE "(subprocess|requests|anthropic|openai|httpx|ANTHROPIC_API|OPENAI_API)" tests/evals/ .github/workflows/skill-evals.yml 2>/dev/null | grep -v -E "(\.pyc|fixtures)" | wc -l
        # Expected: 0
        ```

    Document each command's actual output in the summary file. Any command that does not match expected output is a phase-exit blocker — fix the originating artifact and re-run.

    Final check: the runner's `test_all_seven_new_skills_discovered` test, which was RED at the end of Plan 01 and STILL RED at the end of Plan 02 (only 4 of 7 skills present), MUST now be GREEN. This is the test transition that marks Plan 03's completion AND closes the EVAL-02 requirement gap structurally.
  </action>
  <verify>
    <automated>python -c "import yaml; d = yaml.safe_load(open('.github/workflows/skill-evals.yml')); assert d['name'] == 'Skill Evals'" && for s in wiki-ingest wiki-validate wiki-lint wiki-recommend review dsp-plan dsp-apply; do test -f "tests/evals/$s/evals.json" || { echo "MISSING $s"; exit 1; }; count=$(python -c "import json; print(len(json.load(open('tests/evals/$s/evals.json'))['evals']))"); [ "$count" -ge 10 ] || { echo "$s: $count < 10"; exit 1; }; done && python -m pytest tests/evals/run_skill_evals.py::test_threshold_per_skill tests/evals/run_skill_evals.py::test_all_seven_new_skills_discovered tests/evals/test_runner_adapters.py -v && python -m pytest tests/golden/ --tb=short -q && git diff --quiet tools/apply_engine.py .claude/commands/dsp-apply.md && trip_count=$(($(grep -c "When ingesting an article that proposes Avro schemas under" tests/evals/wiki-ingest/evals.json) + $(grep -c "When ingesting an article that proposes WarpStream" tests/evals/wiki-ingest/evals.json) + $(grep -c "Flags Tableflow-on-CDC-source-topic" tests/evals/review/evals.json) + $(grep -c "Flags exactly-once-v2 on WarpStream" tests/evals/review/evals.json) + $(grep -c "Flags kafka-console-producer usage in verification" tests/evals/review/evals.json) + $(grep -cE "StreamsUncaughtExceptionHandler.{1,5}cited as a nested class" tests/evals/review/evals.json) + $(grep -c "Refuses to plan a Tableflow changelog mode change" tests/evals/dsp-plan/evals.json) + $(grep -c "Refuses to plan OracleXStreamSource with" tests/evals/dsp-plan/evals.json) + $(grep -c "Refuses to plan JSON Schema registration against WarpStream" tests/evals/dsp-plan/evals.json))); [ "$trip_count" -eq 9 ] || { echo "trip-wires: $trip_count != 9"; exit 1; }; echo "9 trip-wires confirmed" && [ $(grep -rE "(subprocess|requests|anthropic|openai|httpx|ANTHROPIC_API|OPENAI_API)" tests/evals/ .github/workflows/skill-evals.yml 2>/dev/null | grep -v -E "(\.pyc|fixtures)" | wc -l) -eq 0 ] && echo "PHASE-EXIT: OK"</automated>
  </verify>
  <done>
    - All 10 verification commands listed in the action block pass.
    - 9 H.1 trip-wires confirmed encoded verbatim across the 7 evals.json files (2 in /wiki:ingest, 4 in /review, 3 in /dsp:plan, 0 in /dsp:apply).
    - All 7 named-skill evals.json files exist with ≥10 cases each.
    - `test_threshold_per_skill` PASSES (≥90% per skill).
    - `test_all_seven_new_skills_discovered` PASSES (closes the coverage gap that started RED at Plan 01).
    - `tests/golden/` regression gate PASSES.
    - `tools/apply_engine.py` and `.claude/commands/dsp-apply.md` byte-identical from milestone start (D-11).
    - No subprocess / requests / model-SDK imports anywhere in tests/evals/ or .github/workflows/skill-evals.yml (D-04).
    - Workflow YAML parses cleanly and contains all required keys.
  </done>
</task>

</tasks>

<verification>
After both tasks complete (Task 1 authors the workflow, Task 2 verifies the entire phase):

1. **Workflow file lands and parses:** `python -c "import yaml; yaml.safe_load(open('.github/workflows/skill-evals.yml'))"` exits 0.
2. **EVAL-03 complete:** the workflow file fails CI on any threshold drop OR malformed case OR missing skill — all three failure paths flow through pytest's exit code, not separate workflow logic.
3. **EVAL-01 + EVAL-02 reconfirmed:** the workflow's pytest run exercises the runner (EVAL-01) and the per-skill JSON files (EVAL-02). Plan 04's Task 2 verification rerun confirms both still pass.
4. **All 9 trip-wires encoded with margin over EVAL-03's ≥5 floor.**
5. **D-11 lock holds:** `git diff --quiet tools/apply_engine.py .claude/commands/dsp-apply.md` exits 0.
6. **D-01 lock holds:** `git diff --stat v1.0..HEAD -- tests/golden/` shows zero files modified (only additions allowed during H.2 are under tests/evals/).
7. **D-04 structural-only:** no model-SDK or subprocess imports in tests/evals/ or .github/workflows/skill-evals.yml.

The phase exits when Task 2's automated verify block passes end-to-end.
</verification>

<success_criteria>
- EVAL-03 satisfied: `.github/workflows/skill-evals.yml` exists, runs the harness on PR and main pushes, fails when any skill drops below 90% (via pytest exit code).
- All 5 ROADMAP.md success criteria for Phase H.2 met (re-listed in this plan's `<objective>`).
- D-06 90% threshold enforced in the runner (not in CI YAML) — keeps the rule centralized.
- D-09 paths-scoped triggers honored — workflow fires only when tests/evals, tests/golden, wiki, .claude/commands, tools, or the workflow file changes.
- D-04 structural-only honored — no model API calls anywhere in the CI path.
- D-11 lock honored — `tools/apply_engine.py` + `.claude/commands/dsp-apply.md` byte-identical from milestone start.
- D-01 lock honored — zero modifications to `tests/golden/`.
- All 9 H.1 trip-wires (well over the ≥5 EVAL-03 floor) are encoded verbatim as expectations[] strings in the 7 evals.json files.
</success_criteria>

<output>
After completion, create `.planning/phases/H.2-eval-harness-extension/H.2-04-SUMMARY.md` documenting:
- The final `.github/workflows/skill-evals.yml` file shape, with annotation explaining each step
- The actual output of all 10 verification commands from Task 2 (paste exit codes and last-line outputs)
- Confirmation that `test_all_seven_new_skills_discovered` transitioned RED→GREEN between Plans 01 and 03
- Final trip-wire roll-up: which 9 trip-wires landed in which evals.json files, with line numbers
- Final case count roll-up: per-skill case totals across MD + JSON formats (e.g., /ask 32, /review 16 MD + 20 JSON wrapper, /dsp:plan 22 MD + 25 JSON wrapper, ...).
- Any deferred work noted in CONTEXT.md `<deferred>` that surfaced as worth promoting (LLM-as-judge, per-skill thresholds, coverage reporting).
</output>
