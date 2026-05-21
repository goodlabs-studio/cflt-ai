---
title: Wiki Validation — patterns/fsi-exactly-once.md
date: 2026-05-18
scope: wiki/patterns/fsi-exactly-once.md
articles_checked: 1
claims_validated: 12
drift_found: 0
stubs_with_expansion_potential: 0
---

# Wiki Validation Report — 2026-05-18

## Scope

Single-article validation: `wiki/patterns/fsi-exactly-once.md` (confidence: medium, last_validated 2026-05-14).

## Claims Validated

| # | Claim (article location) | MCP source | Outcome |
|---|---------------------------|------------|---------|
| 1 | `transaction.timeout.ms` default = 60s / 60000 (L65, L237, L325) | `confluent-docs` — producer-configs.html | **Confirmed**: "Default: 60000 (1 minute)" |
| 2 | `transaction.max.timeout.ms` broker default = 900000ms / 15 min (L65 comment, L246) | `confluent-docs` — broker-configs.html | **Confirmed**: "Default: 900000 (15 minutes)" |
| 3 | Kafka Streams `exactly_once_v2` requires Kafka 2.5+ (L160, L326) | `confluent-docs` — config-streams.html | **Confirmed**: "requires Confluent Platform version 5.5.x / Kafka version 2.5.x or higher" |
| 4 | `exactly_once` setting is deprecated (L161, L326) | `confluent-docs` — config-streams.html | **Confirmed**: "Deprecated config options are `exactly_once` (for EOS version 1) and `exactly_once_beta`" |
| 5 | EOS Streams implicitly sets consumer `isolation.level=read_committed` and producer `enable.idempotence=true` (implied by L156–164) | `confluent-docs` — config-streams.html | **Confirmed**: "consumers are configured with `isolation.level=\"read_committed\"` and producers are configured with `enable.idempotence=true` by default" |
| 6 | Producer `enable.idempotence` default = `true` (L46 sample block) | `confluent-docs` — producer-configs.html | **Confirmed**: "Default: true" |
| 7 | Producer `max.in.flight.requests.per.connection` value of 5 (L50) | `confluent-docs` — producer-configs.html | **Confirmed**: "Default: 5" (with idempotence enabled, max allowed is 5) |
| 8 | Producer `retries=2147483647` effectively infinite (L49) | `confluent-docs` — producer-configs.html | **Confirmed**: "Default: 2147483647" |
| 9 | CC Flink: EOS enabled by default (L183) | `confluent-docs` — flink/concepts/delivery-guarantees.html | **Confirmed**: "Confluent Cloud for Apache Flink provides exactly-once semantics end-to-end by default" |
| 10 | CC Flink: "Kafka transactions are committed approximately every minute" (L183) | `confluent-docs` — flink/concepts/delivery-guarantees.html | **Confirmed**: "Flink commits transactions periodically, approximately every minute" |
| 11 | CC Flink EOS end-to-end latency ~1 minute (L183, L306) | `confluent-docs` — flink/concepts/delivery-guarantees.html | **Confirmed**: "the latency is roughly one minute and depends on the interval at which Kafka commits transactions" |
| 12 | CC Flink at-least-once via `isolation.level=read_uncommitted` enables sub-100ms latency (L183) | `confluent-docs` — flink/concepts/delivery-guarantees.html | **Confirmed**: at-least-once path with `read_uncommitted` yields "end-to-end latency below 100 ms" |

## Drift Instances Found

None.

## Unverifiable Claims (already marked inline)

The article already carries two `⚠️ unverified` markers, both correctly scoped:

- L185 — CC Flink transaction commit interval tunability (~1 minute, user-configurability)
- L288 — IBM MQ Source Connector exact EOS configuration properties / version requirements

Neither is contradicted by available MCP sources; both remain genuinely unverified pending Confluent Support or connector-specific docs not in the `llms.txt` index. No queue entries added — markers already in place.

## Stubs With Expansion Potential

N/A — scope is a non-stub pattern article.

## Overall Wiki Health Assessment (article-scoped)

`patterns/fsi-exactly-once.md` is in good shape:

- Every Kafka/Streams config default referenced in the article matches current Confluent docs (CP `current`, which tracks 8.x / Kafka 4.x).
- The two unverifiable claims are *correctly* marked unverified — neither was over-claimed.
- The article's confidence is `medium`; with 5/5 verifiable claims confirmed and only 2 narrowly-scoped unverified items remaining, an upgrade to `confidence: high` is defensible. Deferred pending user decision since the unverified items touch a managed-service internal (CC Flink) and a third-party connector (IBM MQ Source) — both areas where surface-area for drift is real even if today's claims are accurate.

## Actions Taken

- Bumped `last_validated` on the article to `2026-05-18`.
- No `_queue.md` updates (no drift, no expansion candidates).
- No article-body edits.

---

*Validated against Confluent docs via `confluent-docs` MCP (2026-05-18). 12 claims checked, 0 corrected, 2 unverifiable (pre-existing markers).*

## Re-validation Pass (2026-05-18, second run)

Second pass extended the claim set to cover producer-config defaults and Confluent Cloud Flink delivery semantics. All new claims confirmed against `confluent-docs` MCP. No drift introduced. The L185 ⚠️ unverified marker (CC Flink commit interval *tunability*) remains accurate: docs confirm the ~1 minute cadence but do not document user-configurability.
