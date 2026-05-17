---
phase: H.2-eval-harness-extension
verified: 2026-05-17T00:00:00Z
status: passed
score: 12/12 must-haves verified
---

# Phase H.2: Eval Harness Extension Verification Report

**Phase Goal:** Every cflt-ai skill has `evals/evals.json` scoring prompts against grep-checkable `expectations[]` at 90% pass-rate threshold, gated by CI. Closes silent-drift gap for /review, /wiki:*, /dsp:plan, /dsp:apply. Ports upstream `confluentinc/agent-skills` schema verbatim. Encodes ≥5 of H.1's 9 trip-wires.

**Verified:** 2026-05-17
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Runner `tests/evals/run_skill_evals.py` exists with `MIN_PASS_RATE = 0.90` module constant | VERIFIED | File present (242 lines); `grep -c "^MIN_PASS_RATE = 0.90"` = 1 at line 26 |
| 2 | 7 evals.json files exist at correct paths | VERIFIED | All 7 dirs verified: `wiki-ingest, wiki-validate, wiki-lint, wiki-recommend, review, dsp-plan, dsp-apply` |
| 3 | Each evals.json has ≥10 entries with `skill_name` matching skill (leading slash) | VERIFIED | wiki-ingest=10, wiki-validate=10, wiki-lint=10, wiki-recommend=10, review=20, dsp-plan=25, dsp-apply=10. skill_name values: `/wiki:ingest, /wiki:validate, /wiki:lint, /wiki:recommend, /review, /dsp:plan, /dsp:apply` |
| 4 | All 9 H.1 trip-wires encoded verbatim (4 /review + 3 /dsp:plan + 2 /wiki:ingest = 9) | VERIFIED | Per-file grep counts confirm exactly: ingest=2, review=4, dsp-plan=3, dsp-apply=0; total=9 ≥ 5 floor |
| 5 | Pytest runner discovers all 7 new skills + existing /ask MD cases | VERIFIED | ALL_CASES discovers 8 skills: /ask (32), /dsp:apply (20), /dsp:plan (47), /review (36), /wiki:* (10 each) — total 175 cases |
| 6 | `python -m pytest tests/evals/run_skill_evals.py -v` exits 0 with `test_threshold_per_skill` and `test_all_seven_new_skills_discovered` passing | VERIFIED | `177 passed in 0.10s`; both named tests PASSED |
| 7 | `python -m pytest tests/evals/test_runner_adapters.py -v` exits 0 | VERIFIED | `9 passed in 0.22s` |
| 8 | `python -m pytest tests/golden/ -q --tb=no` exits 0 (existing MD cases unchanged) | VERIFIED | `539 passed in 0.69s` |
| 9 | `.github/workflows/skill-evals.yml` exists with valid YAML, paths-scoped PR trigger, push:main trigger, Python 3.12, three pytest invocations | VERIFIED | YAML parses; triggers `[pull_request, push]`; runs-on ubuntu-latest; 6 steps; 3 distinct pytest invocations (run_skill_evals, test_runner_adapters, tests/golden) |
| 10 | Zero D-04 lock matches in tests/evals/ (no subprocess/requests/anthropic/openai/httpx/model/API keys) | VERIFIED | Only 1 grep hit — a docstring line in test_runner_adapters.py reading "never run a subprocess" (documentation reassurance, not invocation). No SDK imports, no network calls. |
| 11 | `git diff --quiet tools/apply_engine.py .claude/commands/dsp-apply.md tests/golden/` exits 0 (D-11 + D-01 locks) | VERIFIED | D-11 HELD (runtime byte-identical); D-01 HELD (tests/golden/ untouched) |
| 12 | EVAL-01, EVAL-02, EVAL-03 marked Complete in REQUIREMENTS.md traceability | VERIFIED | Lines 79-81: all three rows marked `Complete (H.2-XX)` |

**Score:** 12/12 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tests/evals/run_skill_evals.py` | Runner with MIN_PASS_RATE=0.90 + adapters + threshold gate | VERIFIED | 242 lines; `load_md_cases`, `load_json_cases`, `_structural_pass`, `test_threshold_per_skill`, `test_all_seven_new_skills_discovered`, `EvalCase` namedtuple all present |
| `tests/evals/__init__.py` | Package marker | VERIFIED | Exists |
| `tests/evals/test_runner_adapters.py` | Adapter unit tests | VERIFIED | 9 tests collect + pass |
| `tests/evals/fixtures/sample_evals.json` | Off-glob fixture for adapter tests | VERIFIED | Named `sample_evals.json` (not `evals.json`) so runner glob excludes it |
| `tests/evals/wiki-ingest/evals.json` | 10 cases + 2 H.1 trip-wires verbatim | VERIFIED | 10 cases, 2 trip-wires (Avro src/main/avro/ + WarpStream fetch.min.bytes) |
| `tests/evals/wiki-validate/evals.json` | 10 cases | VERIFIED | 10 cases; skill_name=`/wiki:validate` |
| `tests/evals/wiki-lint/evals.json` | 10 cases | VERIFIED | 10 cases; skill_name=`/wiki:lint` |
| `tests/evals/wiki-recommend/evals.json` | 10 cases | VERIFIED | 10 cases; skill_name=`/wiki:recommend` |
| `tests/evals/review/evals.json` | ≥16 case_refs + 4 trip-wires | VERIFIED | 20 cases (16 case_refs all resolve + 4 trip-wires) |
| `tests/evals/dsp-plan/evals.json` | ≥22 case_refs + 3 trip-wires | VERIFIED | 25 cases (22 case_refs all resolve + 3 trip-wires) |
| `tests/evals/dsp-apply/evals.json` | ≥10 case_refs, 0 trip-wires | VERIFIED | 10 case_refs (all resolve to MD files with `skill: /dsp:apply`); 0 trip-wires per D-08 |
| `.github/workflows/skill-evals.yml` | CI gate workflow | VERIFIED | Valid YAML, dual triggers, Python 3.12, 3 pytest invocations |

### Key Link Verification

| From | To | Via | Status |
|------|-----|-----|--------|
| `run_skill_evals.py` | `tests/golden/*/cases/*.md` | `load_md_cases()` glob | WIRED — yields 89 records; tests pass |
| `run_skill_evals.py` | `tests/evals/*/evals.json` | `load_json_cases()` glob | WIRED — yields 86 records across 7 skills |
| `wiki-ingest/evals.json` | `wiki/concepts/avro-schema-source-directory.md` | verbatim trip-wire string `src/main/avro/` | WIRED — string present |
| `wiki-ingest/evals.json` | `wiki/concepts/warpstream-config-overrides.md` | verbatim trip-wire string `fetch.min.bytes` | WIRED — string present |
| `review/evals.json` | 4 trip-wire wiki concept articles | verbatim trip-wire strings | WIRED — all 4 grep counts = 1 |
| `dsp-plan/evals.json` | 3 trip-wire wiki concept articles | verbatim trip-wire strings | WIRED — all 3 grep counts = 1 |
| `review/evals.json` case_refs | `tests/golden/review/cases/*.md` | filename stem references | WIRED — 16/16 resolve |
| `dsp-plan/evals.json` case_refs | `tests/golden/act/cases/*.md` (plan cases) | filename stem references | WIRED — 22/22 resolve; none have `skill: /dsp:apply` |
| `dsp-apply/evals.json` case_refs | `tests/golden/act/cases/*.md` (apply cases) | filename stem references | WIRED — 10/10 resolve; all have `skill: /dsp:apply` |
| `skill-evals.yml` | `run_skill_evals.py` | pytest invocation | WIRED — step 4 |
| `skill-evals.yml` | `test_runner_adapters.py` | pytest invocation | WIRED — step 5 |
| `skill-evals.yml` | `tests/golden/` | pytest invocation (regression gate) | WIRED — step 6 |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Runner gate passes per-skill 90% threshold | `python3 -m pytest tests/evals/run_skill_evals.py -v` | 177 passed | PASS |
| Adapter unit tests pass | `python3 -m pytest tests/evals/test_runner_adapters.py -v` | 9 passed | PASS |
| Existing golden harness unchanged | `python3 -m pytest tests/golden/ -q --tb=no` | 539 passed | PASS |
| All three gates combined | `python3 -m pytest tests/evals/ tests/golden/ -q --tb=no` | 725 passed in 0.91s | PASS |
| Workflow YAML parses | `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/skill-evals.yml'))"` | Parses, name="Skill Evals", 6 steps | PASS |
| All 7 evals.json valid JSON | `python3 -c "json.load(...)" × 7` | All parse, counts ≥10 | PASS |
| `test_all_seven_new_skills_discovered` transitions RED→GREEN | Sub-test invocation | PASSED | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| EVAL-01 | H.2-01 | Runner parametrizes over skills/cases using upstream schema | SATISFIED | `run_skill_evals.py` collects 175 cases across 8 skills; `EvalCase` namedtuple locked at field order in adapter unit test |
| EVAL-02 | H.2-02, H.2-03 | Each of 7 skills has `evals.json` with ≥10 cases | SATISFIED | All 7 files exist; counts: 10/10/10/10/20/25/10; `test_all_seven_new_skills_discovered` PASSES |
| EVAL-03 | H.2-04 | CI runs harness on PR; 90% gate; ≥5 trip-wires encoded | SATISFIED | `.github/workflows/skill-evals.yml` runs harness on PR + main push; 90% gate enforced inside pytest via `test_threshold_per_skill`; 9 trip-wires encoded (well above ≥5 floor) |

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `tests/evals/test_runner_adapters.py` | docstring text "never run a subprocess" matched D-04 grep | Info | False positive — documentation reassuring no subprocess usage. No actual `subprocess` import or invocation. D-04 lock effectively held. |

No blocker anti-patterns. No TODO/FIXME/placeholder comments in any new file. No hardcoded empty returns. No model-SDK imports. No network calls.

### Trip-Wire Encoding Roll-up (EVAL-03 detail)

| Trip-wire | Target skill | Verbatim string present | Count |
|-----------|--------------|-------------------------|-------|
| #1 Tableflow changelog immutability | /dsp:plan | "Refuses to plan a Tableflow changelog mode change..." | 1 |
| #2 Tableflow-on-CDC | /review | "Flags Tableflow-on-CDC-source-topic claims as a violation..." | 1 |
| #3 Oracle XStream after.state.only | /dsp:plan | "Refuses to plan OracleXStreamSource with..." | 1 |
| #4 KS 4.x StreamsUncaughtExceptionHandler | /review | "Flags `StreamsUncaughtExceptionHandler` cited as a nested class..." | 1 |
| #5 Avro schema source dir | /wiki:ingest | "When ingesting an article that proposes Avro schemas under..." | 1 |
| #6 schema-aware producer | /review | "Flags kafka-console-producer usage in verification snippets..." | 1 |
| #7 WarpStream SR format | /dsp:plan | "Refuses to plan JSON Schema registration against WarpStream..." | 1 |
| #8 WarpStream fetch.min.bytes | /wiki:ingest | "When ingesting an article that proposes WarpStream..." | 1 |
| #9 EOS WarpStream throughput | /review | "Flags exactly-once-v2 on WarpStream claims as a throughput-cost violation..." | 1 |

**Total: 9/9 H.1 trip-wires encoded (180% of EVAL-03 ≥5 floor).**

### Lock Compliance Summary

| Lock | Description | Status |
|------|-------------|--------|
| D-01 | tests/golden/ unchanged (hybrid lock) | HELD — `git diff --quiet tests/golden/` exits 0 |
| D-03 | Verbatim upstream confluentinc/agent-skills schema | HELD — all 7 files use `{skill_name, evals:[{id, prompt, expected_output, files, expectations}]}` |
| D-04 | Structural-only (no LLM/network/subprocess) | HELD — only docstring text mention; no imports |
| D-06 | 90% threshold per skill (MIN_PASS_RATE constant) | HELD — single module-level constant at line 26 |
| D-08 | Trip-wire distribution: 2 ingest + 4 review + 3 plan + 0 apply | HELD — grep counts match exactly |
| D-09 | Paths-scoped CI triggers | HELD — both pull_request and push paths-scoped to same 5 dirs + workflow file |
| D-11 | tools/apply_engine.py + .claude/commands/dsp-apply.md byte-identical | HELD — `git diff --quiet` exits 0 |

### Gaps Summary

No gaps. All 12 locked must-haves verified. Phase goal achieved:

- Unified runner discovers cases from both MD (existing 89) and JSON (new 86 across 7 skills) formats
- 90% per-skill threshold enforced inside pytest (`test_threshold_per_skill`)
- All 7 required skills discovered (`test_all_seven_new_skills_discovered` transitioned RED→GREEN)
- All 9 H.1 trip-wires encoded verbatim (well above ≥5 EVAL-03 floor)
- CI workflow lands as paths-scoped PR + main gate
- Existing /ask MD harness untouched; all 539 golden tests still pass
- Runtime files (`tools/apply_engine.py`, `.claude/commands/dsp-apply.md`) byte-identical from milestone start

725 total pytest assertions green across the unified harness + adapter unit tests + golden regression gate.

---

_Verified: 2026-05-17_
_Verifier: Claude (gsd-verifier)_
