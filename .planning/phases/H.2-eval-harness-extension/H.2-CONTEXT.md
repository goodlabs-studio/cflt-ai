# Phase H.2: Eval harness extension to all cflt-ai skills — Context

**Gathered:** 2026-05-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Close the silent-drift gap where `/review`, `/wiki:ingest`, `/wiki:validate`, `/wiki:lint`, `/wiki:recommend`, `/dsp:plan`, and `/dsp:apply` have no behavioral regression guard. Author a unified eval harness that scores cases against grep-checkable `expectations[]` assertions at a 90% pass threshold, gated by CI on every PR. Encode ≥5 of the H.1 trip-wires as `expectations[]` to keep wiki + skills in lockstep. Existing `/ask` golden harness stays as-is per roadmap success criterion #1 — it predates the new schema and works.

Out of scope: H.3 (plugin install + canon overlay + `/dsp:scaffold`); H.4 (developer profile family); live LLM-as-judge in CI (deferred per D-02); migration of existing markdown-per-case cases to evals.json schema (deferred per D-01 hybrid choice).

</domain>

<decisions>
## Implementation Decisions

### Schema strategy
- **D-01:** Hybrid. Existing markdown-per-case harnesses stay as-is for `/ask` (32 cases), `/review` (16 cases), `/act` covering `/dsp:plan` + `/dsp:apply` (32 cases) — 89 validated cases keep working. **NEW** `evals/evals.json` files in `confluentinc/agent-skills` schema get authored for:
  1. `tests/evals/wiki-ingest/evals.json` — 10 cases for `/wiki:ingest`
  2. `tests/evals/wiki-validate/evals.json` — 10 cases for `/wiki:validate`
  3. `tests/evals/wiki-lint/evals.json` — 10 cases for `/wiki:lint`
  4. `tests/evals/wiki-recommend/evals.json` — 10 cases for `/wiki:recommend`
  5. `tests/evals/review/evals.json` — thin wrapper referencing the existing 16 `/review` MD cases by ID + adds 4 trip-wire expectations (per D-04 distribution)
  6. `tests/evals/dsp-plan/evals.json` — thin wrapper referencing the existing `/dsp:plan` slice of the act harness + adds 3 trip-wire expectations
  7. `tests/evals/dsp-apply/evals.json` — thin wrapper referencing the existing `/dsp:apply` slice of the act harness
- **D-02:** Single pytest runner at `tests/evals/run_skill_evals.py` parametrizes over BOTH formats. The runner discovers `evals.json` files plus the existing `tests/golden/*/cases/*.md` files. Each case (regardless of format) is parsed into a uniform internal `EvalCase` record with `id`, `prompt`, `expected_output`, `expectations[]`, `skill`, `floor_model`. The pytest output reports pass rate per skill.
- **D-03:** Upstream evals.json schema is reproduced **verbatim** (the `{"skill_name": "...", "evals": [{"id": N, "prompt": "...", "expected_output": "...", "files": [], "expectations": ["..."]}]}` shape from `confluentinc/agent-skills/skills/kafka-streams-programming/evals/evals.json`). This keeps cross-pollination clean — a future H.2 follow-up phase could mechanically import upstream eval cases verbatim.

### LLM-in-CI policy
- **D-04:** CI is **structural-only**. No LLM calls in `.github/workflows/skill-evals.yml`. Expectations are grep-checkable against case files and skill artifacts that exist on disk (e.g., "wiki article contains `confidence: high`", "raw/_ingest.md Processed section has 19 entries", "/review output has YAML claim block"). Trip-wire facts encoded as content-presence assertions in expectations strings — no LLM eval needed to catch them.
- **D-05:** Live LLM evaluation deferred. The four structural-only requirements from v1.0 (KNOW-04, KNOW-05, REVW-01, ACT-07) remain explicitly structural-only here. If we want LLM-as-judge in the future, a follow-on phase wires it as a separate nightly workflow with its own threshold — not blocking on PR.

### Threshold
- **D-06:** 90% pass rate uniform across all skills, per roadmap WIKI-08 verbatim. CI workflow `.github/workflows/skill-evals.yml` fails the PR when any skill drops below 90%. Reported per-skill (e.g., `/review: 14/16 = 87.5% — FAIL`) so the failure is actionable.
- **D-07:** No floor-model tiering for the new evals.json files (the existing `/ask` MD harness retains its Haiku-90%/Sonnet-95% tiering since it predates this schema). The 4 new wiki-skill harnesses are floor-agnostic in CI; per-floor tiering can be added as a follow-up if real model-floor regressions emerge.

### Trip-wire distribution (WIKI-07 cross-link)
- **D-08:** The 9 H.1 trip-wires are distributed across 3 skills' eval files such that each trip-wire is encoded in the skill most likely to surface a violation. Total ≥5 (roadmap minimum) — actual is 9, every trip-wire encoded somewhere. Distribution:
  - **`/review` (4 trip-wires)** — claim extraction catches these in customer documents:
    1. `cdc-tableflow-flink-decode-required` (Tableflow on CDC source topic)
    2. `exactly-once-v2-warpstream-throughput-cost` (EOS on WarpStream — review should flag)
    3. `schema-aware-console-producer-required` (kafka-console-producer vs kafka-avro-console-producer)
    4. `kafka-streams-4x-uncaught-exception-handler-import` (KS 4.x import path)
  - **`/dsp:plan` (3 trip-wires)** — gate violations these would catch in fsi-dsp artifact selection:
    5. `tableflow-changelog-mode-immutability` (planning a Tableflow change after first materialization)
    6. `oracle-xstream-source-limitations` (planning OracleXStream with `after.state.only`)
    7. `warpstream-schema-registry-format-constraint` (planning JSON Schema against WarpStream SR)
  - **`/wiki:ingest` (2 trip-wires)** — content-quality assertions for new article authoring:
    8. `avro-schema-source-directory` (avro path Avro 0 vs resources)
    9. `warpstream-config-overrides` (fetch.min.bytes / replication.factor cosmetic)

### CI workflow
- **D-09:** New `.github/workflows/skill-evals.yml` triggered on `pull_request` (paths-scoped to `tests/evals/`, `tests/golden/`, `wiki/`, `.claude/commands/`, `tools/`) AND `push: branches: [main]`. Runs `python -m pytest tests/evals/run_skill_evals.py -v` and fails workflow on non-zero exit. The 90% threshold per skill is enforced inside `run_skill_evals.py` via pytest's per-test-skill collection.
- **D-10:** No floor-model invocation in CI — the runner reads `floor_model` from MD cases (existing convention) but does not call the actual model; CI verifies that the case file's `floor_model` field is set to one of `haiku|sonnet|opus` and the expectations are structurally checkable. This is consistent with D-04 (structural-only).

### Case-authoring approach (Claude's Discretion per D-06)
- **D-11:** Author cases manually from real-world scenarios encountered during v1.0 + recently. For the 4 wiki skill harnesses (40 cases total minimum), draw on:
  - `wiki/_queue.md` for `/wiki:ingest` and `/wiki:lint` cases (real coverage gaps from /ask runs)
  - `raw/_ingest.md` Processed entries for `/wiki:ingest` "happy path" cases
  - `tools/wiki-lint.py` test suite (the H.1-03 TDD tests) for `/wiki:lint` drift detection cases
  - `confluentinc/agent-skills` eval cases as **shape exemplars** (don't copy content — they're different skills — but mirror the structure of "prompt + expected_output + expectations[]")

### Locked / out of scope (carrying forward)
- Existing `/ask` golden harness stays as-is per roadmap success criterion #1.
- 89 existing markdown-per-case cases continue passing; no migration in this phase.
- `tools/apply_engine.py` byte-identical (no runtime changes, eval harness is testing infrastructure).
- `.claude/commands/dsp-apply.md` byte-identical.
- No live LLM evaluation in CI (D-04/D-05).

### Claude's Discretion
- Exact `evals.json` per-case content (within the schema shape locked in D-03)
- Pytest discovery glob pattern (probably `tests/evals/*/evals.json`)
- Per-skill thin-wrapper format for `/review`, `/dsp:plan`, `/dsp:apply` (D-01 items 5/6/7) — these reference existing MD cases by ID; the executor can choose the reference mechanism (path glob vs explicit ID list)
- Whether to emit a coverage report artifact in CI (`pytest-html` or similar) — useful but not required by success criteria

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Source of upstream schema
- `raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/evals/evals.json` — exemplar of the verbatim `{"skill_name": "...", "evals": [...]}` shape we adopt. 32 cases, each with `id`, `prompt`, `expected_output`, `files`, `expectations[]`.
- `raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/evals/evals.json` — second exemplar (different skill domain, same schema).

### cflt-ai existing harness contract
- `tests/golden/ask/cases/*.md` — markdown-per-case exemplar (32 cases); frontmatter shape with `id, query, expected_route, floor_model, tags, required_claims, forbidden_claims`; body has structured "MUST contain"/"MUST NOT contain"/"Negative-space trigger" sections.
- `tests/golden/ask/test_golden_ask.py` — pytest runner for `/ask` MD format; reference for the new `tests/evals/run_skill_evals.py` runner shape.
- `tests/golden/review/cases/*.md` (16 cases) — pattern for review-specific cases (claim extraction reproducibility, premise-challenge step assertions).
- `tests/golden/act/cases/*.md` (32 cases) — covers `/dsp:plan` + `/dsp:apply` via the `skill` field. New `tests/evals/dsp-plan/evals.json` and `tests/evals/dsp-apply/evals.json` reference these MD cases.
- `tests/golden/act/test_golden_act.py` — pytest runner for /act format.

### Roadmap entry
- `.planning/ROADMAP.md` §"Phase H.2: Eval harness extension to all cflt-ai skills" — goal, depends_on, success criteria (EVAL-01, EVAL-02, EVAL-03).

### Prior phase context
- `.planning/phases/H.1-wiki-ingest-agent-skills/H.1-CONTEXT.md` — H.1's trip-wire inventory (D-05 Table 2) is the input to H.2 D-08.
- `.planning/phases/H.1-wiki-ingest-agent-skills/H.1-03-SUMMARY.md` — confirms which 9 trip-wires landed and at what wiki paths (needed for D-08 expectations strings).
- `.planning/phases/G.2c-tool-classification-rename/G.2c-CONTEXT.md` — CI drift gate pattern (G.2c established the version-pin + check-and-diff shape; H.2 reuses for skill-evals.yml).

### Requirements
- `.planning/REQUIREMENTS.md` §"Eval Harness Extension (H.2)" — EVAL-01, EVAL-02, EVAL-03 success criteria.
- `.planning/PROJECT.md` — current state (v2.0 active, H.1 complete) and Key Decisions table (Threshold-gated phase exits ⚠️ revisit — H.2 closes this gap per the entry).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`tests/golden/ask/test_golden_ask.py`** — pytest pattern: `load_case()`, `ALL_CASES = glob(...)`, parametrize, `REQUIRED_FIELDS` check. The new `tests/evals/run_skill_evals.py` runner mirrors this shape but adds JSON discovery.
- **`tests/golden/review/test_golden_review.py`** — same shape as ask. Reference for cross-format compatibility (REVIEW_CASES filtered from ALL_CASES).
- **`tools/wiki-lint.py`** — exit-code-based assertion model (0 = clean, non-zero = findings). New `/wiki:lint` evals cases test this behavior structurally (e.g., "wiki-lint exits 0 on the test fixture").
- **`raw/_ingest.md`** Processed section — real ingest history; cases for `/wiki:ingest` can reference processed entries as "happy path" fixtures.
- **`raw/vendor/confluent-agent-skills/91d1871e/`** — vendored exemplar evals.json files for schema reference (D-03).

### Established Patterns
- **YAML frontmatter comma-separated tag arrays** (locked in H.1 revision). New evals.json cases use JSON arrays natively — no YAML-tag concern.
- **Pytest discovery via glob** (existing in 3 harnesses; new runner adds JSON glob alongside MD glob).
- **Structural-only verification** (existing across v1.0; H.2 D-04 makes this an explicit phase decision rather than a tacit one).
- **Floor-model field on MD cases** (`floor_model: haiku|sonnet|opus`); new evals.json cases don't require this — but the runner accepts an optional `floor_model` field for consistency.
- **Frontmatter-driven CI workflow paths** (G.2c CI workflow + H.1-03 wiki-vendor-drift extension). New skill-evals.yml mirrors the paths-scoping shape.

### Integration Points
- `tests/evals/` is a NEW directory. Existing `tests/` has `golden/` and the unit-test files. `tests/evals/run_skill_evals.py` + 7 `evals/<skill>/evals.json` files live here.
- `.github/workflows/skill-evals.yml` is a NEW file. Existing CI workflows: `canon-parity.yml`, `tool-classification-drift.yml`, `citation-resolution.yml`, `id-stability.yml`. New workflow follows their shape (Node 22 + Python 3.12 standard).
- No runtime integration changes — eval harness lives entirely under `tests/` and `.github/workflows/`. `tools/apply_engine.py`, `.claude/commands/*.md`, `wiki/**/*.md` all untouched.

</code_context>

<specifics>
## Specific Ideas

### Per-skill case count budget
| Skill | Cases | Format | Source |
|-------|-------|--------|--------|
| /ask | 32 | MD (unchanged) | Existing |
| /review | 16 existing + 4 trip-wire expectations | MD + thin JSON wrapper | Existing + D-08 |
| /dsp:plan | ~24 existing + 3 trip-wire expectations | MD + thin JSON wrapper | Existing + D-08 |
| /dsp:apply | ~10 existing | MD + thin JSON wrapper | Existing |
| /wiki:ingest | 10 NEW | JSON | Hand-author with 2 trip-wires + 8 happy/edge cases |
| /wiki:validate | 10 NEW | JSON | Hand-author covering drift, decay, broken-link, orphan, schema-violation, source-attestation |
| /wiki:lint | 10 NEW | JSON | Hand-author covering broken-link, orphan, malformed, decay, drift, schema, exit-code, --fix flag |
| /wiki:recommend | 10 NEW | JSON | Hand-author covering alias-dispatch, write-back, queue-stub, no-coverage |
| **Total** | **89 existing + 40 new + 7 trip-wire expectation strings** | | |

### Expectations[] string patterns (verbatim shape from upstream)
- **Negative space:** `"Does NOT use kafka-console-producer anywhere — uses schema-aware producers (kafka-avro-console-producer or equivalent)"`
- **Positive structure:** `"Generates a docker-compose.yml with broker and schema-registry services"`
- **Import path:** `"App.java imports StreamsUncaughtExceptionHandler from org.apache.kafka.streams.errors (NOT as a nested class under KafkaStreams — that type does not exist in KS 4.x)"`
- **Tool behavior:** `"Asks about or confirms the target environment before generating code"`

All grep-checkable against generated artifacts or case files.

### Trip-wire expectation strings (D-08 inputs)
For `/review` evals (4 trip-wires):
- `"Flags Tableflow-on-CDC-source-topic claims as a violation — citing the Flink decode pattern as the required mitigation"`
- `"Flags exactly-once-v2 on WarpStream claims as a throughput-cost violation — citing the 'EOS enables idempotent producers internally' fact"`
- `"Flags kafka-console-producer usage in verification snippets as a Schema-Registry-incompatible tool — recommends kafka-avro-console-producer"`
- `"Flags `StreamsUncaughtExceptionHandler` cited as a nested class under `KafkaStreams` — corrects to org.apache.kafka.streams.errors import (KS 4.x rename)"`

For `/dsp:plan` evals (3 trip-wires):
- `"Refuses to plan a Tableflow changelog mode change on an already-materialized topic — directs to delete+recreate per immutability rule"`
- `"Refuses to plan OracleXStreamSource with `after.state.only=true` — that config is not supported by Oracle XStream"`
- `"Refuses to plan JSON Schema registration against WarpStream's built-in Schema Registry — accepts Avro or Protobuf only"`

For `/wiki:ingest` evals (2 trip-wires):
- `"When ingesting an article that proposes Avro schemas under `src/main/resources/avro/`, MCP-validation flags this as incorrect and the article cites `src/main/avro/` instead"`
- `"When ingesting an article that proposes WarpStream `fetch.min.bytes` config, MCP-validation flags this as unsupported and the article documents the omission"`

### Test runner skeleton
```python
# tests/evals/run_skill_evals.py
import json, yaml, glob, pytest

EvalCase = namedtuple("EvalCase", ["id", "skill", "prompt", "expected_output", "expectations", "floor_model"])

def load_md_cases():
    """Adapter for existing golden/<skill>/cases/*.md cases."""
    for path in glob.glob("tests/golden/*/cases/*.md"):
        fm = parse_frontmatter(path)
        yield EvalCase(
            id=fm["id"], skill=detect_skill(fm),
            prompt=fm.get("query", fm.get("request", "")),
            expected_output=read_body_must_contain(path),
            expectations=fm.get("required_claims", []) + [f"NOT: {c}" for c in fm.get("forbidden_claims", [])],
            floor_model=fm.get("floor_model"),
        )

def load_json_cases():
    """Loader for new tests/evals/<skill>/evals.json files."""
    for path in glob.glob("tests/evals/*/evals.json"):
        data = json.loads(open(path).read())
        for ev in data["evals"]:
            yield EvalCase(
                id=ev["id"], skill=data["skill_name"],
                prompt=ev["prompt"], expected_output=ev["expected_output"],
                expectations=ev["expectations"], floor_model=ev.get("floor_model"),
            )

ALL_CASES = list(load_md_cases()) + list(load_json_cases())

@pytest.mark.parametrize("case", ALL_CASES, ids=lambda c: f"{c.skill}/{c.id}")
def test_case_well_formed(case):
    assert case.expectations and len(case.expectations) >= 1

def test_threshold_per_skill():
    """Enforce 90% pass rate per skill — per D-06."""
    by_skill = group_by_skill(ALL_CASES)
    for skill, cases in by_skill.items():
        passed = sum(1 for c in cases if all_expectations_grep_match(c))
        rate = passed / len(cases)
        assert rate >= 0.90, f"{skill}: {passed}/{len(cases)} = {rate:.1%} < 90%"
```

### CI workflow skeleton (`.github/workflows/skill-evals.yml`)
```yaml
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
```

### Anti-references / non-goals
- Don't call any model in CI (D-04)
- Don't migrate `/ask`, `/review`, `/act` MD harnesses to evals.json (D-01)
- Don't introduce a Pydantic/JSON Schema for the evals.json shape — upstream's schema is stable and we mirror verbatim
- Don't add per-skill threshold overrides (D-06)
- Don't add live model invocation, even for trip-wire validation — they're encoded as grep-checkable expectations
- Don't introduce new MCP servers
- Don't change `tools/apply_engine.py` or `.claude/commands/dsp-apply.md` — they're testing infrastructure consumers, not testing infrastructure

</specifics>

<deferred>
## Deferred Ideas

- **LLM-as-judge in CI** — D-04/D-05 reject this for cost + determinism. Promote to a follow-on phase if real model-floor regressions emerge (KNOW-04/05, REVW-01, ACT-07 are the candidate canaries).
- **Migration of existing MD harnesses to evals.json** — D-01 keeps the hybrid model. Migrate only if cross-pollination demand grows or a future skill needs to live in both formats.
- **Per-skill threshold tuning** — D-06 keeps 90% uniform. If `/dsp:apply` proves stickier than 90% (real engagement use), promote a per-skill override as a small follow-up.
- **Coverage reporting via pytest-html or similar** — D-11 leaves this as Claude's Discretion. If actually useful, add as a separate workflow artifact.
- **Floor-model tiering on JSON cases** — D-07 keeps these floor-agnostic. Add per-floor expectations if real Haiku/Sonnet drift surfaces.
- **Eval case generation from production session logs** — `confluentinc/agent-skills/tools/skill_review_dashboard.py` is the upstream's session-log mining tool. We deferred this to a possible H.5 (or v3.0 observability phase) per the earlier H milestone discussion.
- **Cross-skill eval sharing** — e.g., a "schema-registry" trip-wire that applies to BOTH `/review` and `/wiki:ingest`. Today's D-08 distribution avoids overlap; if real engagements show the same trip-wire needs to fire from multiple skills, we'd add a shared `tests/evals/_common/expectations.json` later.

</deferred>

---

*Phase: H.2-eval-harness-extension*
*Context gathered: 2026-05-17*
