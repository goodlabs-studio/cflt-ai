---
title: FSI Consumer Configuration
tags: [kafka, fsi, consumers, rebalancing, lag, assignment]
sources: [outputs/reports/confluent-best-practices-quickstart.md]
related: [concepts/consumer-group-rebalancing, concepts/consumer-lag-monitoring, concepts/exactly-once-semantics, patterns/producer-config-fsi, patterns/low-latency-kafka-azure, patterns/dead-letter-queue-design]
confidence: medium
last_updated: 2026-05-13
last_validated: 2026-05-13
---

# FSI Consumer Configuration

## Summary

The canonical consumer configuration for FSI processing apps: manual offset commits, `read_committed` where producers transact, cooperative-sticky assignment (explicit — *not* the OOTB default), static membership for low-churn deploys, fetch-from-follower for in-AZ cost. Pairs with `concepts/consumer-group-rebalancing.md` (protocol generations) and `concepts/consumer-lag-monitoring.md` (lag instrumentation).

## Pattern

### What the consumer owns

1. **Offset-commit strategy** — manual commit **after** processing (Canon). `enable.auto.commit=true` commits on `poll()` *before* you've done the work → at-most-once on crash. Sync commit on shutdown/rebalance; async in steady state.
2. **The consumer group ID** — one group per logical application (Canon), not per instance.
3. **Processing idempotency / dedup** — Kafka gives you at-least-once in practice. The consumer owns dedup keys / upserts so reprocessing is safe.
4. **`max.poll.interval.ms` ≥ worst-case batch processing time** — exceeding it triggers the classic "my consumer randomly stops" rebalance.
5. **Deserialization-error handling** — the poison-pill problem. Wrap with `ErrorHandlingDeserializer` (Spring) or try-catch + skip + DLQ. See `patterns/dead-letter-queue-design.md`.
6. **Rebalance behaviour** — a `ConsumerRebalanceListener` commits offsets on partition revocation; stateful consumers handle state handoff.
7. **`client.rack`** — set it to fetch from a same-AZ follower (cuts cross-AZ egress). Needs `broker.rack` + `RackAwareReplicaSelector` on the cluster — already set up on CC.

### Canonical FSI consumer config

Matches `fsi-dsp:reference/java-consumer/FsiConsumer.java`.

```properties
group.id=<logical-app-name>
enable.auto.commit=false                # Canon: never true in a processing app
auto.offset.reset=earliest              # new deployments; document if you choose latest
isolation.level=read_committed          # if any upstream producer uses transactions
max.poll.records=500                    # cap work per poll → keeps you under max.poll.interval.ms
max.poll.interval.ms=300000             # 5 min worst-case processing window
fetch.min.bytes=1024
fetch.max.wait.ms=500
partition.assignment.strategy=org.apache.kafka.clients.consumer.CooperativeStickyAssignor
# ^ SET THIS EXPLICITLY. The out-of-the-box default is [RangeAssignor, CooperativeStickyAssignor],
#   which uses RangeAssignor (stop-the-world) until every member of the group is cooperative-capable.
client.rack=<az-id>                     # fetch-from-follower
client.id=<app>-<instance>
metrics.recording.level=INFO
# Optional but recommended for deploy-without-rebalance:
# group.instance.id=<stable-id>         # static membership (KIP-345)
```

> ⚠️ **KIP-848 (new consumer rebalance protocol)** is GA as of Kafka 4.0 (early 2025) — broker-coordinated, incremental, no stop-the-world. Clients opt in via `group.protocol=consumer`. Largely obsoletes the eager/cooperative client-side dance. Verify your client version supports it before flipping; the server-side assignor is uniform/range, not cooperative-sticky.

### Dealing with lag

Track **two kinds** (see `concepts/consumer-lag-monitoring.md` for full instrumentation):

- **Offset lag** — `log-end-offset − committed-offset`. Cheap, but high on a low-volume topic isn't urgent.
- **Time lag** — how old is the oldest unprocessed record. This is what the SLA is actually written against.

**Observation surfaces** — `kafka-consumer-groups --describe`, JMX (`records-lag-max`, `records-lag`), broker-side lag emitter, **Confluent Cloud Metrics API** `io.confluent.kafka.server/consumer_lag_offsets` (use on CC, don't roll your own JMX scraper), Burrow / Kafka Lag Exporter.

**Layered alerts**: absolute threshold **and** rate-of-change **and** projected time-to-drain. A *growing* lag is the alert, not a flat-but-nonzero one.

**Why you're lagging — and the fix:**

| Cause | Tell | Fix |
|---|---|---|
| Under-parallelized | Lag spread evenly, all consumers 100% busy, #consumers == #partitions | Add partitions (then consumers) — but see partitioning gotcha. |
| Slow processing (I/O-bound) | Consumers idle waiting on DB/API, not CPU-bound | **Confluent Parallel Consumer** (key-level concurrency *beyond* partition count), or async with careful offset tracking. |
| Hot partition / key skew | One partition's lag dwarfs others | Re-key, salt the key, or split the entity. |
| Rebalance storm | Lag sawtooths; logs full of "Revoking/Assigning partitions" | Usually `max.poll.interval.ms` — see troubleshooting below. |
| GC pauses | Lag spikes correlate with long GC | Right-size heap, G1/ZGC, reduce per-record allocation. |
| Downstream backpressure | Consumer healthy but sink throttling | Batch writes, add sink capacity, or buffer. |
| Expired committed offsets | Lag "resets" or jumps after idle period | `offsets.retention.minutes` (default 7 days) expired an idle group → `auto.offset.reset` kicked in. Commit periodically even when idle. |

### Consumer-group & parallelism strategy

- **Max useful consumers in a group = partition count.** Beyond that, instances sit idle. Provision instances ≤ partitions (+1–2 spare only if using static membership).
- **Cooperative-sticky** → only moved partitions pause during rebalance, not the whole group. **Set `partition.assignment.strategy=CooperativeStickyAssignor` explicitly** — it is *not* the OOTB default. Since Kafka 3.0 the default is `[RangeAssignor, CooperativeStickyAssignor]`, which runs `RangeAssignor` (stop-the-world) until every member supports cooperative.
- **Static membership** (`group.instance.id` + tuned `session.timeout.ms`) → a rolling restart/deploy doesn't trigger a rebalance at all. Big FSI win.
- **Parallel consumption patterns, in order of preference:**
  1. Match partitions to needed parallelism, one thread per partition. Simplest, deterministic.
  2. **Confluent Parallel Consumer** when I/O-bound and you need more concurrency than partitions allow.
  3. **Kafka Streams** when the work is stateful (joins, aggregations, windowing).
  4. **Flink** when it's heavy stateful streaming, multi-stream joins, or you want SQL. See `patterns/flink-runtime-models.md`.
  5. Async/threadpool inside one consumer — only if you really understand offset management.

## When to Use

- Any FSI consumer in a processing app — start from this baseline.
- Reference when reviewing "is this consumer config FSI-compliant?"
- The consumer block of a `/dsp:apply` Terraform module's reference consumer template.

## Caveats

- **`enable.auto.commit=true` is at-most-once on crash.** Never in a processing app.
- **`max.poll.interval.ms` exceeded = the broker ejects the consumer** → rebalance → repeat. Shrink `max.poll.records`, speed up processing, or `pause()`/`resume()`.
- **`auto.offset.reset` is a trap door** — fires when there's no committed offset *or* it's out of range, which happens silently when `offsets.retention.minutes` expires an idle group.
- **`CooperativeStickyAssignor` is not the OOTB default.** Set it explicitly or move the group to KIP-848 `group.protocol=consumer`.

### Troubleshooting

| Symptom | Likely cause | First moves |
|---|---|---|
| Consumer "randomly stops," group constantly rebalancing | Poll-loop iteration exceeds `max.poll.interval.ms` → broker ejects member | Lower `max.poll.records`; speed up processing; `pause()`/`resume()` during long work. |
| `CommitFailedException` | Rebalance happened while processing; assignment is stale | Commit more frequently; shorter work units; rebalance listener; cooperative-sticky helps. |
| Same record processed forever / stuck on one offset | Poison pill — deserialization throws every time | `ErrorHandlingDeserializer` / catch+skip+DLQ. See `patterns/dead-letter-queue-design.md`. |
| Consumer reads from wrong place after deploy | No committed offset (new group) or offsets expired | Expected for new groups; otherwise see "expired committed offsets" above. |
| Fetch-from-follower not reducing cross-AZ cost | Missing `client.rack`, or cluster missing `broker.rack` / `RackAwareReplicaSelector` | Set all three; on CC verify the cluster supports it (Dedicated/Enterprise do). |
| Lag fine but throughput low | `fetch.min.bytes`/`fetch.max.wait.ms` too high → consumer waits | Tune fetch sizing; for low latency, `fetch.min.bytes=1`. |
| `InconsistentGroupProtocolException` | Mixed assignors / mixed `group.protocol` in the same group | Make every instance use the same assignor / protocol; roll carefully. |

## Related

- [Consumer Group Rebalancing](../concepts/consumer-group-rebalancing.md) — eager / cooperative / KIP-848 protocol generations
- [Consumer Lag Monitoring](../concepts/consumer-lag-monitoring.md) — offset vs time lag, CC Metrics API, alert layering
- [Exactly-Once Semantics](../concepts/exactly-once-semantics.md) — `read_committed`, isolation levels
- [FSI Producer Configuration](producer-config-fsi.md) — paired producer-side baseline
- [Low-Latency Kafka Clients on Azure](low-latency-kafka-azure.md) — fraud-tier consumer overlay
- [Dead Letter Queue Design](dead-letter-queue-design.md) — poison-pill routing
- [Top 20 Confluent Gotchas](../synthesis/confluent-gotchas-top-20.md) — #3, #4, #5 are consumer-related
