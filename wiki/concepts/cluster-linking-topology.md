---
title: Cluster Linking Topology
tags: [kafka confluent-cloud cluster-linking dr cfk]
sources: []
related: [patterns/dr-cluster-linking, concepts/fsi-data-streaming-platform, concepts/sla-tiers]
confidence: medium
last_updated: 2026-04-11
last_validated: 2026-04-28
---

# Cluster Linking Topology

## Summary

Cluster Linking is a built-in Confluent Server capability that replicates topics between Kafka clusters at the broker level with byte-for-byte, offset-preserving fidelity. Unlike MirrorMaker 2, it requires no intermediate Connect clusters or additional infrastructure. Links are unidirectional; bidirectional replication requires two links. Six topology patterns cover the major use cases: active-passive DR, active-active, hub-and-spoke, mesh, data sharing, and migration.

## Detail

### How It Works

A cluster link is a logical connection from a source cluster to a destination cluster. Source brokers replicate data directly to destination brokers over the Kafka protocol. Mirror topics on the destination land on the same partition at the same offset as the source -- no offset translation required.

Mirror topics are strictly read-only. Any producer attempt to write to a mirror topic fails. A mirror topic must be promoted or failed over before it becomes writable.

### Link Initiation Types

| Type | Description | Minimum Version |
|------|-------------|-----------------|
| Destination-initiated | Destination reaches out to source. Standard approach. | CP 7.0.0 |
| Source-initiated | Source pushes outbound to destination. Required when destination is behind a firewall or private network. | CP 7.1.0 |

Source-initiated links use `connection.mode` (OUTBOUND on source, INBOUND on destination) and `link.mode` (SOURCE / DESTINATION / BIDIRECTIONAL).

### Bidirectional Mode

Bidirectional mode (CP 7.5+, CFK 3.2.0+) enables DR failback operations: `reverse-and-start`, `reverse-and-pause`, and `truncate-and-restore`. Data still flows in one direction per link -- "bidirectional" is a metadata mode that unlocks advanced lifecycle commands.

On Confluent Cloud, bidirectional mode is not supported on Basic or Standard clusters.

### Key Configuration

| Property | Default | Description |
|----------|---------|-------------|
| `auto.create.mirror.topics.enable` | `false` | Auto-create mirrors on destination |
| `auto.create.mirror.topics.filters` | (none) | JSON with INCLUDE/EXCLUDE topic filters |
| `cluster.link.prefix` | `null` | Prefix for mirror topic names (max 12 chars, immutable after creation) |
| `consumer.offset.sync.enable` | `false` | Sync consumer offsets from source |
| `consumer.offset.sync.ms` | `30000` | Offset sync frequency (min 1000ms) |
| `acl.sync.enable` | `false` | Sync ACLs from source (incompatible with `cluster.link.prefix`) |
| `num.cluster.link.fetchers` | `1` | Fetcher threads per link |
| `mirror.start.offset.spec` | `earliest` | Where new mirrors start: `earliest`, `latest`, or ISO 8601 timestamp |

### Topology Patterns

**Active-Passive (DR):** Two clusters; passive receives mirror copies. On active failure, `mirror failover` promotes mirrors on passive. Use bidirectional mode for failback via `truncate-and-restore` and `reverse-and-start`. RPO > 0 (async replication).

**Active-Active:** Multiple regions active simultaneously with producers writing in each region. Each region mirrors the other's topics. Different topics are authoritative in different regions -- no built-in conflict resolution for same-topic writes.

**Hub-and-Spoke:** Spoke clusters replicate to a hub for global analytics and compliance. Default limit of 10 source clusters per hub (contact Confluent Support to raise).

**Mesh:** Full mesh of links between all clusters. Operationally complex; justified only for tier-1 workloads.

**Data Sharing:** Source shares specific topics with a consuming team's destination. Mirror topics provide workload isolation -- consumers cannot impact producer performance on source.

**Migration:** Move topics from old cluster to new. Create mirrors, sync consumer offsets, then `promote` (checks zero lag, final metadata sync) when ready.

### Promote vs. Failover

| Operation | Behavior | Use Case |
|-----------|----------|----------|
| Promote | Checks for zero lag, final offset/config sync, then converts mirror to regular topic | Planned migration |
| Failover | Immediately stops mirroring, converts mirror. No lag check. | DR when source is unavailable |

### Cloud vs. Platform Differences

| Dimension | Confluent Cloud | Confluent Platform |
|-----------|----------------|-------------------|
| Destination cluster | Dedicated or Enterprise only | Any Confluent Server 7.0.0+ |
| Source cluster | Basic, Standard, Dedicated, Enterprise, or any Kafka 3.0+ | Any Confluent Server or Apache Kafka |
| Bidirectional mode | Not on Basic/Standard | CP 7.5+ |
| Management | CLI, Cloud Console, REST API v3 | kafka-cluster-links / kafka-mirrors scripts |

### Limitations

- **Chaining**: Mirror topics can be chained (A->B->C) but not with `auto.create.mirror.topics.enable` + `cluster.link.prefix` simultaneously.
- **Async only**: RPO > 0. No synchronous replication.
- **No repartitioning**: Partition counts and topic names are preserved exactly during mirroring.
- **Schema Linking is separate**: Cluster Linking replicates topic data/metadata. Schemas require separate Schema Linking configuration.
- **Transactional semantics**: Transactional messages are replicated but cross-topic atomicity is not preserved on the mirror side.

### CFK ClusterLink CRD

CFK reconciles ClusterLink CRs every 300 seconds (configurable via annotation). Mirror topics created outside CFK are deleted on the next reconciliation cycle -- CFK enforces declarative state. When a ClusterLink CR is deleted, all mirror topics are automatically failed over and corresponding KafkaTopic CRs are created.

### Version Requirements Summary

| Feature | Minimum Version |
|---------|----------------|
| Cluster Linking (GA) | CP 7.0.0 |
| Source-initiated links | CP 7.1.0 |
| Bidirectional mode | CP 7.5.0 |
| CFK bidirectional | CFK 3.2.0 + CP 7.5.0 |

## Related

- [DR -- Cluster Linking](patterns/dr-cluster-linking.md) -- FSI DR pattern using CL
- [FSI Data Streaming Platform](concepts/fsi-data-streaming-platform.md) -- platform context
- [SLA Tiers](concepts/sla-tiers.md) -- RPO/RTO targets per tier
