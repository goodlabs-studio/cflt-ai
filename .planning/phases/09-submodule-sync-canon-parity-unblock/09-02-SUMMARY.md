---
phase: 09-submodule-sync-canon-parity-unblock
plan: 02
subsystem: infra
tags: [submodule, drift-gate, ci, fsi-dsp, h3b-pattern, linuxone-accelerator]

# Dependency graph
requires:
  - phase: 09-submodule-sync-canon-parity-unblock
    provides: "raw/repos/fsi-dsp submodule pointer at upstream main HEAD (5a86fd2) — fresh pin for the gate to validate against"
  - phase: H.3b-version-pin-ci-drift-gate
    provides: "tools/check_streaming_skills_drift.py + .github/workflows/streaming-skills-drift.yml — exact pattern this plan mirrors (pure Python + git ls-remote, no Node.js, no API auth)"
provides:
  - "tools/check_submodule_drift.py — stale-submodule drift detector (SHA-match early-return + timestamp-delta fallback, 14-day window)"
  - ".github/workflows/submodule-drift.yml — CI gate on PR + push:main, path-scoped to raw/repos/fsi-dsp + the script + the workflow"
  - "tests/test_check_submodule_drift.py — 6 unit tests covering fresh-pointer / stale-pointer / config-error / transient-error / CLI plumbing / constants contract"
  - "Documented exit-code contract: 0 within window, 1 stale (CI fails), 2 config error, 3 transient/git error (fail-closed)"
affects: [10-accelerator-type-contract, 11-act-rail-dispatch, 12-wiki-ingest-linuxone]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Stale-submodule drift gate mirrors H.3b shape (streaming-skills-drift.yml) — pure Python + git ls-remote, no Node.js, no API auth"
    - "SHA-match early-return → timestamp-delta fallback: if committed SHA equals upstream HEAD, exit OK without resolving timestamps (no network beyond ls-remote); only fall through to %ct comparison when pointers diverge"
    - "Fail-closed transient-error policy: ls-remote failure / timestamp-unresolvable returns EXIT_TRANSIENT_ERR (3), never EXIT_OK — a network blip must never silently look like 'no drift'"
    - "Small monkeypatch-able _git_* helpers: _git_rev_parse_submodule_sha, _git_ls_remote, _git_show_timestamp — pure side-effects, individually testable; pure logic in check_drift() returns (exit_code, message) tuples and never raises"

key-files:
  created:
    - "tools/check_submodule_drift.py (267 lines)"
    - ".github/workflows/submodule-drift.yml (62 lines)"
    - "tests/test_check_submodule_drift.py (160 lines)"
  modified: []

key-decisions:
  - "Mirror H.3b shape exactly (not G.2c): pure Python + git ls-remote, no Node.js — submodule drift needs no upstream-package toolchain, just HEAD SHA comparison"
  - "Comparison axis: SHA-match early-return → timestamp-delta fallback. SHAs equal is the common case post-bump and short-circuits without needing %ct resolution; divergence triggers the 14-day window check"
  - "Drift window: 14 days. Long enough to absorb a normal review-and-merge cycle on upstream main; short enough that the LinuxONE accelerator stays fresh through v2.1's downstream phases (10/11/12)"
  - "Fail-closed on transient errors: EXIT_TRANSIENT_ERR (3), not EXIT_OK. Network blips / auth failures / git missing must never look like 'no drift' to CI — a silent pass would defeat the gate's purpose"
  - "TDD discipline: RED commit lands the 6-test suite before the implementation, GREEN commit lands the script that makes them pass. Each step independently revertable; the script can't ship without proving the failure shapes are covered"
  - "Auto-fetch deliberately NOT triggered when upstream SHA is unknown locally: returning EXIT_TRANSIENT_ERR is preferable to side-effecting a fetch that would hide drift behind a state change"
  - "Three-commit split (test RED / feat GREEN / feat-ci) over the plan's single-commit option: the project's documented commit_convention specifies the three-message shape, and three small commits give cleaner bisect + revert behavior than one combined commit"

patterns-established:
  - "Submodule drift gate template: parent-repo rev-parse for the pin + `git -C <submodule> ls-remote` for upstream + %ct comparison with configurable window — reusable for any future submodules (e.g., a second fsi-dsp-like overlay or a customer-overlay submodule)"

requirements-completed: [SUBM-03]

# Metrics
duration: 4min
completed: 2026-05-23
---

# Phase 09 Plan 02: Submodule drift CI gate Summary

**Added a stale-submodule CI guard (`tools/check_submodule_drift.py` + `.github/workflows/submodule-drift.yml` + 6 unit tests) that fails the workflow when `raw/repos/fsi-dsp` falls more than 14 days behind upstream main HEAD, mirroring the H.3b pattern (pure Python + `git ls-remote`, no Node.js, no API auth).**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-05-23T15:24:09Z
- **Completed:** 2026-05-23T15:27:46Z
- **Tasks:** 3
- **Files created:** 3 (script, workflow, tests)
- **Commits:** 3 (test RED, feat GREEN, feat-ci workflow)

## Accomplishments

- **Drift detector** at `tools/check_submodule_drift.py` (267 lines) — exposes `check_drift()` + `main()` + four exit-code constants (`EXIT_OK = 0`, `EXIT_DRIFT = 1`, `EXIT_CONFIG_ERR = 2`, `EXIT_TRANSIENT_ERR = 3`) + `DRIFT_WINDOW_DAYS = 14`. Helpers `_git_rev_parse_submodule_sha`, `_git_ls_remote`, `_git_show_timestamp` are individually monkeypatch-able for unit tests.
- **CI workflow** at `.github/workflows/submodule-drift.yml` (62 lines) — triggers on PR + push:main, path-scoped to `raw/repos/fsi-dsp` + the gate script + the workflow itself; uses `actions/checkout@v4` with `submodules: true`, Python 3.12, defensive `git --version` step, invokes `python tools/check_submodule_drift.py --check`. Zero Node.js (confirms H.3b shape, not G.2c).
- **Unit tests** at `tests/test_check_submodule_drift.py` (160 lines, 6 tests, all green in 0.65s) — fresh-pointer / stale-pointer / unregistered-submodule / ls-remote-failure / CLI-plumbing / constants contract.
- **Live `--check` against the freshly-bumped (Phase 09-01) submodule:** exits 0 (`OK: submodule at upstream origin/main HEAD (5a86fd28935d)`).
- **Full suite:** 966 passing; 1 pre-existing failure (`test_wiki_citations::test_no_raw_fsi_dsp_paths_in_sources`) carried forward from Phase 09-01's deferred-items.md (originates from `bd7f967` observability wiki commit, not Phase 09).
- **Targeted suites:** new tests (6) + H.3b drift tests (8) + canon-parity (2) + manifest (25) = 41/41 green.

## Final Exit-Code Contract

| Code | Name | Trigger | Message shape (stderr unless OK) |
| ---- | ---- | ------- | ----------------------------- |
| 0 | `EXIT_OK` | SHAs match (fresh pointer), OR SHAs differ but ≤14d delta | `OK: submodule at upstream origin/main HEAD (<sha12>)` or `OK: submodule N.Nd behind upstream origin/main HEAD (within 14d window)` |
| 1 | `EXIT_DRIFT` | SHAs differ and >14d delta | `STALE: raw/repos/fsi-dsp is N.N days behind upstream origin/main HEAD (<sha12>); drift window is 14 days.\nRemediate:\n  git submodule update --remote raw/repos/fsi-dsp\n  git add raw/repos/fsi-dsp\n  git commit -m "chore(submodule): bump fsi-dsp to upstream main"` |
| 2 | `EXIT_CONFIG_ERR` | `git rev-parse HEAD:<submodule_path>` fails (submodule not registered, path unknown) | `submodule <path> not registered in parent repo (git rev-parse failed: ...)` |
| 3 | `EXIT_TRANSIENT_ERR` | `git ls-remote` fails OR `git log -1 --format=%ct` cannot resolve upstream SHA OR ls-remote output malformed/empty | `git ls-remote origin main failed for raw/repos/fsi-dsp: ...` or `could not resolve upstream commit timestamp for <sha12> (git log failed: ...)` |

All three non-zero codes are CI failures (the workflow exits non-zero on any of them) — a transient error must never be treated as "no drift."

## Drift Window Choice (14 days) and Rationale

14 days balances two concerns documented in `.planning/phases/09-submodule-sync-canon-parity-unblock/09-CONTEXT.md` §specifics:

- **Long enough** to absorb a normal "merge to upstream main, then a few-day delay before the cflt-ai bump PR is reviewed and merged" cycle — wider than 7 days because review-week + holiday-week is a realistic delay; narrower than 30 days because beyond 14d the local submodule is materially behind and downstream phases (10/11/12) start risking parity drift with the LinuxONE accelerator tier.
- **Short enough** to catch silent rot: if a Phase 09-style bump shipped 2 weeks ago and no one has touched `raw/repos/fsi-dsp` since, that's the signal to refresh — not a multi-month "we forgot" lag.

The value is a module-level constant (`DRIFT_WINDOW_DAYS = 14`) so future plans can tighten or widen the window with a one-line PR; the unit tests use mocked `now_epoch` values relative to a fixed upstream timestamp, so adjusting the window does not require regenerating fixtures.

## Comparison Axis: SHA-match early-return → timestamp-delta fallback

The script does NOT compare SHAs alone (the H.3b approach), because two SHAs that differ within the 14-day window are *not* drift — they're a normal "upstream advanced a few commits, local pointer is still recent" state. Instead:

```text
       ┌─────────────────────────────────────┐
       │ git rev-parse HEAD:<submodule_path> │
       │  → committed_sha                    │
       └──────────────┬──────────────────────┘
                      │ (CalledProcessError → EXIT_CONFIG_ERR)
                      ▼
       ┌─────────────────────────────────────┐
       │ git -C <submodule> ls-remote        │
       │     origin main                     │
       │  → upstream_sha                     │
       └──────────────┬──────────────────────┘
                      │ (CalledProcessError → EXIT_TRANSIENT_ERR)
                      ▼
       ┌─────────────────────────────────────┐
       │ committed_sha == upstream_sha ?     │
       └────┬──────────────────────┬─────────┘
            │ yes                  │ no
            ▼                      ▼
        EXIT_OK             ┌───────────────────────────┐
       (early return,       │ git -C <submodule>        │
        no %ct call)        │   log -1 --format=%ct     │
                            │   <upstream_sha>          │
                            │  → upstream_ts            │
                            └──────┬────────────────────┘
                                   │ (CalledProcessError → EXIT_TRANSIENT_ERR)
                                   ▼
                            ┌──────────────────────────┐
                            │ (now_epoch - upstream_ts)│
                            │     / 86400 = delta_days │
                            └──────┬───────────────────┘
                                   │
                            ┌──────┴─────────────────┐
                            ▼                        ▼
                  delta_days ≤ 14            delta_days > 14
                       │                            │
                       ▼                            ▼
                   EXIT_OK                     EXIT_DRIFT
                                          (with remediation message)
```

The early-return matters for the common-case (post-bump) state: when the gate fires on a PR that just bumped the submodule, the SHAs match and the script exits in one `git rev-parse` + one `git ls-remote` call — no timestamp resolution, no risk that an unfetched upstream SHA forces a fall-through to EXIT_TRANSIENT_ERR.

## Path-Scoped Trigger Confirmation

The workflow's `on:` block lists exactly three paths under both `pull_request:` and `push:branches:[main]`:

- `raw/repos/fsi-dsp` — fires when the submodule pointer bumps (e.g., a future Phase 09-style refresh)
- `tools/check_submodule_drift.py` — fires when the gate script itself changes (CLI shape, exit-code changes, regex changes)
- `.github/workflows/submodule-drift.yml` — fires when this workflow file changes

The gate does NOT fire on every wiki edit or unrelated tooling change, keeping CI cost proportional to alignment risk.

## Live `--check` Result

```bash
$ python tools/check_submodule_drift.py --check
OK: submodule at upstream origin/main HEAD (5a86fd28935d)
$ echo "exit=$?"
exit=0
```

Verified twice: once during Task 1 (post-implementation), once during Task 3 (post-workflow). The freshly-bumped submodule pointer (Phase 09-01 landed `5a86fd28935d4732f22ea139634987769777faf8`) is byte-equal to `git ls-remote origin main`, so the early-return path is exercised.

## Commit SHAs for Traceability

```text
490b72b test(09-02): add test_check_submodule_drift with 6 behaviors (RED)
1336be5 feat(09-02): add tools/check_submodule_drift.py (drift detection — pure Python + git ls-remote)
12aef2e feat(ci): submodule-drift workflow — 14-day window, mirrors H.3b pattern
```

Files in each commit (verified via `git log -1 --name-only`):
- `490b72b` → `tests/test_check_submodule_drift.py`
- `1336be5` → `tools/check_submodule_drift.py`
- `12aef2e` → `.github/workflows/submodule-drift.yml`

## Files Created

- `tools/check_submodule_drift.py` (267 lines) — drift detector + CLI entry point
- `.github/workflows/submodule-drift.yml` (62 lines) — CI gate
- `tests/test_check_submodule_drift.py` (160 lines) — 6 unit tests

## Decisions Made

- **Mirror H.3b exactly, not G.2c.** Submodule drift needs only HEAD-SHA comparison via `git ls-remote` — no upstream-package npm install, no API auth. The G.2c shape with `actions/setup-node@v4` would be load without purpose; H.3b's lighter shape is the right template.
- **SHA-match early-return → timestamp-delta fallback.** Pure SHA equality (H.3b's check) would falsely report drift the moment upstream advances by one commit, even within the window. The timestamp comparison gives a real measure of staleness; the early-return ensures the common-case (post-bump) is fast and avoids needing the upstream commit object locally.
- **Fail-closed on transient errors.** EXIT_TRANSIENT_ERR (3) is documented and tested explicitly. A network blip / auth-denied / missing git binary must NEVER be treated as "no drift" — that's the silent-rot failure mode this gate is meant to prevent.
- **No auto-fetch in the gate.** When `git log -1 --format=%ct <upstream_sha>` fails because the upstream SHA hasn't been fetched locally, return EXIT_TRANSIENT_ERR rather than `git fetch`-ing it. Auto-fetch hides drift behind a side effect; failing closed surfaces it loudly.
- **TDD RED → GREEN discipline.** RED commit lands the 6-test suite before the implementation; GREEN commit lands the script that makes them pass; each is independently revertable. Tests cover all four exit codes via mocks (no real network in unit tests except the fresh-pointer SHA-match path, which is `pytest.skip`-able if offline).
- **Three commits over one combined commit.** The project's documented `<commit_convention>` lists three message shapes (`test(09-02):` / `feat(09-02):` / `feat(ci):`); this preserves clean bisect + revert behavior and matches H.3b's commit shape.

## Deviations from Plan

None substantive — plan executed as written. Two minor adjustments worth flagging:

1. **`now_epoch` parameter** to `check_drift()` is keyword-only by convention rather than positional. The plan's pseudocode shows it positional with default `None`; the implementation keeps `None` default but the test that uses it (`test_stale_pointer_beyond_window_returns_drift_with_remediation`) passes it as `now_epoch=now_epoch` (kwarg). Both call styles work; the kwarg style is more explicit and matches the dependency-injection pattern used by other testable functions in the repo.
2. **Commit shape.** Plan Task 3 proposed a single `feat(ci): add submodule-drift gate ...` commit covering all three files. Per the executor's `<commit_convention>` block in the prompt context, the three-commit split (test RED / feat GREEN / feat-ci) was used instead. Same files, same content, different commit boundaries — chosen for cleaner bisect and to honor the explicit TDD RED→GREEN discipline.

## Issues Encountered

- **Pre-existing `test_wiki_citations` failure carried forward from Phase 09-01.** `tests/test_wiki_citations.py::TestNoRawPaths::test_no_raw_fsi_dsp_paths_in_sources` flags 6 wiki articles (from commit `bd7f967`) that use raw `raw/repos/fsi-dsp/...` paths in their `sources:` frontmatter instead of `fsi-dsp://` ID form. This failure pre-dates Phase 09 entirely; it's documented in `.planning/phases/09-submodule-sync-canon-parity-unblock/deferred-items.md` from Plan 01.
  - **Resolution:** Out of scope for this plan (per SCOPE BOUNDARY). Confirmed neither the new script nor the new tests touch any wiki article — Phase 09-02 introduces zero new failures. Remediation belongs in Phase 12 wiki ingest discipline or a separate hygiene PR.

## User Setup Required

None — the workflow runs entirely on GitHub-hosted runners using `actions/checkout@v4` + `actions/setup-python@v5`. No secrets, no service accounts, no external API auth.

## Next Phase Readiness

- **Phase 10 (accelerator type contract):** READY. Submodule pointer is locked at `5a86fd2` and the new drift gate will catch silent rot on that pin before Phase 10's type-contract work can land against a stale tree.
- **Phase 11 (act rail dispatch):** Unblocked once Phase 10 publishes the type contract.
- **Phase 12 (wiki ingest):** Unblocked. The drift gate ensures the LinuxONE accelerator content visible on disk matches what Phase 12 will ingest.
- **Carry-forward:** The drift-gate template (parent-repo rev-parse + submodule ls-remote + %ct comparison) is reusable for any future submodules — second fsi-dsp-like overlay, customer-overlay submodule, etc. Document the pattern under wiki/patterns/ if a second submodule lands.

## Self-Check: PASSED

- File `tools/check_submodule_drift.py` exists: FOUND
- File `.github/workflows/submodule-drift.yml` exists: FOUND
- File `tests/test_check_submodule_drift.py` exists: FOUND
- Commit `490b72b` (test RED) exists: FOUND (verified via `git log --oneline | grep 490b72b`)
- Commit `1336be5` (feat GREEN script) exists: FOUND
- Commit `12aef2e` (feat-ci workflow) exists: FOUND
- `pytest tests/test_check_submodule_drift.py -v` exits 0 (6/6): VERIFIED
- `python tools/check_submodule_drift.py --check` exits 0: VERIFIED
- YAML parses (`yaml.safe_load`): VERIFIED
- Workflow contains zero `actions/setup-node@` references: VERIFIED
- Remediation message contains literal `git submodule update --remote raw/repos/fsi-dsp`: VERIFIED (runtime f-string output, not just docstring)
- Module constants `EXIT_OK=0`, `EXIT_DRIFT=1`, `EXIT_CONFIG_ERR=2`, `EXIT_TRANSIENT_ERR=3`, `DRIFT_WINDOW_DAYS=14`: VERIFIED via grep + test_module_exposes_exit_code_and_window_constants

---
*Phase: 09-submodule-sync-canon-parity-unblock*
*Completed: 2026-05-23*
