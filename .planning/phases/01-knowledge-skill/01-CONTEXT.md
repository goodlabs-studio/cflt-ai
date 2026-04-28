# Phase 1: Knowledge Skill - Context

**Gathered:** 2026-04-28
**Status:** Ready for planning

<domain>
## Phase Boundary

A single unified /ask skill with triage routing that collapses /ask and /wiki:recommend into one command with mode flags, a golden test harness proving correctness at model-floor thresholds, and wiki decay rules that keep coverage honest by demoting stale articles and auto-queuing coverage gaps.

</domain>

<decisions>
## Implementation Decisions

### Skill Consolidation & Mode Routing
- Explicit `--mode` flag required on /ask (ephemeral | report | reconsolidate) — no magic inference
- /wiki:recommend kept as a thin alias dispatching to `/ask --mode reconsolidate` — backwards compatibility
- `--mode report` writes to `outputs/reports/` only; `--mode reconsolidate` additionally writes back to wiki — distinct behaviors per persona
- All modes (including ephemeral) queue stubs on wiki misses to `_queue.md` per WIKI-05

### Triage Classifier Design
- Keyword + wiki-hit heuristic: wiki covers >80% of query → wiki-only; config/version-specific → wiki+MCP; multi-hop reasoning needed → deep
- Classifier lives inline in ask.md as a Step 1.5 decision block with explicit routing rules — single file
- `--force-route wiki|mcp|deep` flag bypasses classifier for debugging and golden harness testing
- Deep reasoning = multi-topic synthesis, architecture trade-off analysis, or "design me X" questions; wiki+MCP = single-topic lookup needing live validation

### Golden Harness Architecture
- YAML front matter (query, expected_route, floor_model, tags) + markdown body with expected answer patterns and forbidden patterns
- Structured rubric evaluation: correct route selected + required claims present + forbidden claims absent + sources cited — scored 0-1 per dimension
- `floor_model: haiku` or `floor_model: sonnet` field in YAML front matter per case
- Negative-space cases: queries that should be refused/redirected (out-of-domain, hallucination bait) with `expected: refuse` or `expected: redirect_to_mcp`

### Wiki Decay & Coverage Gaps
- `last_validated` tracked in each article's YAML front matter (existing field in article format spec)
- 90-day decay check runs at query time (during /ask Step 2) AND during `wiki-lint --full`
- Demotion = rewrite `confidence` field from `high` to `medium` in front matter; wiki-lint reports demotion; article still usable but flagged
- Auto-stub appends one-liner to `wiki/_queue.md` under "## Auto-Stubs" with query summary, date, mode — deduped by topic slug

### Claude's Discretion
- Internal implementation details of the rubric scoring (exact thresholds, weighting)
- Test case selection strategy for the 30+ golden cases (which topics to cover)
- Exact wording of the routing heuristic rules in the classifier block

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.claude/commands/ask.md` — current /ask skill with 5-step process (will be extended, not replaced)
- `.claude/commands/wiki/recommend.md` — current reconsolidate skill (process steps 1-7 reusable)
- `.claude/commands/wiki/references/article-format.md` — article format spec with YAML front matter schema
- `.claude/commands/wiki/references/quality-standards.md` — MCP routing and validation rules
- `tools/wiki-lint.py` — already parses front matter, scans for stale articles (>90 days) — extend for decay rule
- `tools/wiki-search.py` — full-text search across articles (usable by classifier for wiki-hit check)
- `wiki/_queue.md` — existing work queue (append target for auto-stubs)
- `wiki/_index.md` — master article registry (informs classifier wiki coverage check)

### Established Patterns
- Skills are markdown files in `.claude/commands/` with Step 1-N process + output format
- Wiki articles use YAML front matter (title, confidence, tags, sources, last_validated)
- CLI tools are Python scripts in `tools/` with argparse, CFLT_WIKI_ROOT env var
- Tests use pytest with fixture-based setup, test classes per logical domain
- Phase 0 established: pytest as test runner, fsi-dsp:// citation URIs, activity log schema

### Integration Points
- `.claude/commands/ask.md` is the entry point (user types `/ask`)
- `.claude/commands/wiki/recommend.md` becomes an alias (user types `/wiki:recommend`)
- `tests/golden/ask/` directory (new) — golden test cases
- `tools/wiki-lint.py` — needs decay rule integration
- `wiki/_queue.md` — auto-stub append target
- `wiki/activity/` — activity log entry per skill invocation

</code_context>

<specifics>
## Specific Ideas

- Three personas map to three modes: IC/SE → ephemeral, Embedded SA → report, SRE/Operator → reconsolidate
- Golden harness must test all three triage routes AND all three modes independently (combinatorial coverage)
- The classifier heuristic should be greppable/testable without running the full LLM — pure rule evaluation on extracted features

</specifics>

<deferred>
## Deferred Ideas

- Nightly harness automation (cron/CI scheduling) — needs CI infrastructure not in scope for Phase 1
- Model migration policy (what happens when a new model drops below threshold) — handled reactively per PROJECT.md
- Observability/metrics on classifier routing decisions — Phase 4+ per roadmap

</deferred>
