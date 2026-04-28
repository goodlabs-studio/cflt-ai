---
title: Consumer Group Rebalancing
tags: [kafka performance]
sources: []
related: [concepts/consumer-lag-monitoring, concepts/exactly-once-semantics, concepts/producer-batching-config]
confidence: medium
last_updated: 2026-04-11
last_validated: 2026-04-28
---

# Consumer Group Rebalancing

## Summary

Consumer group rebalancing redistributes topic-partition assignments among consumers in a group. Three protocol generations exist: eager (stop-the-world, pre-2.4), cooperative/incremental (KIP-429, Kafka 2.4+), and server-side (KIP-848, Kafka 4.0+). Cooperative rebalancing reduces processing pause by ~90%; KIP-848 achieves up to 20x faster rebalancing by moving assignment computation to the broker. Static group membership (KIP-345) eliminates rebalances during rolling restarts entirely.

## Detail

### Rebalancing Protocols

**Eager (Stop-the-World):** Every consumer revokes all assigned partitions before sending a JoinGroup request. No member processes records for the entire rebalance duration. Two synchronous phases: JoinGroup (leader computes assignment) and SyncGroup (coordinator distributes assignment). Duration scales linearly with partition count and consumer count.

**Cooperative/Incremental (KIP-429, Kafka 2.4+):** Only partitions that need to move are revoked. Unaffected consumers continue processing. Multiple shorter rounds: first round identifies and revokes partitions to move; second round assigns them to new owners. Benchmarks show ~90% reduction in processing pause time.

**Server-Side (KIP-848, Kafka 4.0+):** The group coordinator computes target assignment using a server-side assignor. Consumers communicate via continuous heartbeat -- no JoinGroup/SyncGroup phases. Fully incremental with no global synchronization barrier. Benchmarks: 10 consumers adding 900 partitions in 5 seconds vs. 103 seconds with classic protocol.

### Assignment Strategies (Classic Protocol)

| Assignor | Protocol | Behavior |
|----------|----------|----------|
| RangeAssignor | Eager | Per-topic ranges. Can cause uneven load across multiple topics. |
| RoundRobinAssignor | Eager | Round-robin across all topics. Even but high partition movement. |
| StickyAssignor | Eager | Balanced + preserves existing assignments. Still revokes all during JoinGroup. |
| CooperativeStickyAssignor | Cooperative | Same as Sticky but uses cooperative protocol. **Recommended for all new applications.** |

Default since Kafka 3.1: `[RangeAssignor, CooperativeStickyAssignor]` (dual-assignor enables single-rolling-bounce migration to cooperative).

### KIP-848 Server-Side Assignors

| Assignor | Behavior | Default? |
|----------|----------|----------|
| `uniform` | Distributes partitions evenly, sticky | Yes |
| `range` | Contiguous ranges per consumer, sticky | No |

Configured on the broker via `group.consumer.assignors`. Clients override with `group.remote.assignor`. Custom client-side assignors are not supported with KIP-848.

| Platform | KIP-848 Status |
|----------|---------------|
| Apache Kafka 4.0+ | GA. `group.protocol=consumer` must be set explicitly. |
| Confluent Cloud | GA (June 2025). |
| Confluent Platform 8.0 | GA. |

### Static Group Membership (KIP-345, Kafka 2.3+)

Each consumer gets a persistent identity via `group.instance.id`. On graceful shutdown, the consumer does not send a LeaveGroup request. If the same `group.instance.id` rejoins within `session.timeout.ms`, the broker returns the cached assignment without triggering a rebalance. Critical for Kubernetes rolling deployments.

### Key Configuration

| Property | Default | Description |
|----------|---------|-------------|
| `partition.assignment.strategy` | `[RangeAssignor, CooperativeStickyAssignor]` (3.1+) | Assignor class list |
| `group.instance.id` | `null` | Static membership ID |
| `session.timeout.ms` | `45000` (Kafka 3.0+, was 10000) | Time before consumer considered dead |
| `heartbeat.interval.ms` | `3000` | Heartbeat frequency (keep <= 1/3 session timeout) |
| `max.poll.interval.ms` | `300000` | Max time between poll() calls |
| `group.protocol` | `classic` (Kafka 4.0) | `classic` or `consumer` (KIP-848). Expected default in Kafka 5.0. |

### Rebalance Triggers

- Consumer joins or leaves (graceful LeaveGroup or heartbeat timeout)
- `poll()` timeout (`max.poll.interval.ms` exceeded)
- Subscription change (different topics in `subscribe()`)
- Topic metadata change (new partitions added)
- Coordinator broker failover

### Best Practices

Use CooperativeStickyAssignor or KIP-848:
```properties
# Classic protocol (Kafka 2.4+):
partition.assignment.strategy=org.apache.kafka.clients.consumer.CooperativeStickyAssignor

# KIP-848 (Kafka 4.0+):
group.protocol=consumer
```

Enable static membership for Kubernetes:
```properties
group.instance.id=my-app-consumer-0
session.timeout.ms=300000   # 5 min -- covers pod restart time
heartbeat.interval.ms=10000
```

Tune timeouts: Set `max.poll.interval.ms` to worst-case processing time. Limit batch size with `max.poll.records`.

ConsumerRebalanceListener: commit offsets in `onPartitionsRevoked()`. Implement `onPartitionsLost()` separately -- do not commit offsets there since partitions may already be owned by another consumer.

### Monitoring

- `rebalance-latency-avg` -- average rebalance duration
- `rebalance-rate-per-hour` -- rebalance frequency
- `records-lag-avg` -- consumer lag spikes during rebalance

## Related

- [Consumer Lag Monitoring](concepts/consumer-lag-monitoring.md) -- lag spikes during rebalances
- [Exactly-Once Semantics](concepts/exactly-once-semantics.md) -- rebalance impact on EOS
- [Producer Batching Configuration](concepts/producer-batching-config.md) -- producer-side tuning
