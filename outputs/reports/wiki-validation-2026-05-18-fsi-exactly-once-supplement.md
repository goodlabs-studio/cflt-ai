---
title: Wiki Validation — fsi-exactly-once.md (supplement)
date: 2026-05-18
scope: wiki/patterns/fsi-exactly-once.md
articles_checked: 1
claims_checked: 4
claims_confirmed: 4
claims_corrected: 0
claims_still_unverified: 0
supersedes: none
supplements: outputs/reports/wiki-validation-2026-05-18-fsi-exactly-once.md
---

# Wiki Validation Supplement — FSI Exactly-Once Pattern

## Scope

Second-pass revalidation of `wiki/patterns/fsi-exactly-once.md` requested same-day after the earlier IBM MQ Source enrichment. This pass re-checks the **producer/broker numeric config defaults** that the earlier report relied on but did not individually cite. No article mutations applied — all claims confirmed verbatim.

## Additional Claims Validated (beyond the earlier report)

| # | Claim (article line) | MCP source | Outcome |
|---|----------------------|------------|---------|
| 1 | Producer `retries` default = `2147483647` (L50) | `confluent-docs` — `installation/configuration/producer-configs.html` | **Confirmed** — `Default: 2147483647`, valid range `[0,…,2147483647]` |
| 2 | `max.in.flight.requests.per.connection=5` is the idempotence ceiling (L51) | `confluent-docs` — producer-configs | **Confirmed** — "enabling idempotence requires the value of this configuration to be less than or equal to 5, because broker only retains at most 5 batches for each producer" |
| 3 | Producer `transaction.timeout.ms` default = `60000` (1 min) (L65, L237 caveat baseline) | `confluent-docs` — producer-configs | **Confirmed** — `Default: 60000 (1 minute)` |
| 4 | Kafka Streams `exactly_once_v2` requires a cluster of **at least three brokers** by default (L168) | `confluent-docs` — `streams/developer-guide/config-streams.html` | **Confirmed** — "exactly_once_v2 processing requires a cluster of at least three brokers by default" |

## Cross-Check of Earlier Report's Resolved Items

Re-fetched the same source pages used in the earlier report and re-confirmed:

- `transaction.max.timeout.ms` broker default = `900000` (15 minutes) — still matches L246
- Kafka Streams `exactly_once_v2` introduced at CP 5.5.x / Kafka 2.5.x — still matches L159
- `exactly_once` and `exactly_once_beta` are deprecated processing-guarantee values — still matches L161
- IBM MQ Source Connector EOS requirements (worker `exactly.once.source.support=enabled`, distributed mode, ACLs, `state.topic.name`, single task, downstream `read_committed`, 12.x+, priority-queue caveat) — still matches L286–L299 verbatim

## Still Outstanding

- `wiki/patterns/fsi-exactly-once.md` L185: Confluent Cloud Flink transaction commit interval (~1 min) and tunability — still **not surfaced in public MCP sources**. Inline `⚠️ unverified` marker preserved. Queue item open pending Confluent Support disclosure.

## Article Mutations Applied

None. All claims revalidated; no drift detected on this pass. `last_updated` and `last_validated` remain 2026-05-18 (set by the earlier same-day report).

## Wiki Health

Article is in steady state at `confidence: medium` with one tracked inline-unverified claim. Promotion to `confidence: high` is gated on resolving the CC Flink commit-interval claim (the only remaining `⚠️ unverified` marker in the article).

---

*Validated against Confluent docs via `confluent-docs` MCP (2026-05-18). 4 additional claims checked, 0 corrected, 0 unverifiable. Combined with the earlier same-day report: 12 claims checked, 1 enriched, 1 inline-unverified preserved.*
