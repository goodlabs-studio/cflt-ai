---
title: Kafka Streams Topology Patterns
tags: [kafka-streams, topology, dsl, processor-api, confluent-agent-skills]
sources: [raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/topology-patterns.md]
related: [concepts/exactly-once-semantics, concepts/consumer-group-rebalancing, concepts/kafka-streams-architecture, concepts/kafka-streams-debugging, concepts/kafka-streams-config-baseline, concepts/schema-registry-best-practices]
confidence: high
last_updated: 2026-05-16
last_validated: 2026-05-16
source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4
upstream_path: skills/kafka-streams-programming/references/topology-patterns.md
---

# Kafka Streams Topology Patterns

## Summary

A use-case-driven catalogue of canonical Kafka Streams (KS) topology shapes — stateless transforms, enrichment joins, aggregations, windowing, suppression, deduplication, splitting, Processor API escape hatches, and exactly-once. Read it as a decision tree: start from what the user is trying to accomplish, then map to the right KS primitive. Pairs with [Kafka Streams Architecture](../concepts/kafka-streams-architecture.md) (runtime model) and [Kafka Streams Config Baseline](../concepts/kafka-streams-config-baseline.md) (operational defaults).

Sourced from `confluentinc/agent-skills@91d1871e` (Apache-2.0) — upstream maintains an eval gate at 90%+ pass before merge, so this article is `confidence: high` via source attestation rather than per-claim MCP re-validation. Trip-wire micro-articles in `wiki/concepts/` carry full MCP validation.

## Pattern

### Stateless transforms

Filter, map, route, split, merge. No state stores, no rebalance overhead, simplest to operate.

```java
orders.filter((key, order) -> order.getAmount() > 100.0, Named.as("filter-large"))
    .to("large-orders", Produced.with(...).withName("sink-large"));

orders.mapValues(order -> new OrderSummary(order.getId(), order.getTotal()), Named.as("map"))
    .to("summaries", Produced.with(...).withName("sink"));

orders.flatMapValues(order -> order.getLineItems(), Named.as("explode"))
    .to("items", Produced.with(...).withName("sink"));
```

Tune for throughput: `num.stream.threads=4`, `commit.interval.ms=1000`, `consumer.fetch.min.bytes=1048576`, `producer.batch.size=65536`, `producer.linger.ms=20`, `producer.compression.type=lz4`.

### Enrichment joins

| Lookup shape | Pick |
|---|---|
| Same key, co-partitioned, table fits per-instance | Stream-Table Join |
| Lookup key ≠ stream key, table is small, no co-partitioning | GlobalKTable Join (broadcast) |
| Both inputs are tables, FK relationship | Foreign-Key Table-Table Join |
| Both streams with windowed correlation | Stream-Stream Join (requires `JoinWindows`, co-partitioned) |

Stream-Table joins do **not** accept `Named.as()`. GlobalKTable replicates the entire lookup to every instance (higher memory) and skips changelog reconstruction. FK joins create repartition topics under the covers.

### Aggregations

`groupByKey().aggregate(...)` is the standard shape. Re-keying with `selectKey()` triggers a repartition topic. For multi-source rollups, use `cogroup`:

```java
KGroupedStream<String, LoginEvent> app1 = app1Stream.groupByKey(...);
KGroupedStream<String, LoginEvent> app2 = app2Stream.groupByKey(...);

Aggregator<String, LoginEvent, LoginRollup> aggregator =
    (key, event, rollup) -> rollup.add(event);

KTable<String, LoginRollup> rollup = app1.cogroup(aggregator)
    .cogroup(app2, aggregator)
    .aggregate(LoginRollup::new, Materialized.with(Serdes.String(), rollupSerde));
```

Stateful tuning: `statestore.cache.max.bytes=52428800` (50 MB — deduplicates updates per key within the commit interval), `state.dir=/var/kafka-streams/state` (fast local storage; **never NFS**), `processing.guarantee=at_least_once` unless you have specific EOS requirements (see below).

### Windowing decision tree

| Use case | Window | API |
|---|---|---|
| Fixed, non-overlapping (hour, day) | Tumbling | `TimeWindows.ofSizeWithNoGrace(Duration)` |
| Fixed, overlapping (5-min every 1-min) | Hopping | `TimeWindows...advanceBy(Duration)` |
| Continuous monitoring (fraud, rate limiting) | Sliding | `SlidingWindows.ofTimeDifferenceWithNoGrace(Duration)` |
| Activity gaps (session timeout) | Session | `SessionWindows.ofInactivityGapAndGrace(Duration, Duration)` |
| Stream-stream join | Join | `JoinWindows.ofTimeDifferenceWithNoGrace(Duration)` |

Prefer tumbling > sliding > session for resource efficiency. Use grace for bounded out-of-orderness; never unbounded.

For **final-results-only** emit semantics, use suppression with a bounded buffer:

```java
windowedCounts.suppress(Suppressed.untilWindowCloses(
    BufferConfig.maxRecords(10000).shutDownWhenFull()))
    .toStream().map((windowed, count) -> KeyValue.pair(windowed.key(), count))
    .to("final-counts", Produced.with(...));
```

Monitor `suppression-buffer-size-avg` and `suppression-buffer-size-max`. **Never use `BufferConfig.unbounded()` in production.**

### Stream splitting

The modern `split()` API replaces the deprecated `branch()`:

```java
stream.split(Named.as("split-"))
    .branch((k, v) -> "drama".equals(v.getGenre()),
        Branched.withConsumer(ks -> ks.to("drama", Produced.with(...))))
    .branch((k, v) -> "fantasy".equals(v.getGenre()),
        Branched.withConsumer(ks -> ks.to("fantasy", Produced.with(...))))
    .defaultBranch(Branched.withConsumer(ks -> ks.to("other", Produced.with(...))));
```

### Processor API

Escape hatch when DSL is insufficient: conditional forwarding, record metadata access, scheduled operations, custom state store interactions. Use `FixedKeyProcessor` when the key doesn't change, `Processor` when it does. `context.forward(record)` shares object references — use `record.withValue()` to copy.

Punctuators schedule work on stream-time or wall-clock-time intervals:

```java
context.schedule(Duration.ofSeconds(5), PunctuationType.STREAM_TIME, ts -> flushBuffer());
context.schedule(Duration.ofSeconds(20), PunctuationType.WALL_CLOCK_TIME, ts -> heartbeat());
```

`STREAM_TIME` advances with data; `WALL_CLOCK_TIME` fires regardless of input.

### Exactly-once decision

| Use case | Needs EOS? | Reason |
|---|---|---|
| Financial transactions, billing | Yes | Duplicate output = real money problems |
| Cross-topic atomic writes | Yes | All-or-nothing guarantees |
| Non-idempotent state mutations | Yes | Replay corrupts state |
| Aggregations (count, sum, max) | No | State converges, idempotent |
| Enrichment joins | No | Duplicate enriched records harmless |
| Output consumed by external DB | No\* | EOS only covers Kafka side; DB needs idempotent writes |

Cost: ~10-30% throughput, fixed 100 ms commit interval, 2× write amplification, minimum 3 brokers, state-wipe-and-restore on unhandled exception. Configure via `processing.guarantee=exactly_once_v2` — never `exactly_once` (v1 is deprecated). See [Kafka Streams Config Baseline](../concepts/kafka-streams-config-baseline.md) § EOS Configuration.

CC-specific gotcha: transactional IDs expire after 7 days idle, raising `InvalidPidMappingException` on restart.

### Versioned KTables

Use for temporal join correctness when the table updates frequently. Ensures the join uses the table value at the stream record's timestamp, not the latest:

```java
VersionedBytesStoreSupplier supplier = Stores.persistentVersionedKeyValueStore(
    "versioned-store", Duration.ofMinutes(10));
KTable<String, String> table = builder.table("input", Consumed.with(...),
    Materialized.as(supplier).withKeySerde(...).withValueSerde(...));
```

### Recovery and assignment

KIP-1071 (`group.protocol=streams`) is the default on AK 4.2+ / CP 8.2+. Crashes with `UnsupportedVersionException` on older brokers. **Standby replicas, static membership, regex topic patterns, and warm-up replicas are NOT supported with `group.protocol=streams`** — remove the property to fall back to the classic protocol if you need them.

State-restoration tuning:

```properties
consumer.max.poll.interval.ms=600000        # Tolerate slow restoration
restore.consumer.fetch.max.bytes=52428800   # 50 MB — speed up
```

Root cause of restoration loops: RocksDB compaction blocks poll → exceeds `max.poll.interval.ms` → consumer evicted → restore → repeat.

## When to Use

- New Kafka Streams applications — pick the right topology primitive for the use case upfront
- Reviewing an existing KS topology for correctness, especially around joins, windows, and EOS scope
- Architecting an enrichment pipeline where you need to choose between Stream-Table, GlobalKTable, and FK joins
- Sizing a stateful application — partition count, instance count, and standby replicas

## Caveats

- **Max parallelism = number of input partitions.** More instances/threads is idle capacity.
- **Stream-Table joins do not accept `Named.as()`.** Stream-Stream uses `StreamJoined.withName()`, others use `Named.as()`.
- **Repartition topics auto-created by `selectKey()`/`groupBy()` use infinite retention.** Never set retention on them — causes data loss.
- **EOS error amplification:** an unhandled exception in EOS mode wipes local state and restores from the changelog. For large state stores, every error is a 40+ minute outage. Switch to `at_least_once` to break the loop, then fix the bug.
- **CC transactional ID expiry:** apps idle > 7 days on Confluent Cloud throw `InvalidPidMappingException` on restart.

## Related

- [Kafka Streams Architecture](../concepts/kafka-streams-architecture.md) — threading, tasks, state stores, sizing
- [Kafka Streams Config Baseline](../concepts/kafka-streams-config-baseline.md) — operational defaults, EOS config, RocksDB tuning
- [Kafka Streams Debugging](../concepts/kafka-streams-debugging.md) — diagnostics for the patterns in this article
- [Kafka Streams Production Hardening](../concepts/kafka-streams-production-hardening.md) — error handling, health checks, deployment sizing
- [Kafka Streams Schema Patterns](../concepts/kafka-streams-schema-patterns.md) — Avro/Protobuf/JSON Schema for KS state and topics
- [Exactly-Once Semantics](../concepts/exactly-once-semantics.md) — idempotence, transactions, isolation levels
- [Consumer Group Rebalancing](../concepts/consumer-group-rebalancing.md) — rebalance behavior under stateful operators
- [Schema Registry Best Practices](../concepts/schema-registry-best-practices.md) — SR operational surface

---

*Source: confluentinc/agent-skills@91d1871e · skills/kafka-streams-programming/references/topology-patterns.md · Ingested 2026-05-16 · Apache-2.0*
