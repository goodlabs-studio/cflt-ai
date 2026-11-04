# App dependency remediation — 2026-11-04

Scope: clear open Dependabot alerts on `goodlabs-studio/cflt-ai` (88 open: 1 critical, 36 high, 35 medium, 16 low — all npm, all under `app/`).
Branch: `sriram-branch`. Operator: Claude Code (session-driven), requested by Sriram Kannan.

## Log

- 20:33Z Started. Toolchain: node v26.13.0, pnpm 11.20.0 local (CI release.yml pins pnpm 9). Overrides present in both package.json `pnpm` field (pnpm 9) and pnpm-workspace.yaml (pnpm 10+) — keep in sync.
- Baseline (before any change): `app/` install --frozen-lockfile ✅, `pnpm typecheck` ✅, `pnpm build` ✅.
- Python suite needed `fsi-dsp` submodule (was uninitialized; SSH clone failed → initialized over HTTPS at pinned `4687db88`) and `python-docx` in a scratch venv (py3.11, matches CI). Baseline: **1258 passed, 3 failed, 1 skipped**; CI suites: evals 200 ✅, runner adapters 9 ✅, golden 678 ✅; wiki-lint exit 0; check-citations ✅ (42/78).
- Pre-existing failures (unrelated to app/, not introduced here):
  - `test_wiki_tools::test_flox_manifest_exists`, `::test_flox_manifest_has_pyyaml_deps` — no `.flox/` env on this machine (flox optional per CONTRIBUTING).
  - `test_wiki_citations::TestNoRawPaths::test_no_raw_fsi_dsp_paths_in_sources` — `wiki/patterns/flink-coe-security.md` cites a raw `raw/repos/fsi-dsp/...` path instead of an `fsi-dsp://` URI.
- Started fsi-dsp doc review (user request, mid-job): two read-only background agents → `outputs/reports/fsi-dsp-doc-review-2026-11-04-part-a.md` (docs/, README, EXECSUMMARY, CLAUDE.md) and `-part-b.md` (accelerators/, scenarios/, reference/, observability/, modules/). `.planning/` and `.github/` skipped.
- Push guard note: `gh api` now denied for Claude (deny rules added earlier at user request) → used saved alert export instead. Max patched floor per package from alerts: electron ≥42.11.9 (so 41.x insufficient → chose 45.x current stable), dompurify ≥3.4.17, mermaid ≥11.16.1, tar ≥7.5.18, vite ≥6.4.4, postcss ≥8.5.23, js-yaml ≥4.3.2, @xmldom/xmldom ≥0.9.12, katex ≥0.18.2, extract-zip (no fix).
- `pnpm audit` baseline: low 13 / moderate 37 / high 53 / critical 2.
- Step 1 (direct bumps in package.json): electron ^45.2.2, electron-builder ^26.18.1, vite ^6.4.5, postcss ^8.5.32, electron-vite ^3.1.0, mermaid ^11.17.2; then `pnpm install` + `pnpm update`. Audit → low 1 / moderate 11 / high 34 / critical 1. Remaining all transitive (tar, brace-expansion, js-yaml, @xmldom/xmldom, form-data, browserslist, baseline-browser-mapping, minimatch, katex) → overrides next. `pnpm install` exited 1 on `ERR_PNPM_IGNORED_BUILDS electron-winstaller` (new Windows-installer dep of electron-builder 26; not needed for mac builds) → must set it in allowBuilds.
- Electron 45.2.2 rejected by pnpm 11 `minimumReleaseAge` (published 2026-11-03, <24h) → respected policy, pinned `^45.2.1` (2026-10-31). Had to `git checkout` the lockfile (policy validates existing lockfile entries before resolving) and re-resolve; this undid the earlier `pnpm update`, so re-ran it after overrides.
- npm marks katex 0.18.11 deprecated ("accidentally published with breaking changes") → override katex to exact `0.18.10` (patched ≥0.18.2, not deprecated; mermaid declares ^0.16.47).
- Overrides (identical in `package.json` pnpm field + `pnpm-workspace.yaml`): tar ^7.5.21, brace-expansion (1.x ^1.1.21 / 2.x ^2.1.7 / 3–5.x ^5.0.12), js-yaml (3.x ^3.15.2 / 4.x ^4.3.2), @xmldom/xmldom ^0.9.12, form-data ^4.0.6, browserslist ^4.28.7, baseline-browser-mapping ^2.11.0, minimatch (7–10.x → ^11.0.1), katex 0.18.10, dompurify ^3.4.17, postcss ^8.5.23, nanoid ^3.3.18, source-map-js ^1.2.2, @babel/core ^7.29.6, postcss-selector-parser ^6.1.5; kept existing @tootallnate/once, tmp. Added `allowBuilds.electron-winstaller: false` (Windows-only installer, not needed).
- `extract-zip` (alert with no upstream fix) is gone from the tree: Electron 45 uses `@electron-internal/extract-zip`.
- **`pnpm audit`: 0 / 0 / 0 / 0** (was low 13 / mod 37 / high 53 / crit 2). Resolved: electron 45.2.1, electron-builder 26.18.1, vite 6.4.5, mermaid 11.17.2, dompurify 3.4.17, katex 0.18.10.
- typecheck ✅, build ✅ after upgrades.
- **Pre-existing CI bug found & fixed:** `pnpm-workspace.yaml` had no `packages:` field → pnpm 9 (pinned in `release.yml`) fails `pnpm install --frozen-lockfile` with "packages field missing or empty". Reproduced on the ORIGINAL HEAD files too (so release builds were already broken). Added `packages: ["."]`. Verified frozen install now passes on pnpm 9.15.9 and pnpm 11.20.0.
- Side request (user): subagents default to Haiku → set `env.CLAUDE_CODE_SUBAGENT_MODEL=haiku` in `~/.claude/settings.json` (global; new sessions). Recorded in memory `subagents-default-haiku`.
- Packaging smoke: `CSC_IDENTITY_AUTO_DISCOVERY=false electron-builder --mac --dir` ✅ (electron-builder 26.18.1 with minimatch 11 / tar 7.5.22 overrides; unsigned, notarization skipped as expected). Packaged runtime: Electron 45.2.1 / Chrome 156.0.8078.75.
- Python after deps change: 1258 passed / 3 failed (identical set to baseline — **0 regressions**); evals 200 ✅, adapters 9 ✅, golden 678 ✅, wiki-lint exit 0, citations ✅.
- Fixed one of the 3 pre-existing failures: `wiki/patterns/flink-coe-security.md` cited a raw `raw/repos/fsi-dsp/...` path → replaced with `fsi-dsp://accelerator/confluent-on-linuxone` (MANIFEST id verified). Now **1259 passed / 2 failed**; remaining 2 are `test_flox_manifest_*` (no `.flox/` env on this machine — flox optional per CONTRIBUTING; CI doesn't run this file).
- **Correction to earlier /wiki:lint pass today:** its 42 "MISSING-SOURCE" findings were false positives from the uninitialized `fsi-dsp` submodule. With the submodule present: 0 missing-source, and 15 real **STALE-SOURCE** findings (cited fsi-dsp files changed after `last_validated`). `wiki/_queue.md` Lint Findings regenerated (160 findings: stale 68, decayed 46, unverified 24, stale-source 15, stubs 3, low-confidence 3, vendor-drift 1).

## Checkpoint (update after every step)

- **State:** all fixes done and verified; committing on `sriram-branch` (2 commits: app deps; wiki citation + queue). fsi-dsp review agents still running.
- **Next:** push — BLOCKED by user's Claude-only push guard (pre-push hook + deny rules). Ask user: lift guard for this push, or push from own terminal. Then fold fsi-dsp review results into this log.
- **Rollback:** `git revert` the two commits (or `git reset --hard <prior HEAD dd5fb5c>` before push).
