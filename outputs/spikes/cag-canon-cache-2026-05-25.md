# Spike: Cache-Augmented Generation for cflt-ai canon

**Date:** 2026-05-25
**Author:** Claude (spike spawned from review of arXiv:2412.15605v1)
**Status:** Measurement complete; recommendation below.

## Premise

Chan et al. 2024 ("Don't Do RAG: When Cache-Augmented Generation is All You
Need for Knowledge Tasks") shows that for bounded knowledge bases that fit a
long-context LLM, preloading + KV-caching beats retrieval (RAG) on latency,
retrieval error rate, and architecture. cflt-ai's internal knowledge surfaces
— canon overlays, wiki, vendored skills, MANIFEST — are bounded, slow-changing,
and high-trust. The question this spike answers: **how big is the bundle, and
where does it pay off?**

External MCP sources (`confluent-docs`, `context7`) are out of scope — they're
remote, version-sensitive, and the whole point is that they're fresher than any
local snapshot. CAG can't replace them. It can replace repeated re-reads of our
own knowledge.

## What was built

- **`tools/canon_preload.py`** (~220 lines, pure stdlib) — assembles three
  named bundles from internal canon. CLI subcommands: `size`, `emit`, `files`.
- **`tests/test_canon_preload.py`** — 23 unit tests; all pass.

The tool produces deterministic, cache-friendly text or JSON output suitable
for emission as the first content block in a Claude API call (where Anthropic's
prompt-prefix cache will pick it up automatically when marked
`cache_control: ephemeral`).

## Measured sizes

```
bundle          files       bytes     ~tokens
------          -----     -------    --------
canon               6       29782        7445
navigation         13      214295       53573
full              122     1366736      341684
```

(Token estimates use a 4 chars/token heuristic; Anthropic's tokenizer differs by ≤10%.)

### Bundle contents

| Bundle | Includes | Excludes | Fits in |
|---|---|---|---|
| **canon** | CLAUDE.md, MANIFEST.yaml, canon/base/defaults.yaml, canon/industry/fsi/overrides.yaml, canon/customer/acme-bank/overrides.yaml | Everything else | Anywhere |
| **navigation** | canon + wiki/_index, _graph, _queue + 4 SKILL.md headers | Wiki article bodies, skill references/ | Sonnet 4.6 (200k), Opus 4.7 (1M) — comfortable headroom |
| **full** | navigation + entire wiki/concepts + wiki/patterns + all 4 skill references/ trees | Nothing internal | Opus 4.7 1M only — exceeds Sonnet 4.6 200k |

### Per-skill SKILL.md breakdown (FYI)

| Skill | SKILL.md bytes | references/ bytes (files) |
|---|---|---|
| kafka-streams-programming | 15,677 | 104,690 (7) |
| developing-kafka-python-client | 38,959 | 84,971 (16) |
| kafka-schema-registry | 9,973 | 39,057 (4) |
| confluent-cloud-cdc-tableflow | 26,264 | 87,963 (5) |

## Cost model

Anthropic prompt-prefix cache: 5-minute ephemeral TTL; minimum prefix size
1024 tokens to be cacheable.

| Token type | Sonnet 4.6 | Opus 4.7 |
|---|---|---|
| Base input | $3.00 / M | $15.00 / M |
| Cache write | $3.75 / M (1.25×) | $18.75 / M (1.25×) |
| Cache read (hit) | $0.30 / M (10% base) | $1.50 / M (10% base) |

**Break-even** (number of cache-hit reads before the cache-write premium is
amortized): ~3 reads at Sonnet rates, ~3 reads at Opus rates. After that
every additional hit saves 90% of the input cost on the cached portion.

## Scenarios — where it pays off

### 1. `/wiki:validate --full` sweep (83 articles)

Today: each article validated against MCP + cross-referenced. Per-invocation
the skill carries ~50k tokens of canon + wiki TOC + skill context regardless
of which article it's working on.

| Strategy | Input tokens billed | Cost (Sonnet) |
|---|---|---|
| **No caching** (status quo) | 83 × 53k = 4.4M | ~$13.20 |
| **Navigation cached** | 53k write + 82 × 53k cached read | ~$0.20 + $1.30 = ~$1.50 |
| **Single Opus 4.7 sweep with full bundle preloaded in context** | 342k once + per-article reasoning | ~$5.13 (input) + output |

**Verdict:** ~88% savings vs status quo with navigation caching. **CLEAR WIN.**
If the skill spec restructures `/wiki:validate` to fan out per-article with a
cached prefix, the math holds. If instead it runs as one big Opus subagent that
reads everything once, that's also a win on different math (more output cost,
less input redundancy).

### 2. `/ask` interactive session

Today: each `/ask` reads canon + searches wiki on demand. The model often
re-reads the same canon/skill context across queries within the same chat.

| Strategy | Assumes | Outcome |
|---|---|---|
| **No caching** | 1-2 queries / session | Current behavior; no change |
| **Navigation cached** | 5+ queries in 5 min | Break-even at 3 reads; clear win at 5+ |
| **Full cached** | 10+ queries in 5 min on Opus | Win, but write cost is steeper |

**Verdict:** marginal for single queries; worth it for deep-dive sessions.
The user has to opt in by structuring questions in a session. **DEFER** until
session-pattern data justifies the change.

### 3. `/review` one-off

Each `/review` is its own session; no prefix repetition across reviews.

**Verdict:** caching adds write-cost overhead with no read amortization.
**NO WIN.** Status quo wins.

### 4. `/ask --mode reconsolidate`

Reconsolidate rewrites articles after discoveries — needs broad wiki context.
A single reconsolidate touches multiple articles + skills.

**Verdict:** load `navigation` bundle into the Opus 4.7 subagent at session
start; no per-query API call repetition, so caching mechanics don't help, but
having the bundle in context replaces multiple targeted Read calls with
zero-cost in-context lookups. **MODERATE WIN.**

## Recommendation

**Adopt the navigation bundle for `/wiki:validate --full` sweeps. Defer
everywhere else.**

Specifically:

1. **Action now (small):** Land `tools/canon_preload.py` + tests (this commit).
   Tool is decoupled — anyone can `python3 tools/canon_preload.py emit
   --bundle navigation > prefix.md` for ad-hoc experiments.

2. **Action soon (medium):** Add a section to `.claude/commands/wiki/validate.md`
   documenting the preload pattern for full-corpus sweeps: emit navigation
   bundle as the first context block; subsequent per-article work cites article
   paths and uses targeted Reads. The skill spec should call out that for
   sweeps of ≥10 articles, the preload write cost pays back inside the run.

3. **Action later (large, conditional):** If session-usage data shows >5 `/ask`
   queries per 5-min window are common, document the same pattern for `/ask
   --mode reconsolidate` and possibly a new `/ask --preloaded` flag for
   batch-mode workflows.

4. **Don't do:** Wire prompt caching into `/review` — single-shot reviews don't
   repeat the prefix, so the cache write is wasted overhead.

## Limits & caveats

- **Token estimates are approximate** (4 chars/token heuristic). Anthropic's
  tokenizer yields ~3.5-4.0 for this content mix; expect ±10% variance.
- **Anthropic cache TTL is 5 minutes ephemeral.** Outside that window the
  prefix re-writes at the cache-write premium. Long-running batch sweeps
  benefit; sporadic invocations do not.
- **Claude Code runtime mediates `cache_control` markers.** The skill spec
  can't directly emit `cache_control: ephemeral` — that's an API-level
  concern. The practical lever is **prompt order**: putting the bundle first
  in the context lets the runtime cache it implicitly when invocations
  repeat. Skill specs should be written so the deterministic prefix comes
  first.
- **Bundle staleness is the failure mode.** If the wiki updates land mid-cache,
  the cached prefix is stale until the 5-min TTL expires. For
  `/wiki:validate`, this is acceptable (the sweep is the update). For `/ask`
  interactive, it could surprise the user. Mitigation: skill spec can re-emit
  the bundle when it detects writes to `wiki/` in the current session.
- **MCP routing is unchanged.** `confluent-docs` and `context7` remain
  authoritative for anything outside the bundle. CAG does not replace MCP —
  it replaces repeated re-reads of internal canon that MCP can't answer
  anyway.

## Next steps (if approved)

1. Commit `tools/canon_preload.py` + tests as a standalone tool (this spike).
2. Open a follow-up to add a `## Preload pattern for full sweeps` section to
   `.claude/commands/wiki/validate.md`.
3. Optional: instrument one `/wiki:validate --full` run with-and-without the
   preload prefix and compare actual Anthropic billing. The numbers above are
   modeled, not measured.

## Files

- `tools/canon_preload.py` — bundle assembler + CLI
- `tests/test_canon_preload.py` — 23 unit tests
- `outputs/spikes/cag-canon-cache-2026-05-25.md` — this report

## Reference

Chan, B.J., Chen, C-T., Cheng, J-H., Huang, H-H. (2024). *Don't Do RAG: When
Cache-Augmented Generation is All You Need for Knowledge Tasks.* arXiv:2412.15605v1.
