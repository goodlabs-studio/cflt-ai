---
title: The Confluent Best-Practice Quickstart — Producers to Networking
status: golden
mode: deep
generated: 2026-05-12
reconciled: 2026-05-12
supersedes: confluent-best-practices-quickstart-review-2026-05-12.md (review corrections applied)
audience: Confluent SE / Staff SA / platform engineering
sources: cflt-ai wiki, Confluent Canon (CLAUDE.md), fsi-dsp reference repo
---

# The Confluent Best-Practice Quickstart

**One document to sanity-check what you have, size what you're about to build, troubleshoot what's broken, and improve what works.**

This is opinionated. Where there's a "correct" answer in 2026 I give it; where it genuinely depends, I say so and give you the decision rule. It's organized **client → contract → cluster → integration → compute → analytics → platform → cross-cutting** because that's the order you actually touch things: a developer writes a producer before they think about networking, but the gotchas compound downward.

**How to use it**
- **Sanity check:** jump to §12 (Sanity-Check Checklists) — one pre-flight list per component.
- **Plan a new cluster / compute pool:** §11 (Capacity Planning).
- **Troubleshoot:** §10 (Triage Decision Tree) → then the component section's "Troubleshooting" subsection.
- **Improve:** read the "Optimizations" subsection for the component, then Appendix A (Top 20 Gotchas).

> **On validation:** claims below are cross-checked against the **Confluent Canon** (CLAUDE.md), the **cflt-ai wiki**, and the **fsi-dsp** reference assets. Version- and feature-recency-sensitive claims (Tableflow GA surface, CC cluster-type limits, Flink CC capabilities, KIP-848) are flagged ⚠️ and should be re-confirmed with `confluent-docs` MCP or `/wiki:validate` before you quote exact numbers to a customer. The *patterns* are stable; the *numbers* drift.

> **Reconciliation note (2026-05-12) — this is the golden version.** The corrections from `confluent-best-practices-quickstart-review-2026-05-12.md` have been folded in: (1) the canonical producer block now leads with `compression.type=lz4` (Canon default) with `zstd` as the storage-constrained override; (2) `CooperativeStickyAssignor` is described as a **required explicit setting**, not the out-of-the-box default — the OOTB default is `[RangeAssignor, CooperativeStickyAssignor]`, which runs `RangeAssignor` until every member is cooperative; (3) topic-naming examples now follow the FSI canon form `<domain>.<application>.<entity>.<event>` (ADR-007), with the versioned-topic variant called out as the sanctioned exception; (4) a sub-millisecond / market-data caveat box is added next to the latency-tier overlay; (5) the IBM MQ Source Connector is named explicitly as the canonical mainframe bridge; plus minor config notes (`confluent.tier.enable` per broker, `config.storage.topic` single-partition). The ⚠️ recency-sensitive numbers (CC cluster-type / Freight specs, per-CKU limits, Tableflow GA surface, KIP-848 client matrix, custom-connector-on-PrivateLink) still warrant a `confluent-docs` MCP / `/wiki:validate` pass before being quoted with exact figures — that pass was budget-bounded in this run.

---

## Part I — Producers

### What the producer owns (non-negotiable responsibilities)

1. **The data contract.** The schema (Avro/Protobuf), and just as importantly its *semantics*: what the fields mean, what's nullable, what a tombstone means, what units, what timezone. The schema registry stores the structure; the producer team owns the meaning. Treat the schema like a published API — because it is.
2. **The key.** Partition assignment = `hash(key) % partitions` (or null → sticky partitioner). The key is the **ordering contract** — all records for a key land on one partition and are ordered. Choosing the key is a design decision, not a default. For keyed entity streams, *always* set a key; relying on the sticky partitioner means no ordering guarantee.
3. **Serialization & wire format.** Avro/Protobuf in prod (Canon: JSON Schema is prototype/debug only). The serializer writes a magic byte + 4-byte schema ID; consumers need the *same* Schema Registry (or a Schema-Linked mirror).
4. **Delivery guarantee on the produce side.** `acks`, `enable.idempotence`, transactions. The producer decides whether a write is durable, idempotent, or transactional.
5. **Headers** — tracing/correlation IDs, schema metadata, routing hints, encryption metadata (CSFLE).
6. **Timestamps & tombstones** — `CreateTime` vs broker `LogAppendTime`; `null` value = delete marker on compacted topics. The producer must know which it's emitting.

### Canonical producer config (FSI baseline — matches fsi-dsp `reference/java-producer/FsiProducer.java`)

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
linger.ms=20                            # 20 ms — counterintuitively often *lowers* p99 under load
buffer.memory=33554432                  # 32 MB; raise if you see BufferExhausted

# ── Identity / observability ──
client.id=<app>-<instance>
metrics.recording.level=INFO

# ── Schema Registry ──
value.serializer=io.confluent.kafka.serializers.KafkaAvroSerializer
auto.register.schemas=false             # PROD: register in CI, not from the client
use.latest.version=true                 # or pin a version
```

**Transactional producer (only when you need atomic produce-or-produce-and-consume):**
```properties
transactional.id=<stable-per-instance-id>   # MUST be stable & unique per producer instance
# then in code: initTransactions() → beginTransaction() → send()... → sendOffsetsToTransaction() → commitTransaction()
# and consumers downstream MUST set isolation.level=read_committed
```

### Optimizations (the ones that matter, in order of impact)

| Knob | Effect | Default-ish recommendation |
|---|---|---|
| `linger.ms` + `batch.size` | The single biggest throughput lever. Larger batches → fewer requests → less broker CPU & better compression ratios. | `linger.ms=5–20`, `batch.size=32–128 KB`. `linger.ms=0` is **not** "fastest" under load — it floods the broker with tiny requests. |
| `compression.type` | `lz4` ≈ best CPU/ratio for throughput; `zstd` ≈ best ratio for storage cost; `gzip` only for cold-path. Compression happens per batch, so bigger batches compress better. | `lz4` general, `zstd` if storage $ matters (Canon). |
| `acks` + `enable.idempotence` | `acks=all` + idempotence = exactly-once *per partition* with no throughput penalty worth caring about on modern brokers. | Always on. |
| `max.in.flight.requests.per.connection` | With idempotence, 5 is safe and keeps the pipe full while preserving order. Without idempotence, >1 risks reordering on retry. | 5. |
| Partitioner | Sticky (default since 2.4 / "uniform sticky" KIP-794 in 3.3+) batches null-keyed records well. Custom partitioner only when a business rule (e.g. co-partition with another topic) requires it. | Default; set a key for keyed topics. |
| `delivery.timeout.ms` | The real "give up" bound. Make it ≥ `linger.ms + request.timeout.ms + retry budget`. | 120 s typical; lower for latency-tier apps that prefer fast-fail + DLQ. |
| `buffer.memory` / `max.block.ms` | Backpressure surface. `max.block.ms` is how long `send()` blocks when the buffer is full before throwing. | 32–64 MB buffer; `max.block.ms` 60 s, or short + DLQ for latency tiers. |

**Latency-tier overlay** (sub-100 ms, e.g. fraud): `linger.ms=0–5`, smaller `batch.size`, `delivery.timeout.ms` low, fast-fail to a DLQ rather than long retries, co-locate the producer in the cluster's region/AZ, and keep the connection warm (see fsi-dsp `*-low-latency-azure` reference + wiki `patterns/low-latency-kafka-azure.md`).

> **⚠️ Sub-millisecond (market-data) tier — read this.** The overlay above covers the **<100 ms** FSI tiers (risk, compliance). It does **not** cover the **sub-ms market-data tier**: `acks=all` + cross-AZ ISR waits *cannot* meet a sub-ms SLA — a single cross-AZ hop is ~1–2 ms before replication even starts. That tier needs an explicit, *documented* decision: single-AZ co-location (accept the AZ-failure blast radius), or a deliberate `acks` / `min.insync.replicas` durability trade-off, with producers and consumers pinned to the AZ of the partition leaders. This is a Canon FSI conversation — exactly-once / durability implications for anything that later feeds regulatory reporting (see Part X on async cross-region replication and `patterns/dr-cluster-linking.md`) — not just an ops tuning knob.

### Producer-side triage & troubleshooting

| Symptom / exception | What it usually means | First moves |
|---|---|---|
| `TimeoutException: Expiring N record(s)` / "producer lag" | `send()`s are queuing faster than they drain — undersized batches, slow/overloaded broker, network, or `delivery.timeout.ms` too tight. | Check JMX `record-queue-time-avg`, `request-latency-avg`, `buffer-available-bytes`; check broker `RequestQueueSize` / `RequestHandlerAvgIdlePercent`. Raise `batch.size`/`linger.ms`, then `buffer.memory`, then look at the broker. |
| `BufferExhaustedException` / `send()` blocking | Buffer full, broker can't keep up. | Raise `buffer.memory`; investigate broker; consider backpressure in the app. |
| `OutOfOrderSequenceException` | Idempotence sequence gap — almost always `acks≠all`, a broker that lost the producer's state, or a buggy custom retry wrapper. | Confirm `acks=all` and you're not catching+re-sending exceptions manually; check for broker restarts/segment deletion. |
| `ProducerFencedException` | A newer producer instance with the same `transactional.id` exists (zombie/duplicate). | Ensure `transactional.id` is unique per instance; you've been fenced — exit and let the new instance own it. |
| `UnknownProducerIdException` | The producer's PID metadata aged out of the partition (topic retention shorter than producer idle period, or aggressive segment deletion). Known sharp edge. | Don't set absurdly low topic retention; upgrade brokers; the producer will recover by re-initializing. |
| `NotEnoughReplicasException` / `NOT_ENOUGH_REPLICAS_AFTER_APPEND` | `min.insync.replicas` not met — a replica is down/lagging. | Check ISR (`kafka-topics --describe`), broker health, `replica.lag.time.max.ms`. On CC this is a Confluent-side incident. |
| `SerializationException` from the Avro serializer | Can't reach Schema Registry, auth wrong, compat mode rejected the schema, or subject naming mismatch. | Check SR endpoint + `basic.auth.user.info`, check `auto.register.schemas` policy, check the subject name strategy matches the consumer's. |
| Throughput plateaus well below link/broker capacity | Tiny batches (`linger.ms=0`), no compression, single producer instance, or hot partition (skewed key). | Raise `linger.ms`; enable `lz4`/`zstd`; add producer instances; check partition skew. |

**"Is this a producer problem?" rule of thumb:** if the *commit/append* path is slow or erroring → producer/broker. If records *arrive but consumers fall behind* → consumer/partitioning. If records *arrive but are wrong* → schema/contract.

---

## Part II — Consumers

### What the consumer owns

1. **Offset-commit strategy.** Manual commit **after** processing — never `enable.auto.commit=true` in a processing app (Canon). Auto-commit commits on `poll()` *before* you've done the work → at-most-once on crash. Commit synchronously on shutdown/rebalance, async in steady state.
2. **The consumer group ID** — one group per logical application (Canon), not per instance. Instances in a group share partitions.
3. **Processing idempotency / dedup.** Kafka gives you at-least-once in practice (even with EOS, the *external* side can see retries). The consumer owns dedup keys / upserts so reprocessing is safe.
4. **`max.poll.interval.ms` ≥ worst-case batch processing time.** If a `poll()` loop iteration takes longer than this, the broker assumes you're dead and triggers a rebalance — the classic "my consumer randomly stops" bug.
5. **Deserialization-error handling** — the poison-pill problem. Wrap with `ErrorHandlingDeserializer` (Spring) / try-catch + skip + DLQ. One bad record must not loop forever.
6. **Rebalance behaviour** — a `ConsumerRebalanceListener` that commits offsets on partition revocation, and (for stateful consumers) handles state handoff.
7. **`client.rack`** — set it so the consumer can fetch from a same-AZ follower (cuts cross-AZ egress cost; needs `broker.rack` + `replica.selector.class=org.apache.kafka.common.replica.RackAwareReplicaSelector` on the cluster — on CC it's already set up).

### Canonical consumer config (matches fsi-dsp `reference/java-consumer/FsiConsumer.java`)

```properties
group.id=<logical-app-name>
enable.auto.commit=false                # Canon: never true in a processing app
auto.offset.reset=earliest              # new deployments; document deliberately if you choose latest
isolation.level=read_committed          # if any upstream producer uses transactions
max.poll.records=500                    # cap work per poll → keeps you under max.poll.interval.ms
max.poll.interval.ms=300000             # 5 min worst-case processing window; raise if batches are heavy
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

⚠️ **KIP-848 (the new "consumer rebalance protocol")** is GA as of Kafka 4.0 (early 2025): broker-coordinated, incremental, no "stop-the-world." On CC and recent CP it's available; clients opt in via `group.protocol=consumer`. It largely obsoletes the eager/cooperative client-side dance. Verify your client version supports it before flipping.

### Dealing with lag

**Two kinds of lag — track both:**
- **Offset lag** — `log-end-offset − committed-offset`. Cheap, but a high number on a low-volume topic isn't urgent and a low number on a firehose might be.
- **Time lag** — how old is the oldest unprocessed record. This is what your SLA is actually written against.

**How to observe it** (wiki `concepts/consumer-lag-monitoring.md`):
- `kafka-consumer-groups --bootstrap-server ... --describe --group g` (point-in-time)
- Client JMX: `records-lag-max`, `records-lag` per partition
- Broker-side lag emitter (continuous, no client cooperation)
- **Confluent Cloud Metrics API**: `io.confluent.kafka.server/consumer_lag_offsets` — use this on CC, don't roll your own JMX scraper
- Burrow / Kafka Lag Exporter for Prometheus
- **Layered alerts:** absolute threshold **and** rate-of-change **and** projected time-to-drain. A flat-but-nonzero lag is fine; a *growing* lag is the alert.

**Why you're lagging — and the fix:**

| Cause | Tell | Fix |
|---|---|---|
| Under-parallelized | Lag spread evenly, all consumers 100% busy, #consumers == #partitions | Add partitions (then add consumers) — but see Gotcha #6 about the cost of repartitioning a keyed topic. |
| Slow processing (I/O-bound) | Consumers idle waiting on a DB/API, not CPU-bound | **Confluent Parallel Consumer** (key-level concurrency *beyond* partition count), or async processing with careful offset tracking. Don't just add instances — they'll sit idle past partition count. |
| Hot partition / key skew | One partition's lag dwarfs the others | Re-key, add a salt to the key, or split the entity. |
| Rebalance storm | Lag sawtooths; logs full of "Revoking/Assigning partitions" | See troubleshooting below — usually `max.poll.interval.ms`. |
| GC pauses | Lag spikes correlate with long GC | Right-size heap, use G1/ZGC, reduce per-record allocation. |
| Downstream backpressure | Consumer healthy but sink (DB/HTTP) throttling | Batch writes, add sink capacity, or buffer; don't let it manifest as Kafka lag you can't explain. |
| Expired committed offsets | Lag "resets" or jumps after idle period | `offsets.retention.minutes` (default 7 days) expired an idle group → `auto.offset.reset` kicked in. Commit periodically even when idle, or pin the group. |

### Consumer-group & parallelism strategy

- **Max useful consumers in a group = partition count.** Beyond that, instances sit idle. Provision instances ≤ partitions (plus 1–2 spare for fast failover only if using static membership).
- **Cooperative-sticky** assignor → only the moved partitions pause during rebalance, not the whole group. **Set `partition.assignment.strategy=CooperativeStickyAssignor` explicitly** — it is *not* the out-of-the-box default. Since Kafka 3.0 the default `partition.assignment.strategy` is `[RangeAssignor, CooperativeStickyAssignor]`, which runs `RangeAssignor` (stop-the-world) until every member supports cooperative; you only get the incremental behaviour once you pin the strategy. (Or move the whole group to KIP-848 `group.protocol=consumer` — note its server-side assignor is uniform/range, not "cooperative-sticky".)
- **Static membership** (`group.instance.id` + tuned `session.timeout.ms`) → a rolling restart/deploy doesn't trigger a rebalance at all. Big win for FSI apps that deploy frequently.
- **Parallel consumption patterns, in order of preference:**
  1. Match partitions to needed parallelism, one thread per partition. Simplest, deterministic.
  2. **Confluent Parallel Consumer** when processing is I/O-bound and you need more concurrency than partitions allow (it commits safely with key-level ordering).
  3. **Kafka Streams** when the work is stateful (joins, aggregations, windowing) — don't hand-roll that.
  4. **Flink** when it's heavy stateful streaming, multi-stream joins, or you want SQL. (See Part VI.)
  5. Async/threadpool inside one consumer — only if you *really* understand offset management; easy to get wrong.

### Consumer-side troubleshooting

| Symptom | Likely cause | First moves |
|---|---|---|
| Consumer "randomly stops," group constantly rebalancing | A poll-loop iteration exceeds `max.poll.interval.ms` → broker ejects the member → rebalance → repeat | Lower `max.poll.records`; speed up processing; `pause()`/`resume()` during long work; or raise `max.poll.interval.ms` (with eyes open). |
| `CommitFailedException` | A rebalance happened while you were processing; your assignment is stale | Commit more frequently; shorten work units; with cooperative-sticky this is rarer; use a rebalance listener. |
| Same record processed forever / consumer stuck on one offset | Poison pill — deserialization throws every time, offset never advances | `ErrorHandlingDeserializer` / catch + skip + route to DLQ (wiki `patterns/dead-letter-queue-design.md`). |
| Consumer reads from the wrong place after a deploy | No committed offset (new group) or offsets expired → `auto.offset.reset` | Expected for new groups; for old groups, see "expired committed offsets" above. |
| Fetch-from-follower not reducing cross-AZ cost | Missing `client.rack`, or cluster missing `broker.rack` / `RackAwareReplicaSelector` | Set all three; on CC verify the cluster supports it (Dedicated/Enterprise do). |
| Lag fine but throughput low | `fetch.min.bytes` too high + `fetch.max.wait.ms` too high → consumer waits; or `max.partition.fetch.bytes` too small | Tune fetch sizing; for low latency, `fetch.min.bytes=1`. |
| `InconsistentGroupProtocolException` | Mixed assignors / mixed `group.protocol` in the same group | Make every instance use the same assignor / protocol; roll carefully. |

---

## Part III — Topics & Clusters: what to set, and where (Confluent Cloud vs Confluent Platform)

### The mental model

On **Confluent Cloud** you own *topic-level* config and *cluster sizing*; Confluent owns broker internals, RF, durability invariants, and the OS. On **Confluent Platform** you own *everything down to the kernel*. The hard part of CP is the part CC does for you for free; the hard part of CC is that you *can't* override the things you used to tune.

### Topic config (applies to both CC and CP)

```properties
# Set explicitly on every governed topic (fsi-dsp module/topic produces these from SLA tier):
cleanup.policy=delete            # or compact, or "compact,delete" for time-bounded changelogs
retention.ms=...                 # event-time driven (Canon); per SLA tier
retention.bytes=...              # belt-and-suspenders cap
max.message.bytes=...            # ≤ cluster max (1 MB default; raising it has broker-memory cost)
min.insync.replicas=2            # CC: fixed at 2, not settable. CP: set it.
# compaction tuning (compacted topics only):
min.cleanable.dirty.ratio=0.5
segment.ms=...                   # how fast tombstones become eligible
delete.retention.ms=...          # tombstone visibility window for consumers
message.timestamp.type=CreateTime  # or LogAppendTime if you don't trust producers
```

**Partition count.** Canon's starting heuristic is `6 × peak MB/s` — but that's a *prior*, not an answer. The real formula:

```
partitions = max(
   ceil(peak_throughput_MBps / per_partition_throughput_MBps),   # ~10–25 MB/s/partition is a sane planning number
   ceil(required_consumer_parallelism),                          # you can't have more consumers than partitions
   ceil(peak_produce_rate / per_partition_produce_capacity)
) + headroom
```
Then sanity-check against the costs: more partitions = slower rebalances, slower broker recovery, slower controller failover, more produce-request overhead, and (CP) per-broker replication limits (keep it to low-thousands of partitions per broker for replication health — KRaft raises *cluster-wide* limits dramatically but per-broker replication work is still bounded). **You can add partitions but never remove them**, and adding them changes `hash(key) % n` so it breaks per-key ordering for keyed topics. Don't "round up to be safe."

### Confluent Cloud cluster types — pick one ⚠️ (limits change; confirm via docs/SA before quoting)

| Type | Use it when | Networking | Notable limits / features |
|---|---|---|---|
| **Basic** | Dev/test, demos | Public only | No SLA, no Cluster Linking *source*, smallest limits, cheapest. Never prod. |
| **Standard** | Smaller prod workloads | Public (limited private) | 99.99% SLA, RBAC, Cluster Linking source, no fixed CKU — but lower ceilings than Dedicated/Enterprise. |
| **Enterprise** | Prod, want elastic + private + zero capacity planning | Private only (PrivateLink / PSC) | Serverless/auto-scaling, 99.99% SLA, log-based billing, multi-AZ, no CKUs to size. Strong default for new private prod workloads. |
| **Dedicated** | Need BYOK/self-managed keys, highest limits, strict single-tenant isolation, VPC peering / Transit Gateway, or Cluster Linking at scale | Public, PrivateLink/PSC, VPC peering, AWS Transit Gateway | Single-tenant, **CKU-sized** (you plan capacity), BYOK, all networking modes. The "I need control on CC" option. |
| **Freight** ⚠️ | High-throughput firehose (logs, telemetry, clickstream) where seconds of latency is fine | Private | Object-storage-backed writes → ~10× cheaper $/GB, but **latency is seconds, not milliseconds**. Wrong choice for transactional / low-latency. |

**Decision rule:** Standard if it fits and you don't need private networking → Enterprise for most new private prod → Dedicated if you need BYOK / peering / Transit Gateway / Cluster-Linking-at-scale / single-tenant → Freight only for latency-tolerant firehoses. RF is always 3 and `min.insync.replicas` always 2 on CC; `unclean.leader.election` is always false. Don't write runbooks that assume otherwise.

### Confluent Platform — the broker/cluster knobs you now own

```properties
# Durability invariants (the things CC sets for you):
default.replication.factor=3
min.insync.replicas=2
unclean.leader.election.enable=false        # NEVER true in prod
auto.create.topics.enable=false             # explicit topic creation only (Canon)
auto.leader.rebalance.enable=true

# KRaft (ZooKeeper is removed as of Kafka 4.0 / CP 8.0):
# - 3 (or 5) dedicated controller nodes, NOT co-located with brokers in prod
# - process.roles, controller.quorum.voters / controller.quorum.bootstrap.servers
# - watch metadata log size, controller failover time

# Throughput / IO:
num.network.threads=...                     # ~ #cores/2 start
num.io.threads=...                          # ~ #disks * 2..8
num.replica.fetchers=4..8                   # raise for many partitions / high replication load
replica.lag.time.max.ms=30000
socket.send.buffer.bytes / socket.receive.buffer.bytes  # raise on high-BDP links
log.segment.bytes / log.retention.* / log.roll.ms

# Storage / scale-out:
confluent.tier.feature=true                 # Tiered Storage: cluster feature flag …
confluent.tier.enable=true                  #   … plus per-broker enable (required alongside the feature flag)
confluent.tier.backend=S3                   #   … plus backend + bucket/region/credentials (S3 | GCS | Azure)
                                            # → smaller local disks, faster broker recovery/rebalance
confluent.balancer.enable=true              # Self-Balancing Clusters → auto partition rebalance on add/remove
broker.rack=<az>                            # rack awareness → replicas span AZs; enables fetch-from-follower

# JVM & OS (don't skip these):
# heap ~6 GB even on huge nodes (rely on page cache); G1 or ZGC
# vm.swappiness=1, vm.max_map_count high, file descriptors high, XFS, mount noatime
```

CFK exposes most of this declaratively (see Part VIII). On bare metal/VMs you own the lot — see fsi-dsp `scenarios/cfk-openshift/values/kafka.yaml` and the LinuxONE tuning patterns in the wiki for worked examples.

---

## Part IV — Schema Registry

### What Schema Registry / the schema team owns

- **Subject naming strategy.** `TopicNameStrategy` by default (Canon). `RecordNameStrategy` / `TopicRecordNameStrategy` only for genuine multi-event-type topics or event-union patterns — and then it's a deliberate, documented choice because it changes how producers and consumers resolve schemas.
- **Compatibility mode** per subject (Canon: `BACKWARD` default, escalate to `FULL` for shared consumer contracts):
  - `BACKWARD` — new schema can read old data → **consumers upgrade first**. Adding a field *with a default* is OK; adding a required field or removing a field is not.
  - `FORWARD` — old schema can read new data → **producers upgrade first**.
  - `FULL` — both. The safe default for contracts with many independent consumers.
  - `*_TRANSITIVE` — checks against *all* prior versions, not just the last. Use for long-lived, widely-shared schemas.
- **Schema IDs in the wire format** — magic byte + 4-byte ID. **IDs are not portable across environments** (dev ID 100 ≠ prod ID 100). Use **Schema Linking** for CC↔CC / CC↔CP, or export/import — never assume IDs match.
- **References** — compose schemas instead of shipping one 4000-line Avro file. Versioned, reusable, governable.
- **Data Contracts** (Confluent's feature) — schema + **rules** (validation, domain constraints) + **migration rules** (transform on read across breaking versions) + metadata/tags. This is where CSFLE tags live too.
- **CSFLE** (client-side field-level encryption) — tag PII fields in the schema; the client encrypts those fields against a KMS *before* the record hits the broker. Even Confluent can't read them. The FSI PII answer. (fsi-dsp `docs/csfle-guide.md`.)

### Best practices (opinionated)

- **Avro by default** (Canon ADR-001 / fsi-dsp `docs/adr/001-avro-over-protobuf.md`) — best evolution story, compact, native unions, first-class in Flink/Connect/ksqlDB. **Protobuf** when you're polyglot / gRPC-native. **JSON Schema** prototype/debug only.
- **`auto.register.schemas=false` in prod.** Register schemas in **CI** (fail the build on incompatibility — `mvn schema-registry:test-compatibility`); clients use `use.latest.version=true` or a pinned version. Auto-register from clients = governance bypass + a race where two instances register slightly different "latest" schemas.
- **Set compatibility per subject**, not just globally, when you have mixed requirements. Consider `latest.compatibility.strict=true`.
- **Pre-register before deploy** — never let the first message in production be the thing that registers the schema.
- **Stream Governance package (CC):** Essentials vs **Advanced** — Advanced adds Stream Lineage, Stream Catalog (business metadata/tags), more schemas, Data Contracts, Schema Linking. For FSI governance, Advanced is the baseline.

### CC vs CP

- **CC:** managed SR per environment; governance via Stream Governance packages; Schema Linking for DR/migration.
- **CP:** you run the SR cluster — 3 nodes behind a load balancer, `_schemas` topic with **RF 3 and compaction on** (corruption risk if compaction gets disabled), leader election among nodes, mTLS, RBAC via MDS. fsi-dsp `scenarios/cfk-openshift/values/schemaregistry.yaml`.

### Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Schema being registered is incompatible with an earlier schema` | Breaking change vs the compat mode (added required field under BACKWARD, removed field under FORWARD, etc.) | Diff the schemas; add defaults; or — for a genuinely breaking change — stand up a new topic and migrate consumers. Keep the canon naming form `<domain>.<application>.<entity>.<event>`; a `_v2`-style suffix on the `<entity>` segment is the sanctioned versioned-topic exception (fsi-dsp ADR-007 / wiki `patterns/topic-naming.md`, `concepts/schema-evolution-strategies.md`). |
| `Subject not found` | Subject naming strategy mismatch between producer/consumer, or schema simply not registered | Confirm both sides use the same strategy; register in CI. |
| Schema IDs differ across envs | They always do — IDs are per-registry | Schema Linking or export/import; never hardcode IDs. |
| Serializer can't reach SR / 401 / 403 | Network, `basic.auth.credentials.source` / `basic.auth.user.info`, RBAC on the subject | Check endpoint + creds + role bindings on the subject resource. |
| `_schemas` topic growing unbounded / weird SR behaviour | Compaction got disabled on `_schemas` | Restore `cleanup.policy=compact` on `_schemas` immediately; this topic is SR's database. |

---

## Part V — Kafka Connect

### Three deployment models — pick deliberately

| Model | You provide | Confluent provides | Use when |
|---|---|---|---|
| **Fully-managed connector on CC** | Connector config only | Connector code, workers, autoscaling, SLA, monitoring | The default for FSI (Canon/memory: vendor-backed, consolidation — one contract covers 200+ source/sink connectors). Use whenever a fully-managed connector exists for your source/sink. |
| **Custom Connector on CC** ("bring your own plugin") | The connector plugin (JAR/zip) | The runtime infrastructure to run it | Confluent doesn't offer a managed connector for your system, but you still want zero-ops runtime. ⚠️ Limitations: plugin size caps, sensitive-config handling, not available on every networking mode/region (historically not on PrivateLink clusters — verify current). |
| **Self-managed Connect** (you run Connect Distributed against CC or CP Kafka) | Workers (VMs/K8s), plugins, ops | Nothing (it's yours) | You need a connector/SMT Confluent doesn't run, full config control, in-your-network egress, or exactly-once source semantics with full control. fsi-dsp `reference/connect-configs/` + `scenarios/cfk-openshift/values/connect.yaml`. ADR-004 (`docs/adr/004-onprem-connect.md`) documents the on-prem Connect decision. |

### What you own in self-managed Connect

```properties
# Worker identity & internal topics — these MUST be compacted, RF 3:
group.id=fsi-connect-cluster
offset.storage.topic=connect-offsets        offset.storage.replication.factor=3   offset.storage.partitions=25
config.storage.topic=connect-configs        config.storage.replication.factor=3   # config.storage.topic MUST have exactly 1 partition
status.storage.topic=connect-status         status.storage.replication.factor=3   status.storage.partitions=5
# (If cleanup.policy on these ever becomes 'delete', connectors silently lose state — see Gotcha #11.)

# Converters (Avro + Schema Registry):
key.converter=org.apache.kafka.connect.storage.StringConverter
value.converter=io.confluent.connect.avro.AvroConverter
value.converter.schema.registry.url=...
value.converter.basic.auth.credentials.source=USER_INFO

# Error handling / DLQ (set on the connector):
errors.tolerance=all
errors.deadletterqueue.topic.name=<conn>.dlq
errors.deadletterqueue.context.headers.enable=true
errors.log.enable=true
errors.retry.timeout=...

# Exactly-once source (KIP-618):
exactly.once.source.support=enabled         # worker-level; then per-connector transaction.boundary

plugin.path=/opt/kafka-connect/plugins      # classpath isolation lives here
# Rebalance protocol: connect.protocol=sessioned (incremental cooperative, default since 2.3+)
```

Plus: secrets via `ConfigProvider` (never plaintext in configs), per-connector `consumer.override.*` / `producer.override.*`, monitoring via `/connectors/{n}/status` + JMX (`connect-worker-metrics`, `source-task-metrics`, `sink-task-metrics`).

### Performance tuning

- **`tasks.max`** = `min(source/topic partitions, target parallelism, worker cores available)`. More than the partition count → idle tasks. Sink connector parallelism is **hard-capped by topic partitions** regardless of `tasks.max`.
- **Sink batching** — `consumer.override.max.poll.records`, `consumer.override.fetch.max.bytes`, `batch.size` (JDBC sink), `flush.size` (object-store sinks).
- **Object-store sinks (S3/GCS/ADLS)** — the "small files problem": low `flush.size` / short `rotate.interval.ms` → millions of tiny objects → slow downstream queries + huge API bills. Target ~128 MB–1 GB files. Set `partitioner.class` (e.g. `TimeBasedPartitioner` + `path.format` + `partition.duration.ms` + `timezone`) for query-friendly layout. **Or skip the connector entirely and use Tableflow** (Part VII) — it solves compaction/small-files/catalog for you.
- **JDBC source** — `mode=timestamp+incrementing` (not `timestamp` alone — clock skew loses rows), `poll.interval.ms`, `batch.max.rows`, `numeric.mapping=best_fit`, `validate.non.null=false` for views.
- **CDC (Debezium)** — `snapshot.mode`, `max.batch.size` / `max.queue.size`, `heartbeat.interval.ms` (critical on Postgres — advances the replication slot LSN so WAL doesn't grow forever), `publication.autocreate.mode`, `signal.data.collection` for incremental snapshots, `slot.name` management.
- **SMTs run inline on the worker thread.** Heavy SMT chains throttle throughput. Do real transformation in **Flink**, not SMTs — SMTs are for light reshaping (rename, mask, route, add header), not joins/aggregations.

### Troubleshooting

| Symptom | Cause | First moves |
|---|---|---|
| Connector `RUNNING` but a task `FAILED` | Task-level error not surfaced at connector level | `GET /connectors/{n}/status` → read the task trace; that's the real error. |
| Connector "forgets" / replays everything on restart | `connect-offsets` not compacted, or wrong worker `group.id`, or you pointed it at a different Kafka | Verify internal topics are compacted RF3; verify `group.id`/cluster. |
| Rebalance loops across workers | Worker `group.id` collisions, `session.timeout.ms` too low, slow plugin init | Unique `group.id` per Connect cluster; raise `session.timeout.ms`; check plugin load time. |
| Sink lag growing | Under-tasked, slow target, large records, target throttling | Raise `tasks.max` up to partition count; batch writes; check target. |
| Source connector duplicates downstream | At-least-once by default | Enable exactly-once source (KIP-618) *or* make the consumer idempotent (preferred — outbox/upsert). |
| `ClassNotFoundException` / connector won't load | `plugin.path` wrong, missing JDBC driver, classpath leakage | Fix `plugin.path`; bundle the driver in the plugin dir; don't dump jars on the worker classpath. |
| Garbage in the topic / sink | Converter mismatch (produced Avro, configured `JsonConverter` or vice versa) | Align converters with what's actually on the topic. |
| DLQ filling up | Schema drift, target constraint violations, poison records | Inspect DLQ headers (`errors.deadletterqueue.context.headers.enable=true`) — they carry the original topic/partition/offset + exception. |
| Postgres WAL/disk filling next to a Debezium connector | No heartbeat → replication slot LSN never advances | Set `heartbeat.interval.ms`; monitor `pg_replication_slots`. |

---

## Part VI — Flink

### Three ways to run it

| Model | What it is | You own |
|---|---|---|
| **Confluent Cloud for Apache Flink** (fully managed) | Serverless Flink SQL (+ Table API). Kafka topics auto-appear as tables (catalog = environment, database = cluster). Compute pools sized in **CFUs**. Checkpointing fully managed. | Statement SQL, statement properties, `max_cfu` per pool, state TTL. *Not* checkpoint intervals, state backends, parallelism internals. |
| **Confluent Manager for Apache Flink (CMF)** on CFK/K8s | Confluent-supported Flink Operator + management plane for CP. Application & session deployments. | Everything: checkpointing (`execution.checkpointing.interval`), state backend (RocksDB + incremental + S3/filesystem for checkpoints), parallelism, `taskmanager.numberOfTaskSlots`, memory (`taskmanager.memory.process.size` + managed-memory fraction), restart strategy, K8s HA, savepoints/upgrades. fsi-dsp `scenarios/cfk-openshift/flink/`. |
| **Self-managed open-source Flink** against CC/CP Kafka | DIY. Supported by the community, not Confluent. | All of the above, plus you're on your own for support. |

### Flink best practices (apply on every model)

- **Watermarks:** `BOUNDED_OUT_OF_ORDERNESS` with a *bounded* delay — never unbounded (Canon). And set **`table.exec.source.idle-timeout`** (or per-source idleness) — otherwise a quiet partition stalls the global watermark and **windows never fire** ("my aggregation produces nothing" — almost always this).
- **State TTL — the big one.** Unbounded **regular joins** and **non-windowed aggregations** keep state **forever** unless you set `sql.state-ttl` (CC) / `table.exec.state.ttl` (CP). This is the #1 surprise CFU/cost blow-up and OOM cause. Set a TTL on *every* non-windowed stateful operator. Prefer **interval joins**, **temporal (versioned-table) joins**, and **lookup joins** — they have bounded state by construction.
- **Windows:** tumbling < sliding/hop < session in resource cost (Canon: prefer tumbling). Use the modern **window TVFs** (`TUMBLE`, `HOP`, `CUMULATE`) over legacy grouped-window syntax. `CUMULATE` for early-fire dashboards.
- **Changelog output:** `upsert-kafka` for CDC-style / aggregated output keyed by PK (Canon); plain `kafka` connector for append-only streams.
- **Determinism:** `scan.startup.mode=earliest-offset` for reproducible replay (Canon); `latest-offset` for ephemeral/exploratory.
- **Schema:** Flink reads Avro/Protobuf/JSON-SR from Schema Registry automatically on CC; mind key format vs value format.
- **Table API over DataStream API** for new work unless you need low-level control (Canon). On CC, SQL + Table API are the surface (no DataStream on CC ⚠️).
- **CP serialization:** POJO/Avro/Row types — **never let it fall back to Kryo** (silent throughput killer; you'll see it in the logs as "must be processed as GenericType").
- **Don't** build huge fan-out regular joins on non-key columns — that's the state-explosion footgun.

### Flink troubleshooting

| Symptom | Cause | First moves |
|---|---|---|
| Backpressure (high `busyTimeMsPerSecond` / `backPressuredTimeMsPerSecond`) | A downstream operator is the bottleneck — skewed keys, slow sink, under-parallelized, RocksDB disk I/O | Find the first backpressured operator from the *sink* upward; that's the culprit. Rebalance keys / add parallelism / speed the sink. |
| Checkpoints timing out / failing (CP) — or statement `DEGRADED` (CC) | Backpressure (barriers can't flow), huge state, slow checkpoint storage, RocksDB pressure | CP: enable **unaligned checkpoints**, tune RocksDB, faster checkpoint store, raise timeout, reduce state (TTL!). CC: usually a schema/permission issue on a source/sink topic, or pool out of CFUs. |
| Windows never produce output | Watermark not advancing — idle partition with no idleness timeout, or watermark delay too tight, or event-time skew | Set `table.exec.source.idle-timeout`; check the source's event-time field; loosen the bound. |
| State growth / OOM / runaway CFUs | Missing TTL on a regular join or non-windowed agg; `COUNT(DISTINCT ...)` over unbounded high-cardinality key; `GROUP BY` on a near-unique key | Add `state-ttl`; switch to interval/temporal/lookup join; reconsider the key. |
| Statement stuck `PENDING` (CC) | Compute pool out of CFU capacity | Raise `max_cfu` (remember: **can't be decreased** — size to realistic peak, not paranoid peak); or split work across pools. |
| Job won't restore from savepoint after a code change (CP) | Operator UID / job graph changed → state can't be mapped | Assign stable operator UIDs; on intentional changes, restore with `--allowNonRestoredState` or start fresh. |
| "GenericType / Kryo" in CP logs, throughput tanks | Type the framework couldn't analyze → Kryo serialization | Use Avro/Row/POJO with proper getters/setters; register types; never ship Kryo in prod. |

---

## Part VII — Tableflow

**What it is ⚠️:** a Confluent Cloud feature that materializes Kafka topics as **open table formats — Apache Iceberg and Delta Lake** — in object storage, with automatic schema mapping from Schema Registry, automatic table maintenance (compaction, snapshot expiry), and catalog integration (AWS Glue, Snowflake Open Catalog/Polaris, Unity Catalog, REST catalog). It replaces the hand-rolled "Kafka → S3 sink connector → compaction job → small-file cleanup → catalog sync" pipeline. Iceberg support GA'd in 2025; Delta Lake added. (cflt-ai wiki `patterns/fsi-l1-reference-architecture.md` uses it as the operational→analytical bridge: Cluster Linking → CC Tableflow → Databricks.)

**Best practices (opinionated):**
- **Enable it on topics that have a registered schema** (SR-managed) — schemaless/raw-bytes topics are limited.
- **Choose Iceberg** unless you're committed to Databricks/Delta specifically — broader engine support (Snowflake, Athena, Trino, Spark, DuckDB, Flink…).
- **Point it at your own bucket (BYOB)** for data residency and cost control, vs Confluent-managed storage — important for FSI.
- **Mind the backfill window:** Tableflow reads the *topic*, so the topic's retention governs how much history materializes. For full history, use infinite retention on the topic, or seed the table from a compacted "current state" topic.
- **It's near-real-time (minutes), not sub-second.** It's an analytical sink, not an operational read path. Kafka stays the system of record.
- **Partition the Iceberg table** on a sensible low-cardinality column (date, region) for query pruning.
- **Costs** = Tableflow throughput + storage + object-store API calls + downstream catalog/query engine. Cheaper and far less ops than DIY, but not free.

**Triage:**
- Table not updating → topic has no new data; or schema not registered; or topic was deleted/recreated; or the IAM role Tableflow uses lost write access to the bucket/catalog.
- Schema-evolution surprise → an incompatible change shows up as a new column or a failed mapping; keep the topic's SR compatibility tight.
- Glue/Unity catalog errors → the Tableflow IAM role needs both bucket-write and catalog-write permissions; check the trust policy.
- "Where's my history?" → only what's still within topic retention materializes; this is expected.
- Reader incompatibility → confirm your query engine supports the chosen format/version (Iceberg v2 vs Delta reader features vary).

---

## Part VIII — Kubernetes (Confluent for Kubernetes / CFK)

**CFK** is the supported operator for running Confluent Platform on K8s/OpenShift: CRDs for `Kafka`, `KRaftController` (ZooKeeper legacy is gone in CP 8.0 / Kafka 4.0), `Connect`, `SchemaRegistry`, `KsqlDB`, `ConfluentRestProxy`, `ControlCenter`, plus declarative `Topic` / `Schema` / `ClusterLink` / `ConfluentRolebinding` CRs (GitOps-friendly). Worked examples: fsi-dsp `scenarios/cfk-openshift/` and `scenarios/cfk-openshift-linuxone/`; wiki `patterns/aks-kafka-tuning.md` for the Azure/AKS variant.

### Best practices

- **Storage:** dedicated SSD `StorageClass` (Premium SSD v2 / io2 / local NVMe per workload — see `aks-kafka-tuning.md`), `volumeClaimTemplate` per broker, reclaim policy **Retain**, never `emptyDir` for brokers. Note `volumeClaimTemplate` is effectively immutable — use an expandable StorageClass from day one.
- **Spread & rack awareness:** `podAntiAffinity` **required** (not preferred), `oneReplicaPerNode: true`, map the topology-zone label to `rack.awareness` so replicas span AZs (and fetch-from-follower works).
- **Resources / QoS:** requests == limits for brokers (Guaranteed QoS); heap ~6 GB even on huge nodes (leave RAM for page cache); **don't put a tight CPU limit on brokers** — CPU throttling on a broker is a latency disaster.
- **Disruption:** `PodDisruptionBudget maxUnavailable=1`; CFK rolls one broker at a time and **will not proceed while partitions are under-replicated** — that's a feature, not a hang (see Gotcha #17).
- **KRaft:** 3 (or 5) **dedicated** controller pods, not co-located with brokers in prod.
- **Networking:** per-broker external access via LoadBalancer / NodePort / OpenShift Route with port-based routing or SNI; **advertised listeners must be resolvable and routable by clients**; headless service for in-cluster-only.
- **Security:** `autoGeneratedCerts` for dev only; cert-manager / your PKI + mTLS between components for prod; RBAC via MDS; secrets via `CredentialStoreConfig` / external-secrets / Vault CSI — never inline.
- **Tiered Storage:** configure an object store for offload — shrinks local disk, makes broker recovery and rebalances dramatically faster.
- **Don't co-locate** Connect / ksqlDB / Flink TaskManagers on the broker nodes in prod — resource contention will bite you under load.
- **Mainframe / z/OS bridge:** the canon-named canonical pattern is the **IBM MQ Source Connector → Kafka** (Canon FSI overlay) — run it as a fully-managed CC connector where available, else self-managed Connect (Part V); pair with **IBM LinuxONE** for z/OS offload compute (`scenarios/cfk-openshift-linuxone/`, fsi-dsp ADR-009; wiki `concepts/linuxone-kafka-integration.md`, `patterns/linuxone-kafka-tuning.md`).
- **Upgrades:** check the CFK ↔ CP version compatibility matrix every time; keep all CRs in Git.

### Troubleshooting

| Symptom | Cause | First moves |
|---|---|---|
| Broker pod `CrashLoopBackOff` | PVC won't bind; JVM heap > container limit → `OOMKilled` (exit 137); advertised-listener misconfig; KRaft quorum can't form | `kubectl describe pod` + `kubectl logs --previous`; check heap vs limit; check controller quorum config; check PVC/StorageClass. |
| Rolling update stuck | A broker is under-replicated and CFK (correctly) won't take down the next one | Find the lagging broker / bad disk — `kafka-topics --describe --under-replicated-partitions`; fix that, the roll continues. |
| Cluster ID / `meta.properties` mismatch after PVC reuse | Re-attached an old data volume to a new logical cluster | Don't reuse PVCs across cluster identities; restore from backup or wipe deliberately. |
| All RBAC auth suddenly fails | MDS (metadata service) is down | Check the MDS pods / its backing topics; everything authz-related depends on it. |
| Clients connect to bootstrap then fail | Advertised broker addresses aren't resolvable/routable from where clients run | Fix advertised listeners / DNS / Route config; test from a client pod *and* from outside. |
| Can't resize a broker disk | `volumeClaimTemplate` is immutable | Need an expandable StorageClass; otherwise it's a rebuild-broker operation. |
| Certs expired, components can't talk | No rotation automation | cert-manager with renewal; alert on cert expiry; have the rotation runbook ready (fsi-dsp `docs/rotation-runbook.md`). |

---

## Part IX — Security

### AuthN — how callers prove who they are

| Mechanism | Where | Verdict |
|---|---|---|
| **mTLS** | CP, CFK; CC via certain configs | **Preferred in FSI** (Canon: never username/password in FSI). Mind CRL/OCSP and cert rotation. |
| **SASL/OAUTHBEARER (OIDC)** | CC (human + workload identity federation), CP | The modern default for CC; ADR-006 (`docs/adr/006-oauth-vs-api-keys.md`) picks OAuth over long-lived API keys. |
| **API keys** | CC | Fine for apps if scoped to a per-application **service account** and **rotated** (fsi-dsp `docs/rotation-runbook.md`). Never per-team, never in git. |
| **SASL/SCRAM** | CP | Acceptable *over TLS* — salted/iterated. Strictly better than PLAIN. |
| **SASL/PLAIN** | — | Only over TLS, and even then avoid in FSI. PLAIN over plaintext = credentials in cleartext on the wire. |
| **SASL/GSSAPI (Kerberos)** | CP | For integrating with existing AD/Kerberos estates. |

### AuthZ

- **RBAC** — CC native; CP via **MDS**. Bind roles at the **narrowest resource scope** (topic / group / subject / connector / cluster), use **prefix bindings** for topic families (`{domain}.{app}.*`), one **service account per application** (Canon — not per team). Deny is implicit; there's no "deny" rule, so don't grant broadly and try to claw back.
- **ACLs** — the lower-level mechanism (CP, and CC for fine-grained control). Never `User:ANONYMOUS` allowed, never wildcard `*` topic ACLs, minimize `super.users` (ideally none in prod).

### Encryption

- **In transit:** TLS 1.2+/1.3 **everywhere**, including inter-broker and inter-component. No plaintext listeners in prod.
- **At rest:** CC encrypts by default; **BYOK / self-managed keys** on Dedicated and Enterprise. CP: disk-level encryption is your responsibility (LUKS / cloud disk encryption / on LinuxONE, CEX/pervasive encryption — fsi-dsp `docs/linuxone-cex-guide.md`).
- **CSFLE (client-side field-level encryption):** tag PII fields in the schema; client encrypts against a KMS (AWS KMS / Azure Key Vault / GCP KMS / HashiCorp Vault) before the record leaves the producer. The broker — and Confluent — only ever see ciphertext for those fields. **This is the FSI PII answer.** (fsi-dsp `docs/csfle-guide.md`.)

### Audit & secrets

- **Audit logs on every prod cluster** (Canon). On CC: the audit-log topic → SIEM/observability via the HTTP Sink Connector pipeline (wiki `patterns/audit-log-siem-integration.md` — auth failures, RBAC denials, config changes, access-transparency events → Splunk/Dynatrace). On CP: ship audit logs to a dedicated cluster.
- **Secrets:** never plaintext in connector configs / `connect-distributed.properties` — use `ConfigProvider` (`FileConfigProvider`, `DirectoryConfigProvider`, Vault provider) or the platform secret store; on CC use connector secret management. Rotate everything; alert on age.
- **Compliance mapping:** wiki `concepts/fsi-compliance.md` + fsi-dsp `docs/compliance-guide.md` map the CI/CD audit trail to OCC/FFIEC, PRA, MAS, APRA, OSFI.

### Common security mistakes (the ones that show up in audits)

PLAIN over plaintext · API keys in git · no rotation · RBAC bound at cluster scope instead of resource scope · `super.users` in prod · `auto.register.schemas=true` bypassing governance · wildcard ACLs / `User:ANONYMOUS` · inter-broker plaintext · mTLS without CRL/OCSP · public endpoints on an FSI cluster · audit logging off or not forwarded.

---

## Part X — Networking

### Confluent Cloud connectivity (by cluster type) ⚠️

| Option | Direction | CIDR overlap OK? | Cluster types | Notes |
|---|---|---|---|---|
| **Public internet** | n/a | n/a | Basic, Standard, Dedicated | TLS + IP allowlists. Fine for dev; generally not FSI prod. |
| **AWS PrivateLink / Azure Private Link / GCP Private Service Connect** | one-way (you → CC) | **Yes** (no overlap concerns) | Enterprise, Dedicated | The recommended private option. Per-AZ endpoints; **zonal DNS** records (`*.<region>.aws.private.confluent.cloud` etc.) — clients must resolve the zonal endpoints. |
| **VPC / VNet peering** | two-way | **No** (must be non-overlapping) | Dedicated only | More setup; route tables; only when you genuinely need CC → you. |
| **AWS Transit Gateway** | hub | non-overlapping | Dedicated only | Many-VPC hub-and-spoke. |

- **Enterprise clusters: PrivateLink/PSC only** — no peering.
- **Fully-managed connectors on a private cluster** need a way to reach *your* source — Confluent provides egress mechanisms (static egress IPs / PrivateLink to your endpoint depending on connector); plan this, it's a common surprise. ⚠️ Custom Connectors historically aren't available on PrivateLink clusters — verify current.
- **Cluster Linking** over private networking: both link endpoints must be mutually reachable; CC↔CC is straightforward; **CC↔CP** needs the CP side reachable from CC (via your DC connectivity or a public endpoint) — design the link path explicitly.

### Confluent Platform networking

- **`advertised.listeners` is the #1 footgun.** It must be the address clients *actually use* to reach each broker — not the bind address. Multiple listeners (internal / external / replication) on different ports; **SANs in the broker certs must match every advertised name**; LB/Route SNI for external access.
- Firewall the right ports: 9092 (broker), 9093 (KRaft controller), 8081 (SR), 8083 (Connect), 8090 (MDS), 9021 (Control Center).
- High-bandwidth-delay links: raise `socket.send.buffer.bytes` / `socket.receive.buffer.bytes`; jumbo frames in the DC where supported. On LinuxONE: HiperSockets MTU, SMC-D/SMC-R cross-frame transport (wiki `patterns/linuxone-kafka-tuning.md`).
- DNS: bootstrap resolves to a load balancer; brokers then advertise their own hostnames — **clients must resolve those too**. Split-horizon DNS or a service-discovery layer (fsi-dsp uses Consul — ADR-003, `docs/adr/003-consul-service-discovery.md`) handles the DR endpoint flip cleanly.

### Latency & cost

- **Cross-AZ ≈ 1–2 ms** added per hop; `acks=all` waits for ISR which may span AZs — budget for it in latency-tier apps.
- **Cross-region replication is async, always** (Cluster Linking) — never synchronous across regions. RPO=0 across regions doesn't exist; design for it (wiki `patterns/dr-cluster-linking.md`, `dr-multi-region-cluster.md` for the within-region MRC RPO=0 option on CP).
- **Fetch-from-follower (`client.rack` + `broker.rack` + `RackAwareReplicaSelector`)** keeps consumer fetch traffic in-AZ — typically **30–50% off inter-AZ egress**. Do this.
- **Cross-AZ traffic is the silent cost line** (replication + cross-AZ consumer fetch). **Freight clusters** trade latency for object-storage-backed writes that slash inter-AZ replication cost — use them for latency-tolerant firehoses.
- Co-locate latency-critical clients in the cluster's region (ideally AZ); keep connections warm; be ILB-aware (wiki `patterns/low-latency-kafka-azure.md`, fsi-dsp `*-low-latency-azure` reference).

---

## Part XI — Capacity Planning Cheat Sheets

### New Confluent Cloud cluster

1. **Measure peak, not average** — peak ingress MB/s, peak produce req/s, peak partition count, peak connection count.
2. **Compute egress** ≈ ingress × (number of independent consumer groups) + internal replication. Fan-out is the multiplier people forget.
3. **Pick the type:** Standard (fits the ceilings, public/limited-private OK) → Enterprise (private + elastic + no capacity math) → Dedicated (BYOK / peering / Transit Gateway / Cluster-Linking-at-scale / single-tenant). Freight only for latency-tolerant firehoses.
4. **Dedicated only — size CKUs** from the ingress/egress/partition/connection/request limits per CKU (⚠️ the per-CKU numbers change — use Confluent's current sizing guidance / the sizing tool / your SE). **Add 30–40% headroom.** Multi-AZ always for prod.
5. **RF=3, min.insync=2, unclean leader election off** — these are fixed on CC; don't plan around changing them.

### New Flink compute pool (CC)

- Start `max_cfu` = **5 dev / 10–20 staging / 20–50 prod** (fsi-dsp `modules/flink/variables.tf` validation set: 5/10/20/30/40/50).
- CFU burn ∝ statement parallelism × state size × throughput. **The biggest single variable is state** — so set `sql.state-ttl` on every unbounded stateful op before you size anything.
- **`max_cfu` cannot be decreased after creation** — size to realistic peak, not paranoid peak.
- One pool per environment/team boundary (isolation + billing clarity). Pool exhaustion → statements stuck `PENDING`; that's your signal to raise `max_cfu` or split work.

### New Connect cluster (self-managed)

- Workers: ~enough heap for the connector's buffering (2–8 GB typical), CPU for SMTs/converters; scale workers to spread `tasks.max` across them.
- `tasks.max` ≤ source/topic partitions; internal topics compacted RF3; DLQ topic provisioned; secrets via ConfigProvider.
- If you're doing object-store sinks at scale, seriously evaluate **Tableflow** instead.

### New CP broker (bare metal / VM / LinuxONE)

- NVMe/SSD, dedicated data disks; ~6 GB heap + 32–64 GB+ RAM (page cache does the real work); 10 GbE+ NIC; XFS, `noatime`; `vm.swappiness=1`; high FD limits.
- RF=3, `min.insync.replicas=2`, `unclean.leader.election.enable=false`, `auto.create.topics.enable=false`.
- 3 (or 5) **dedicated** KRaft controllers, separate from brokers.
- Keep partitions-per-broker in the low thousands for replication health; enable Tiered Storage to keep local disk small and recovery fast; enable Self-Balancing Clusters.
- Size for **60–70% of peak**; rack-aware across AZs. LinuxONE specifics: wiki `patterns/linuxone-kafka-tuning.md`, `linuxone-validation-suite.md`.

---

## Part XII — Triage Decision Tree (symptom → layer → first check)

```
Records aren't getting durably written / produce is slow or erroring
   → PRODUCER / BROKER layer
   → check: producer JMX (record-queue-time, request-latency, buffer-available),
            broker RequestHandlerAvgIdlePercent, ISR / min.insync, network
   → see Part I troubleshooting

Records ARE written but consumers fall behind
   → CONSUMER / PARTITIONING layer
   → check: offset lag AND time lag (CC Metrics API), per-partition lag (skew?),
            rebalance frequency, max.poll.interval.ms vs actual processing time,
            GC pauses, downstream backpressure
   → see Part II troubleshooting

Records ARE delivered but they're wrong / unreadable / rejected
   → SCHEMA / CONTRACT layer
   → check: subject naming strategy match, compatibility mode, schema IDs across envs,
            converter config (Connect), SR connectivity/auth
   → see Part IV troubleshooting

A connector is RUNNING but nothing's flowing (or it's replaying)
   → CONNECT layer
   → check: GET /connectors/{n}/status task trace, internal topics compacted?,
            tasks.max vs partitions, DLQ headers, plugin.path/classpath
   → see Part V troubleshooting

A Flink statement produces nothing / costs a fortune / keeps degrading
   → FLINK layer
   → check: watermark advancing? (idle-timeout), state TTL set?, backpressured operator,
            compute pool out of CFUs?, checkpoint health (CP)
   → see Part VI troubleshooting

Clients can't connect at all (or connect then fail)
   → NETWORKING layer
   → check: can the client RESOLVE and ROUTE to every advertised broker address, per-AZ?,
            PrivateLink zonal DNS, advertised.listeners (CP), security.protocol/TLS/SASL match
   → see Part X

Auth works for some, fails for others / RBAC denials
   → SECURITY layer
   → check: MDS up?, role binding scope (resource vs cluster), service-account principal,
            cert validity, audit log for the denial reason
   → see Part IX

A CFK rolling op is "stuck"
   → KUBERNETES layer
   → check: under-replicated partitions (CFK won't proceed until URP=0 — by design),
            pod OOMKilled (exit 137 = heap > limit), PVC binding, KRaft quorum
   → see Part VIII
```

---

## Appendix A — Top 20 Gotchas, Tips & Workarounds

1. **`enable.idempotence=true` is the default since Kafka 3.0** — but it *implies* `acks=all`, `retries>0`, `max.in.flight≤5`. If you override `acks=1` you **silently lose** idempotence and ordering guarantees. Don't override acks down.
2. **`UnknownProducerIdException` after low retention** — the producer's PID metadata aged out of the partition. Don't set topic retention shorter than your producer's idle period; upgrade brokers; the producer self-heals by re-initializing.
3. **`auto.offset.reset` is a trap door, not a setting you'll often see fire.** It only triggers when there's *no* committed offset or the committed offset is *out of range* — which happens silently when `offsets.retention.minutes` (default 7 days) expires an idle group's offsets. Commit periodically even when idle, or pin the group.
4. **`enable.auto.commit=true` commits on `poll()` before you've processed** → at-most-once on crash. Never in a processing app. Manual commit *after* processing.
5. **`max.poll.interval.ms` exceeded = the broker ejects the consumer** → rebalance → the symptom looks like "my consumer randomly stops." Shrink `max.poll.records`, speed up processing, or `pause()`/`resume()`.
6. **More partitions are not free, and you can't remove them.** They slow rebalances, broker recovery, controller failover, and add produce-request overhead — and adding partitions to a *keyed* topic breaks `hash(key) % n` so per-key ordering is lost going forward. Size deliberately; don't "round up to be safe."
7. **On Confluent Cloud, RF (3), `min.insync.replicas` (2), and `unclean.leader.election` (false) are fixed.** Don't write runbooks or capacity plans that assume you can change them.
8. **Schema IDs are not portable across environments.** Dev ID 100 ≠ prod ID 100. Use Schema Linking or export/import; never hardcode schema IDs or assume they match.
9. **`auto.register.schemas=true` in producers = governance bypass + a race** registering slightly-different "latest" schemas. Register in CI (fail the build on incompat); clients use `use.latest.version=true` or a pinned version.
10. **Compatibility direction matters.** Adding a field *without a default* breaks `BACKWARD`. Removing a field breaks `FORWARD`. Know which side (producers vs consumers) upgrades first and pick the mode accordingly; use `FULL` for widely-shared contracts.
11. **Kafka Connect's `connect-offsets` / `connect-configs` / `connect-status` must be compacted, RF 3.** If `cleanup.policy` ever becomes `delete` (common after a botched migration), connectors **silently lose state** — they replay or forget. Check these after any cluster move.
12. **`tasks.max` > partition count = idle tasks doing nothing.** Sink connector parallelism is hard-capped by topic partitions regardless of `tasks.max`. Set it to `min(partitions, target parallelism, worker capacity)`.
13. **Object-store sink "small files problem":** low `flush.size` / short `rotate.interval.ms` → millions of tiny S3/GCS objects → slow queries + huge API bills. Target ~128 MB–1 GB files — or use **Tableflow** and stop hand-rolling this.
14. **Flink: unbounded regular joins and non-windowed aggregations keep state FOREVER without `sql.state-ttl` / `table.exec.state.ttl`.** This is the #1 surprise CFU/cost blow-up and OOM cause on CC Flink. Set a TTL on every non-windowed stateful operator; prefer interval/temporal/lookup joins.
15. **Flink: watermarks don't advance if a partition is idle** → windows never fire → output is silent. Set `table.exec.source.idle-timeout`. "My aggregation produces nothing" is almost always this or a too-tight watermark bound.
16. **Flink: `max_cfu` on a CC compute pool cannot be decreased after creation.** Size to realistic peak, not paranoid peak. Pool exhaustion → statements stuck `PENDING`.
17. **CFK rolling upgrades stall by design while any partition is under-replicated** — the operator won't take down the next broker until URP=0. A "stuck" roll almost always means a lagging broker or a bad disk, not a CFK bug. Find the URP, fix it, the roll continues.
18. **`advertised.listeners` (CP) / broker-hostname DNS resolution (CC PrivateLink) is the #1 connectivity footgun.** Clients reach the bootstrap, then fail to reach the brokers it returns. Verify every client can *resolve and route to* every advertised address, per-AZ. Test from inside *and* outside the network.
19. **SASL/PLAIN without TLS ships credentials in cleartext.** In FSI: mTLS or SASL/OAUTHBEARER. If you must use SASL, it's SCRAM-over-TLS minimum — never PLAIN-over-plaintext. And API keys never go in git.
20. **Cross-AZ traffic is the silent cost driver** (`acks=all` replication + consumers fetching from leaders across AZs). Enable fetch-from-follower (`client.rack` + `broker.rack` + `RackAwareReplicaSelector`) — typically 30–50% off inter-AZ egress. **Bonus #21:** Freight clusters trade ms-latency for ~10× cheaper throughput when you genuinely don't need low latency — right tool for log/telemetry firehoses, wrong tool for transactions.

### Tips / tricks / workarounds

- **Always `--dry-run` before `--execute`** on `kafka-consumer-groups --reset-offsets`. Always.
- **`kcat`** for quick inspection: `kcat -b <broker> -t <topic> -C -o -1 -c1` peeks the last message; `-L` lists metadata.
- **`linger.ms=0` is not "low latency" under load** — small lingers (5–20 ms) cut request count and often *lower* p99. fsi-dsp ships `linger.ms=20`.
- **For "exactly once into a database," prefer the outbox pattern + idempotent consumer** over Connect/Streams EOS gymnastics (wiki `patterns/fsi-exactly-once.md`).
- **Static membership (`group.instance.id`) + tuned `session.timeout.ms`** = deploy/restart a consumer without triggering a rebalance.
- **On CC, use the Metrics API + Stream Lineage** instead of rolling your own JMX scraping.
- **Test schema compatibility in CI** (`mvn schema-registry:test-compatibility`) before merge — never let production be the first compat check.
- **Flink enrichment: `LOOKUP JOIN` against an `upsert-kafka` / JDBC table** beats a regular join — bounded state.
- **`cleanup.policy=compact,delete`** for changelog topics that also need a time bound (compact for current state, delete for the floor).
- **DR endpoint flip:** put a service-discovery indirection (Consul / DNS) in front of `bootstrap.servers` so failover is one atomic change, not a config push to every client (wiki `patterns/dr-cluster-linking.md`, fsi-dsp ADR-003).
- **`message.timestamp.type=LogAppendTime`** if you don't trust producers' clocks and your retention/windowing depends on timestamps — but know it overwrites the producer's CreateTime.

---

## Appendix B — Sanity-Check Checklists

**Producer config**
- [ ] `enable.idempotence=true`, `acks=all` (and you haven't overridden acks down anywhere)
- [ ] `max.in.flight.requests.per.connection ≤ 5`
- [ ] `delivery.timeout.ms ≥ linger.ms + request.timeout.ms + retry budget`
- [ ] `compression.type` set (lz4/zstd), `batch.size` 32–128 KB, `linger.ms` 5–20
- [ ] `auto.register.schemas=false` in prod; schema registered in CI
- [ ] keyed topics: a real key is set (not relying on the sticky partitioner)
- [ ] transactional? `transactional.id` stable+unique per instance; downstream consumers `read_committed`

**Consumer config**
- [ ] `enable.auto.commit=false`; manual commit *after* processing; commit on revoke
- [ ] `max.poll.interval.ms ≥ worst-case batch processing time`; `max.poll.records` tuned to fit
- [ ] `auto.offset.reset` deliberate (and you know it'll fire if the group goes idle past `offsets.retention.minutes`)
- [ ] `partition.assignment.strategy=CooperativeStickyAssignor` set **explicitly** (OOTB default is `[RangeAssignor, CooperativeStickyAssignor]`) — or `group.protocol=consumer` / KIP-848
- [ ] `client.rack` set (fetch-from-follower)
- [ ] deserialization errors routed to a DLQ, not looping
- [ ] consumer instances ≤ partition count
- [ ] static membership (`group.instance.id`) if you deploy frequently

**New topic**
- [ ] `cleanup.policy`, `retention.ms`/`retention.bytes`, `max.message.bytes` all set explicitly
- [ ] partition count derived from throughput AND consumer parallelism — not "rounded up"
- [ ] naming follows `<domain>.<application>.<entity>.<event>` (FSI canon / ADR-007; wiki `patterns/topic-naming.md`) — any versioned-topic variant uses the sanctioned `_v2`-on-`<entity>` exception
- [ ] compacted topic? `min.cleanable.dirty.ratio`, `segment.ms`, `delete.retention.ms` considered
- [ ] CP only: RF=3, `min.insync.replicas=2` set on the topic

**New CC cluster**
- [ ] type chosen on the decision rule (Standard → Enterprise → Dedicated → Freight)
- [ ] peak (not average) ingress/egress/partitions/connections estimated; egress accounts for fan-out
- [ ] Dedicated: CKUs sized from current per-CKU limits + 30–40% headroom; multi-AZ
- [ ] networking: PrivateLink/PSC for private (Enterprise/Dedicated); peering only on Dedicated if needed
- [ ] BYOK needed? → Dedicated or Enterprise
- [ ] Cluster Linking source needed? → Standard/Dedicated (not Basic)

**New Flink compute pool (CC)**
- [ ] `max_cfu` = 5 dev / 10–20 staging / 20–50 prod, sized to realistic peak (can't decrease later)
- [ ] every unbounded stateful statement has `sql.state-ttl` set
- [ ] one pool per environment/team boundary
- [ ] watermark strategy bounded; `table.exec.source.idle-timeout` set on quiet sources
- [ ] `scan.startup.mode=earliest-offset` where deterministic replay matters

**Connect connector**
- [ ] right model chosen (fully-managed CC → custom connector CC → self-managed)
- [ ] `tasks.max ≤ partition count`
- [ ] DLQ configured (`errors.tolerance=all`, `errors.deadletterqueue.topic.name`, context headers on)
- [ ] converters match what's actually on the topic
- [ ] self-managed: internal topics compacted RF3; secrets via ConfigProvider; `plugin.path` correct
- [ ] object-store sink: `flush.size`/`rotate.interval.ms` tuned for big files (or use Tableflow)
- [ ] Debezium/Postgres: `heartbeat.interval.ms` set

**CFK deployment**
- [ ] SSD StorageClass, `volumeClaimTemplate` (expandable), reclaim Retain, no `emptyDir` for brokers
- [ ] `podAntiAffinity` required + rack awareness mapped to AZ label
- [ ] broker requests==limits (Guaranteed QoS); ~6 GB heap; no tight CPU limit on brokers
- [ ] `PodDisruptionBudget maxUnavailable=1`; dedicated KRaft controllers (3/5)
- [ ] advertised listeners resolvable+routable by clients; per-broker external access configured
- [ ] mTLS between components; secrets external; CFK↔CP version matrix checked
- [ ] Tiered Storage configured; CRs in Git

**Security baseline**
- [ ] mTLS or SASL/OAUTHBEARER (no PLAIN-over-plaintext; SCRAM-over-TLS at minimum)
- [ ] per-application service accounts; RBAC bound at resource scope; no `super.users` in prod; no wildcard ACLs
- [ ] TLS everywhere including inter-broker/inter-component
- [ ] BYOK on Dedicated/Enterprise if required; CSFLE on PII fields
- [ ] audit logs on, forwarded to SIEM (wiki `patterns/audit-log-siem-integration.md`)
- [ ] secrets via ConfigProvider/Vault; rotation automated; nothing in git
- [ ] compliance mapping documented (wiki `concepts/fsi-compliance.md`)

**Networking**
- [ ] private connectivity (PrivateLink/PSC) for prod; zonal DNS records resolvable per-AZ
- [ ] fully-managed connectors' egress path to your sources planned
- [ ] Cluster Linking path between clusters explicitly designed (esp. CC↔CP)
- [ ] CP: `advertised.listeners` = real client-reachable addresses; cert SANs match; ports open
- [ ] fetch-from-follower enabled (`client.rack` + `broker.rack` + `RackAwareReplicaSelector`)
- [ ] latency-critical clients co-located in cluster region/AZ
- [ ] DR endpoint indirection (Consul/DNS) in front of `bootstrap.servers`

---

## Appendix C — Reference Assets Index

**cflt-ai wiki** (`wiki/`)
- Producers: `concepts/producer-batching-config.md`
- Consumers: `concepts/consumer-group-rebalancing.md`, `concepts/consumer-lag-monitoring.md`
- EOS: `concepts/exactly-once-semantics.md`, `patterns/fsi-exactly-once.md`
- Cluster Linking / DR: `concepts/cluster-linking-topology.md`, `patterns/dr-cluster-linking.md`, `patterns/dr-mirrormaker2.md`, `patterns/dr-multi-region-cluster.md`
- Schema: `concepts/schema-evolution-strategies.md`, `patterns/fsi-governance-automation.md`, `patterns/topic-naming.md`
- Connect / DLQ: `patterns/dead-letter-queue-design.md`
- Flink: `concepts/flink-checkpointing.md`
- K8s: `patterns/aks-kafka-tuning.md`
- Security/audit: `patterns/audit-log-siem-integration.md`, `concepts/fsi-compliance.md`
- Networking/latency: `patterns/low-latency-kafka-azure.md`
- LinuxONE: `concepts/linuxone-platform-foundations.md`, `concepts/linuxone-kafka-integration.md`, `patterns/linuxone-kafka-tuning.md`, `patterns/linuxone-flink-validation-tuning.md`, `patterns/linuxone-validation-suite.md`, `patterns/fsi-l1-reference-architecture.md`
- Governance/SLA: `concepts/sla-tiers.md`, `concepts/fsi-data-streaming-platform.md`

**fsi-dsp reference repo** (`raw/repos/fsi-dsp/`)
- Producers: `reference/java-producer/`, `reference/python-producer/`, `reference/dotnet-producer/`, `reference/{java,python}-producer-low-latency-azure/`
- Consumers: `reference/java-consumer/`, `reference/python-consumer/`, `reference/dotnet-consumer/`, `reference/{java,python}-consumer-low-latency-azure/`
- Connect: `reference/connect-configs/` (distributed worker properties, JDBC source/sink examples)
- Flink SQL: `reference/flink-sql/` (tumbling window, stream-table join enrichment, filter-and-route, DLQ pattern)
- Terraform modules: `modules/topic/` (governed topic = topic+schema+RBAC+DR mirror), `modules/flink/` (compute pool + statements)
- Ansible roles: `ansible/roles/cp_topic`, `cp_schema`, `cp_rbac`, `cp_connect`, `cp_dr_mm2`, `cp_dr_mrc`, `cp_observability`, `cfk_operator`, `cfk_topic`
- Scenarios: `scenarios/cc-gcp/` (CC on GCP + OAuth + Flink), `scenarios/cfk-openshift/` (Kafka/Connect/SR/Flink/MM2 on OpenShift), `scenarios/cfk-openshift-linuxone/`
- Docs: `docs/csfle-guide.md`, `docs/schema-guide.md`, `docs/dr-runbook.md`, `docs/rotation-runbook.md`, `docs/compliance-guide.md`, `docs/cloud-providers.md`, `docs/linuxone-*` guides
- ADRs: `docs/adr/001-avro-over-protobuf`, `002-compatibility-by-tier`, `003-consul-service-discovery`, `004-onprem-connect`, `005-cluster-linking-over-mrc`, `006-oauth-vs-api-keys`, `007-topic-naming`, `008-dr-tier-classification`, `009-linuxone-kafka-offload`, `010-low-latency-azure-kafka-profile`

---

*Confluent Canon applied throughout (CLAUDE.md "Always-On Rules"): RF3/`min.insync=2`, `acks=all`+idempotence, `BACKWARD` compat default, Avro-first, bounded watermarks, `upsert-kafka` for changelogs, Cluster Linking over MM2 for CC↔CC, mTLS/RBAC + audit logs in FSI, IBM/LinuxONE bridge pattern for mainframe. No deviations introduced.*

---

*Golden source — reconciled 2026-05-12 against `confluent-best-practices-quickstart-review-2026-05-12.md` (41 claims reviewed). 3 substantive corrections applied (compression default → `lz4`; cooperative-sticky is an explicit setting, not the OOTB default; topic naming → `<domain>.<application>.<entity>.<event>` per ADR-007) + 2 config notes (`confluent.tier.enable` per broker; `config.storage.topic` single partition) + 2 additions (sub-ms market-data caveat box; IBM MQ Source Connector named as the mainframe bridge). Validated against Confluent Canon + cflt-ai wiki + fsi-dsp reference repo. Live `confluent-docs`/`context7` MCP re-validation was budget-bounded this run — items flagged ⚠️ (CC cluster-type/Freight limits, per-CKU sizing numbers, Tableflow GA surface, KIP-848 client support, custom-connector-on-PrivateLink) should still be re-confirmed via `confluent-docs` MCP or `/wiki:validate` before quoting exact numbers to a customer. Patterns are stable; numbers drift.*
