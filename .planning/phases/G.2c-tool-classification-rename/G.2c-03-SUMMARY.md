---
phase: G.2c-tool-classification-rename
plan: 03
subsystem: ci
tags: [github-actions, drift-detection, mcp-confluent, tool-classification, actg-01]

# Dependency graph
requires:
  - phase: G.2c-01
    provides: regenerate_tool_classification.py with --check mode (bidirectional drift detection)
provides:
  - GitHub Actions workflow that runs --check on every PR and push-to-main
  - Continuous enforcement of tool_classification.json <-> mcp-confluent registry parity
  - Path-scoped triggers so the workflow only runs when classification could have changed
affects: [G.2a, G.2b, future-mcp-confluent-version-bumps]

# Tech tracking
tech-stack:
  added: [actions/setup-node@v4]
  patterns: [path-scoped workflow triggers, dual-trigger PR+push-to-main, fail-fast tool verification]

key-files:
  created: [.github/workflows/tool-classification-drift.yml]
  modified: []

key-decisions:
  - "Workflow uses Node 22 (matches .mcp.json runtime) + Python 3.12 (matches existing CI workflows)"
  - "Path filters scoped to JSON, generator, and workflow file — does not run on unrelated commits"
  - "Verify npm --version step added before generator call to surface PATH issues with a clear error instead of cryptic FileNotFoundError deep in subprocess.run stack"
  - "No submodules:true on checkout (unlike canon-parity.yml) — drift check is self-contained and does not consult fsi-dsp"
  - "Dual-trigger pull_request + push:main (D-07) — PRs gate merges, push catches direct-to-main or merge-commit drift"

patterns-established:
  - "Drift-detection CI gate pattern: install pinned upstream → diff against committed artifact → fail bidirectionally"
  - "actions/setup-node@v4 + actions/setup-python@v5 combo for Python tooling that shells out to npm"

requirements-completed: [ACTG-01]

# Metrics
duration: 1min
completed: 2026-05-15
---

# Phase G.2c Plan 03: Tool-classification drift CI workflow Summary

**GitHub Actions workflow that runs `regenerate_tool_classification.py --check` on every PR + push-to-main, blocking merges when tool_classification.json diverges from the live @confluentinc/mcp-confluent registry in either direction.**

## Performance

- **Duration:** ~1 min
- **Started:** 2026-05-15T19:53:40Z
- **Completed:** 2026-05-15T19:54:55Z
- **Tasks:** 1
- **Files modified:** 1 (created)

## Accomplishments
- New workflow `.github/workflows/tool-classification-drift.yml` (55 lines) with bidirectional drift detection
- Path-scoped triggers: only runs when classification JSON, generator, or workflow itself changes
- Dual-trigger pattern (PR + push-to-main) ensures both review-time and merge-time gates
- Style matches existing canon-parity.yml / manifest-citations.yml / wiki-lint.yml (Python 3.12, actions/checkout@v4, actions/setup-python@v5)
- Node 22 setup added (matches .mcp.json runtime) since the generator npm-installs `@confluentinc/mcp-confluent`
- Defensive `npm --version` step surfaces PATH issues as a clear error rather than a cryptic FileNotFoundError in the generator's subprocess call

## Task Commits

1. **Task 1: Write tool-classification-drift.yml** — `1bb49d7` (ci)

## Files Created/Modified
- `.github/workflows/tool-classification-drift.yml` — new file; defines the drift-detection workflow

## Decisions Made
- **Node 22, Python 3.12** — Node 22 matches `.mcp.json` (same toolchain we ship the act rail with); Python 3.12 matches existing workflows. Keeps CI runtime aligned with developer/production runtime.
- **Path-scoped triggers** — Only runs when `tool_classification.json`, `regenerate_tool_classification.py`, or the workflow itself changes. Avoids burning CI minutes on unrelated PRs.
- **Dual-trigger PR + push:main per D-07** — PR gate blocks merge-time drift; push gate catches drift introduced via direct push to main or merge commits that bypass the path filter on the PR.
- **Defensive `npm --version` step** — Generator's `subprocess.run(["npm", "install", ...])` would otherwise raise FileNotFoundError with no actionable message. Explicit verification step renders the failure mode obvious.
- **No `submodules: true` on checkout** — Unlike canon-parity.yml and manifest-citations.yml, this workflow does not consult fsi-dsp; it's purely classification JSON ↔ npm package. Saves the submodule fetch.

## Deviations from Plan

None — plan executed exactly as written. The exact YAML content specified in Task 1 Step 2 was committed verbatim.

## Issues Encountered

**Sanity-check `--check` invocation deferred to post-merge.** Plan Step 5 asks for a local `python tools/regenerate_tool_classification.py --check` to confirm the workflow would be green on first push. This requires `tool_classification.json` to have a populated `mcp_confluent_version` field, which is the deliverable of G.2c-02 (running in parallel as a sibling executor). The current JSON still has the original snake_case shape from before G.2c-01/02 and lacks the version pin, so `--check` exits with "No --version provided and tool_classification.json has no mcp_confluent_version field". This is expected per the plan dependency order (G.2c-03 depends on G.2c-01, not G.2c-02); the workflow's CI run will exercise the full path after both G.2c-02 and G.2c-03 merge to main. Workflow correctness is verified statically (YAML parse, structural assertions, all acceptance grep checks pass).

## User Setup Required

None — no external service configuration required. The workflow runs on Confluent's GitHub Actions runners (ubuntu-latest) using public actions.

## Next Phase Readiness

- ACTG-01 is now an **enforced property** rather than a snapshot: G.2c-02 fixes the JSON, this workflow keeps it fixed.
- Next mcp-confluent version bump (e.g., 1.3.0 → 1.4.0) is a deliberate, reviewable PR that must include the regenerated JSON; CI will fail until the regeneration is committed.
- G.2a (mcp-confluent tool-call executor) can now rely on `tool_classification.json` keys matching live tool names, unblocking the runtime classification lookup.

---

## Self-Check: PASSED

**File existence:**
- FOUND: .github/workflows/tool-classification-drift.yml

**Commit existence:**
- FOUND: 1bb49d7 (ci(G.2c-03): add tool-classification-drift workflow)

**Acceptance criteria (from plan):**
- `test -f .github/workflows/tool-classification-drift.yml` → exit 0 (OK)
- YAML parse via `python -c "import yaml; yaml.safe_load(...)"` → exit 0 (OK)
- Structural assertions (name, triggers, steps, --check invocation, setup-node, setup-python) → all passed
- All grep-based acceptance checks → all matched
- `git diff --quiet` on protected files (tool_classification.json, profile JSONs, tests/, apply_engine.py) → exit 0 (no protected files modified by this plan)

---
*Phase: G.2c-tool-classification-rename*
*Completed: 2026-05-15*
