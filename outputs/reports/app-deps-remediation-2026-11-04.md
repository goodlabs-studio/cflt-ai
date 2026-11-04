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
- Committed `9850790` (app deps) and `99f2246` (wiki citation + queue + this log) on `sriram-branch`. Push guard kept in place per user decision; **user pushes from their own terminal** (`git push origin sriram-branch`).
- fsi-dsp review **part B** (accelerators/, scenarios/, reference/, observability/, modules/) was stopped by the user mid-run; it had not written its report yet, so no part-B output exists. Not restarted. Part A (docs/, README, EXECSUMMARY, CLAUDE.md) still running.
- fsi-dsp review part B was then **resumed by the user** from its transcript; running again (same agent, report still pending).
- fsi-dsp review part B **stopped by the user again** after the resume; no part-B report written. Treating part B as cancelled unless the user asks to re-run it.
- fsi-dsp review part B handed back a **PARTIAL** report → `outputs/reports/fsi-dsp-doc-review-2026-11-04-part-b.md` (33/48 files read in full; mechanical scans over all 48). Counts: Critical 2 / High 16 / Medium 17 / Low 14. Spot-checked both Criticals myself:
  - C1 confirmed: `accelerators/confluent-on-linuxone/layers/04-audit/patches/kafka-audit.yaml` line 21 `confluent.security.event.router.config` fails `json.loads` (stray `"` before each route object) → FSI audit routing would not load.
  - C2 confirmed: `accelerators/confluent-on-linuxone/RUNBOOK.md` ~L95-99 copies secret templates to world-readable `/tmp`, edits real values there, and `oc apply`s from it.
  - Unread: 5 reference READMEs, 7 observability, 3 modules; H12/M16 unverified; M10 internal-looking hostnames NOT resolved (per never-connect rule) — needs human check.
- fsi-dsp review **part A complete** → `outputs/reports/fsi-dsp-doc-review-2026-11-04-part-a.md` (35/35 files; 55 findings: Critical 2 / High 15 / Medium 24 / Low 14; all relative links resolve; no credentials/IPs). Spot-checked both Criticals:
  - Client-identifying app codes still present in fsi-dsp `docs/adr/002:24`, `docs/adr/004:8,15` (and per report `docs/schema-guide.md:6,37`) — confirmed. This is the residue the 2026-09-29 client-data audit scrubbed from cflt-ai but not fsi-dsp.
  - `docs/csfle-guide.md` client config never sets `auto.register.schemas=false` / `use.latest.version=true` — confirmed (rule-less schema could be registered → plaintext PII).
- **Redacted** the client codes (and a client-specific domain example) from the part-A report before committing, so cflt-ai history doesn't regain them. Rescan of both reports + this log: 0 hits.

## Checkpoint (update after every step)

- **State:** DONE except push (user) and optional part-B remainder. Local commits on `sriram-branch`: 9850790, 99f2246, + review-reports commit.
- **Open items for the user:** (1) `git push origin sriram-branch` from own terminal; (2) fsi-dsp fixes belong in the fsi-dsp repo — top priority: remove client app codes, fix audit router JSON (part B C1), stop staging secrets in /tmp (part B C2), harden CSFLE client config (part A C2); (3) part B unread: 5 reference, 7 observability, 3 modules READMEs + M10 hostname check (human); (4) remaining 2 pytest failures are local flox env only.
- **Rollback:** `git revert` the three commits.
