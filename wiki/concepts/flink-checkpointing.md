---
title: Flink Checkpointing
tags: [flink confluent-cloud performance]
sources:
  - https://nightlies.apache.org/flink/flink-docs-master/docs/dev/datastream/fault-tolerance/checkpointing/
  - https://nightlies.apache.org/flink/flink-docs-master/docs/ops/state/checkpoints_vs_savepoints/
  - https://nightlies.apache.org/flink/flink-docs-master/docs/ops/state/state_backends/
  - https://nightlies.apache.org/flink/flink-docs-master/docs/ops/state/checkpointing_under_backpressure/
  - https://nightlies.apache.org/flink/flink-docs-master/docs/ops/state/large_state_tuning/
  - https://docs.confluent.io/cloud/current/flink/overview.html
  - https://docs.confluent.io/cloud/current/flink/concepts/comparison-with-apache-flink.html
  - https://docs.confluent.io/cp-flink/current/jobs/configure/checkpointing.html
  - https://flink.apache.org/2020/10/15/from-aligned-to-unaligned-checkpoints-part-1-checkpoints-alignment-and-backpressure/
  - https://flink.apache.org/2018/02/28/an-overview-of-end-to-end-exactly-once-processing-in-apache-flink-with-apache-kafka-too/
related: [concepts/exactly-once-semantics, concepts/consumer-lag-monitoring]
confidence: medium
last_updated: 2026-04-11
last_validated: 2026-04-28
---

# Flink Checkpointing

## Summary

Flink checkpointing is the core fault-tolerance mechanism for stateful stream processing. It periodically creates consistent distributed snapshots of operator state, keyed state, and source connector offsets using an asynchronous variant of the Chandy-Lamport algorithm. On failure, the JobManager restores the entire job to the latest completed checkpoint, rewinds sources to their checkpointed positions, and resumes processing with exactly-once or at-least-once guarantees. In Confluent Cloud for Apache Flink, checkpointing is fully managed -- users do not configure checkpoint intervals, state backends, or storage; on Confluent Platform (self-managed via CMF), all standard Flink checkpoint properties are user-configurable.

## Detail

### Checkpoint Barrier Mechanism (Chandy-Lamport)

Flink's checkpointing uses **asynchronous barrier snapshotting**, a variant of the Chandy-Lamport distributed snapshot algorithm. The process:

1. The **Checkpoint Coordinator** (part of the JobManager) triggers a checkpoint by instructing all source operators to inject a numbered **checkpoint barrier** into their output streams.
2. Source operators record their current offsets (e.g., Kafka partition offsets) and emit the barrier downstream.
3. Barriers flow through the operator graph alongside regular data records, dividing the stream into a **pre-checkpoint epoch** (events reflected in the snapshot) and a **post-checkpoint epoch** (events to be re-processed on recovery).
4. When each operator receives a barrier on all its input channels, it snapshots its state and forwards the barrier downstream.
5. When all sink operators have received all barriers and acknowledged the snapshot, the checkpoint is marked **complete**.

Recovery is whole-cluster: on failure, the JobManager rolls back the entire job (not just the failed node) to the most recent completed checkpoint.

### Aligned vs Unaligned Checkpoints

#### Aligned Checkpoints (Default)

For multi-input operators (joins, unions), **barrier alignment** ensures a consistent cut across all input streams:

- When a barrier arrives on one input channel but not yet on another, the operator **blocks** the fast channel.
- It continues consuming from channels that have not sent a barrier yet.
- Once barriers arrive on all channels, the operator snapshots its state and unblocks all channels.

Alignment is required for exactly-once semantics. The blocking behavior means that under **backpressure**, checkpoint completion can stall or timeout -- the barrier on the backpressured channel cannot arrive until data ahead of it is processed.

#### Unaligned Checkpoints (Flink 1.11+, FLIP-76)

Unaligned checkpoints decouple checkpoint speed from backpressure:

- When the first barrier arrives on any input, the operator **immediately** forwards the barrier to outputs without waiting for other channels.
- The operator snapshots its state **plus all in-flight data** (network buffer contents) between barriers across input and output channels.
- On recovery, the in-flight buffered data is restored and replayed before new data.

| Aspect | Aligned | Unaligned |
|---|---|---|
| Backpressure tolerance | Poor -- barriers blocked behind data | Good -- barriers overtake buffers |
| Checkpoint size | Operator state only | Operator state + in-flight buffers |
| Recovery speed | Fast | Slightly slower (must replay buffers) |
| Checkpointing mode | `EXACTLY_ONCE` or `AT_LEAST_ONCE` | `EXACTLY_ONCE` only |
| Max concurrent checkpoints | Any | Must be `1` |

**Decision heuristic**: enable unaligned checkpoints only when the **alignment duration** is a significant fraction of total checkpoint time. In the Flink Web UI, if alignment duration >> (sync duration + async duration), unaligned checkpoints will help.

### State Backends

#### HashMapStateBackend

- Stores state as Java objects on the JVM heap.
- Fastest access -- no serialization/deserialization during processing.
- Limited by available heap memory; practical limit ~10 GB per slot before GC pressure becomes problematic.
- **Full checkpoints only** -- the entire heap state is serialized and written to checkpoint storage on every checkpoint.
- Best for: development, testing, small-state production workloads, latency-critical applications with bounded state.

#### EmbeddedRocksDBStateBackend

- Stores state in an embedded RocksDB instance on local disk (SSTables).
- State can exceed available memory -- disk-backed with LRU block cache.
- **Supports incremental checkpoints** -- only changed SSTable files are uploaded since the last checkpoint, dramatically reducing checkpoint I/O for large state.
- Slower per-access due to serialization/deserialization overhead.
- Practical for state sizes from tens of GB to TB scale.
- Best for: production workloads with large or unbounded state.

| Criterion | HashMapStateBackend | EmbeddedRocksDBStateBackend |
|---|---|---|
| State size | < 10 GB per slot | 10 GB to TB-scale |
| Access latency | Nanoseconds (heap) | Microseconds (serde + disk) |
| Incremental checkpoints | No | Yes |
| Checkpoint I/O | Full state every time | Deltas only (incremental) |
| GC impact | High for large state | Minimal (off-heap via RocksDB) |
| State TTL cleanup | Immediate on access | Deferred until RocksDB compaction |

#### Incremental Checkpoints (RocksDB Only)

Incremental checkpoints track which SSTable files RocksDB has created and deleted since the previous checkpoint. Only the delta is uploaded to checkpoint storage. For large state (tens of GB+), this reduces checkpoint I/O by orders of magnitude compared to full checkpoints.

State TTL cleanup with incremental checkpoints depends on RocksDB compaction cycles. For checkpoint sizes below ~200 MB, expired state may not be removed until compaction runs. Savepoints force a clean copy and will remove expired state regardless.

### Checkpoint Storage

| Storage | Description | Use Case |
|---|---|---|
| `JobManagerCheckpointStorage` | Stores checkpoint state in JobManager heap memory. | Development/testing only. Not production-safe -- state lost if JM fails. |
| `FileSystemCheckpointStorage` | Stores checkpoint state on a durable distributed filesystem (S3, HDFS, GCS, Azure Blob). | Production. Required for any workload where checkpoint durability matters. |

### Savepoints vs Checkpoints

| Dimension | Checkpoints | Savepoints |
|---|---|---|
| Purpose | Automatic crash recovery | Planned, manual operations |
| Lifecycle | Managed by Flink (created, retained, cleaned up automatically) | Created, owned, deleted by the user; Flink never auto-deletes |
| Trigger | Periodic (`execution.checkpointing.interval`) | On-demand via CLI or REST API |
| Format | May use optimized, backend-specific formats (e.g., incremental RocksDB) | Always canonical (non-incremental) format -- portable across backends and Flink versions |
| Speed | Optimized for fast creation and recovery | Slower (full state serialization) |
| Portability | Tied to same state backend, may be version-specific | Portable across backends, cluster configs, and Flink versions |

**When to use each**:

- **Checkpoints**: Always enabled in production for automated fault tolerance. Let Flink manage the lifecycle.
- **Savepoints**: Take before any planned change -- upgrading Flink version, modifying job graph, changing parallelism, migrating between clusters. Also useful as periodic "insurance" backups alongside checkpoints.

### Key Configuration Properties

| Property | Default | Description |
|---|---|---|
| `execution.checkpointing.interval` | None (disabled) | Must be set to a value > 0 to enable checkpointing. Value in ms. Start with `60000` (1 min) for moderate workloads, `600000` (10 min) for large-state jobs. |
| `execution.checkpointing.mode` | `EXACTLY_ONCE` | `EXACTLY_ONCE` (barrier alignment) or `AT_LEAST_ONCE` (no alignment, records may cross epoch boundaries). |
| `execution.checkpointing.timeout` | `600000` (10 min) | Time in ms after which an in-progress checkpoint is aborted. Frequent timeouts signal backpressure, large state, or slow storage. |
| `execution.checkpointing.min-pause` | `0` | Minimum ms between the end of one checkpoint and the start of the next. Guarantees cooldown between checkpoints. |
| `execution.checkpointing.max-concurrent-checkpoints` | `1` | Maximum simultaneous checkpoint attempts. Setting > 1 is incompatible with unaligned checkpoints. |
| `execution.checkpointing.unaligned.enabled` | `false` | Enables unaligned checkpoints. Requires `EXACTLY_ONCE` mode and `max-concurrent-checkpoints = 1`. |
| `execution.checkpointing.externalized-checkpoint-retention` | N/A (must be set) | `RETAIN_ON_CANCELLATION` keeps files after job cancel; `DELETE_ON_CANCELLATION` removes them. |
| `state.checkpoints.num-retained` | `1` | Completed checkpoints to retain. Values > 1 allow fallback to an older checkpoint if the latest is corrupt. |

#### Setting via Flink SQL

```sql
SET 'execution.checkpointing.interval' = '60000';
SET 'execution.checkpointing.mode' = 'EXACTLY_ONCE';
SET 'execution.checkpointing.timeout' = '600000';
SET 'execution.checkpointing.min-pause' = '500';
SET 'execution.checkpointing.unaligned.enabled' = 'true';
SET 'state.checkpoints.num-retained' = '3';
```

### Confluent Cloud Flink Specifics

#### Fully Managed Checkpointing

Confluent Cloud for Apache Flink is a fully managed, serverless Flink service. The Confluent docs state explicitly:

> "You don't need to know about or interact with Flink clusters, state backends, checkpointing, or any of the other aspects that are usually involved when operating a production-ready Flink deployment."

What this means in practice:

- **Checkpointing is enabled and configured automatically** -- users do not set `execution.checkpointing.interval`, state backends, or checkpoint storage locations.
- **State backend selection** is handled by the platform (not user-configurable).
- **Checkpoint storage** is provisioned and managed by the platform.
- **Fault tolerance and recovery** are automatic -- failed jobs restart from the latest checkpoint without user intervention.
- **Watermarks** are applied automatically using a default strategy based on the `$rowtime` system column, unlike OSS Flink where watermark strategies must be defined manually.

#### Confluent Platform (Self-Managed via CMF)

For Confluent Platform for Apache Flink (deployed via Confluent Manager for Flink), checkpoint configuration is fully user-accessible:

- Set at the **ComputePool** level (applies to all statements in the pool).
- Overridden at the **Statement** level (statement-level takes precedence).
- All standard Flink checkpoint properties are available, including `execution.checkpointing.interval`, `state.checkpoints.dir`, and `state.backend.type`.

#### Key Differences Summary

| Aspect | OSS Flink | Confluent Cloud | Confluent Platform (CMF) |
|---|---|---|---|
| Checkpoint config | User sets all properties | Fully managed/automatic | User-configurable at pool and statement level |
| State backend | User chooses and configures | Platform-managed | User-configurable |
| Checkpoint storage | User provisions (S3/HDFS) | Platform-provisioned | User provisions (S3/HDFS) |
| Watermarks | Manual definition required | Default on `$rowtime` | Manual or configured |
| Savepoints | User-triggered via CLI/REST | Not clearly exposed in docs | Available |

> **Confidence note**: The exact checkpoint interval, state backend, and retained checkpoint count used by Confluent Cloud internally are not documented. Whether CC Flink SQL sessions accept `execution.checkpointing.*` properties via `SET` is not confirmed -- the messaging strongly implies these are not user-accessible.

### Kafka Source/Sink Interaction with Checkpoints

#### Kafka Source: Offset Commits on Checkpoint Completion

The Kafka source connector is a stateful operator whose state is the current read offset for each assigned partition.

1. On checkpoint trigger, the source records current offsets into checkpoint state.
2. After checkpoint **completes successfully**, offsets are committed back to Kafka (via the consumer group coordinator).
3. Flink does **not** rely on committed Kafka offsets for fault tolerance. Commits are purely for **monitoring/observability** -- consumer lag dashboards, Confluent Cloud metrics, etc.
4. On recovery, Flink restores offsets from checkpoint state and seeks the consumer to those positions, regardless of what was committed to Kafka.
5. If checkpointing is not enabled, Flink does not commit offsets to Kafka at all.

#### Kafka Sink: Two-Phase Commit for Exactly-Once

For exactly-once delivery to Kafka sinks, Flink uses a two-phase commit (2PC) protocol integrated with Kafka transactions:

1. **Between checkpoints**: The sink writes records to Kafka within an open transaction. Records are invisible to `read_committed` consumers.
2. **Checkpoint barrier arrives**: The sink flushes pending records, pre-commits the transaction, and acknowledges the checkpoint.
3. **Checkpoint completes**: The Checkpoint Coordinator notifies the sink. The sink **commits** the Kafka transaction, making records visible.
4. **On failure before commit**: The transaction is aborted. Records are discarded. Recovery from checkpoint replays them.

Critical config interaction -- **`transaction.timeout.ms`** (Kafka broker-side, default: 15 minutes) must be greater than the maximum possible checkpoint duration plus expected recovery time. If a checkpoint takes longer than this timeout, the broker aborts the transaction.

Rule of thumb:

```
transaction.timeout.ms >= execution.checkpointing.interval
                        + execution.checkpointing.timeout
                        + expected_downtime_buffer
```

**Output latency implication**: with exactly-once Kafka sinks, data is not visible to downstream `read_committed` consumers until the next checkpoint commits. A 60-second checkpoint interval means up to 60 seconds of additional end-to-end latency.

#### `scan.startup.mode` Interaction

The `scan.startup.mode` property (`earliest-offset`, `latest-offset`, `group-offsets`, `timestamp`) controls where the Kafka source initially begins reading:

- Used **only on cold start** (no checkpoint or savepoint to restore from).
- When restoring from a checkpoint or savepoint, the startup mode is **completely ignored** -- the source resumes from offsets stored in checkpoint state.
- This is why `scan.startup.mode = 'earliest-offset'` matters for deterministic replay from scratch but has no effect on crash recovery.

### Troubleshooting

#### Checkpoint Timeouts

**Symptom**: Checkpoints fail with timeout errors (exceeding `execution.checkpointing.timeout`).

**Root causes**:

| Cause | Diagnosis | Fix |
|---|---|---|
| Backpressure | Alignment duration dominates checkpoint time in Flink Web UI | Enable unaligned checkpoints; fix the slow operator (scale up, reduce skew) |
| Large state size | High async duration; growing checkpoint sizes | Switch to RocksDB with incremental checkpoints; add state TTL |
| Slow checkpoint storage | High async duration with stable state sizes | Upgrade storage throughput; use faster filesystem |
| GC pauses (HashMapStateBackend) | Long sync duration; GC logs show stop-the-world events | Switch to RocksDB backend |

#### Backpressure Impact on Checkpoints

Even when checkpoints do not timeout, backpressure can cause them to take much longer than the interval, leading to cascading delays:

- With `max-concurrent-checkpoints = 1`, checkpoint N+1 cannot start until N finishes.
- If checkpoint duration approaches the interval, the job is effectively always checkpointing, adding constant overhead.
- Use `execution.checkpointing.min-pause` to guarantee breathing room between checkpoints.

#### State Size Growth

**Symptom**: Checkpoint sizes grow monotonically, eventually causing timeouts or storage exhaustion.

**Root causes and mitigations**:

- **Missing state TTL**: Stateful operations (joins, dedup, aggregations) retain state for inactive keys forever by default. Set `table.exec.state.ttl` in Flink SQL to expire stale state. This is the single most impactful setting for controlling state growth.
- **Large windows**: Window operators retain all data until the window fires. Use the narrowest window that meets business requirements.
- **Unbounded key cardinality**: Upsert/CDC patterns grow with distinct key count. Monitor key cardinality and apply TTL.

```sql
-- Set state TTL to 24 hours in Flink SQL
SET 'table.exec.state.ttl' = '86400000';
```

#### Additional Gotchas

- **Exactly-once + Kafka sink latency**: Output is delayed by up to one checkpoint interval because transactions commit only on checkpoint completion.
- **Unaligned + concurrent checkpoints**: You cannot use unaligned checkpoints with `max-concurrent-checkpoints > 1`.
- **Single retained checkpoint**: With `state.checkpoints.num-retained = 1` (default), a corrupt latest checkpoint means no recovery point. Set to 2-3 for production.
- **Incremental checkpoint + state TTL**: With RocksDB incremental checkpoints, expired state is not removed until RocksDB compaction runs. Checkpoint sizes may not shrink immediately after TTL expiration.

## Related

- [Exactly-Once Semantics](concepts/exactly-once-semantics) -- end-to-end delivery guarantees, Kafka transaction integration
- [Consumer Lag Monitoring](concepts/consumer-lag-monitoring) -- offset commits on checkpoint completion feed consumer lag metrics
