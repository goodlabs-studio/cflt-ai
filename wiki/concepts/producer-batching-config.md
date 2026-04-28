---
title: Producer Batching Configuration
tags: [kafka performance producers]
sources:
  - https://kafka.apache.org/41/configuration/producer-configs/
  - https://docs.confluent.io/platform/current/installation/configuration/producer-configs.html
  - https://books.japila.pl/kafka-internals/clients/producer/RecordAccumulator/
  - https://docs.confluent.io/platform/current/kafka/producer-metrics.html
  - https://www.confluent.io/blog/apache-kafka-message-compression/
  - https://cwiki.apache.org/confluence/display/KAFKA/An+analysis+of+the+impact+of+max.in.flight.requests.per.connection+and+acks+on+Producer+performance
related: [concepts/exactly-once-semantics, concepts/consumer-lag-monitoring, patterns/aks-kafka-tuning]
confidence: medium
last_updated: 2026-04-17
last_validated: 2026-04-28
---

# Producer Batching Configuration

## Summary

Kafka producers batch records per-partition in the `RecordAccumulator` before the background `Sender` thread transmits them to brokers. Batching behavior is controlled primarily by `batch.size` (16 KB default) and `linger.ms` (5 ms default as of Kafka 4.0, previously 0), whichever threshold triggers first. Proper tuning of batching, compression, and in-flight pipelining parameters directly determines producer throughput, latency, and memory footprint. This article covers the internal batch lifecycle, key configuration properties, compression trade-offs, tuning profiles, `acks` interaction, monitoring metrics, and common pitfalls.

## Detail

### RecordAccumulator Internals

The producer has three core components relevant to batching:

- **`KafkaProducer`** -- user-facing API accepting `send()` calls.
- **`RecordAccumulator`** -- buffers records into per-partition batches in memory.
- **`Sender` thread** -- background I/O thread that drains ready batches and transmits `Produce` requests to brokers.

The `RecordAccumulator` maintains a `ConcurrentMap<TopicPartition, Deque<ProducerBatch>>` -- one `ArrayDeque` of `ProducerBatch` objects per topic-partition.

**Key operations:**

| Operation | Behavior |
|-----------|----------|
| `append()` | Looks up (or lazily creates) the `Deque` for the target partition. Attempts `tryAppend()` on the last (active) batch. If the batch is full or absent, allocates a new `ProducerBatch` from the `BufferPool`. |
| `ready()` | Scans all partition deques and selects broker nodes with batches ready to send. A batch is ready when: (a) it reached `batch.size`, (b) `linger.ms` elapsed, (c) the accumulator is being flushed, or (d) memory is exhausted. |
| `drain()` | Collects ready batches per broker, respecting `max.request.size`, and hands them to the `Sender` thread. |

### Batch Lifecycle

1. **Allocation** -- A `ProducerBatch` is allocated from the `BufferPool`. Post-KIP-782, initial allocation uses `batch.initial.size` (4 KB default) with expandable buffers, reducing memory waste when batches don't fill.
2. **Filling** -- Records are appended via `MemoryRecordsBuilder`. The batch accepts records until it reaches `batch.size` or `linger.ms` expires.
3. **Ready** -- The batch is marked ready for the `Sender` thread.
4. **Drain** -- The `Sender` groups partition-batches destined for the same broker into a single `Produce` request.
5. **In-flight** -- The batch awaits broker acknowledgement. Up to `max.in.flight.requests.per.connection` batches can be in-flight per broker connection simultaneously.
6. **Completion** -- On success (or final failure after retries / `delivery.timeout.ms` expiry), the batch's `Future` completes and the buffer is returned to the `BufferPool`.

### Memory Pool (`buffer.memory`)

The `BufferPool` manages a fixed pool of memory sized by `buffer.memory` (32 MB default). It pools `ByteBuffer` instances of exactly `batch.size` for reuse. Buffers of other sizes (e.g., oversized records) are allocated directly and GC'd. When the pool is exhausted, `send()` blocks up to `max.block.ms` before throwing `TimeoutException`.

### Key Configuration Properties

All defaults verified against [Apache Kafka 4.1 Producer Configs](https://kafka.apache.org/41/configuration/producer-configs/).

| Property | Default | Unit | Description |
|----------|---------|------|-------------|
| `batch.size` | `16384` | bytes (16 KB) | Maximum size of a single batch per partition. A full batch sends immediately regardless of `linger.ms`. Setting to 0 disables batching. |
| `linger.ms` | `5` (Kafka 4.0+); `0` (Kafka <4.0) | ms | Time to wait for additional records before sending a non-full batch. Changed in Kafka 4.0 because efficiency gains from larger batches offset the 5 ms wait. |
| `buffer.memory` | `33554432` | bytes (32 MB) | Total memory for buffering unsent records across all partitions, including in-flight requests and compression buffers. |
| `max.block.ms` | `60000` | ms (60 s) | Maximum time `send()` and `partitionsFor()` block when `buffer.memory` is exhausted or metadata unavailable. |
| `max.request.size` | `1048576` | bytes (1 MB) | Maximum size of a single `Produce` request. Also caps the maximum uncompressed record size. Must align with broker `message.max.bytes`. |
| `max.in.flight.requests.per.connection` | `5` | count | Unacknowledged requests per broker connection. Higher values increase pipelining but can cause reordering on retry unless idempotence is enabled (which handles reordering for values <= 5). |
| `compression.type` | `none` | -- | Per-batch compression codec: `none`, `gzip`, `snappy`, `lz4`, `zstd`. |
| `send.buffer.bytes` | `131072` | bytes (128 KB) | TCP socket send buffer (`SO_SNDBUF`). Set to `-1` for OS default. This is the TCP-level buffer, not the application-level `buffer.memory`. |
| `acks` | `all` (Kafka 3.0+) | -- | `all`/`-1`: wait for all ISR replicas. `1`: leader only. `0`: fire-and-forget. |
| `delivery.timeout.ms` | `120000` | ms (2 min) | Upper bound on total delivery time (batching + send + retries + ack wait). Must be >= `linger.ms` + `request.timeout.ms`. |

### How `batch.size` and `linger.ms` Interact

These two settings form a "whichever comes first" gate:

- If `batch.size` worth of records accumulates for a partition, the batch sends **immediately** regardless of `linger.ms`.
- If `linger.ms` expires before the batch fills, the batch sends at whatever size it has reached.
- With `linger.ms=0` (pre-Kafka 4.0 default), batches send as soon as the `Sender` thread picks them up -- effectively only batching records that arrive between `Sender` thread wake-ups.
- With `linger.ms=5` (Kafka 4.0+ default), the producer intentionally waits 5 ms to accumulate more records, which typically produces larger batches and reduces per-record overhead enough to offset the delay.

### Compression Trade-offs

Compression is applied **per batch**, so larger batches (higher `batch.size` + `linger.ms`) yield better compression ratios.

| Codec | Compression Ratio | Speed | CPU Cost | Recommendation |
|-------|-------------------|-------|----------|----------------|
| `none` | 1.0x | N/A | Zero | Latency-sensitive workloads, CPU-constrained environments, already-compressed data |
| `lz4` | ~2-3x | Fastest | Low | **Default recommendation for throughput.** Best speed-to-ratio trade-off. |
| `snappy` | ~1.5-2.5x | Very fast | Low | Legacy workloads. LZ4 is generally preferred in modern Kafka. |
| `zstd` | ~3-5x | Moderate | Moderate-high | Storage-constrained clusters, high fan-out topics, archival. Tunable levels (default 3). |
| `gzip` | ~3-4x | Slow | Highest | **Avoid.** Throughput drops to ~830 msg/s vs ~3400 for LZ4/Snappy in benchmarks. Only if compatibility requires it. |

The broker stores data in the producer's compressed format and does not recompress (unless `compression.type` is set differently at the topic level). Consumer decompression is typically cheaper than producer compression.

### Tuning Profiles

#### Latency-Optimized

```properties
# Minimize time-to-broker for each record
batch.size=16384
linger.ms=0
compression.type=none
max.in.flight.requests.per.connection=5
```

Trade-offs: More requests, smaller batches, higher per-record overhead, higher broker load. Use for real-time event processing, market data, interactive applications.

#### Throughput-Optimized

```properties
# Maximize records per request, reduce per-record overhead
batch.size=131072
linger.ms=50
compression.type=lz4
buffer.memory=67108864
max.in.flight.requests.per.connection=5
```

Trade-offs: Higher tail latency (up to `linger.ms` + network RTT + replication). Use for log ingestion, metrics pipelines, ETL, batch-oriented workloads.

#### Balanced (Recommended Starting Point)

```properties
# Good throughput without excessive latency
batch.size=65536
linger.ms=10
compression.type=lz4
buffer.memory=33554432
```

Trade-offs: Modest batching delay with meaningful throughput improvement. Suitable for most general-purpose streaming workloads.

### `acks` Interaction with Batching

With `acks=all` (default since Kafka 3.0), the leader waits for all ISR replicas to acknowledge before responding. This adds ~2-5 ms latency compared to ~1-2 ms for `acks=1`. Total produce latency is roughly:

```
total_latency = linger.ms + network_rtt + leader_write + ISR_replication_wait
```

**Why batching matters more with `acks=all`:** Each request pays the ISR replication penalty. Sending many small batches means paying that penalty per batch. Larger, well-filled batches amortize the replication latency over more records, often yielding *lower* per-record latency despite the added `linger.ms` delay.

**Pipelining interaction:** With `max.in.flight.requests.per.connection=5`, the producer can have 5 batches in-flight per broker. Because `acks=all` increases per-request latency, pipelining is essential to maintain throughput:

```
effective_throughput = max_in_flight * batch_size / ack_latency
```

**Idempotence constraint:** With `enable.idempotence=true` (default since Kafka 3.0), `acks` must be `all` and `max.in.flight.requests.per.connection` must be <= 5. Ordering is preserved via sequence numbers even with 5 in-flight requests.

### JMX Monitoring Metrics

MBean: `kafka.producer:type=producer-metrics,client-id={clientId}`

| Metric | Description | Watch For |
|--------|-------------|-----------|
| `batch-size-avg` | Average bytes per batch per partition per request | Low values relative to `batch.size` = batches sending before filling. Increase `linger.ms`. |
| `batch-size-max` | Maximum batch size observed | Consistently at `batch.size` = batches are filling; consider increasing `batch.size`. |
| `record-queue-time-avg` | Average time (ms) a batch spent in the accumulator | High values = backpressure from broker or network. |
| `record-queue-time-max` | Maximum time (ms) a batch waited in the accumulator | Spikes indicate transient backpressure or GC pauses. |
| `records-per-request-avg` | Average records per produce request | Low values = poor batching efficiency. |
| `compression-rate-avg` | Compression ratio (compressed/uncompressed) | Values near 1.0 with compression enabled = data not compressible. |
| `buffer-available-bytes` | Free bytes in `buffer.memory` | Approaching 0 = near buffer exhaustion; `send()` will start blocking. |
| `buffer-total-bytes` | Total `buffer.memory` configured | Reference value. |
| `bufferpool-wait-time-total` | Total time (ns) blocked waiting for buffer space | Non-zero and growing = `buffer.memory` undersized for throughput. |
| `request-latency-avg` | Average time (ms) for a produce request round-trip | High with `acks=all` may indicate slow ISR replicas. |

**Alerting thresholds (starting points):**

- `bufferpool-wait-time-total` > 0 sustained -- increase `buffer.memory` or reduce throughput
- `record-queue-time-avg` > 1000 ms -- investigate broker health, network, ISR lag
- `batch-size-avg` < 25% of `batch.size` -- increase `linger.ms`
- `buffer-available-bytes` < 10% of `buffer-total-bytes` -- approaching exhaustion

### Common Pitfalls

**1. `batch.size=0` disables batching entirely.** Creates a new `ProducerBatch` object per record (GC churn), defeats TCP pipelining, and triggers the Nagle algorithm at low TPS. Every record becomes its own `ProduceRequest` — one record, one full TCP round trip. `linger.ms=0` alone already gives immediate dispatch behavior; `batch.size=0` adds cost with zero benefit. **Never set `batch.size=0`.**

**2. `batch.size` too small for high-throughput workloads.** The 16 KB default fills quickly under volume, producing many small requests with fixed per-request overhead. Increase to 64-128 KB for throughput-oriented scenarios.

**3. `linger.ms=0` combined with `acks=all`.** Sends partially-filled batches immediately, then waits for ISR replication on each tiny batch. You pay the `acks=all` latency penalty per batch. Setting `linger.ms=5-20` often *reduces* overall latency because fewer, larger requests complete faster.

**4. `buffer.memory` exhaustion.** When producers outpace broker ingestion, the 32 MB buffer fills. `send()` blocks for `max.block.ms` (60 s), then throws `TimeoutException`. Symptoms: application threads hang, throughput drops to zero in bursts. Increasing `buffer.memory` buys time but masks the root cause -- also investigate broker health.

**5. `max.request.size` < record size.** If a single record exceeds `max.request.size` (1 MB default), the producer throws `RecordTooLargeException` immediately with no retry. Must be coordinated with broker `message.max.bytes` and topic `max.message.bytes`.

**6. Oversized `batch.size` wasting memory with many partitions.** Each partition allocates at least one batch buffer. With 1000 partitions and `batch.size=1MB`, that is ~1 GB for empty buffers. Post-KIP-782, `batch.initial.size` (4 KB default) mitigates this with expandable buffers, but the concern applies for older client versions.

**7. `delivery.timeout.ms` misconfiguration.** Must be >= `linger.ms` + `request.timeout.ms`. If set too low, the producer times out batches before they get sent, especially with high `linger.ms` values.

**8. `max.in.flight.requests.per.connection=1` for ordering.** Destroys throughput, especially with `acks=all`, because only one batch is in-flight per broker. With `enable.idempotence=true` (default), ordering is preserved with up to 5 in-flight requests -- no reason to set this to 1.

## Related

- [Exactly-Once Semantics](concepts/exactly-once-semantics) -- idempotence and transactional producer constraints on batching configs
- [Consumer Lag Monitoring](concepts/consumer-lag-monitoring) -- downstream impact of producer batching on end-to-end latency
- [AKS Kafka Tuning](patterns/aks-kafka-tuning) -- platform-specific producer tuning in Kubernetes environments
