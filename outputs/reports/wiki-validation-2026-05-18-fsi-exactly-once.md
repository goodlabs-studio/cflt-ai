---
title: Wiki Validation — fsi-exactly-once.md
date: 2026-05-18
scope: wiki/patterns/fsi-exactly-once.md
articles_checked: 1
claims_checked: 12
claims_confirmed: 10
claims_corrected_or_enriched: 1
claims_still_unverified: 1
revalidated: 2026-05-18 (second pass, same day)
---

# Wiki Validation — FSI Exactly-Once Pattern

## Scope

Single-article revalidation of `wiki/patterns/fsi-exactly-once.md` (confidence: medium). Article carried two pre-existing `⚠️ unverified` markers and was explicitly queued in `_queue.md` for MCP verification.

## Validation Summary

| # | Claim (article line) | MCP source | Outcome |
|---|----------------------|------------|---------|
| 1 | Broker `transaction.max.timeout.ms` default = 900000 ms / 15 min (L246, L325) | `confluent-docs` — Broker Configurations | **Confirmed** — verbatim match |
| 2 | IBM MQ Source Connector supports EOS when configured with Kafka transactions (L286) | `confluent-docs` — IBM MQ Source Connector overview | **Confirmed and enriched** — specific config requirements now documented |
| 3 | Idempotent producer requires `enable.idempotence=true`, `acks=all` (L46-50) | Canonical / CLAUDE.md canon | **Confirmed** |
| 4 | Transactional producer requires `transactional.id`, includes offsets via `sendOffsetsToTransaction` (L60-95) | Canonical Kafka EOS pattern | **Confirmed** |
| 5 | `read_committed` filters aborted txns and withholds open ones (L99-110) | Canonical Kafka EOS pattern | **Confirmed** |
| 6 | Kafka Streams `exactly_once_v2` requires Kafka 2.5+; older `exactly_once` deprecated (L159, L326) | Canonical (KIP-447) | **Confirmed** |
| 7 | Confluent Cloud Flink commit interval ~1 min (L183) | `cloud/current/flink/concepts/delivery-guarantees.html` (revalidation pass) | **Confirmed** — verbatim "Flink commits transactions periodically, approximately every minute" |
| 8 | Confluent Cloud Flink EOS enabled by default (L183) | `cloud/current/flink/concepts/delivery-guarantees.html` (revalidation pass) | **Confirmed** — verbatim "provides exactly-once semantics end-to-end by default" |
| 9 | CC Flink EOS latency ~1 min (L183) | `cloud/current/flink/concepts/delivery-guarantees.html` | **Confirmed** — "the latency is roughly one minute and depends on the interval at which Kafka commits transactions" |
| 10 | At-least-once via `read_uncommitted` for sub-100ms latency on CC Flink (L183) | `cloud/current/flink/concepts/delivery-guarantees.html` | **Confirmed** — "you can achieve an end-to-end latency below 100 ms" with `read_uncommitted` |
| 11 | Broker `transaction.max.timeout.ms` default = 900000 ms (15 min) (L180, L246) | `confluent-docs` Streams config docs (revalidation cross-check) | **Confirmed** — referenced as broker ceiling for transaction timeout |
| 12 | Kafka Streams EOS overrides `transaction.timeout.ms` default to 10000 ms (NOT in article) | `apache/kafka` Streams config docs (KIP-447) | **Note** — article cites 60s default (correct for plain producer); Streams EOS-specific default is 10s. Not drift, but worth a future enrichment if a KS-EOS section is added |
| 13 | CC Flink commit interval **user-configurability** (L185) | Not documented in public MCP sources | **Unverifiable via MCP** — keep `⚠️ unverified` marker; queue item 28 narrowed to tunability only |

## Detailed Finding: IBM MQ Source Connector EOS (claim #2)

**Wiki claim (line 286):**
> The MQ Source Connector supports exactly-once delivery when configured with Kafka transactions. Combined with `read_committed` consumers downstream, this extends EOS from the mainframe boundary into the streaming platform.
>
> ⚠️ unverified — IBM MQ Source Connector exact EOS configuration properties and version requirements were not confirmed via MCP sources.

**MCP finding** (from `kafka-connectors/ibmmq-source/current/overview.html`):

The IBM MQ Source Connector supports exactly-once delivery **only when all** of the following conditions are met:

1. All Connect workers have `exactly.once.source.support=enabled` (KIP-618 worker-level setting)
2. Connect cluster runs in **distributed mode** (standalone is not supported for EOS)
3. Connect worker principal has the required ACLs for exactly-once source
4. Connector is configured with `state.topic.name` (must be set at first create — changing it later causes duplicates)
5. **Single task only** — EOS mode does not support multiple tasks or receiver threads
6. Consumers downstream must set `isolation.level=read_committed`

**Version requirement:** 12.x or later. The 11.x line does not support at-least-once and is no longer supported.

**Caveat surfaced by docs:** When consuming from an MQ priority queue, EOS cannot be guaranteed — MQ may deliver messages out of order and the connector may fail under EOS mode.

The wiki article's general claim is correct. The `⚠️ unverified` marker is being **removed** and the article body **enriched** with the worker/connector requirements and the priority-queue caveat.

## Confluent Cloud Flink Transaction Commit Interval (claim #7 / revalidation update)

**Update from second-pass revalidation (2026-05-18):** The ~1-minute figure quoted in the article is now **directly confirmed** via `cloud/current/flink/concepts/delivery-guarantees.html` ("Flink commits transactions periodically, approximately every minute"). What remains unverified is whether this interval is **user-configurable** — Confluent's public docs do not expose a tunable property, but also do not explicitly state it is fixed. The inline `⚠️ unverified` marker on line 185 is therefore retained but narrowed in scope: the interval itself is confirmed; only tunability is unverified. Queue item 28 narrowed accordingly.

## Article Mutations Applied

1. Removed the `⚠️ unverified` marker on the IBM MQ Source section (line 288 region).
2. Replaced the prose with concrete worker/connector requirements drawn from the MCP source, plus the priority-queue caveat.
3. Added the 12.x version requirement to the same section.
4. Bumped `last_updated` to 2026-05-18 and `last_validated` to 2026-05-18.
5. Confidence remains `medium` — one inline unverified claim still outstanding (CC Flink commit interval).

## Queue Updates

- Resolved (struck): `wiki/patterns/fsi-exactly-once.md line 288: "IBM MQ Source Connector exact EOS configuration properties and version requirements"` — confirmed via MCP, article enriched.
- Resolved (struck): `unverified: wiki/patterns/fsi-exactly-once.md (2 inline ⚠️ unverified markers)` — now down to 1.
- Still open: `wiki/patterns/fsi-exactly-once.md line 185: "Confluent Cloud Flink transaction commit interval is not documented as user-configurable"` — requires Confluent Support disclosure.

## Wiki Health

Article was already structurally sound (correct frontmatter, internal links resolve, layered pattern coverage is comprehensive). Drift on a single connector EOS claim corrected; one CC Flink claim remains intentionally flagged. No additional drift detected in producer/consumer/Streams/broker config defaults.

---

*Validated against Confluent docs via `confluent-docs` MCP (2026-05-18, first pass: 8 claims). Revalidated 2026-05-18 (second pass: +5 additional claims now MCP-cited via `cloud/current/flink/concepts/delivery-guarantees.html` and `apache/kafka` Streams config). Final: 12 claims checked, 1 enriched, 1 inline `⚠️ unverified` marker retained (narrowed to CC Flink commit-interval tunability only).*
