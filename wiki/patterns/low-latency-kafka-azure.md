---
title: Low-Latency Kafka Clients on Azure
tags: [kafka azure latency fsi performance fraud-detection rebalance ilb]
sources: []
related: [concepts/sla-tiers, concepts/fsi-data-streaming-platform, patterns/dr-cluster-linking, patterns/fsi-exactly-once]
confidence: medium
last_updated: 2026-05-06
last_validated: 2026-05-06
---

# Low-Latency Kafka Clients on Azure

## Summary

Kafka workloads with sub-100ms end-to-end SLAs running on Azure-hosted clients face two compounding problems the throughput-default profile does not address: (1) the default client tuning trades 20-500ms of latency for batching efficiency, and (2) Azure Internal Load Balancer kills idle TCP at 4 minutes with no RST/FIN, manifesting as silent connection death. A third concern — rebalance latency from pod restart — turns into a multi-second p99 outlier that can dominate the SLA budget. This pattern is a named profile that addresses all three through three orthogonal layers, shipped as the `*-low-latency-azure` reference artifacts in fsi-dsp (citation, never code fork).

## When to use

All three conditions must hold:

1. **Latency tier ≤ 100ms.** Real-time fraud detection, intraday risk signals, market-data fan-out, access-transparency event streams. Anything where p99 budget is dominated by per-message latency rather than throughput.
2. **Azure compute behind an Internal Load Balancer.** Any Azure-hosted Kafka client where ILB sits in the connection path — AKS, App Service, VM behind ILB, Container Apps, etc. ILB's 4-minute idle timeout is the maximum and is not configurable lower.
3. **Throughput is modest.** Sustained throughput below ~50 MB/s. The latency tuning sacrifices batching efficiency by design.

If any condition fails, use the throughput-default profile (`reference/{java,python}-{producer,consumer}` in fsi-dsp) and tune incrementally.

## Three orthogonal layers

The named profile stacks three independent concerns. Each can be reasoned about and adopted separately, but the profile bundles them because workloads requiring one almost always require the others.

### Layer 1: Latency-favored client tuning

Replaces throughput-batching defaults with immediate-dispatch settings.

**Producer:**

| Setting | Default | Profile | Rationale |
|---|---|---|---|
| `compression.type` | `zstd` | `none` | No compression CPU at low TPS; gain back the per-message latency |
| `batch.size` | 32_768 | 16_384 | Absorbs micro-bursts without holding messages |
| `linger.ms` | 20 (Kafka 4.0+: 5) | 0 | Immediate dispatch — every send releases without batching wait |

Idempotency, `acks=all`, and infinite retries are unchanged. Durability properties hold.

**Consumer:**

| Setting | Default | Profile | Rationale |
|---|---|---|---|
| `max.poll.records` | 500 | 10 (Java) | Smaller batches → faster per-poll completion |
| `max.poll.interval.ms` | 300_000 | 600_000 | 10-minute headroom for backpressure stalls |
| `fetch.min.bytes` | 1024 | 1 | Broker returns immediately with any data |
| `fetch.max.wait.ms` | 500 | 0 | No broker-side batching delay |

### Layer 2: Azure ILB-aware connection management

Azure Internal Load Balancer enforces a 4-minute idle TCP timeout. The kill is silent — no RST, no FIN, no log entry — and the default Kafka client doesn't see it until the next produce or fetch fails with `TimeoutException`. The 10-second default reconnect floor introduces multi-second blind spots.

| Setting | Default | Profile | Mechanism |
|---|---|---|---|
| `socket.keepalive.enable` | `false` | `true` | OS-level TCP keepalive probes detect ILB kill within seconds |
| `connections.max.idle.ms` | 540_000 | 180_000 | 3-minute proactive recycle, before ILB fires at 4 minutes |
| `reconnect.backoff.max.ms` | 10_000 | 1_000 | 1-second cap on reconnect backoff (default 10s creates blind spots) |

These three settings together survive the ILB idle kill without operator intervention. The 3-minute recycle proactively rotates connections; the keepalive probes catch any kill that does occur within seconds; the tightened reconnect collapses the recovery window.

### Layer 3: Rebalance avoidance (consumers)

A 30-second consumer rebalance is a 30-second p99 latency outlier. For a workload with a sub-100ms budget, this single event consumes 300× the budget — and rebalances fire on every pod restart, deployment, network blip, or session timeout under default static membership semantics.

**Cooperative-sticky assignment** (KIP-429): Set `partition.assignment.strategy=org.apache.kafka.clients.consumer.CooperativeStickyAssignor`. Rebalances become incremental — partitions in flight don't pause during reassignment. The single biggest win for steady-state latency stability under rebalances that do happen.

**Static group membership** (KIP-345): Set `group.instance.id` to a stable identifier per consumer instance (pod ordinal, hostname, etc.). A pod restart within `session.timeout.ms` does not trigger rebalance at all — the consumer rejoins the group with its previous identity and resumes its prior partition assignment. Avoiding the rebalance is strictly better than handling it well.

**Decoupled poll/process with backpressure** (Java consumer only): The standard pattern processes each record inline in the poll loop and commits synchronously after the batch. This couples consumer-group health (heartbeat liveness) to downstream processing latency — a slow downstream stalls the heartbeat and triggers rebalance. The Java low-latency variant runs the poll loop on a dedicated thread whose only job is `poll()` plus heartbeat. Records hand off to a worker thread via a bounded `LinkedBlockingQueue` (capacity 1000). When the queue fills, the poll thread calls `consumer.pause()` to stop fetching while heartbeats continue; `consumer.resume()` fires when the queue drains. Offsets are tracked in a `ConcurrentHashMap<TopicPartition, OffsetAndMetadata>` and committed asynchronously from the poll thread.

The Python variant does not include the decoupled pattern — `confluent-kafka` users wanting it should fork the variant and add a `queue.Queue` between `consumer.poll()` and the handler.

## Canonical implementation

The profile ships as named fsi-dsp reference artifacts. **Customer overlays cite the artifact ID; they never fork the code.**

| Artifact | MANIFEST ID |
|---|---|
| Java producer | `reference/java-producer-low-latency-azure` |
| Java consumer | `reference/java-consumer-low-latency-azure` |
| Python producer | `reference/python-producer-low-latency-azure` |
| Python consumer | `reference/python-consumer-low-latency-azure` |

Each artifact carries a `capabilities` block in `MANIFEST.yaml`:

```yaml
capabilities:
  latency_tier: sub_100ms
  cloud: azure
  connection_resilience: ilb_aware
  backpressure: queue_decoupled  # consumer artifacts only
```

The act-rail's `fsi_dsp_coverage` gate (gate 2) matches request shape against these capabilities. A request like "low-latency consumer on Azure" resolves to the consumer artifact by capability match.

## Tradeoffs

**You give up:**

- **Throughput.** With `linger.ms=0`, no compression, and small batches, sustained throughput is roughly 5-10× lower than the throughput-default profile. Workloads above ~50 MB/s sustained should not adopt this profile without revisiting the tuning.
- **Network bandwidth.** No producer-side compression means ~3-4× more bytes on the wire per message. At very high message rates this affects egress costs and broker network capacity.
- **Memory** (Java consumer). The bounded work queue plus offset map adds ~1-2 MB of steady-state heap per consumer instance.
- **Commit chattiness.** Async commits per cycle increase commit traffic to the broker by ~10× compared to per-batch sync commit. Modern Confluent Cloud and CP clusters absorb this comfortably; very small clusters may not.
- **Maintenance surface.** Two variants per language doubles the surface for client tuning patches. Both variants share the same business logic; only the configuration and (for Java consumer) the threading model differ.

**You get:**

- **p99 latency under 100ms** in steady state and across pod restarts.
- **Survival across Azure ILB idle kills** with no operator intervention.
- **No rebalance-induced latency cliffs** on pod restart with static membership configured.
- **Predictable produce timing** for upstream observability — no linger jitter contaminating the latency histogram.

## Detection and validation

The profile's success conditions are observable. Recommended SLO instrumentation:

- **Producer p99 send latency.** Should be < 50ms under steady load. Histogram via Kafka client metrics (`record-send-rate`, `record-send-total` plus client-side timing).
- **Consumer p99 end-to-end.** Topic timestamp → handler completion. Should be < 100ms under steady load and across rebalance/restart events.
- **Connection cycling rate.** Should match the 3-minute recycle. Sudden divergence (e.g., spikes to broker-driven cycles) suggests ILB is winning the race; tighten `connections.max.idle.ms`.
- **Consumer rebalance rate.** Should be near-zero under static membership. Any rebalance is a p99 outlier; investigate.

## See also

- `reference/java-{producer,consumer}-low-latency-azure/` — fsi-dsp implementation
- `reference/python-{producer,consumer}-low-latency-azure/` — fsi-dsp implementation
- ADR-010: Low-Latency Azure Kafka Profile (in fsi-dsp)
- KIP-429 (cooperative sticky), KIP-345 (static membership)
- Microsoft Azure Load Balancer idle timeout documentation
- `concepts/sla-tiers` — where this pattern fits in the FSI SLA framework
- `patterns/dr-cluster-linking` — DR pattern compatible with this profile
