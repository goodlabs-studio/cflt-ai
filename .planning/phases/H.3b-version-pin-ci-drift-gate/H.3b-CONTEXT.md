# Phase H.3b: Version pin + CI drift gate — Context

**Gathered:** 2026-05-17
**Status:** Ready for planning
**Mode:** Auto (--auto) — defaults selected from G.2c drift-gate pattern, H.1 vendor-sources schema, H.3a install state

<domain>
## Phase Boundary

Pin `streaming-skills-plugin` version + author the CI drift gate that fails any PR that drifts off the pinned version without updating the pin. Mirrors v1.0 Phase G.2c's pattern byte-for-byte where structurally possible: generator script with `--check` mode + path-scoped GitHub Actions workflow + dual `pull_request` + `push:main` triggers + bidirectional drift detection (live commit vs pinned commit; missing-but-installed; installed-but-missing).

After H.3b: `tools/vendor-sources.json` has a second entry (`streaming-skills-plugin`) alongside the existing `confluent-agent-skills` entry, with `kind: "claude-plugin"`; `tools/check_streaming_skills_drift.py` runs in `--check` mode against the upstream plugin manifest and exits non-zero on any pin drift; `.github/workflows/streaming-skills-drift.yml` fires on PR + push:main when any of (pin file, generator, workflow file) change.

**Out of scope:**
- /dsp:scaffold wrapper (H.3c — last sub-phase)
- Auto-bump PR generator (would create PRs that bump the pin; H.3b only DETECTS drift, doesn't auto-fix)
- Versioned changelog enforcement (don't gate on whether the upstream commit was a real version bump vs a routine commit)
- Plugin manifest content validation beyond the gitCommitSha pin (don't enforce that the four upstream skill names stay stable — different concern)

</domain>

<decisions>
## Implementation Decisions

### Pin file location and schema
- **D-01:** Extend the existing `tools/vendor-sources.json` (created in H.1) with a new entry for the plugin, rather than create a separate `tools/vendor-plugins.json`. Reason: H.1 D-? specifically marked the `kind` field as free-form to accommodate future kinds. Adding `kind: "claude-plugin"` here is the minimum-friction extension. One file, two kinds.
- **D-02:** New entry shape:
  ```json
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
  ```
  The `commit` field is the bidirectional anchor — same as `confluent-agent-skills` entry. Drift check compares against `git ls-remote https://github.com/confluentinc/agent-skills HEAD` (or the GitHub Releases API for the version tag, whichever is more reliable for the plugin marketplace publishing model).

### Drift-check generator
- **D-03:** New script `tools/check_streaming_skills_drift.py` (separate file, not extending `tools/regenerate_tool_classification.py` — different upstream source, different schema, different check semantics). Mirror the G.2c file's CLI shape exactly: `--check` flag for the CI gate (exits non-zero on drift); default mode without `--check` prints the comparison summary and exits 0 (useful for local diagnosis).
- **D-04:** Drift detection signals (all three cause `--check` to exit non-zero):
  1. **commit drift** — `git ls-remote https://github.com/confluentinc/agent-skills HEAD` returns a SHA that doesn't match the pinned `commit` field
  2. **marketplace not registered** — `~/.claude/plugins/known_marketplaces.json` doesn't contain `confluent-agent-skills` entry
  3. **plugin not installed** — `~/.claude/plugins/installed_plugins.json` doesn't contain `streaming-skills-plugin@confluent-agent-skills`
  Signals 2 + 3 are warnings in CI (the CI runner doesn't have local Claude plugins installed) — the `--check` mode in CI ONLY enforces signal 1; signals 2 + 3 are diagnostic for local runs.
- **D-05:** Use only Python stdlib + `subprocess.run` (for `git ls-remote`). No new dependency. Same posture as `regenerate_tool_classification.py` which uses `subprocess.run` for `npm`.

### CI workflow
- **D-06:** New `.github/workflows/streaming-skills-drift.yml` mirroring `.github/workflows/tool-classification-drift.yml` exactly:
  - `name: Streaming Skills Plugin Drift`
  - `pull_request` + `push: branches: [main]` triggers
  - Path scoping: `tools/vendor-sources.json`, `tools/check_streaming_skills_drift.py`, `.github/workflows/streaming-skills-drift.yml`
  - Steps: checkout → setup-python 3.12 → run `python tools/check_streaming_skills_drift.py --check`
  - No Node.js step (the check uses `git ls-remote`, not npm)
- **D-07:** Workflow does NOT setup-node — that's the only structural deviation from G.2c. Node was needed there because the generator npm-installed the upstream package; H.3b just queries `git ls-remote` so no Node toolchain needed.

### Test surface
- **D-08:** Unit tests for the drift checker: `tests/test_check_streaming_skills_drift.py` (new file) covering:
  1. Pin-matches-mock-HEAD → `--check` exits 0
  2. Pin-mismatches-mock-HEAD → `--check` exits 1, prints drift report to stderr
  3. vendor-sources.json missing the `streaming-skills-plugin` entry → exits 2 (config error, distinct from drift)
  4. `git ls-remote` returns empty / network failure → exits 3 (transient error, distinct from drift) — but in CI this is fail-loud because the upstream is reachable on github.com
- **D-09:** Test uses `monkeypatch` to mock `subprocess.run` for `git ls-remote` — no real network calls during tests. The CI workflow run is the only place real `git ls-remote` happens. Pattern matches `regenerate_tool_classification.py`'s test posture.

### Folded Todos
None — `todo match-phase H.3b` returned zero matches.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project canon
- `CLAUDE.md` (project root) — Working Style + canon overlay enforcement (informs drift-check error messages: every override traceable to canon).
- `.planning/REQUIREMENTS.md` §INST-01 — "`.github/workflows/streaming-skills-drift.yml` fails PRs that bump the upstream plugin without updating the pin (mirrors G.2c drift-gate pattern)".

### Prior-phase contexts (patterns to mirror)
- `.planning/phases/G.2c-tool-classification-rename/G.2c-CONTEXT.md` — Generator + `--check` mode + CI drift gate pattern. H.3b is the second instance.
- `.planning/phases/H.1-wiki-ingest-agent-skills/H.1-CONTEXT.md` — `tools/vendor-sources.json` schema + `kind` field provenance (H.1 D-? declared `kind` as free-form to support claude-plugin later).
- `.planning/phases/H.3a-plugin-install-canon-overlay-wiki-article/H.3a-CONTEXT.md` — D-02 explicitly deferred pinning to H.3b; references the install state at SHA 91d1871e that H.3b now formalizes.

### Existing exemplars
- `tools/regenerate_tool_classification.py` — Generator with `--check` mode; CLI shape to mirror.
- `.github/workflows/tool-classification-drift.yml` — CI workflow shape to mirror (minus the Node.js step).

### Existing code under modification
- `tools/vendor-sources.json` — Extend with `streaming-skills-plugin` entry.
- `tools/check_streaming_skills_drift.py` (new) — Drift check generator.
- `.github/workflows/streaming-skills-drift.yml` (new) — CI workflow.
- `tests/test_check_streaming_skills_drift.py` (new) — Unit tests.

### Runtime sources (read-only — drift check consults these)
- `~/.claude/plugins/installed_plugins.json` — installed state with `gitCommitSha`.
- `~/.claude/plugins/known_marketplaces.json` — marketplace registration.
- `https://github.com/confluentinc/agent-skills` — upstream HEAD for `git ls-remote`.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`tools/regenerate_tool_classification.py` CLI shape** — `--check` flag, `--dry-run` flag, `--help` text style — H.3b's script copies the CLI shape verbatim, swaps the data source.
- **`.github/workflows/tool-classification-drift.yml` structure** — Path-scoped triggers, defensive `npm --version` (here it's `git --version` instead), `Setup Python 3.12`, single check step.
- **`tools/vendor-sources.json` `kind` field** — Already extensible; just add `claude-plugin` value.
- **G.2c's defensive verb-step pattern** — `npm --version` proved Node was on PATH; H.3b uses `git --version` for the same diagnostic visibility before the check step runs.

### Established Patterns
- **CI exits non-zero on drift; print structured stderr report** — G.2c convention; H.3b matches.
- **Path-scoped triggers** — Only fire when the workflow could affect outcomes (pin file + script + workflow file).
- **Test mocks subprocess.run** — No network in tests; reality check happens in CI.
- **Bidirectional drift signals** — G.2c flagged 3 (live > pinned, pinned > live, parser-extracted-zero); H.3b flags 3 (commit mismatch, marketplace missing, plugin missing).

### Integration Points
- **`tools/vendor-sources.json`** — Append one entry.
- **`tools/check_streaming_skills_drift.py`** (new) — New file.
- **`.github/workflows/streaming-skills-drift.yml`** (new) — New file.
- **`tests/test_check_streaming_skills_drift.py`** (new) — New file.
- **No engine changes, no canon changes, no profile changes.**

</code_context>

<specifics>
## Specific Ideas

- **`git ls-remote` over GitHub API**: avoids API rate limits, no auth needed, works in any CI runner with `git` (always present). Mirrors how the upstream Claude plugin marketplace itself probably resolves HEAD.
- **Exit-code semantics** (mirrors `regenerate_tool_classification.py`):
  - 0 = no drift (good)
  - 1 = drift detected (CI fail)
  - 2 = config error (vendor-sources.json missing entry / malformed)
  - 3 = transient error (network, git unavailable) — CI treats as fail; locally human can retry
- **Drift report shape** (stderr): one line per signal + recommendation:
  ```
  STREAMING_SKILLS_PLUGIN drift detected:
    pinned commit: 91d1871ef8c320be92bca955c8e42492a2778cb4
    live HEAD:     abc1234567890def...
  To fix: bump tools/vendor-sources.json streaming-skills-plugin.commit to <live SHA>, then re-run `/plugin install streaming-skills-plugin@confluent-agent-skills` locally and commit any resulting changes.
  ```

</specifics>

<deferred>
## Deferred Ideas

- **Auto-bump-PR generator** — Like Renovate but for this one pin. Useful but not in scope; manual PR is fine for now.
- **Per-skill drift** (e.g., does the `kafka-streams-programming/SKILL.md` content match what we authored the overlay against?) — More fine-grained than commit-pin drift. Defer until the overlay article needs more granular protection.
- **Combined vendor-drift workflow** — Eventually merge `tool-classification-drift.yml`, `streaming-skills-drift.yml`, and any future vendor-drift workflows into one. Premature now (2 workflows, different toolchains).
- **`tools/regenerate_vendor_plugins.py`** that actually re-installs the plugin and bumps the pin in one shot — `regenerate_tool_classification.py` does this for the tool table; H.3b's checker doesn't because plugin install is a Claude Code action, not a CLI action.

### Reviewed Todos (not folded)
None.

</deferred>

---

*Phase: H.3b-version-pin-ci-drift-gate*
*Context gathered: 2026-05-17 (auto-mode)*
