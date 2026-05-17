# Phase H.2: Eval harness extension to all cflt-ai skills — Discussion Log

> **Audit trail only.** Decisions captured in `H.2-CONTEXT.md`; this log preserves alternatives considered.

**Date:** 2026-05-17
**Phase:** H.2-eval-harness-extension
**Areas discussed:** Schema strategy, LLM-in-CI policy, Threshold strictness, Trip-wire encoding mapping

---

## Schema strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Hybrid — keep MD, add JSON for wiki skills only (Recommended) | Existing /ask, /review, /act stay markdown-per-case (89 cases keep working). NEW evals.json for the 4 wiki skills + thin JSON wrappers for /review, /dsp:plan, /dsp:apply referencing existing MD cases. Single pytest runner consumes both formats. | ✓ |
| Migrate everything to evals.json | Convert all 89 cases + author new ones. Stronger uniformity; substantial migration; breaks v1.0 invariants. | |
| Keep MD only — abandon evals.json schema | Document MD as cflt-ai's shape. Reinterpret WIKI-08 success criterion. Cross-pollination becomes manual translation. | |

**User's choice:** Hybrid
**Notes:** Pre-existing markdown-per-case format already encodes more than upstream evals.json (required_claims/forbidden_claims/floor_model/negative_space). The hybrid keeps the richer format where it's already paying its way; adopts JSON only where new authoring is happening. Discovery during scout: 89 existing cases — substantially more than expected.

---

## LLM-in-CI policy

| Option | Description | Selected |
|--------|-------------|----------|
| Structural-only (Recommended) | CI runs regex/file checks. No model calls. Matches v1.0 behavior. Trip-wires encoded as content-presence assertions. | ✓ |
| Hybrid — structural in CI + LLM nightly | Per-PR structural + nightly LLM-as-judge on a sample. Catches floor-model drift without per-PR cost. Adds workflow complexity. | |
| Full LLM-as-judge in CI | Every PR runs LLM eval. Real $$ cost, non-deterministic. Matches upstream confluentinc/agent-skills for some cases. | |

**User's choice:** Structural-only
**Notes:** KNOW-04, KNOW-05, REVW-01, ACT-07 remain structural-only per v1.0 closure decisions. Live LLM evaluation explicitly deferred to a future phase if real regressions surface.

---

## Threshold strictness

| Option | Description | Selected |
|--------|-------------|----------|
| 90% uniform (Recommended) | Matches upstream + roadmap WIKI-08 verbatim. Simple to enforce. Engineering-load minimal. | ✓ |
| Per-skill: 95% for /dsp:apply, 90% others | /dsp:apply has highest stakes (real cloud changes via terraform-module). | |
| Floor-model tiered (Haiku 90%, Sonnet 95%) | Mirrors existing /ask harness. Per-floor expectations already in case frontmatter. | |

**User's choice:** 90% uniform
**Notes:** Existing /ask harness retains its tiering (it predates the new schema). New JSON cases are floor-agnostic. Per-skill or per-floor overrides can be added as small follow-ups if real regressions emerge.

---

## Trip-wire encoding mapping

| Option | Description | Selected |
|--------|-------------|----------|
| Distribute across /review, /dsp:plan, /wiki:ingest (Recommended) | 4 in /review (claim extraction), 3 in /dsp:plan (gate violations), 2 in /wiki:ingest (content-quality). Total 9; minimum 5 satisfied. | ✓ |
| Concentrate in /review only | All 9 as /review expectations. Simpler distribution; less coverage. | |
| Cover all 9 across all 7 skills | Maximum coverage; 63 case-expectations to author. | |

**User's choice:** Distribute across /review, /dsp:plan, /wiki:ingest
**Notes:** Distribution matches each trip-wire to the skill most likely to surface a violation. CONTEXT.md D-08 has the per-trip-wire expectation strings ready to drop into evals.json files.

---

## Claude's Discretion (decided without AskUserQuestion, documented in CONTEXT.md)

- **D-11 case authoring approach:** Hand-write 40 new wiki-skill cases manually. Draw on `wiki/_queue.md` (real coverage gaps), `raw/_ingest.md` Processed (happy-path fixtures), `tools/wiki-lint.py` TDD tests (drift-detection cases), and `confluentinc/agent-skills` upstream cases (shape exemplars only).
- **CI workflow path scoping:** `tests/evals/**, tests/golden/**, wiki/**, .claude/commands/**, tools/**` — broad enough to catch skill behavior changes without firing on README edits.
- **Pytest runner location:** `tests/evals/run_skill_evals.py` per roadmap EVAL-01.
- **Per-skill grouping in runner:** Pytest `group_by_skill` collects cases by `EvalCase.skill` field; the per-skill 90% threshold check is the merge gate.
- **Test runner skeleton documented in `<specifics>`** so the executor doesn't have to invent the adapter pattern between MD and JSON formats.

## Deferred Ideas

- LLM-as-judge in CI — D-04/D-05 reject; defer to a follow-on phase if model-floor regressions emerge
- Migration of MD harnesses to JSON — D-01 keeps hybrid; migrate only if cross-pollination demand grows
- Per-skill threshold tuning — D-06 keeps 90% uniform; per-skill overrides if real engagement use proves any skill stickier
- Coverage reporting via pytest-html — D-11 leaves as Claude's Discretion
- Floor-model tiering on JSON cases — D-07 keeps floor-agnostic; add tiering if real drift surfaces
- Session-log mining via skill_review_dashboard.py — upstream's tool; defer to v3.0 observability phase
- Cross-skill eval sharing — D-08 distribution avoids overlap today; add `_common/expectations.json` later if multiple skills need the same trip-wire
