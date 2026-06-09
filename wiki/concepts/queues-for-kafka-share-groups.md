---
title: Queues for Kafka (Share Groups)
tags: [kafka concepts consumer queues share-groups kip-932 fsi]
sources: []
related: [concepts/consumer-group-rebalancing, patterns/dead-letter-queue-design, concepts/exactly-once-semantics, concepts/consumer-lag-monitoring, concepts/sla-tiers]
confidence: medium
last_updated: 2026-06-09
last_validated: 2026-06-09
---

# Queues for Kafka (Share Groups)

## Summary

**Share groups** (KIP-932, "Queues for Kafka") add a second consumption model to Kafka alongside the classic consumer group. In a share group, **multiple consumers cooperatively read from the same partitions** and each record is **individually acknowledged** rather than tracked by a committed offset. This decouples consumer parallelism from partition count — you can run more consumers than partitions — and gives Kafka native queue semantics (competing consumers, per-message acknowledgement, redelivery, and poison-message rejection) that previously required the Confluent Parallel Consumer or application-level workarounds. The trade-off: delivery is **at-least-once only** (no EOS) and **per-key ordering is not preserved**, so share groups fit work-distribution workloads, not ordered state-machine processing.

> **Validation status (confidence: medium).** This article is compiled from KIP-932 and the Apache Kafka share-group design. Version/GA status and exact config property names + defaults below are marked "verify" and should be confirmed against `confluent-docs` (the dedicated Share Groups page was not resolvable via MCP at authoring time). Run `/wiki:validate` once the canonical Confluent Platform / Cloud share-groups page is reachable.

## Detail

### Why share groups exist

In a classic consumer group, a partition is owned by **at most one consumer in the group**. Consumer parallelism is therefore capped by partition count, and three queue-style needs are awkward:

- **Scaling consumers past partitions** — you must over-partition up front to add consumers later.
- **Competing consumers / work distribution** — fan a stream of independent tasks across a pool of workers without partition affinity.
- **Per-message handling** — a single slow or failed record causes head-of-line blocking on its partition; offset commits acknowledge *position*, not individual records.

Share groups address all three by moving acknowledgement from offset-based (per partition) to record-based (per message).

### Consumer groups vs. share groups

| Dimension | Consumer group (classic) | Share group (KIP-932) |
|-----------|--------------------------|------------------------|
| Partition ownership | Exclusive — 1 consumer per partition per group | Shared — many consumers read the same partition |
| Parallelism ceiling | ≤ partition count | Independent of partition count |
| Progress tracking | Committed offset per partition | Per-record acknowledgement (Accept/Release/Reject) |
| Redelivery | Reprocess from last commit (coarse) | Per-record, via Release or lock timeout |
| Ordering | Per-partition order preserved | **Not** preserved across redeliveries |
| Delivery semantics | At-least-once; EOS via transactions | **At-least-once only** |
| Client | `KafkaConsumer` | `KafkaShareConsumer` |
| Group type | `group.type=consumer` (or classic) | `group.type=share` |
| Best for | Ordered, partition-aligned stream processing | Queue / competing-consumer / work distribution |

### How delivery works

When a share consumer polls, the **share-partition leader** (the broker leading that partition) hands it a batch of records and **acquires** them — placing a per-record lock for a bounded duration. While a record is acquired by one member, no other member receives it. The consumer then acknowledges each record:

- **Accept** — processed successfully; the record's state advances and it will not be redelivered.
- **Release** — return the record for redelivery to any member (e.g., transient failure, backpressure).
- **Reject** — a poison record; do not redeliver. Archived immediately.

A record is also eligible for redelivery if its **acquisition lock times out** (the consumer died or stalled). Each record carries a **delivery count**; once it exceeds the configured delivery-count limit it is **archived** (effectively a built-in poison-message terminus — see [Dead Letter Queue Design](patterns/dead-letter-queue-design.md)).

The leader tracks in-flight state between the **Share-Partition Start Offset (SPSO)** and **Share-Partition End Offset (SPEO)**, and persists share-group state to an internal topic (commonly `__share_group_state`). KRaft is required.

### Key configuration

> **verify** — names and defaults below follow KIP-932; confirm against `confluent-docs` before treating as canonical.

| Scope | Property | Purpose |
|-------|----------|---------|
| Broker enablement | `group.share.enable` | Master switch for the share-group feature (`true` to enable). **verify** |
| Group | `group.share.record.lock.duration.ms` | How long an acquired record stays locked before it can be redelivered. **verify default** |
| Group | `group.share.delivery.count.limit` | Max delivery attempts before a record is archived. **verify default** |
| Group | `group.share.session.timeout.ms` / `group.share.heartbeat.interval.ms` | Share-group membership liveness. **verify** |
| Group | `group.share.max.size` | Max members in a share group. **verify** |
| Client | `group.type=share` | Selects the share-group protocol for the consumer. |
| Client | `share.acknowledgement.mode` | `implicit` (poll acks the previous batch) or `explicit` (app acks each record). **verify** |

Tooling: `kafka-share-groups.sh` (the share-group analogue of `kafka-consumer-groups.sh`) describes/lists share groups and resets share-group offsets; Admin API and Confluent CLI expose equivalent operations. **verify CLI path**

### Maturity

KIP-932 shipped as **Early Access / Preview in Apache Kafka 4.0**, with general availability targeted for a later 4.x release. Confluent Platform / Confluent Cloud availability tracks the corresponding release train. **verify exact GA version and CP/CC availability against `confluent-docs` release notes.**

### Share groups vs. DLQ vs. Parallel Consumer

- **vs. classic consumer + DLQ topology** — share groups provide native redelivery and a delivery-count-limited archive path, reducing the need for hand-built retry-topic ladders ([Dead Letter Queue Design](patterns/dead-letter-queue-design.md)). A DLQ is still useful when you need the *rejected payload retained and inspectable*; share-group archival is state, not a replay topic.
- **vs. Confluent Parallel Consumer** — the Parallel Consumer library delivers key-level/unordered parallelism client-side on top of classic groups; share groups move that capability into the broker protocol, removing the external dependency for new work.

## FSI Applicability

Per the [SLA tiers](concepts/sla-tiers.md) and FSI canon overlay, apply share groups deliberately:

- **Good fits** — competing-consumer work distribution where per-message acknowledgement and redelivery matter more than ordering: compliance/sanctions screening task queues, fraud-case distribution to an analyst worker pool, asynchronous reconciliation jobs.
- **Do not use for ordered state changes** — share groups do **not** preserve per-key order and are **at-least-once only**. For regulatory state transitions requiring exactly-once (e.g., ledger/balance event sequences, regulatory reporting), keep the transactional consume-process-produce pattern and classic groups — see [Exactly-Once Semantics](concepts/exactly-once-semantics.md). If a share group is used on a financial path, idempotency MUST be enforced at the processing layer.
- **Security** — mTLS + RBAC still apply; share-group operations require RBAC grants on both the group and the topic. Audit logging applies to share-group admin operations.
- **Monitoring** — partition-offset lag does not describe a share group; track unacked/in-flight record counts and redelivery rates instead of classic [consumer lag](concepts/consumer-lag-monitoring.md). **verify exact share-group metric identities against `confluent-docs` + the observability mapping before alerting.**

## Related

- [Consumer Group Rebalancing](concepts/consumer-group-rebalancing.md) — the classic ownership model share groups depart from
- [Dead Letter Queue Design](patterns/dead-letter-queue-design.md) — redelivery/poison-message handling that share-group Reject + delivery-count-limit partially subsumes
- [Exactly-Once Semantics](concepts/exactly-once-semantics.md) — why share groups (at-least-once) are not an EOS substitute on regulated paths
- [Consumer Lag Monitoring](concepts/consumer-lag-monitoring.md) — contrast with share-group in-flight/redelivery monitoring
- [SLA Tiers](concepts/sla-tiers.md) — latency-tier framing for choosing the consumption model

**Supporting asset:** [`share_group_topic` Terraform module proposal](../../proposals/fsi-dsp/share_group_topic/README.md) — a governed queue-topic module + worker-pool RBAC, staged for contribution to fsi-dsp.
