---
title: Kafka Streams Architecture
tags: [kafka-streams, architecture, topology, runtime, confluent-agent-skills]
sources: [raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/architecture.md]
related: [concepts/exactly-once-semantics, concepts/flink-checkpointing, patterns/flink-runtime-models, concepts/fsi-data-streaming-platform, concepts/kafka-streams-config-baseline, concepts/kafka-streams-debugging]
confidence: high
last_updated: 2026-05-16
last_validated: 2026-05-16
source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4
upstream_path: skills/kafka-streams-programming/references/architecture.md
---

# Kafka Streams Architecture

## Summary

How Kafka Streams (KS) actually works inside the JVM: it's a client library, not a separate cluster. Each instance is a consumer that processes records and produces results back to Kafka. This article is the canonical reference for the threading model (StreamThread, Task, Subtopology, GlobalStreamThread), the topology-to-partitions-to-tasks mapping, RocksDB state stores, the commit-and-flush cycle, changelog and repartition topics, and the load-bearing **memory formula** that other articles cross-reference for sizing.

Sourced from `confluentinc/agent-skills@91d1871e` (Apache-2.0) — upstream maintains an eval gate at 90%+ pass before merge, so this article is `confidence: high` via source attestation rather than per-claim MCP re-validation. Trip-wire micro-articles in `wiki/concepts/` carry full MCP validation.

## Detail

### Core concepts

Kafka Streams is a **client library** — it runs inside your JVM process, not on a separate cluster. Each instance connects to Kafka as a consumer, processes records, and produces results back to Kafka.

### Threading model

```
KafkaStreams instance
├── StreamThread-1 (Java thread)
│   ├── Consumer (polls assigned partitions)
│   ├── Task 0_0 (partition 0 of subtopology 0)
│   │   ├── Processor topology
│   │   └── State stores (RocksDB)
│   ├── Task 0_1 (partition 1 of subtopology 0)
│   └── Producer (writes to output/changelog topics)
├── StreamThread-2
│   └── ...
├── GlobalStreamThread (if GlobalKTable is used)
│   └── Reads ALL partitions of global topics
└── StateRestoreThread
    └── Replays changelogs to rebuild state stores
```

- **StreamThread** — event loop: poll → process → commit. One thread handles multiple tasks.
- **Task** — unit of parallelism. One task per input partition per subtopology. A task owns its state stores.
- **Subtopology** — an independent processing graph with no shared state. KS creates separate subtopologies for disconnected parts of the topology.
- **GlobalStreamThread** — separate thread for `GlobalKTable`; reads every partition and builds a local copy of the entire table.

### How partitions map to tasks

```
Input topic: orders (6 partitions)
Topology:    orders → groupByKey → aggregate → output

Tasks created: 6 (one per partition)
If 2 instances with 1 thread each:  3 tasks per instance
If 1 instance with 3 threads:        2 tasks per thread
```

**Max parallelism = number of input partitions.** More instances/threads than partitions means idle capacity.

### State stores

Each stateful task has its own state-store instance, backed by RocksDB by default:

- **Partitioned** — task 0_0 only has state for partition 0's keys.
- **Persistent** — survives restarts via local RocksDB files.
- **Recoverable** — backed by changelog topics; can be rebuilt from scratch.
- **Off-heap** — RocksDB memory (block cache, write buffers) is NOT controlled by JVM heap settings.

### Lifecycle states

```
CREATED → REBALANCING → RUNNING → PENDING_SHUTDOWN → NOT_RUNNING   (normal path)
RUNNING → PENDING_ERROR → ERROR                                     (error path)
```

`CREATED` (not started), `REBALANCING` (task assignment), `RUNNING` (processing), `PENDING_SHUTDOWN` (draining), `NOT_RUNNING` (clean exit), `ERROR` (unrecoverable).

### Commit and flush

Commit cycle (`commit.interval.ms`): (1) flush state stores → (2) flush producer → (3) commit offsets.

- At-least-once: async, 30 s default.
- Exactly-once: transactional (atomic), 100 ms default.

**Cache** (`statestore.cache.max.bytes`) sits in front of RocksDB. Deduplicates updates per key within the commit interval. 50 MB cache + 30 s commits = downstream sees only the latest value per key per cycle.

### Changelog topics

Every state store has a changelog: `<application.id>-<store-name>-changelog`.

- Non-windowed: `cleanup.policy=compact`
- Windowed: `cleanup.policy=compact,delete`

These enable recovery by replaying. Standby replicas stay warm by continuously replaying.

### Repartition topics

Created by `selectKey()`, `groupBy()`, `map()` when the key changes. Naming: `<application.id>-<operator-name>-repartition`. **Retention: infinite — DO NOT set retention. Setting it causes data loss.**

### GlobalKTable vs KTable

| Aspect | KTable | GlobalKTable |
|---|---|---|
| Distribution | Partitioned | Replicated to all instances |
| Co-partitioning for joins | Required | Not required |
| Join key | Must match table key | Any field |
| Memory | Per partition | Full table per instance |
| Changelog | Yes | No (reads source directly) |

Use GlobalKTable when: the lookup is small (< few GB), join key ≠ record key, or co-partitioning is impractical.

## Sizing Guidelines

### Parallelism

`total_threads = instances × num.stream.threads ≤ input_partitions`

More threads than partitions = idle (hot standbys). For multi-sub-topology applications, use `topology.describe()` for actual task count.

Sizing rules:

- **Stateless:** more threads/instance (match CPU), fewer instances.
- **Stateful:** fewer threads/instance, size for RocksDB. Prefer fewer large instances over many small (restoration is expensive).

### Memory (stateful apps) — canonical reference {#memory}

Other articles cross-reference this section for the RocksDB memory formula.

```
JVM heap: application objects + serde buffers + cache
  - statestore.cache.max.bytes is on-heap (divided among threads)
  - Typical: 512 MB – 2 GB heap

RocksDB off-heap: per state-store instance
  - block_cache (50 MB) + write_buffers (16 MB × 3) = 98 MB per instance
  - Non-windowed: store_instances = partitions_per_instance × stores
  - Windowed:     store_instances = partitions_per_instance × stores × 3 (segments)
  - Typical: 1 – 10 GB off-heap

Container total = heap + off-heap + OS overhead (~256 MB)
Set MaxRAMPercentage=75 to leave room for RocksDB
```

**Worked example (windowed aggregation):**

- 40 partitions, 1 windowed store, 4 instances → 10 partitions/instance
- Windowed segments: 10 × 1 × 3 = 30 store instances per app
- RocksDB memory: 30 × 98 MB ≈ 2.9 GB off-heap
- Container: 2 GB heap + 2.9 GB RocksDB + 256 MB OS ≈ 5.2 GB minimum

**`BoundedMemoryRocksDBConfig`:** for apps with many stores, share a single block cache across all RocksDB instances to limit total off-heap. See [Kafka Streams Config Baseline § Performance Tuning](kafka-streams-config-baseline.md).

### Disk (stateful apps)

```
RocksDB disk = state_size × 3 (SST files + WAL + compaction overhead)
Standby replicas double the disk requirement
Use fast local storage (SSD), never NFS/EBS
Monitor disk usage with alerts at 70%
```

The 3× factor accounts for active SST files, WAL, and temporary compaction files. Windowed stores create multiple segments per partition, increasing disk needs.

**Always use persistent volumes (PVCs) in Kubernetes for stateful apps.** Ephemeral storage forces full state restoration on every restart — hours for large state stores.

### Network and broker sizing

```
Stateless broker overhead:  ~1×  input volume (read + write output)
Stateful broker overhead:   ~1.5–2× input volume (+ changelog writes)
EOS broker overhead:        ~2×  input volume (+ transaction markers)
```

Changelog topics are replicated by `replication.factor` (default 3). Each state store creates one changelog topic. Repartition topics add broker load approximately matching the original topic being remapped.

### Scaling

- **Scale out** (add instances): network/memory-bound apps. Tasks reassign after rebalance.
- **Scale up** (add threads/resources): CPU-bound. Must increase `num.stream.threads` and adjust heap/RocksDB caps.

## Related

- [Exactly-Once Semantics](exactly-once-semantics.md) — EOS in stream processing
- [Flink Checkpointing](flink-checkpointing.md) — alternative streaming runtime context (Chandy-Lamport vs KS commit cycle)
- [Flink Runtime Models](../patterns/flink-runtime-models.md) — Flink vs Kafka Streams runtime trade-offs
- [FSI Data Streaming Platform](fsi-data-streaming-platform.md) — platform context
- [Kafka Streams Config Baseline](kafka-streams-config-baseline.md) — operational defaults, RocksDB tuning
- [Kafka Streams Debugging](kafka-streams-debugging.md) — diagnostic counterpart

---

*Source: confluentinc/agent-skills@91d1871e · skills/kafka-streams-programming/references/architecture.md · Ingested 2026-05-16 · Apache-2.0*
