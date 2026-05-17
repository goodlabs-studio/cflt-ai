# Phase H.1: Wiki ingest from confluent-agent-skills references — Discussion Log

> **Audit trail only.** Decisions are captured in `H.1-CONTEXT.md`; this log preserves alternatives considered.

**Date:** 2026-05-16
**Phase:** H.1-wiki-ingest-agent-skills
**Areas discussed:** Source acquisition, Wiki namespacing, Trip-wire articles shape, Drift detection

---

## Source acquisition

| Option | Description | Selected |
|--------|-------------|----------|
| Vendored copy at pinned SHA (Recommended) | Copy needed reference files into `raw/vendor/confluent-agent-skills/<commit-sha>/` at ingest time. Pin in `tools/vendor-sources.json`. Upgrade = explicit PR. Deterministic, reviewable diffs, no submodule operational tax. | ✓ |
| Git submodule under raw/repos/ | Match fsi-dsp pattern — add as submodule. Pointer commit is the version. Slightly heavier in-repo state. | |
| Runtime fetch via gh api at ingest time | /wiki:ingest pulls files from upstream API when invoked, pinning by ref. Minimum repo footprint; upstream availability becomes a prerequisite. | |

**User's choice:** Vendored copy at pinned SHA
**Notes:** Mirrors G.2c pattern exactly. Pin recorded in new `tools/vendor-sources.json`; same file will be extended by H.3b for `streaming-skills-plugin`. Live upstream SHA captured during context-gathering: `91d1871ef8c320be92bca955c8e42492a2778cb4`.

---

## Wiki namespacing

| Option | Description | Selected |
|--------|-------------|----------|
| Standard wiki/concepts and wiki/patterns (Recommended) | Live alongside our own articles, distinguished by frontmatter `source: confluent-agent-skills@<sha>` and provenance footer. Same cross-linking, same _index/_graph, no fragmentation. | ✓ |
| Vendor subdir wiki/vendor/confluent/ | Separate namespace. Clear at-a-glance provenance; harder for cross-linking since search lives in two trees. | |
| Topic-prefixed filenames | confluent.kafka-streams-debugging.md. Visual distinction without filesystem split; introduces naming convention to maintain. | |

**User's choice:** Standard wiki/concepts and wiki/patterns
**Notes:** Downstream skills (/ask, /review, /dsp:plan) treat articles uniformly by confidence + validation status, not by origin. Frontmatter `source` field provides provenance without fragmenting the wiki.

---

## Trip-wire articles shape

| Option | Description | Selected |
|--------|-------------|----------|
| Standalone confidence:high micro-articles (Recommended) | Each trip-wire fact gets its own short article. Cite-able independently by /review, /dsp:plan, /ask. Matches WIKI-07 verbatim. Parent articles cross-link. | ✓ |
| Inline only with anchor links | Trip-wire facts stay embedded in parent ingest articles. Less file proliferation; anchor-aware citation tax. | |
| Both — inline + standalone redirect stub | Best discoverability; highest maintenance burden (two surfaces to keep in sync). | |

**User's choice:** Standalone micro-articles
**Notes:** 9 trip-wires identified (exceeds the 8 minimum), each enumerated in CONTEXT.md `<decisions>` D-05 table with target article path and upstream source.

---

## Drift detection

| Option | Description | Selected |
|--------|-------------|----------|
| Frontmatter SHA + /wiki:validate flag (Recommended) | Every ingested article carries `source: confluent-agent-skills@<sha>`. /wiki:validate compares SHA against current pin and emits drift finding when stale. Passive — doesn't block merges. | ✓ |
| Active CI drift gate (G.2c-style) | wiki-vendor-drift.yml fails PRs when SHA lags upstream main. Stronger guarantee; overkill for content articles. | |
| Scheduled cron, no per-PR gate | Weekly job re-runs /wiki:validate against upstream, opens tracking issue on drift. Lower friction; staleness can land in PRs. | |
| Nothing automated — manual re-ingest on demand | Trust upstream cadence; re-ingest when noticed. Lowest cost, highest staleness risk. | |

**User's choice:** Frontmatter SHA + /wiki:validate flag
**Notes:** Content drift isn't a fail-PR concern the way classification keys are. Existing 90-day `last_validated` decay rule already provides one staleness surface; SHA-based check layers on top. Stretch goal in D-10 to compare against upstream main during routine validation.

---

## Claude's Discretion (decided without AskUserQuestion, documented in CONTEXT.md)

- **MCP re-validation strategy (D-07):** Selective. Trip-wires get full MCP re-validation (verbatim cited downstream → accuracy stakes high). Parent articles get source attestation (`source: confluent-agent-skills@<sha>` + their evals gate at 90%+ before merge). Saves ~60% ingest time without measurable correctness loss.
- **Article inventory locked (D-05/D-13):** 10 parent articles + 9 trip-wire micro-articles identified from the 26 upstream reference files (project scaffolds dropped). Full table in CONTEXT.md.
- **WarpStream framing:** Three WarpStream trip-wires include an explicit "competitive context, not FSI production guidance" paragraph per the FSI vendor-backing rule (memory feedback_confluent_supported_connectors.md). Verbatim paragraph captured in CONTEXT.md `<specifics>`.
- **Vendor-sources.json schema:** Forward-compatible with H.3b's `streaming-skills-plugin` pin — `kind: wiki-source` vs `kind: claude-plugin` discriminator.
- **Vendor directory tracked in repo (not gitignored):** So `git log` surfaces SHA bumps as auditable changes.

## Deferred Ideas

- Active CI drift gate for vendor sources — rejected for H.1; promote if a future incident demands it
- Re-ingest automation triggered by upstream releases — D-10 stretch goal; defer if /wiki:validate can't accommodate cleanly
- Ingesting upstream `evals/evals.json` as wiki content — they're CI gates over there, not knowledge content; H.2 can fetch separately if needed
- Vendoring other Confluent repos (e.g., confluentinc/tutorials) — schema accommodates, but scope-creep for H.1
- Frontmatter `vendor: true` shortcut field — not worth schema change for one phase
