---
title: DR — MirrorMaker 2
tags: [kafka mirrormaker2 dr cfk confluent-platform fsi]
sources: [fsi-dsp://adr/005, fsi-dsp://script/mirror-failback]
related: [patterns/dr-cluster-linking, patterns/dr-multi-region-cluster, concepts/sla-tiers, concepts/fsi-data-streaming-platform]
confidence: high
last_updated: 2026-04-11
---

# DR — MirrorMaker 2

## Summary

DR pattern for CFK on OpenShift and Confluent Platform on RHEL deployments using MirrorMaker 2 connectors (MirrorSourceConnector, MirrorCheckpointConnector, MirrorHeartbeatConnector). Simpler failover than Cluster Linking because DR topics are standard writable Kafka topics — no mirror promotion needed. Failback is more complex, requiring connector direction reversal. RPO bounded by async replication lag; failover takes ~3 minutes vs. ~5 minutes for CL.

## Pattern

### Architecture Differences from Cluster Linking

| Aspect | Cluster Linking | MirrorMaker 2 |
|--------|----------------|---------------|
| Replication | Broker-level cluster link | Kafka Connect connectors |
| Mirror promotion | Required (6-step failover) | Not needed (topics already writable) |
| Topic naming on DR | Same name as source | Prefixed: `east.{name}` |
| Failover speed | ~5 min | ~3 min (simpler — no promotion) |
| Consumer offsets | Automatic (same topic name) | Needs translation (MirrorCheckpointConnector) |
| Per-topic lag | `confluent kafka mirror list` | Prometheus/JMX (REST API for connector state only) |
| CLI dependency | `confluent` CLI required | No `confluent` CLI needed (`curl` to Connect REST) |

### Failover

Set `FSI_DR_BACKEND=mm2` for all commands. Execute when primary is confirmed down:

1. Pre-flight checks verify MM2 Connect health (5 checks: Connect reachable, MirrorSource RUNNING, MirrorCheckpoint RUNNING, DR bootstrap reachable, Consul reachable)
2. **Pause MM2 connectors** — Stops replication. DR topics are immediately writable.
3. **Flip Consul** — Set `fsi/kafka/active-region = west`
4. **Verify DNS** — Confirm endpoint resolution to DR region
5. **Resume application connectors** (if applicable)
6. **Validate**

No mirror promotion step. This is the key simplification over Cluster Linking.

### Failback

More complex than CL failback — requires connector direction reversal:

1. **Verify primary** — Confirm East cluster is reachable
2. **Pause application connectors on DR**
3. **Delete existing MM2 connectors** (east→west direction)
4. **Create reversed MM2 connectors** (west→east) — Swap source/target aliases and bootstrap servers
5. **Wait for sync** — Data flows DR → Primary until near-zero lag
6. **Stop reversed connectors, flip Consul** back to primary
7. **Recreate original MM2 connectors** (east→west)
8. **Resume application connectors, validate**

### Consumer Offset Handling

DR consumers read from prefixed topics (`east.corebanking.transactions.v1.account-transaction`). For consumer group offset migration after failover:

- MirrorCheckpointConnector writes translated offsets to `{source-alias}.checkpoints.internal`
- Consumers use `RemoteClusterUtils.translateOffsets()` API to look up correct offsets
- If MirrorCheckpointConnector was not running before failover, consumers must reset offsets to `latest` or a specific timestamp

### Mirror Lag Monitoring

MM2 does not expose per-topic mirror lag via REST API. Three approaches for production monitoring:

1. **Prometheus JMX Exporter** (recommended for CFK): `replication-latency-ms` metric via JMX on MirrorSourceConnector tasks. CFK Connect pods expose JMX on port 7203.
2. **Consumer group lag**: Monitor MM2's internal consumer group lag on the source cluster.
3. **Checkpoint topic**: Query `{source-alias}.checkpoints.internal` on the target cluster.

## When to Use

- CFK on OpenShift deployments (no Cluster Linking available)
- Confluent Platform on RHEL deployments (CL or MM2 available; MM2 when CL is not licensed)
- Environments where simpler failover (no promotion step) is prioritized
- Teams already running Kafka Connect infrastructure

## Caveats

- Topic renaming (`east.{topic}`) complicates consumer configuration and monitoring
- Consumer offset translation requires MirrorCheckpointConnector to have been running; if it wasn't, offsets are lost
- Failback requires connector deletion and recreation — operationally heavier than CL failback
- No per-topic lag via REST API; requires Prometheus/JMX integration for production monitoring
- Task count (`tasks.max`) must be tuned for replication throughput

## Related

- [DR — Cluster Linking](patterns/dr-cluster-linking.md) — alternative for CC deployments
- [DR — Multi-Region Cluster](patterns/dr-multi-region-cluster.md) — RPO=0 on CP
- [SLA Tiers](concepts/sla-tiers.md) — tier-based RPO/RTO targets
