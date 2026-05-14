---
title: Kafka Connect Deployment Models
tags: [kafka, connect, deployment, fsi, eos, dlq, debezium]
sources: [outputs/reports/confluent-best-practices-quickstart.md]
related: [patterns/dead-letter-queue-design, concepts/exactly-once-semantics, patterns/fsi-governance-automation, patterns/fsi-exactly-once, concepts/schema-registry-best-practices]
confidence: medium
last_updated: 2026-05-13
last_validated: 2026-05-13
---

# Kafka Connect Deployment Models

## Summary

Three Kafka Connect deployment models on Confluent — **fully-managed on CC**, **Custom Connector on CC** (bring-your-own plugin), and **self-managed Connect Distributed**. The FSI default is fully-managed (Canon / memory: vendor consolidation — one contract covers 200+ source/sink connectors). Pick deliberately by combining: does Confluent already manage your source/sink? do you need network/config control? do you need exactly-once source semantics with full operator visibility? Pairs with `patterns/dead-letter-queue-design.md` and `concepts/exactly-once-semantics.md` for the error-handling and EOS surfaces.

## Pattern

### The three models

| Model | You provide | Confluent provides | Use when |
|---|---|---|---|
| **Fully-managed connector on CC** | Connector config only | Connector code, workers, autoscaling, SLA, monitoring | The default for FSI. Use whenever a fully-managed connector exists for your source/sink. |
| **Custom Connector on CC** ("bring your own plugin") | The connector plugin (JAR/zip) | The runtime infrastructure | Confluent doesn't offer a managed connector for your system, but you still want zero-ops runtime. ⚠️ Limitations: plugin size caps, sensitive-config handling, not available on every networking mode/region (historically not on PrivateLink clusters — verify current). |
| **Self-managed Connect** (Connect Distributed against CC or CP Kafka) | Workers (VMs/K8s), plugins, ops | Nothing (it's yours) | You need a connector/SMT Confluent doesn't run, full config control, in-your-network egress, or exactly-once source semantics with full control. See `fsi-dsp:reference/connect-configs/` + `scenarios/cfk-openshift/values/connect.yaml`. ADR-004 documents the on-prem Connect decision. |

### What you own in self-managed Connect

```properties
# Worker identity & internal topics — these MUST be compacted, RF 3:
group.id=fsi-connect-cluster
offset.storage.topic=connect-offsets        offset.storage.replication.factor=3   offset.storage.partitions=25
config.storage.topic=connect-configs        config.storage.replication.factor=3   # config.storage.topic MUST have exactly 1 partition
status.storage.topic=connect-status         status.storage.replication.factor=3   status.storage.partitions=5
# If cleanup.policy on these becomes 'delete', connectors silently lose state.

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

- **`tasks.max`** = `min(source/topic partitions, target parallelism, worker cores available)`. More than the partition count → idle tasks. **Sink connector parallelism is hard-capped by topic partitions** regardless of `tasks.max`.
- **Sink batching** — `consumer.override.max.poll.records`, `consumer.override.fetch.max.bytes`, `batch.size` (JDBC sink), `flush.size` (object-store sinks).
- **Object-store sinks (S3/GCS/ADLS) — the "small files problem".** Low `flush.size` / short `rotate.interval.ms` → millions of tiny objects → slow downstream queries + huge API bills. Target ~128 MB–1 GB files. Set `partitioner.class` (e.g. `TimeBasedPartitioner` + `path.format` + `partition.duration.ms` + `timezone`) for query-friendly layout. **Or skip the connector entirely and use Tableflow** — it solves compaction/small-files/catalog for you.
- **JDBC source** — `mode=timestamp+incrementing` (not `timestamp` alone — clock skew loses rows), `poll.interval.ms`, `batch.max.rows`, `numeric.mapping=best_fit`, `validate.non.null=false` for views.
- **CDC (Debezium)** — `snapshot.mode`, `max.batch.size`, `max.queue.size`, `heartbeat.interval.ms` (**critical on Postgres** — advances replication slot LSN so WAL doesn't grow forever), `publication.autocreate.mode`, `signal.data.collection` for incremental snapshots, `slot.name` management.
- **SMTs run inline on the worker thread.** Heavy SMT chains throttle throughput. Do real transformation in **Flink**, not SMTs — SMTs are for light reshaping (rename, mask, route, add header), not joins/aggregations.

## When to Use

- **Fully-managed CC** — first option for any FSI project. One vendor contract covers the breadth.
- **Custom Connector on CC** — your source/sink is unsupported, but you don't want to run workers. Mind the size/networking limits.
- **Self-managed Connect** — you genuinely need full control (exactly-once source with operator transparency, custom SMTs, in-your-network egress, on-prem source).

### Decision matrix

| Need | Model |
|---|---|
| Source/sink is in Confluent's managed catalog | Fully-managed |
| Source/sink is bespoke, runtime should still be Confluent's | Custom Connector (verify PrivateLink + size + secret-handling) |
| KIP-618 exactly-once source with operator-level transaction control | Self-managed |
| On-prem source where Connect must sit in your network | Self-managed (ADR-004) |
| You can't have any worker ops at all | Fully-managed (and accept the catalog constraint) |

## Caveats

- **Internal topics MUST be compacted, RF 3.** `config.storage.topic` must have exactly 1 partition. If `cleanup.policy` becomes `delete`, connectors silently lose state.
- **DLQ must be configured per connector**, not just per worker — and `errors.deadletterqueue.context.headers.enable=true` so the original topic/partition/offset + exception travel with the bad record.
- **At-least-once by default.** Source connector duplicates downstream unless you enable EOS source (KIP-618) *or* make the consumer idempotent (preferred — outbox/upsert, see `patterns/fsi-exactly-once.md`).
- **Custom Connector on PrivateLink** — historically not supported; ⚠️ verify current support before committing.
- **Sink connector parallelism is hard-capped by topic partitions.** No amount of `tasks.max` fixes an under-partitioned topic.

### Triage

| Symptom | Cause | First moves |
|---|---|---|
| Connector `RUNNING` but a task `FAILED` | Task-level error not surfaced at connector level | `GET /connectors/{n}/status` → read the task trace. |
| Connector "forgets" / replays everything on restart | `connect-offsets` not compacted, or wrong worker `group.id`, or pointed at a different Kafka | Verify internal topics are compacted RF3; verify `group.id`/cluster. |
| Rebalance loops across workers | Worker `group.id` collisions, `session.timeout.ms` too low, slow plugin init | Unique `group.id` per cluster; raise `session.timeout.ms`; check plugin load time. |
| Sink lag growing | Under-tasked, slow target, large records, target throttling | Raise `tasks.max` up to partition count; batch writes; check target. |
| Source connector duplicates downstream | At-least-once by default | Enable EOS source (KIP-618) *or* make the consumer idempotent (outbox/upsert). |
| `ClassNotFoundException` / connector won't load | `plugin.path` wrong, missing JDBC driver, classpath leakage | Fix `plugin.path`; bundle the driver in the plugin dir; don't dump jars on the worker classpath. |
| Garbage in the topic / sink | Converter mismatch (produced Avro, configured `JsonConverter` or vice versa) | Align converters with what's actually on the topic. |
| DLQ filling up | Schema drift, target constraint violations, poison records | Inspect DLQ headers (`errors.deadletterqueue.context.headers.enable=true`). |
| Postgres WAL/disk filling next to a Debezium connector | No heartbeat → replication slot LSN never advances | Set `heartbeat.interval.ms`; monitor `pg_replication_slots`. |

## Related

- [Dead Letter Queue Design](dead-letter-queue-design.md) — DLQ topic design, headers, reprocessing strategies
- [Exactly-Once Semantics](../concepts/exactly-once-semantics.md) — KIP-618 exactly-once source mechanics
- [FSI Governance Automation](fsi-governance-automation.md) — Terraform module for connector deployment
- [FSI Exactly-Once Pattern](fsi-exactly-once.md) — outbox/upsert as the consumer-side EOS answer
- [Schema Registry Best Practices](../concepts/schema-registry-best-practices.md) — converter/SR config
- [Top 20 Confluent Gotchas](../synthesis/confluent-gotchas-top-20.md) — #11, #12, #13 are Connect-related
