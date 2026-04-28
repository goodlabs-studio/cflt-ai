---
title: Consumer Lag Monitoring
tags: [kafka observability performance]
sources: []
related: [concepts/consumer-group-rebalancing, concepts/sla-tiers, concepts/fsi-data-streaming-platform]
confidence: medium
last_updated: 2026-04-11
last_validated: 2026-04-28
---

# Consumer Lag Monitoring

## Summary

Consumer lag is the difference between the log-end offset of a partition and the last committed offset of a consumer group. Monitoring approaches range from CLI tools through client-side JMX, broker-side lag emitters (Confluent Platform), the Confluent Cloud Metrics API, and third-party tools (Burrow, Kafka Lag Exporter). Time-based lag is more actionable than offset-based lag for alerting because it maps directly to SLAs. The `records-lead` metric is an orthogonal data-loss risk indicator.

## Detail

### What Consumer Lag Is

```
lag(partition) = log_end_offset(partition) - committed_offset(consumer_group, partition)
```

Lag is per-partition, per-consumer-group. Aggregate lag is the sum across all assigned partitions.

### Monitoring Approaches

#### CLI: `kafka-consumer-groups.sh --describe`

Point-in-time diagnostic. Queries `__consumer_offsets` and broker metadata. Useful for ad-hoc debugging but not continuous monitoring.

#### Client-Side JMX (Consumer JVM)

MBean: `kafka.consumer:type=consumer-fetch-manager-metrics,client-id="{clientId}",topic="{topic}",partition="{partition}"`

| Attribute | Description |
|-----------|-------------|
| `records-lag` | Current lag for this partition |
| `records-lag-max` | Max lag across all assigned partitions (aggregate MBean) |
| `records-lead` | Distance from log start offset -- data loss risk if near zero |
| `records-lead-min` | Minimum lead observed |

These require JMX access to the consumer's JVM.

#### Broker-Side (Confluent Platform 7.5+)

```properties
confluent.consumer.lag.emitter.enabled=true
confluent.consumer.lag.emitter.interval.ms=30000
```

MBean: `kafka.server:type=tenant-metrics,member={memberId},topic={topicName},consumer-group={groupName},partition={partitionId},client-id={clientId}`

Attribute: `consumer-lag-offsets`. Offset lag only, not latency. Not reported for empty or dead groups.

Do not confuse with `kafka.server:type=FetcherLagMetrics,name=ConsumerLag` -- that is follower replica lag, not consumer application lag.

#### Confluent Cloud Metrics API

Metric: `io.confluent.kafka.server/consumer_lag_offsets`. Minimum 1-minute granularity. No JMX access to brokers.

#### Third-Party Tools

**Burrow** (LinkedIn): Evaluates offset movement patterns over a sliding window (default 10 samples). Statuses: OK, WARNING (advancing but lag growing), ERR/STALLED (no offset movement), ERR/STOPPED (no commits in window).

**Kafka Lag Exporter** (seglo): Estimates time-based lag via offset commit timestamp interpolation. Key metric: `kafka_consumergroup_group_max_lag_seconds`.

### Offset Lag vs. Time-Based Lag

Offset lag is dimensionless without throughput context -- 1M records could mean 10 seconds or 10 hours. Time-based lag maps directly to SLAs: "consumer is 5 minutes behind" is actionable.

### Alert Strategies

Static offset thresholds fail because the same lag means different things at different throughput levels.

**Time-based:** Alert on estimated time lag via Kafka Lag Exporter.

**Rate-of-change:** Alert when lag is growing, not just high:
```promql
rate(kafka_consumergroup_lag[10m]) > 100
```

**Layered alerts (recommended):**

| Severity | Condition |
|----------|-----------|
| WARN | Lag > 50,000 for 10 min AND growing |
| CRIT | Lag > 500,000 for 15 min OR time_lag > 15 min |
| CRIT | `records-lead-min < 1000` (data loss imminent) |
| CRIT | No offset commits in 15 min AND lag > 0 |

### Common Lag Patterns

| Pattern | Shape | Cause |
|---------|-------|-------|
| Rebalance spike | Sawtooth | Processing halts during rebalance |
| Steady-state | Flat, low | Normal periodic commit gap |
| Linear growth | Rising line | Consumers cannot keep up |
| Plateau | Flat, high | Keeping up but never clearing backlog |
| Sudden drop to zero | Step down | Offset reset -- investigate if intentional |
| Periodic spikes | Regular bumps | Batch producers writing in bursts |

## Related

- [Consumer Group Rebalancing](concepts/consumer-group-rebalancing.md) -- rebalances cause lag spikes
- [SLA Tiers](concepts/sla-tiers.md) -- tier-based lag alert thresholds
- [FSI Data Streaming Platform](concepts/fsi-data-streaming-platform.md) -- platform monitoring context
