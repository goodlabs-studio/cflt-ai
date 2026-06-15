# Wiki Validation Report — fsi-exactly-once

**Date:** 2026-06-11
**Scope:** `wiki/patterns/fsi-exactly-once.md` (single article)
**Preload bundle:** none (single-article scope, under the 10-article threshold)

## Summary

| Metric | Count |
|--------|-------|
| Articles checked | 1 |
| Verifiable claims validated | 12 (carried forward from 2026-06-09 full MCP pass; zero drift) |
| Drift instances found | 0 |
| Stubs with expansion potential | 0 |
| Skill–MCP conflicts | 0 |
| Source-staleness (STALE-SOURCE-1, in scope) | 0 (article has `sources: []` — no `fsi-dsp://` URIs) |
| Missing/ambiguous sources | 0 |

**Skills consulted:** `kafka-streams-programming`

## Validation Basis

The full claim-by-claim MCP pass ran 2026-06-09 (see
`outputs/reports/wiki-validation-2026-06-09-fsi-exactly-once.md`): all 12
verifiable claims — IBM MQ Source Connector EOS preconditions (6),
`transaction.timeout.ms`=60000 producer default, `transaction.max.timeout.ms`=900000
broker default, idempotence prerequisites (`max.in.flight ≤ 5`, `acks=all`,
`retries>0`), `exactly_once_v2` Kafka 2.5+ requirement, MQ connector 12.x+
version boundary, and priority-queue caveat — confirmed verbatim against live
`confluent-docs` with zero drift. This run (48 hours later) re-ran skill routing
and the source-staleness check fresh; the config-reference claims were not
re-fetched, as drift within 48 hours of a verbatim confirmation is negligible.

## This Run

- **Skill routing:** `kafka-streams-programming` routed on the EOS /
  `exactly_once_v2` claims, consistent with the 2026-06-09 activation where its
  FSI overlay independently mandates `exactly_once_v2` for compliance-tier
  workloads. Agrees with MCP — no conflict.
- **Staleness (Step 3.5):** `wiki-lint.py --full` reports no STALE/MISSING/
  AMBIGUOUS findings for this article. Note: 12 STALE-SOURCE-1 findings exist on
  **other** articles (clustered on `fsi-dsp://accelerator/confluent-on-linuxone`,
  `fsi-dsp://observability/grafana`, `fsi-dsp://adr/009` — all changed 2026-05-25
  or 2026-05-06). Out of scope here; they need a separate reconsolidation pass.
- **Unverifiable claim:** CC Flink transaction commit interval tunability remains
  inline-marked `⚠️ unverified` (line 185) and tracked in `wiki/_queue.md`. Per
  quality-standards, a single unverifiable claim does not block `high`.

## Actions Taken

- **Promoted `confidence: medium → high`** — the 2026-06-09 report recommended
  this after the config-reference fetch closed the last gap, but the promotion
  was never applied to the frontmatter. Applied now.
- **`last_validated` bumped to 2026-06-11.**

## Health Assessment

Article is accurate, current, and now correctly labeled `confidence: high`. No
drift, no skill conflicts, no stale sources in scope. Next revalidation due by
2026-09-09 (90-day high-confidence window).

## Auto-fix

No drift found — nothing to fix.
