---
phase: H.3b-version-pin-ci-drift-gate
plan: 01
type: execute
wave: 1
depends_on: [H.3a-01]
files_modified:
  - tools/vendor-sources.json
  - tools/check_streaming_skills_drift.py
  - .github/workflows/streaming-skills-drift.yml
  - tests/test_check_streaming_skills_drift.py
autonomous: true
requirements: [INST-01]
requirements_addressed: [INST-01]

must_haves:
  truths:
    - "`tools/vendor-sources.json` contains a `streaming-skills-plugin` top-level entry with `kind: \"claude-plugin\"`, `commit: \"91d1871ef8c320be92bca955c8e42492a2778cb4\"`, `version: \"1.0.0\"`, `marketplace: \"confluent-agent-skills\"`, `plugin_name: \"streaming-skills-plugin\"`, `drift_check: \"tools/check_streaming_skills_drift.py\"`"
    - "The existing `confluent-agent-skills` entry in `tools/vendor-sources.json` is UNCHANGED (same commit SHA, same kind, same fields)"
    - "`tools/check_streaming_skills_drift.py` exists and exposes `--check`, `--dry-run`, `--help` CLI flags (CLI shape mirrors `tools/regenerate_tool_classification.py`)"
    - "`--check` mode exits 0 when pinned commit matches `git ls-remote https://github.com/confluentinc/agent-skills HEAD`; exits 1 on commit drift; exits 2 on config error (missing/malformed vendor-sources entry); exits 3 on transient error (network/git unavailable)"
    - "`--check` mode prints a structured drift report to stderr when exit code is non-zero (named signal + pinned vs live SHAs + fix instructions)"
    - "Default mode (no `--check` flag) prints the comparison summary and exits 0 regardless of drift — useful for local diagnosis"
    - "`.github/workflows/streaming-skills-drift.yml` exists; fires on `pull_request` AND `push: branches: [main]`; path-scoped to `tools/vendor-sources.json`, `tools/check_streaming_skills_drift.py`, `.github/workflows/streaming-skills-drift.yml`"
    - "Workflow steps: checkout@v4 → setup-python@v5 (python 3.12) → defensive `git --version` step → `python tools/check_streaming_skills_drift.py --check`"
    - "Workflow does NOT setup Node.js (unlike tool-classification-drift.yml — the streaming-skills check uses git ls-remote, not npm)"
    - "`tests/test_check_streaming_skills_drift.py` exists with ≥ 4 test cases covering: (1) pin matches mock HEAD → exit 0, (2) pin mismatches → exit 1, (3) vendor-sources missing entry → exit 2, (4) git unavailable → exit 3"
    - "Tests mock `subprocess.run` via `monkeypatch` — no real `git ls-remote` calls during test"
    - "`pytest tests/test_check_streaming_skills_drift.py -v` exits 0"
    - "Running `python tools/check_streaming_skills_drift.py` (default mode, no flags) on the current pin succeeds (exit 0) — proves the script is syntactically correct"
    - "`pytest tests/` exit 0 (or only same 2 pre-existing failures as H.4a/H.4b/H.4c — no NEW failures)"
    - "No changes to `tools/regenerate_tool_classification.py`, `.github/workflows/tool-classification-drift.yml`, `tools/apply_engine.py`, `canon/`, or any profile JSON"
  artifacts:
    - path: "tools/vendor-sources.json"
      provides: "Vendor sources pin file — extended with streaming-skills-plugin entry (kind: claude-plugin)"
      contains:
        - "streaming-skills-plugin"
        - "claude-plugin"
        - "91d1871ef8c320be92bca955c8e42492a2778cb4"
        - "confluent-agent-skills"
        - "drift_check"
    - path: "tools/check_streaming_skills_drift.py"
      provides: "Drift-check generator with --check mode for CI gate; default mode for local diagnosis"
      contains:
        - "argparse"
        - "git ls-remote"
        - "subprocess.run"
        - "--check"
        - "streaming-skills-plugin"
        - "vendor-sources.json"
    - path: ".github/workflows/streaming-skills-drift.yml"
      provides: "GitHub Actions workflow that fails PRs which drift off the pinned streaming-skills-plugin commit without bumping the pin"
      contains:
        - "name: Streaming Skills Plugin Drift"
        - "pull_request"
        - "push:"
        - "branches:"
        - "main"
        - "tools/vendor-sources.json"
        - "tools/check_streaming_skills_drift.py"
        - "actions/checkout@v4"
        - "actions/setup-python@v5"
        - "python-version: '3.12'"
        - "python tools/check_streaming_skills_drift.py --check"
    - path: "tests/test_check_streaming_skills_drift.py"
      provides: "Unit tests for the drift-check generator using subprocess.run mocking"
      contains:
        - "monkeypatch"
        - "subprocess"
        - "test_pin_matches_head_exits_zero"
        - "test_pin_mismatches_head_exits_one"
        - "test_missing_entry_exits_two"
        - "test_git_unavailable_exits_three"
  key_links:
    - from: ".github/workflows/streaming-skills-drift.yml"
      to: "tools/check_streaming_skills_drift.py"
      via: "Workflow's `run:` step invokes the generator with --check; exit code determines PR pass/fail"
      pattern: "tools/check_streaming_skills_drift.py --check"
    - from: "tools/check_streaming_skills_drift.py"
      to: "tools/vendor-sources.json"
      via: "Script reads the streaming-skills-plugin entry from vendor-sources.json; pin commit is the source of truth"
      pattern: "vendor-sources.json"
    - from: "tools/check_streaming_skills_drift.py"
      to: "https://github.com/confluentinc/agent-skills"
      via: "git ls-remote returns the upstream HEAD commit SHA; compared against pinned commit"
      pattern: "git ls-remote"
---

<objective>
Land the version pin + CI drift gate so any unpinned-bump of `streaming-skills-plugin` is caught at PR time. Mirrors G.2c's drift-gate pattern exactly — same generator/`--check`/CI shape, swapped target (git ls-remote against confluentinc/agent-skills HEAD instead of npm-installed mcp-confluent).

After this plan: INST-01 is fully satisfied (install was H.3a; pin + CI drift gate is H.3b). The vendor-pin discipline is consistent across two vendor sources (`confluent-agent-skills` for wiki ingest, `streaming-skills-plugin` for runtime install). Single PLAN.md, single wave, autonomous. ~4 files: 1 JSON edit + 3 new files.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/H.3b-version-pin-ci-drift-gate/H.3b-CONTEXT.md
@.planning/phases/H.3a-plugin-install-canon-overlay-wiki-article/H.3a-CONTEXT.md
@.planning/phases/G.2c-tool-classification-rename/G.2c-CONTEXT.md
@.planning/phases/H.1-wiki-ingest-agent-skills/H.1-CONTEXT.md
@tools/vendor-sources.json
@tools/regenerate_tool_classification.py
@.github/workflows/tool-classification-drift.yml

<interfaces>
<!-- New vendor-sources.json shape (after H.3b appends the plugin entry) -->
{
  "confluent-agent-skills": { ... existing ... },
  "streaming-skills-plugin": {
    "upstream": "https://github.com/confluentinc/agent-skills",
    "repo": "confluentinc/agent-skills",
    "marketplace": "confluent-agent-skills",
    "plugin_name": "streaming-skills-plugin",
    "version": "1.0.0",
    "commit": "91d1871ef8c320be92bca955c8e42492a2778cb4",
    "installed_at": "2026-05-17",
    "kind": "claude-plugin",
    "license": "Apache-2.0",
    "drift_check": "tools/check_streaming_skills_drift.py"
  }
}

<!-- CLI shape — mirrors tools/regenerate_tool_classification.py -->
usage: check_streaming_skills_drift.py [-h] [--check] [--dry-run]

Drift check for streaming-skills-plugin pin in tools/vendor-sources.json.
Compares the pinned commit against the upstream HEAD via git ls-remote.

options:
  -h, --help    show this help message and exit
  --check       CI mode — exit non-zero on drift, missing entry, or transient error
  --dry-run     Print the comparison summary without changing any files (default)

<!-- Workflow skeleton — mirrors tool-classification-drift.yml -->
name: Streaming Skills Plugin Drift
on:
  pull_request:
    paths:
      - 'tools/vendor-sources.json'
      - 'tools/check_streaming_skills_drift.py'
      - '.github/workflows/streaming-skills-drift.yml'
  push:
    branches: [main]
    paths:
      - 'tools/vendor-sources.json'
      - 'tools/check_streaming_skills_drift.py'
      - '.github/workflows/streaming-skills-drift.yml'
jobs:
  check-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: git --version
      - run: python tools/check_streaming_skills_drift.py --check
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Extend tools/vendor-sources.json with streaming-skills-plugin entry (kind: claude-plugin)</name>
  <files>
    - tools/vendor-sources.json
  </files>
  <read_first>
    - tools/vendor-sources.json (current — confluent-agent-skills entry; preserve byte-identical)
    - .planning/phases/H.3b-version-pin-ci-drift-gate/H.3b-CONTEXT.md (D-02 exact shape)
  </read_first>
  <action>
    Edit `tools/vendor-sources.json` to add the `streaming-skills-plugin` entry alongside the existing `confluent-agent-skills` entry. Final file content:

    ```json
    {
      "confluent-agent-skills": {
        "upstream": "https://github.com/confluentinc/agent-skills",
        "commit": "91d1871ef8c320be92bca955c8e42492a2778cb4",
        "ingested_at": "2026-05-16",
        "vendor_path": "raw/vendor/confluent-agent-skills/91d1871e/",
        "license": "Apache-2.0",
        "kind": "wiki-source"
      },
      "streaming-skills-plugin": {
        "upstream": "https://github.com/confluentinc/agent-skills",
        "repo": "confluentinc/agent-skills",
        "marketplace": "confluent-agent-skills",
        "plugin_name": "streaming-skills-plugin",
        "version": "1.0.0",
        "commit": "91d1871ef8c320be92bca955c8e42492a2778cb4",
        "installed_at": "2026-05-17",
        "kind": "claude-plugin",
        "license": "Apache-2.0",
        "drift_check": "tools/check_streaming_skills_drift.py"
      }
    }
    ```

    The `confluent-agent-skills` entry is BYTE-IDENTICAL to its current state. The `streaming-skills-plugin` entry is new.
  </action>
  <acceptance_criteria>
    - File parses as valid JSON: `python3 -c "import json; json.load(open('tools/vendor-sources.json'))"` exits 0.
    - `python3 -c "import json; d = json.load(open('tools/vendor-sources.json')); assert 'confluent-agent-skills' in d; assert 'streaming-skills-plugin' in d; assert d['streaming-skills-plugin']['kind']=='claude-plugin'; assert d['streaming-skills-plugin']['commit']=='91d1871ef8c320be92bca955c8e42492a2778cb4'; assert d['streaming-skills-plugin']['drift_check']=='tools/check_streaming_skills_drift.py'"` exits 0.
    - Existing `confluent-agent-skills` entry unchanged: `python3 -c "import json; d = json.load(open('tools/vendor-sources.json')); assert d['confluent-agent-skills']['commit']=='91d1871ef8c320be92bca955c8e42492a2778cb4'; assert d['confluent-agent-skills']['kind']=='wiki-source'; assert d['confluent-agent-skills']['ingested_at']=='2026-05-16'"` exits 0.
  </acceptance_criteria>
</task>

<task type="auto">
  <name>Task 2: Author tools/check_streaming_skills_drift.py — drift-check generator with --check, --dry-run, --help CLI flags</name>
  <files>
    - tools/check_streaming_skills_drift.py
  </files>
  <read_first>
    - tools/regenerate_tool_classification.py (CLI shape + argparse pattern + exit-code conventions to mirror)
    - tools/vendor-sources.json (post-Task 1 — read the streaming-skills-plugin entry)
    - .planning/phases/H.3b-version-pin-ci-drift-gate/H.3b-CONTEXT.md (D-03, D-04, D-05 — exit codes + drift signals)
  </read_first>
  <action>
    Create `tools/check_streaming_skills_drift.py` with the structure below. Use Python stdlib only (json, subprocess, argparse, sys, pathlib). No third-party deps.

    ```python
    #!/usr/bin/env python3
    """
    tools/check_streaming_skills_drift.py — Drift check for streaming-skills-plugin pin.

    Compares the pinned commit in tools/vendor-sources.json against the upstream
    HEAD via `git ls-remote https://github.com/confluentinc/agent-skills HEAD`.

    Used by .github/workflows/streaming-skills-drift.yml as the CI gate. Mirrors
    the G.2c pattern (tools/regenerate_tool_classification.py): same CLI shape,
    same exit-code semantics, same defensive structure.

    Exit codes:
      0 = no drift (pinned commit matches upstream HEAD)
      1 = drift detected (commit mismatch) — CI fails
      2 = config error (vendor-sources.json missing entry, malformed, or wrong shape)
      3 = transient error (git unavailable, network failure, ls-remote returned empty)
    """
    from __future__ import annotations

    import argparse
    import json
    import subprocess
    import sys
    from pathlib import Path

    REPO_ROOT = Path(__file__).resolve().parent.parent
    VENDOR_SOURCES_PATH = REPO_ROOT / "tools" / "vendor-sources.json"
    PLUGIN_KEY = "streaming-skills-plugin"
    UPSTREAM_URL = "https://github.com/confluentinc/agent-skills"


    def load_pin() -> dict:
        """Load the streaming-skills-plugin entry from vendor-sources.json.

        Raises SystemExit(2) if the file or entry is missing/malformed.
        """
        if not VENDOR_SOURCES_PATH.exists():
            print(f"ERROR: {VENDOR_SOURCES_PATH} not found", file=sys.stderr)
            sys.exit(2)
        try:
            data = json.loads(VENDOR_SOURCES_PATH.read_text())
        except json.JSONDecodeError as e:
            print(f"ERROR: {VENDOR_SOURCES_PATH} is not valid JSON: {e}", file=sys.stderr)
            sys.exit(2)
        if PLUGIN_KEY not in data:
            print(f"ERROR: {VENDOR_SOURCES_PATH} missing required entry {PLUGIN_KEY!r}", file=sys.stderr)
            sys.exit(2)
        entry = data[PLUGIN_KEY]
        if "commit" not in entry or not entry["commit"]:
            print(f"ERROR: {PLUGIN_KEY} entry missing 'commit' field", file=sys.stderr)
            sys.exit(2)
        return entry


    def fetch_upstream_head(upstream_url: str = UPSTREAM_URL) -> str:
        """Fetch the upstream HEAD commit SHA via `git ls-remote`.

        Raises SystemExit(3) if git is unavailable, the call fails, or the output
        is empty/malformed.
        """
        try:
            result = subprocess.run(
                ["git", "ls-remote", upstream_url, "HEAD"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except FileNotFoundError:
            print("ERROR: git not found on PATH — cannot check upstream HEAD", file=sys.stderr)
            sys.exit(3)
        except subprocess.TimeoutExpired:
            print(f"ERROR: git ls-remote {upstream_url} timed out", file=sys.stderr)
            sys.exit(3)

        if result.returncode != 0:
            print(f"ERROR: git ls-remote failed (exit {result.returncode}):", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(3)

        stdout = result.stdout.strip()
        if not stdout:
            print(f"ERROR: git ls-remote {upstream_url} returned empty output", file=sys.stderr)
            sys.exit(3)

        # ls-remote output format: "<sha>\tHEAD"
        first_line = stdout.splitlines()[0]
        parts = first_line.split()
        if not parts or len(parts[0]) < 40:
            print(f"ERROR: git ls-remote output malformed: {first_line!r}", file=sys.stderr)
            sys.exit(3)

        return parts[0]


    def report_drift(pinned: str, live: str, entry: dict) -> None:
        """Print a structured drift report to stderr."""
        print("STREAMING_SKILLS_PLUGIN drift detected:", file=sys.stderr)
        print(f"  pinned commit: {pinned}", file=sys.stderr)
        print(f"  live HEAD:     {live}", file=sys.stderr)
        print(f"  upstream:      {entry.get('upstream', UPSTREAM_URL)}", file=sys.stderr)
        print(
            f"To fix: bump tools/vendor-sources.json {PLUGIN_KEY}.commit to {live!r}, "
            f"then re-run `/plugin install streaming-skills-plugin@confluent-agent-skills` "
            f"locally and commit any resulting changes.",
            file=sys.stderr,
        )


    def main(argv: list[str] | None = None) -> int:
        parser = argparse.ArgumentParser(
            description="Drift check for streaming-skills-plugin pin in tools/vendor-sources.json.",
            epilog="Exit codes: 0 no drift, 1 drift detected, 2 config error, 3 transient error.",
        )
        parser.add_argument(
            "--check",
            action="store_true",
            help="CI mode — exit non-zero on drift, missing entry, or transient error",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print the comparison summary without changing any files (default)",
        )
        args = parser.parse_args(argv)

        entry = load_pin()
        pinned = entry["commit"]
        live = fetch_upstream_head(entry.get("upstream", UPSTREAM_URL))

        drift = pinned != live

        if drift:
            if args.check:
                report_drift(pinned, live, entry)
                return 1
            print(f"DRIFT: pinned={pinned} live={live}", file=sys.stdout)
        else:
            print(f"OK: pinned={pinned} matches live HEAD", file=sys.stdout)

        return 0


    if __name__ == "__main__":
        sys.exit(main())
    ```

    Make the file executable (`chmod +x tools/check_streaming_skills_drift.py`).
  </action>
  <acceptance_criteria>
    - File `tools/check_streaming_skills_drift.py` exists.
    - `python3 tools/check_streaming_skills_drift.py --help` exits 0 and prints help text containing `--check` and `--dry-run`.
    - `python3 tools/check_streaming_skills_drift.py` (default mode) exits 0 (assuming local git ls-remote succeeds and pin matches; if drift exists on upstream, prints DRIFT but still exits 0 in default mode).
    - File contains literal strings: `argparse`, `--check`, `git`, `ls-remote`, `vendor-sources.json`, `streaming-skills-plugin`.
    - `grep -c "exit 1" tools/check_streaming_skills_drift.py` returns ≥ 1 (drift exit code path).
    - `grep -c "sys.exit(2)" tools/check_streaming_skills_drift.py` returns ≥ 2 (config error paths).
    - `grep -c "sys.exit(3)" tools/check_streaming_skills_drift.py` returns ≥ 3 (transient error paths).
    - File is executable: `test -x tools/check_streaming_skills_drift.py`.
  </acceptance_criteria>
</task>

<task type="auto">
  <name>Task 3: Author .github/workflows/streaming-skills-drift.yml — CI workflow mirroring tool-classification-drift.yml (minus Node.js)</name>
  <files>
    - .github/workflows/streaming-skills-drift.yml
  </files>
  <read_first>
    - .github/workflows/tool-classification-drift.yml (shape to mirror — keep formatting + comment style + step structure)
    - .planning/phases/H.3b-version-pin-ci-drift-gate/H.3b-CONTEXT.md (D-06, D-07)
  </read_first>
  <action>
    Create `.github/workflows/streaming-skills-drift.yml` with this content (mirror G.2c's workflow's structure exactly; only differences: name, paths, no Node step, defensive `git --version` instead of `npm --version`):

    ```yaml
    name: Streaming Skills Plugin Drift

    # Bidirectional check (H.3b CONTEXT D-04): fails the workflow when the
    # streaming-skills-plugin commit pinned in tools/vendor-sources.json drifts
    # from the upstream HEAD at https://github.com/confluentinc/agent-skills.
    #
    # Triggers scoped to changes that could affect alignment:
    #   - vendor-sources.json itself (hand-edits, pin bumps)
    #   - the drift-check script (CLI changes, regex changes, exit-code changes)
    #   - this workflow file
    #
    # Mirrors .github/workflows/tool-classification-drift.yml (Phase G.2c) structure
    # except no Node.js setup — this check uses `git ls-remote` instead of npm.

    on:
      pull_request:
        paths:
          - 'tools/vendor-sources.json'
          - 'tools/check_streaming_skills_drift.py'
          - '.github/workflows/streaming-skills-drift.yml'
      push:
        branches:
          - main
        paths:
          - 'tools/vendor-sources.json'
          - 'tools/check_streaming_skills_drift.py'
          - '.github/workflows/streaming-skills-drift.yml'

    jobs:
      check-drift:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4

          - name: Setup Python
            # Python 3.12 matches the other FSI CI workflows
            # (tool-classification-drift.yml, canon-parity.yml, wiki-lint.yml).
            uses: actions/setup-python@v5
            with:
              python-version: '3.12'

          - name: Verify git is on PATH
            # Fail fast with a clear message if git is missing — the check script
            # uses `git ls-remote` to fetch upstream HEAD. ubuntu-latest always has
            # git, but the defensive verb-step makes failures legible.
            run: git --version

          - name: Check streaming-skills-plugin pin against upstream HEAD
            # Exit codes:
            #   0 = no drift; 1 = drift (PR fails); 2 = config error; 3 = transient/git error.
            # All non-zero outcomes are CI failures because they all indicate the pin
            # cannot be safely trusted as the authoritative reference.
            run: python tools/check_streaming_skills_drift.py --check
    ```
  </action>
  <acceptance_criteria>
    - File `.github/workflows/streaming-skills-drift.yml` exists.
    - `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/streaming-skills-drift.yml'))"` exits 0 (valid YAML).
    - `grep -c "^name: Streaming Skills Plugin Drift$" .github/workflows/streaming-skills-drift.yml` returns 1.
    - File contains literal strings: `pull_request`, `push:`, `branches:`, `main`, `tools/vendor-sources.json`, `tools/check_streaming_skills_drift.py`, `actions/checkout@v4`, `actions/setup-python@v5`, `python-version: '3.12'`, `git --version`, `python tools/check_streaming_skills_drift.py --check`.
    - Workflow does NOT contain Node.js setup: `grep -c "actions/setup-node" .github/workflows/streaming-skills-drift.yml` returns 0; `grep -c "npm" .github/workflows/streaming-skills-drift.yml` returns 0.
  </acceptance_criteria>
</task>

<task type="auto">
  <name>Task 4: Author tests/test_check_streaming_skills_drift.py with 4+ test cases covering all 4 exit codes (0/1/2/3)</name>
  <files>
    - tests/test_check_streaming_skills_drift.py
  </files>
  <read_first>
    - tools/check_streaming_skills_drift.py (post-Task 2 — module under test)
    - tests/test_profile_gating.py (existing test patterns — monkeypatch usage)
    - .planning/phases/H.3b-version-pin-ci-drift-gate/H.3b-CONTEXT.md (D-08, D-09 — test surface)
  </read_first>
  <action>
    Create `tests/test_check_streaming_skills_drift.py`:

    ```python
    """
    Phase H.3b — Unit tests for tools/check_streaming_skills_drift.py.

    Mocks subprocess.run via monkeypatch so no real `git ls-remote` calls happen
    during tests. CI workflow run is the only place real network calls happen.
    """
    import json
    import subprocess
    from pathlib import Path
    from types import SimpleNamespace

    import pytest

    from tools import check_streaming_skills_drift as drift_mod


    PINNED_SHA = "91d1871ef8c320be92bca955c8e42492a2778cb4"
    DIFFERENT_SHA = "abc1234567890def1234567890abcdef12345678"


    @pytest.fixture
    def fake_vendor_sources(tmp_path, monkeypatch):
        """Point the module's VENDOR_SOURCES_PATH at a tmp file we control."""
        data = {
            "streaming-skills-plugin": {
                "upstream": "https://github.com/confluentinc/agent-skills",
                "repo": "confluentinc/agent-skills",
                "marketplace": "confluent-agent-skills",
                "plugin_name": "streaming-skills-plugin",
                "version": "1.0.0",
                "commit": PINNED_SHA,
                "installed_at": "2026-05-17",
                "kind": "claude-plugin",
                "license": "Apache-2.0",
                "drift_check": "tools/check_streaming_skills_drift.py"
            }
        }
        path = tmp_path / "vendor-sources.json"
        path.write_text(json.dumps(data, indent=2))
        monkeypatch.setattr(drift_mod, "VENDOR_SOURCES_PATH", path)
        return path


    def _mock_subprocess_run(returncode: int, stdout: str = "", stderr: str = "", raise_exc=None):
        """Build a subprocess.run replacement returning a CompletedProcess-like object."""
        def _runner(*args, **kwargs):
            if raise_exc is not None:
                raise raise_exc
            return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)
        return _runner


    def test_pin_matches_head_exits_zero(fake_vendor_sources, monkeypatch):
        """When ls-remote returns the same SHA as the pin, --check exits 0."""
        monkeypatch.setattr(
            subprocess,
            "run",
            _mock_subprocess_run(returncode=0, stdout=f"{PINNED_SHA}\tHEAD\n"),
        )
        exit_code = drift_mod.main(["--check"])
        assert exit_code == 0


    def test_pin_mismatches_head_exits_one(fake_vendor_sources, monkeypatch, capsys):
        """When ls-remote returns a different SHA, --check exits 1 and prints drift report."""
        monkeypatch.setattr(
            subprocess,
            "run",
            _mock_subprocess_run(returncode=0, stdout=f"{DIFFERENT_SHA}\tHEAD\n"),
        )
        exit_code = drift_mod.main(["--check"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "drift detected" in captured.err.lower()
        assert PINNED_SHA in captured.err
        assert DIFFERENT_SHA in captured.err


    def test_default_mode_does_not_exit_nonzero_on_drift(fake_vendor_sources, monkeypatch, capsys):
        """Default mode (no --check) prints summary but always exits 0."""
        monkeypatch.setattr(
            subprocess,
            "run",
            _mock_subprocess_run(returncode=0, stdout=f"{DIFFERENT_SHA}\tHEAD\n"),
        )
        exit_code = drift_mod.main([])  # no flags
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "DRIFT" in captured.out


    def test_missing_entry_exits_two(tmp_path, monkeypatch):
        """Empty vendor-sources.json (no streaming-skills-plugin key) exits 2."""
        path = tmp_path / "vendor-sources.json"
        path.write_text("{}")
        monkeypatch.setattr(drift_mod, "VENDOR_SOURCES_PATH", path)
        with pytest.raises(SystemExit) as exc_info:
            drift_mod.main(["--check"])
        assert exc_info.value.code == 2


    def test_malformed_json_exits_two(tmp_path, monkeypatch):
        """Malformed JSON exits 2 (config error)."""
        path = tmp_path / "vendor-sources.json"
        path.write_text("{not valid json")
        monkeypatch.setattr(drift_mod, "VENDOR_SOURCES_PATH", path)
        with pytest.raises(SystemExit) as exc_info:
            drift_mod.main(["--check"])
        assert exc_info.value.code == 2


    def test_missing_commit_field_exits_two(tmp_path, monkeypatch):
        """Entry without commit field exits 2 (config error)."""
        path = tmp_path / "vendor-sources.json"
        path.write_text(json.dumps({"streaming-skills-plugin": {"version": "1.0.0"}}))
        monkeypatch.setattr(drift_mod, "VENDOR_SOURCES_PATH", path)
        with pytest.raises(SystemExit) as exc_info:
            drift_mod.main(["--check"])
        assert exc_info.value.code == 2


    def test_git_unavailable_exits_three(fake_vendor_sources, monkeypatch):
        """When git command is not on PATH, --check exits 3."""
        monkeypatch.setattr(
            subprocess,
            "run",
            _mock_subprocess_run(returncode=0, raise_exc=FileNotFoundError("git not found")),
        )
        with pytest.raises(SystemExit) as exc_info:
            drift_mod.main(["--check"])
        assert exc_info.value.code == 3


    def test_git_returns_empty_output_exits_three(fake_vendor_sources, monkeypatch):
        """When ls-remote returns empty output, --check exits 3."""
        monkeypatch.setattr(
            subprocess,
            "run",
            _mock_subprocess_run(returncode=0, stdout=""),
        )
        with pytest.raises(SystemExit) as exc_info:
            drift_mod.main(["--check"])
        assert exc_info.value.code == 3


    def test_git_nonzero_returncode_exits_three(fake_vendor_sources, monkeypatch):
        """When ls-remote returncode != 0, --check exits 3."""
        monkeypatch.setattr(
            subprocess,
            "run",
            _mock_subprocess_run(returncode=128, stderr="remote not found"),
        )
        with pytest.raises(SystemExit) as exc_info:
            drift_mod.main(["--check"])
        assert exc_info.value.code == 3
    ```
  </action>
  <acceptance_criteria>
    - File `tests/test_check_streaming_skills_drift.py` exists.
    - `grep -c "def test_" tests/test_check_streaming_skills_drift.py` returns ≥ 4 (at minimum: pin_matches, pin_mismatches, missing_entry, git_unavailable).
    - `pytest tests/test_check_streaming_skills_drift.py -v` exits 0 — all tests pass.
    - Tests cover all 4 exit codes: `grep -c "exit_code == 0" tests/test_check_streaming_skills_drift.py` returns ≥ 1; `grep -c "exit_code == 1" tests/test_check_streaming_skills_drift.py` returns ≥ 1; `grep -c "exit_info.value.code == 2" tests/test_check_streaming_skills_drift.py` returns ≥ 1; `grep -c "exit_info.value.code == 3" tests/test_check_streaming_skills_drift.py` returns ≥ 1.
    - Tests use `monkeypatch` not real subprocess: `grep -c "monkeypatch" tests/test_check_streaming_skills_drift.py` returns ≥ 4.
  </acceptance_criteria>
</task>

<task type="auto">
  <name>Task 5: Full regression + run live drift check + write H.3b-01-SUMMARY.md</name>
  <files>
    - .planning/phases/H.3b-version-pin-ci-drift-gate/H.3b-01-SUMMARY.md
  </files>
  <read_first>
    - tools/check_streaming_skills_drift.py (post-Task 2)
    - .github/workflows/streaming-skills-drift.yml (post-Task 3)
    - tests/test_check_streaming_skills_drift.py (post-Task 4)
  </read_first>
  <action>
    1. **Live check** (proves the script works against the real upstream): `python3 tools/check_streaming_skills_drift.py --check`. Expected outcomes:
       - Exit 0 = pin matches live HEAD (most likely — H.3a installed at SHA 91d1871e earlier today; upstream HEAD has likely not moved).
       - Exit 1 = drift exists (upstream moved past our pin). If this happens, document in SUMMARY but DO NOT auto-fix; the drift-detection succeeding is itself the goal of H.3b. Note the drift in SUMMARY's "Drift detected (informational)" section.
       - Exit 3 = git ls-remote failed (network). Note in SUMMARY; the CI workflow will exercise this for real.
    2. Run unit tests: `pytest tests/test_check_streaming_skills_drift.py -v` — must exit 0.
    3. Run family tests + golden + full pytest:
       - `pytest tests/test_profile_gating.py tests/test_per_family_isolation.py tests/test_canon_overlay.py tests/test_check_streaming_skills_drift.py -v` — must exit 0.
       - `pytest tests/golden/ -v` — must exit 0.
       - `pytest tests/ -v --tb=short` — must exit 0 (or only the same 2 pre-existing failures persist).
    4. YAML lint sanity on the workflow: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/streaming-skills-drift.yml'))"`.

    Write `.planning/phases/H.3b-version-pin-ci-drift-gate/H.3b-01-SUMMARY.md`:
    ```markdown
    # H.3b-01 Summary

    **Plan:** H.3b-01 — Version pin + CI drift gate
    **Status:** Complete
    **Date:** 2026-05-17

    ## What landed
    - `tools/vendor-sources.json` — extended with `streaming-skills-plugin` entry (kind: claude-plugin, commit pinned at 91d1871e)
    - `tools/check_streaming_skills_drift.py` — drift-check generator with --check/--dry-run/--help; exit codes 0/1/2/3 matching G.2c semantics
    - `.github/workflows/streaming-skills-drift.yml` — CI workflow with pull_request + push:main triggers, path-scoped, mirrors G.2c (minus Node.js)
    - `tests/test_check_streaming_skills_drift.py` — N test cases covering all 4 exit codes via subprocess mocking

    ## Requirements
    - INST-01: ✓ Fully satisfied (install was H.3a; pin + CI drift gate is H.3b; bidirectional drift detection in place)

    ## ROADMAP success criteria (H.3b)
    1. ✓ tools/vendor-sources.json contains pinned streaming-skills-plugin version + commit
    2. ✓ .github/workflows/streaming-skills-drift.yml exists; fails on PR when upstream plugin's manifest version differs from pinned without matching update
    3. ✓ Drift-gate generator has --check mode that exits non-zero on drift (mirrors G.2c pattern exactly)

    ## Live drift check result
    - `python3 tools/check_streaming_skills_drift.py --check` → exit code [0/1/3]
    - Pinned: 91d1871ef8c320be92bca955c8e42492a2778cb4
    - Live HEAD: [actual]
    - [if drift] Note: drift detection works correctly — upstream has moved past pin; CI will fail any PR until pin is bumped (intentional H.3b behavior, not a defect)

    ## Regression results
    - `pytest tests/test_check_streaming_skills_drift.py`: [N]/[N] PASS
    - `pytest tests/test_profile_gating.py + test_per_family_isolation.py + test_canon_overlay.py`: [N]/[N] PASS
    - `pytest tests/golden/`: [N]/[N] PASS
    - `pytest tests/`: [N+2 - 2 pre-existing failures] PASS

    ## Vendor-pin discipline now uniform across:
    - `confluent-agent-skills` (kind: wiki-source) — H.1 vendored at SHA 91d1871e, used by /wiki:ingest
    - `streaming-skills-plugin` (kind: claude-plugin) — H.3a installed at SHA 91d1871e, used by upstream-skill activations
    Both pinned in tools/vendor-sources.json; both have generator/CI gate (wiki-source via wiki-lint.py drift detection from H.1-03; plugin via H.3b new gate).

    ## Deferred
    - Auto-bump-PR generator (Renovate-like) — not blocking
    - Per-skill drift (finer than commit-pin) — defer until overlay article needs more protection
    - Combined vendor-drift workflow (merge with tool-classification-drift) — premature

    ## Self-Check: PASSED
    ```
  </action>
  <acceptance_criteria>
    - `.planning/phases/H.3b-version-pin-ci-drift-gate/H.3b-01-SUMMARY.md` exists with `## Self-Check: PASSED`.
    - SUMMARY contains literal strings: `INST-01`, `streaming-skills-plugin`, `91d1871e`, `--check`, `vendor-pin discipline`.
    - SUMMARY documents the live drift check exit code.
    - `pytest tests/test_check_streaming_skills_drift.py -v` exits 0.
    - `git status` shows only the 4 plan-listed files + SUMMARY + STATE/ROADMAP/REQUIREMENTS metadata.
  </acceptance_criteria>
</task>

</tasks>

<verification>
After all tasks complete:

1. **Pin in place** — `python3 -c "import json; assert json.load(open('tools/vendor-sources.json'))['streaming-skills-plugin']['commit']=='91d1871ef8c320be92bca955c8e42492a2778cb4'"` exits 0.
2. **Check script works** — `python3 tools/check_streaming_skills_drift.py --help` exits 0; `python3 tools/check_streaming_skills_drift.py` exits 0 (default mode never errors on drift alone).
3. **CI workflow valid** — `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/streaming-skills-drift.yml'))"` exits 0.
4. **Tests pass** — `pytest tests/test_check_streaming_skills_drift.py -v` exits 0.
5. **No regressions** — `pytest tests/` exits 0 (or only same 2 pre-existing failures from H.4a/H.4b/H.4c).
6. **No spillover** — `git status` shows only the 4 plan-modified files + SUMMARY + .planning metadata. Nothing in `apply_engine.py`, `canon/`, `tools/profiles/`, `tests/golden/`.

All 6 must pass before phase complete. Failure → gap closure.
</verification>
