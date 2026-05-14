---
title: FSI Producer Configuration
tags: [kafka, fsi, producers, idempotence, transactions, durability]
sources: [outputs/reports/confluent-best-practices-quickstart.md]
related: [concepts/producer-batching-config, concepts/exactly-once-semantics, concepts/schema-evolution-strategies, patterns/fsi-exactly-once, patterns/low-latency-kafka-azure, patterns/topic-naming]
confidence: medium
last_updated: 2026-05-13
last_validated: 2026-05-13
---

# FSI Producer Configuration

## Summary

The canonical producer configuration for FSI workloads: idempotent + transactional where needed, `acks=all`, `compression.type=lz4` (Canon throughput default), batched for throughput without sacrificing latency at the p99. Pairs with `concepts/producer-batching-config.md` (RecordAccumulator internals) and `patterns/fsi-exactly-once.md` (how the producer fits into the five-layer EOS pattern). This article is the *config and triage* surface; the deeper why-batching-works content lives in `producer-batching-config`.

## Pattern

### What the producer owns

1. **The data contract** — schema (Avro/Protobuf) and its semantics: nullability, tombstones, units, timezones. Treat the schema like a published API.
2. **The key** — partition assignment = `hash(key) % partitions` (or null → sticky partitioner). The key is the ordering contract; relying on the sticky partitioner means no ordering guarantee.
3. **Serialization & wire format** — Avro/Protobuf in prod (Canon); JSON Schema is prototype/debug only. Magic byte + 4-byte schema ID.
4. **Delivery guarantee on produce** — `acks`, `enable.idempotence`, transactions.
5. **Headers** — tracing/correlation IDs, schema metadata, routing hints, CSFLE metadata.
6. **Timestamps & tombstones** — `CreateTime` vs `LogAppendTime`; `null` value = delete marker on compacted topics.

### Canonical FSI producer config

Matches `fsi-dsp:reference/java-producer/FsiProducer.java`.

```properties
# ── Durability / exactly-once-per-partition (Canon: MANDATORY in prod) ──
enable.idempotence=true                 # default since 3.0; do not disable
acks=all                                # never 0 or 1 for durable workloads
retries=2147483647                      # bounded in practice by delivery.timeout.ms
max.in.flight.requests.per.connection=5 # safe with idempotence; ordering preserved
delivery.timeout.ms=120000              # total time a send may take (incl. retries)
request.timeout.ms=30000

# ── Throughput / batching (tune per profile — see below) ──
compression.type=lz4                    # throughput default (Canon); switch to zstd only if storage $/GB matters
batch.size=32768                        # 32 KB
linger.ms=20                            # often *lowers* p99 under load vs linger.ms=0
buffer.memory=33554432                  # 32 MB; raise if you see BufferExhausted

# ── Identity / observability ──
client.id=<app>-<instance>
metrics.recording.level=INFO

# ── Schema Registry ──
value.serializer=io.confluent.kafka.serializers.KafkaAvroSerializer
auto.register.schemas=false             # PROD: register in CI, not from the client
use.latest.version=true                 # or pin a version
```

### Transactional producer

Only when you need atomic produce-or-produce-and-consume:

```properties
transactional.id=<stable-per-instance-id>   # MUST be stable & unique per producer instance
# code flow: initTransactions() → beginTransaction() → send()... →
#            sendOffsetsToTransaction() → commitTransaction()
# downstream consumers MUST set isolation.level=read_committed
```

See `patterns/fsi-exactly-once.md` for the full five-layer pattern (idempotent + transactional producers, `read_committed` consumers, outbox, idempotency keys, saga orchestration).

### Optimizations by impact

| Knob | Effect | Recommended default |
|---|---|---|
| `linger.ms` + `batch.size` | Single biggest throughput lever. Bigger batches → fewer requests → less broker CPU + better compression. | `linger.ms=5–20`, `batch.size=32–128 KB`. `linger.ms=0` is **not** "fastest" under load. |
| `compression.type` | `lz4` ≈ best CPU/ratio for throughput; `zstd` ≈ best ratio for storage cost; `gzip` only for cold-path. | `lz4` general (Canon), `zstd` if storage $/GB matters. |
| `acks` + `enable.idempotence` | `acks=all` + idempotence = exactly-once per partition with no meaningful throughput penalty on modern brokers. | Always on. |
| `max.in.flight.requests.per.connection` | With idempotence, 5 is safe and keeps the pipe full while preserving order. Without idempotence, >1 risks reordering on retry. | 5. |
| Partitioner | Sticky (default since 2.4 / "uniform sticky" KIP-794 in 3.3+) batches null-keyed records well. | Default; set a real key for keyed topics. |
| `delivery.timeout.ms` | The real "give up" bound. Make it ≥ `linger.ms + request.timeout.ms + retry budget`. | 120 s typical; lower for latency-tier apps that prefer fast-fail + DLQ. |
| `buffer.memory` / `max.block.ms` | Backpressure surface. `max.block.ms` is how long `send()` blocks when buffer is full. | 32–64 MB; `max.block.ms` 60 s, or short + DLQ for latency tiers. |

### Latency-tier overlay (sub-100 ms)

Examples: fraud detection, risk decisioning. See `patterns/low-latency-kafka-azure.md` and `fsi-dsp:reference/*-low-latency-azure/`.

- `linger.ms=0–5`, smaller `batch.size`
- `delivery.timeout.ms` low; fast-fail to DLQ rather than long retries
- Co-locate the producer in the cluster's region/AZ
- Keep connections warm; be ILB-aware

> ⚠️ **Sub-millisecond (market-data) tier.** The overlay above covers <100 ms tiers (risk, compliance). It does **not** cover sub-ms market data: `acks=all` + cross-AZ ISR waits cannot meet sub-ms SLAs — a single cross-AZ hop is ~1–2 ms before replication even starts. That tier needs an explicit documented decision: single-AZ co-location (accept AZ-failure blast radius), or a deliberate `acks` / `min.insync.replicas` trade-off, with producers and consumers pinned to the AZ of partition leaders. This is a Canon FSI conversation — EOS / durability implications for anything that later feeds regulatory reporting — not just an ops tuning knob.

## When to Use

- Any FSI producer writing to a durable topic — start from this baseline, then layer on latency or EOS overlays.
- Reference for code reviews when "is this producer config FSI-compliant?" is the question.
- The producer block of a `/dsp:apply` Terraform module's reference producer template.

## Caveats

- `enable.idempotence=true` *implies* `acks=all`, `retries>0`, `max.in.flight≤5`. Overriding `acks=1` silently disables idempotence and ordering guarantees (Gotcha #1 in `synthesis/confluent-gotchas-top-20.md`).
- `UnknownProducerIdException` — the producer's PID metadata aged out of the partition. Don't set topic retention shorter than the producer's idle period.
- `OutOfOrderSequenceException` — almost always `acks≠all`, broker that lost producer state, or a buggy custom retry wrapper.
- `transactional.id` must be **stable and unique per producer instance**. Reusing it triggers `ProducerFencedException` (the new instance fences the old).
- `auto.register.schemas=true` is a governance bypass and a race when two instances race to register slightly-different "latest" schemas. Register in CI; clients pin or use `use.latest.version=true`. See `concepts/schema-registry-best-practices.md`.

### Triage

| Symptom / exception | Likely meaning | First moves |
|---|---|---|
| `TimeoutException: Expiring N record(s)` | Sends queueing faster than they drain. | Check `record-queue-time-avg`, `request-latency-avg`, `buffer-available-bytes`; broker `RequestQueueSize`, `RequestHandlerAvgIdlePercent`. Raise `batch.size`/`linger.ms`, then `buffer.memory`, then look at the broker. |
| `BufferExhaustedException` / `send()` blocking | Buffer full, broker can't keep up. | Raise `buffer.memory`; investigate broker; consider app-level backpressure. |
| `OutOfOrderSequenceException` | Idempotence sequence gap. | Confirm `acks=all` and no manual catch+re-send; check for broker restarts / segment deletion. |
| `ProducerFencedException` | A newer producer with the same `transactional.id` exists. | Ensure `transactional.id` is unique per instance; exit and let the new instance own it. |
| `NotEnoughReplicasException` / `NOT_ENOUGH_REPLICAS_AFTER_APPEND` | `min.insync.replicas` not met. | Check ISR (`kafka-topics --describe`), broker health, `replica.lag.time.max.ms`. On CC this is a Confluent-side incident. |
| `SerializationException` from Avro serializer | Can't reach SR, auth wrong, compat rejected schema, or subject naming mismatch. | Check SR endpoint + `basic.auth.user.info`, `auto.register.schemas` policy, subject name strategy. |
| Throughput plateaus well below capacity | Tiny batches, no compression, single producer, or hot partition. | Raise `linger.ms`; enable `lz4`/`zstd`; add producer instances; check partition skew. |

**Rule of thumb:** if the *commit/append* path is slow or erroring → producer/broker. If records *arrive but consumers fall behind* → consumer/partitioning (`patterns/consumer-config-fsi.md`). If records *arrive but are wrong* → schema/contract (`concepts/schema-registry-best-practices.md`).

## Related

- [Producer Batching Configuration](../concepts/producer-batching-config.md) — RecordAccumulator internals, tuning profiles, JMX
- [Exactly-Once Semantics](../concepts/exactly-once-semantics.md) — idempotent and transactional producer mechanics
- [FSI Exactly-Once Pattern](fsi-exactly-once.md) — five-layer EOS including producer/transaction layer
- [Low-Latency Kafka Clients on Azure](low-latency-kafka-azure.md) — sub-100ms tuning overlay
- [Schema Registry Best Practices](../concepts/schema-registry-best-practices.md) — `auto.register.schemas`, subject strategy, CI compatibility checks
- [Topic Naming Convention](topic-naming.md) — `<domain>.<application>.<entity>.<event>` (ADR-007)
- [Top 20 Confluent Gotchas](../synthesis/confluent-gotchas-top-20.md) — #1, #2, #19 are producer-related
