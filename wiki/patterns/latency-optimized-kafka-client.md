---
title: Latency-Optimized Kafka Client
tags: [kafka latency performance producers consumers fsi tuning]
sources:
  - https://docs.confluent.io/platform/current/installation/configuration/producer-configs.html
  - https://docs.confluent.io/platform/current/installation/configuration/consumer-configs.html
  - https://kafka.apache.org/documentation/#producerconfigs
  - https://kafka.apache.org/documentation/#consumerconfigs
related:
  - concepts/azure-connection-management
  - patterns/low-latency-kafka-azure
  - patterns/producer-config-fsi
  - patterns/consumer-config-fsi
  - concepts/producer-batching-config
  - concepts/consumer-group-rebalancing
  - concepts/sla-tiers
confidence: high
last_updated: 2026-05-18
last_validated: 2026-05-18
---

# Latency-Optimized Kafka Client

## Summary

The Apache Kafka client defaults are tuned for sustained throughput, not end-to-end latency. For workloads with a p99 budget under ~100 ms (real-time fraud detection, intraday risk, market-data fan-out, access-transparency streams), four levers dominate the latency budget: producer batching (`linger.ms`, `batch.size`, `compression.type`), consumer fetching (`fetch.min.bytes`, `fetch.max.wait.ms`, `max.poll.records`), rebalance avoidance (cooperative-sticky assignment + static group membership), and connection-management knobs that interact with cloud load balancers. This pattern is the **cloud-agnostic** baseline; the Azure-specific overlay that addresses Internal Load Balancer silent kills lives in [Low-Latency Kafka Clients on Azure](low-latency-kafka-azure.md) and the canonical ILB reference is [Azure Connection Management](../concepts/azure-connection-management.md).

## Pattern

### When to use

All three conditions should hold:

1. **Latency-tier SLA ≤ 100 ms end-to-end** (FSI: risk, fraud, compliance event streams; market-data fan-out).
2. **Sustained throughput under ~50 MB/s per client.** The tuning trades batching efficiency for immediate dispatch — high-TPS workloads should keep the throughput-default profile.
3. **Durability remains non-negotiable.** Idempotent producer, `acks=all`, transactional semantics where applicable. Latency optimization here never relaxes durability.

If any condition fails, use the [FSI Producer Configuration](producer-config-fsi.md) and [FSI Consumer Configuration](consumer-config-fsi.md) baselines and tune incrementally with a single lever at a time.

### Four lever categories

The pattern bundles four orthogonal lever categories. Each can be reasoned about independently; bundle adoption is recommended because workloads requiring one usually require the others.

| Category | What it shapes | Producer levers | Consumer levers |
|---|---|---|---|
| Batching | per-message wait | `linger.ms`, `batch.size`, `compression.type` | `fetch.min.bytes`, `fetch.max.wait.ms`, `max.poll.records` |
| Group health | rebalance-induced cliffs | n/a | `partition.assignment.strategy`, `group.instance.id`, `session.timeout.ms` |
| Connection lifecycle | reconnect blind spots | `connections.max.idle.ms`, `reconnect.backoff.max.ms`, `socket.keepalive.enable` (librdkafka) | same |
| Durability invariants | end-to-end correctness | `acks=all`, `enable.idempotence=true`, `delivery.timeout.ms` | `isolation.level=read_committed` (when paired with transactional producers) |

### Producer tuning

Replace throughput batching with immediate dispatch. Keep idempotence and acks unchanged.

| Property | Kafka 3.x / 4.x default | Latency profile | Why |
|---|---|---|---|
| `linger.ms` | `0` (Kafka 4.0+: `5` per KIP-1083) | `0` | No artificial wait before flushing a partition batch |
| `batch.size` | `16384` (16 KB) | `16384` (unchanged) or `8192` | Smaller batches absorb micro-bursts without holding low-rate partitions |
| `compression.type` | `none` (producer-side) | `none` for sub-50 ms tier; `lz4` for 50–100 ms tier | Compression CPU adds 1–5 ms per batch; skip it at the tightest tier |
| `acks` | `all` (since AK 3.0) | `all` | Durability invariant; do not relax |
| `enable.idempotence` | `true` (since AK 3.0) | `true` | Durability invariant |
| `max.in.flight.requests.per.connection` | `5` | `5` | Highest value compatible with idempotence (≤5); maintains pipelining |
| `delivery.timeout.ms` | `120000` (2 min) | `30000` for tight tiers | Fail-fast so retries don't silently inflate p99 |

The Kafka 4.0 `linger.ms` default change from `0` to `5` ms (KIP-1083) is documented in the current Confluent Platform producer-configs reference: *"The default changed from 0 to 5 in Apache Kafka 4.0 as the efficiency gains from larger batches typically result in similar or lower producer latency despite the increased linger."* For sub-50 ms tiers the latency profile keeps the explicit `linger.ms=0` override; for 50–100 ms tiers the new 4.0 default is acceptable.

### Consumer tuning

The default `fetch.min.bytes=1` already gives immediate broker response; the larger lever is **per-poll batch size** and the fetch-wait ceiling.

| Property | Kafka 3.x / 4.x default | Latency profile | Why |
|---|---|---|---|
| `fetch.min.bytes` | `1` byte | `1` (unchanged) | Broker returns the first available bytes; no aggregation wait |
| `fetch.max.wait.ms` | `500` | `100` or lower | Cap on how long the broker holds the fetch when `fetch.min.bytes` isn't satisfied |
| `max.poll.records` | `500` | `10`–`50` | Smaller per-poll batches → shorter handler completion → faster heartbeat cadence |
| `max.poll.interval.ms` | `300000` (5 min) | `600000` (10 min) | Headroom for occasional slow batches; rebalance cost outweighs a long timeout |
| `enable.auto.commit` | `true` | `false` | Always commit after processing in latency-sensitive workloads |
| `isolation.level` | `read_uncommitted` | `read_committed` | Required when reading topics written by transactional producers |

> ⚠️ unverified — the `fetch.min.bytes` default of `1` byte is the canonical AK value; the companion Azure pattern article currently cites `1024` for this default. That value is incorrect for stock Apache Kafka and should be reconciled in [Low-Latency Kafka Clients on Azure](low-latency-kafka-azure.md); this article uses the AK canonical default.

### Rebalance avoidance

Rebalances dominate p99 outliers for any consumer running tighter than ~1 s budget. Three levers, all consumer-side:

- **`partition.assignment.strategy = org.apache.kafka.clients.consumer.CooperativeStickyAssignor`** (KIP-429). Rebalances become incremental — partitions not being moved keep flowing. Single biggest steady-state win when a rebalance does occur.
- **`group.instance.id = <stable-per-instance>`** (KIP-345). A consumer restart within `session.timeout.ms` rejoins with its previous identity and skips the rebalance entirely.
- **Decoupled poll/process loop** (Java consumer). Keep the poll thread doing only `poll()` + heartbeat; hand records to a bounded worker queue; call `consumer.pause()` / `consumer.resume()` on backpressure. Prevents downstream slowness from killing group health. (Python `confluent-kafka` users wanting this pattern need to add it themselves; the library doesn't bundle it.)

For the canonical FSI consumer baseline that bundles these defaults explicitly, see [FSI Consumer Configuration](consumer-config-fsi.md).

The next consumer protocol generation — **KIP-848 / server-side rebalancing** — moves assignment to the broker, sub-second rebalance times, and removes the eager-vs-cooperative client choice. See [Consumer Group Rebalancing](../concepts/consumer-group-rebalancing.md) for current GA matrix and migration.

### Connection lifecycle (cloud-agnostic)

| Property | Default | Latency profile | Why |
|---|---|---|---|
| `connections.max.idle.ms` | `540000` (9 min) | `180000` (3 min) on Azure ILB paths; default elsewhere | Avoids silent kill by cloud load balancers with shorter idle timeouts |
| `reconnect.backoff.ms` | `50` | `50` | Initial backoff floor |
| `reconnect.backoff.max.ms` | `1000` (1 s) | `1000` (already aggressive) | Caps recovery latency; older docs cite 10 s — incorrect for AK 3.x/4.x |
| `socket.keepalive.enable` (librdkafka only) | `false` | `true` for any cloud with silent-kill LB behavior | OS-level TCP keepalive detects dead connections |
| `socket.connection.setup.timeout.ms` | `10000` | `5000` for tight tiers | Fail-fast on broker churn |

Apache Kafka Java clients **do not expose `socket.keepalive.enable`**; the JVM follows the OS default (`net.ipv4.tcp_keepalive_*` on Linux). librdkafka-based clients (`confluent-kafka-python`, `-go`, `-dotnet`, `librdkafka` C) do expose it. See [Azure Connection Management](../concepts/azure-connection-management.md) for the full ILB silent-kill model.

### Cloud-specific overlays

This article is the cross-cloud baseline. Apply the appropriate overlay on top:

- **Azure (any compute behind an ILB):** [Low-Latency Kafka Clients on Azure](low-latency-kafka-azure.md) — bundles this baseline with ILB-aware connection management (3-minute recycle, librdkafka keepalive) and rebalance avoidance into a single named profile, plus the `*-low-latency-azure` fsi-dsp reference artifacts.
- **AWS:** NLB sends TCP RST on idle close (350 s default), so the silent-kill problem doesn't apply; the baseline above is sufficient. Cross-AZ data cost is the dominant operational concern — use `client.rack` for follower fetching. See [Network Connectivity by Cluster Tier](../concepts/network-connectivity-by-tier.md).
- **GCP:** Internal TCP LB behaves like NLB (observable termination). Same as AWS guidance.
- **Bare metal / on-prem CP:** No LB-induced kill; baseline above plus `aks-kafka-tuning` broker-side knobs adapted to your hardware.

## Observability and validation

The pattern's success conditions are measurable; instrument these before claiming the profile is doing its job.

| Metric | Target under tight tier | Source |
|---|---|---|
| Producer `record-send-rate` p99 send latency | < 20 ms | Kafka client JMX |
| Consumer end-to-end (Kafka record timestamp → handler complete) | < 100 ms | App-side histogram with topic-timestamp baseline |
| `consumer-rebalance-rate` | near-zero in steady state | Kafka consumer JMX |
| Connection cycle rate | matches `connections.max.idle.ms` cadence | Kafka client JMX (`connection-close-rate`) |
| `record-error-rate` (producer) | zero | Kafka producer JMX |

If rebalances are non-zero in steady state, check `group.instance.id` is set and `session.timeout.ms` is large enough to absorb pod restarts. If connection-cycle rate is dominated by broker-driven closes rather than the configured recycle, the cloud LB is winning the race — tighten `connections.max.idle.ms` further or move to PrivateLink / VPC peering.

## Caveats

- **Throughput sacrifice.** `linger.ms=0` + `compression.type=none` + small fetch batches reduces sustained throughput by ~5–10× vs the throughput baseline. Workloads above ~50 MB/s sustained should not adopt this profile without revisiting the tuning per-lever.
- **Bandwidth/cost.** No producer-side compression means ~3–4× more wire bytes per message; affects egress cost and broker network capacity at scale.
- **Commit chattiness.** Manual per-batch commits at small `max.poll.records` increase commit traffic ~10× vs default. Modern CC and CP clusters absorb this; very small clusters may not.
- **Memory footprint** (Java decoupled consumer). Bounded queue + offset map ~1–2 MB steady-state heap per consumer instance.
- **Maintenance surface.** Latency variants double the surface for client patches; keep business logic identical and isolate the differences to config + (Java consumer) threading model.
- **Durability not negotiable.** This pattern is incompatible with `acks=1`, `acks=0`, `enable.idempotence=false`, or `enable.auto.commit=true` in any FSI context. If a workload genuinely cannot tolerate `acks=all` latency, the answer is architectural (move processing closer, use Streams/Flink for in-cluster processing) — not relaxing durability.

## Related

- [Azure Connection Management for Kafka Clients](../concepts/azure-connection-management.md) — canonical ILB silent-kill reference and the three connection properties that defeat it
- [Low-Latency Kafka Clients on Azure](low-latency-kafka-azure.md) — Azure-specific overlay (this baseline + ILB connection mgmt + rebalance avoidance bundled as a named profile)
- [FSI Producer Configuration](producer-config-fsi.md) — durability-first baseline this profile extends
- [FSI Consumer Configuration](consumer-config-fsi.md) — manual commit + CooperativeSticky + static membership baseline
- [Producer Batching Configuration](../concepts/producer-batching-config.md) — RecordAccumulator internals and the throughput-vs-latency frontier
- [Consumer Group Rebalancing](../concepts/consumer-group-rebalancing.md) — KIP-429 cooperative-sticky, KIP-345 static membership, KIP-848 server-side
- [AKS Kafka Tuning](aks-kafka-tuning.md) — broker-side context when running CFK clients on AKS
- [SLA Tiers](../concepts/sla-tiers.md) — where this pattern fits in the FSI SLA framework
