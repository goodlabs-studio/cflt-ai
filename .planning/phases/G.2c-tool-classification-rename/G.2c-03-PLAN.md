---
phase: G.2c-tool-classification-rename
plan: 03
type: execute
wave: 2
depends_on:
  - G.2c-01
files_modified:
  - .github/workflows/tool-classification-drift.yml
autonomous: true
requirements_addressed:
  - ACTG-01
must_haves:
  truths:
    - "A GitHub Actions workflow at .github/workflows/tool-classification-drift.yml exists"
    - "The workflow triggers on pull_request and on push to main"
    - "The workflow runs `python tools/regenerate_tool_classification.py --check` and fails on non-zero exit"
    - "The workflow sets up Node.js (so `npm install` works inside the generator) and Python (so the generator can run)"
    - "The workflow scopes its triggers to PRs that touch the classification JSON, the generator script, or the workflow file itself — does not run on every commit unrelated to classification"
  artifacts:
    - path: ".github/workflows/tool-classification-drift.yml"
      provides: "CI drift detection between tool_classification.json and live @confluentinc/mcp-confluent registry"
      contains: "regenerate_tool_classification.py --check"
  key_links:
    - from: ".github/workflows/tool-classification-drift.yml"
      to: "tools/regenerate_tool_classification.py"
      via: "Workflow step invokes `python tools/regenerate_tool_classification.py --check`"
      pattern: "python tools/regenerate_tool_classification.py --check"
    - from: "Workflow trigger paths"
      to: "Files whose changes warrant a drift check"
      via: "on.pull_request.paths and on.push.paths"
      pattern: "tools/profiles/tool_classification.json"
---

<objective>
Add a GitHub Actions workflow that runs `python tools/regenerate_tool_classification.py --check` on every PR touching the classification JSON or the generator, and on every push to main. This is the ongoing enforcement half of ACTG-01: it prevents the classification table from drifting out of alignment with the live `@confluentinc/mcp-confluent` registry after G.2c-02's big-bang rewrite. Per D-07 and D-08, the check is bidirectional and any divergence (missing or extra keys) fails the workflow non-zero.

Purpose: G.2c-02 fixes the classification table once; this CI gate keeps it fixed forever. Without it, the next mcp-confluent version bump (or a careless hand-edit) could re-introduce snake_case rot or stale entries.

Output: A single GitHub Actions workflow file. No application code, no test changes, no JSON changes.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@.planning/phases/G.2c-tool-classification-rename/G.2c-CONTEXT.md
@.planning/phases/G.2c-tool-classification-rename/G.2c-01-PLAN.md
@.github/workflows/canon-parity.yml
@.github/workflows/manifest-citations.yml
@.github/workflows/wiki-lint.yml

<interfaces>
<!-- Existing workflow style to mirror. From .github/workflows/canon-parity.yml: -->

```yaml
name: Canon Parity

on:
  pull_request:
    paths:
      - 'canon/**'
      - 'raw/repos/fsi-dsp/**'
      - 'tools/check-canon-parity.py'

jobs:
  check-parity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: true

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install pyyaml

      - name: Check canon <-> fsi-dsp parity
        run: python tools/check-canon-parity.py
```

<!-- Generator CLI contract (from G.2c-01-PLAN.md Task 2): -->

```
python tools/regenerate_tool_classification.py --check
```

Exits 0 on parity, exit 1 with diff on drift. Requires `npm` available (npm-installs `@confluentinc/mcp-confluent` into a temp prefix) and Python 3.12+ (uses `Path`, `tempfile.TemporaryDirectory`, `subprocess.run(check=True)`).
</interfaces>
</context>

<tasks>

<task id="01" type="auto">
  <name>Task 1: Write tool-classification-drift.yml — CI gate that fails PRs on classification ↔ live-registry divergence</name>
  <files>.github/workflows/tool-classification-drift.yml</files>
  <read_first>
    - .github/workflows/canon-parity.yml (existing style: name, on.pull_request.paths, actions/checkout@v4, actions/setup-python@v5, named steps with explicit exit-code commentary)
    - .github/workflows/manifest-citations.yml (second style reference — confirm whether the repo standardizes on actions/setup-node@v4)
    - .github/workflows/wiki-lint.yml (third style reference)
    - tools/regenerate_tool_classification.py (the generator that --check invokes — confirms that the script uses `subprocess.run(['npm', 'install', ...])`, so Node.js + npm must be present in the CI runner)
    - .planning/phases/G.2c-tool-classification-rename/G.2c-CONTEXT.md (D-07, D-08 — bidirectional check, runs on PR and push to main)
    - tools/profiles/tool_classification.json (the file the workflow gates on)
  </read_first>
  <action>
    Step 1: Confirm the repo's existing workflow patterns by listing them: `ls -la .github/workflows/`. The new file slots in alphabetically and uses the same actions versions for consistency.

    Step 2: Author `.github/workflows/tool-classification-drift.yml` with the following exact content:

    ```yaml
    name: Tool Classification Drift

    # Bidirectional check (D-07, D-08): fails the workflow when the committed
    # tool_classification.json diverges from the live @confluentinc/mcp-confluent
    # registry pinned by the JSON's `mcp_confluent_version` field.
    #
    # Triggers scoped to changes that could affect alignment:
    #   - tool_classification.json itself (hand-edits, version bumps)
    #   - the generator script (changes to the regex, classifier, or CLI)
    #   - this workflow file
    on:
      pull_request:
        paths:
          - 'tools/profiles/tool_classification.json'
          - 'tools/regenerate_tool_classification.py'
          - '.github/workflows/tool-classification-drift.yml'
      push:
        branches:
          - main
        paths:
          - 'tools/profiles/tool_classification.json'
          - 'tools/regenerate_tool_classification.py'
          - '.github/workflows/tool-classification-drift.yml'

    jobs:
      check-drift:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4

          - name: Setup Node.js
            # Generator npm-installs @confluentinc/mcp-confluent into a temp prefix;
            # Node 22 matches the .mcp.json runtime so we test against the same toolchain.
            uses: actions/setup-node@v4
            with:
              node-version: '22'

          - name: Setup Python
            uses: actions/setup-python@v5
            with:
              python-version: '3.12'

          - name: Verify npm is on PATH
            # Fail fast with a clear message if the Node.js setup did not export npm,
            # rather than letting the generator's subprocess.run raise a cryptic
            # FileNotFoundError deep in the stack.
            run: npm --version

          - name: Check tool_classification.json against live mcp-confluent registry
            # Exit 0 = no drift; exit 1 = drift detected, blocks PR / fails main push.
            # Drift means: (a) live registry has a tool not in committed JSON, or
            # (b) committed JSON has a key the live registry doesn't, or
            # (c) the parser extracted zero tools (regex broke).
            # All three are bugs that need a human PR to fix.
            run: python tools/regenerate_tool_classification.py --check
    ```

    Step 3: Validate the YAML parses cleanly:
    ```
    python -c "import yaml; yaml.safe_load(open('.github/workflows/tool-classification-drift.yml'))"
    ```
    Expected: exits 0, no output.

    Step 4: Validate the workflow structurally with `actionlint` if available, otherwise rely on the YAML parse + manual review:
    ```
    which actionlint && actionlint .github/workflows/tool-classification-drift.yml || echo "actionlint not installed locally; CI will catch syntax errors on first PR"
    ```

    Step 5: Sanity-check that `--check` works locally (this is the same invocation the workflow runs):
    ```
    python tools/regenerate_tool_classification.py --check
    ```
    Expected: exits 0 with "OK: tool_classification.json matches mcp-confluent registry." on stderr — confirms G.2c-02 left the JSON in a passing state and this workflow will be green on first push.

    Step 6: Commit `ci(G.2c-03): add tool-classification-drift workflow`.

    Note: The workflow does NOT need `submodules: true` (unlike canon-parity.yml) — the drift check operates purely on `tools/profiles/tool_classification.json` and an npm-installed package; the fsi-dsp submodule is irrelevant.
  </action>
  <verify>
    <automated>python -c "import yaml; w=yaml.safe_load(open('.github/workflows/tool-classification-drift.yml')); assert w['name']=='Tool Classification Drift'; trig = w[True] if True in w else w.get('on'); assert 'pull_request' in trig and 'push' in trig; assert 'tools/profiles/tool_classification.json' in trig['pull_request']['paths']; assert 'tools/regenerate_tool_classification.py' in trig['pull_request']['paths']; steps = w['jobs']['check-drift']['steps']; assert any('regenerate_tool_classification.py --check' in (s.get('run') or '') for s in steps), 'workflow does not invoke --check'; assert any('setup-node' in (s.get('uses') or '') for s in steps), 'workflow does not set up node'; assert any('setup-python' in (s.get('uses') or '') for s in steps), 'workflow does not set up python'; print('OK')"</automated>
  </verify>
  <acceptance_criteria>
    - `test -f .github/workflows/tool-classification-drift.yml` exits 0
    - `python -c "import yaml; yaml.safe_load(open('.github/workflows/tool-classification-drift.yml'))"` exits 0
    - `grep -c "python tools/regenerate_tool_classification.py --check" .github/workflows/tool-classification-drift.yml` returns at least 1
    - `grep "name: Tool Classification Drift" .github/workflows/tool-classification-drift.yml` returns a match
    - `grep -c "pull_request:" .github/workflows/tool-classification-drift.yml` returns at least 1
    - `grep -c "branches:" .github/workflows/tool-classification-drift.yml` returns at least 1 (push to main scope)
    - `grep -c "main" .github/workflows/tool-classification-drift.yml` returns at least 1
    - `grep "actions/checkout@v4" .github/workflows/tool-classification-drift.yml` returns a match
    - `grep "actions/setup-node@v4" .github/workflows/tool-classification-drift.yml` returns a match
    - `grep "actions/setup-python@v5" .github/workflows/tool-classification-drift.yml` returns a match
    - `grep "tools/profiles/tool_classification.json" .github/workflows/tool-classification-drift.yml` returns a match (path filter present on at least one trigger)
    - `grep "tools/regenerate_tool_classification.py" .github/workflows/tool-classification-drift.yml` returns a match (path filter present on at least one trigger)
    - `git diff --quiet tools/apply_engine.py tools/profiles/tool_classification.json tools/profiles/read-only.json tools/profiles/engineer.json tools/profiles/break-glass.json tests/` exits 0 (this plan touches ONLY the workflow file)
    - Running `python tools/regenerate_tool_classification.py --check` locally exits 0 (proving the workflow would be green on first push, given G.2c-02 already passed)
  </acceptance_criteria>
  <done>Workflow file exists, parses as valid YAML, triggers on PR + push-to-main with appropriate path scoping, sets up Node 22 and Python 3.12, and invokes `python tools/regenerate_tool_classification.py --check` as the gating step. Local `--check` invocation passes — this CI gate is green on first push and ready to catch the next drift event.</done>
</task>

</tasks>

<verification>
- `test -f .github/workflows/tool-classification-drift.yml` exits 0
- `python -c "import yaml; yaml.safe_load(open('.github/workflows/tool-classification-drift.yml'))"` exits 0
- `grep "python tools/regenerate_tool_classification.py --check" .github/workflows/tool-classification-drift.yml` returns a match
- `python tools/regenerate_tool_classification.py --check` exits 0 locally (the workflow would pass on first push)
- `git diff --name-only` shows ONLY `.github/workflows/tool-classification-drift.yml` was added (this plan is isolated to CI)
</verification>

<success_criteria>
1. A drift-detection workflow exists in `.github/workflows/` and is named consistently with the existing canon-parity / manifest-citations / wiki-lint style.
2. The workflow triggers on PR and push-to-main, scoped to changes that could affect classification alignment.
3. The workflow installs both Node.js (for the generator's npm-install step) and Python (for the generator script itself).
4. The single gating step is `python tools/regenerate_tool_classification.py --check`, which exits 1 on any bidirectional divergence per D-08.
5. Local invocation confirms the gate is currently green — combined with G.2c-02's rewrite, the classification table is now both correct AND continuously enforced.
6. Together with G.2c-01 (generator) and G.2c-02 (data rewrite), this completes ACTG-01 as an enforced property rather than a snapshot.
</success_criteria>

<output>
After completion, create `.planning/phases/G.2c-tool-classification-rename/G.2c-03-SUMMARY.md` per the standard summary template.
</output>
