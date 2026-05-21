---
title: Kafka Connect Deployment Models
tags: [kafka, connect, deployment, architecture, confluent-cloud, confluent-platform]
sources: [outputs/reports/confluent-best-practices-quickstart.md]
related: [patterns/connect-deployment-models, patterns/dead-letter-queue-design, concepts/exactly-once-semantics, concepts/schema-registry-best-practices, concepts/cdc-source-connector-setup, concepts/network-connectivity-by-tier]
confidence: medium
last_updated: 2026-05-18
last_validated: 2026-05-18
---

# Kafka Connect Deployment Models

## Summary

Kafka Connect is the integration framework that moves data between Kafka and external systems through reusable connector plugins. Architecturally it is a separate JVM process model — a *worker* — that hosts *connector* instances, each of which is broken into a configurable number of *tasks* that do the per-partition I/O. There are two foundational runtime modes in OSS Apache Kafka (standalone, distributed) and three Confluent-specific deployment models that wrap distributed mode with progressively less operator surface: fully-managed connectors on Confluent Cloud, Custom Connector on CC (bring-your-own-plugin), and self-managed Connect Distributed. The operational decision matrix lives in `patterns/connect-deployment-models.md`; this article covers what each model *is* at the architecture level so the decision makes sense.

## Detail

### What Kafka Connect is

Connect is a framework, not a runtime. The framework gives you:

- A **plugin model** — connectors are JARs that implement either a `SourceConnector` or `SinkConnector` interface plus matching `SourceTask` / `SinkTask` interfaces.
- A **task model** — the framework partitions the connector's work into N tasks based on the connector's own `taskConfigs(maxTasks)` method. For source connectors N is bounded by the producer side (often partitions of the source system, e.g., database tables or partitions); for sink connectors N is hard-capped by the topic partition count regardless of `tasks.max` (sink tasks consume from a single consumer group, one task per partition is the upper bound).
- A **converter pipeline** — bytes-on-the-wire ↔ Connect's internal `SchemaAndValue` ↔ external system. `key.converter` and `value.converter` are configured at the worker level (and overridable per connector) and decide whether records on Kafka are Avro, Protobuf, JSON Schema, raw JSON, or strings.
- **Single Message Transforms (SMTs)** — lightweight per-record functions chained between the source task and the converter (or after the converter for sinks). SMTs run inline on the task thread; heavy transformation belongs in Flink, not SMTs.
- A **REST API** for connector lifecycle (`POST /connectors`, `GET /connectors/{n}/status`, `PUT /connectors/{n}/config`, etc.). The REST API is the only supported control plane in distributed mode.
- A **rebalance protocol** for task assignment across workers. Since Apache Kafka 2.3, Connect uses *incremental cooperative rebalancing* (KIP-415) — only the affected tasks stop on a rebalance, the rest keep running. Worker config: `connect.protocol=sessioned` (default since 2.3).

### Standalone vs distributed: the OSS-level concept

OSS Kafka Connect ships two runtime modes, and every Confluent deployment model is a flavor of one of them.

| Mode | What runs | Where state lives | Use case |
|---|---|---|---|
| **Standalone** | A single Connect worker process | Offsets and config in **local files** on disk (`offset.storage.file.filename`) | Development, single-host edge collection, throwaway ingest. Not fault-tolerant — losing the host loses the state. |
| **Distributed** | A cluster of Connect workers sharing one `group.id` | Offsets, configs, and statuses in **internal Kafka topics** (`offset.storage.topic`, `config.storage.topic`, `status.storage.topic`), all of which must be compacted with RF 3 | Every production deployment. Workers form a group, the framework distributes tasks, the REST API is uniform across workers. |

All Confluent deployment models below are distributed mode. Standalone exists in the OSS framework but is not a production option.

### The three internal topics (distributed mode invariant)

Distributed mode persists all framework state into Kafka itself, which is why these topics are non-optional and why their settings are load-bearing:

- **`offset.storage.topic`** — source connector progress (the offsets the framework writes back so a source task can resume from where it left off). Compacted; recommended ~25 partitions; RF 3.
- **`config.storage.topic`** — connector configs and target task counts. **Exactly 1 partition** (the framework relies on single-partition ordering); compacted; RF 3.
- **`status.storage.topic`** — connector/task status events surfaced through the REST API. Compacted; small (~5 partitions); RF 3.

If `cleanup.policy` on any of these accidentally becomes `delete`, connectors silently lose state on restart — the workers can't recover prior offsets or configs from the topic.

### The three Confluent deployment models

Distributed mode is the foundation; the three Confluent options differ in *who runs the workers* and *who controls the plugin set*.

| Model | Who owns the workers | Who owns the plugin | Control surface |
|---|---|---|---|
| **Fully-managed connector on CC** | Confluent | Confluent (catalog of ~200+ connectors) | Connector config only, via CC API/UI/Terraform. No worker config. No `tasks.max` tuning beyond a published per-connector ceiling. |
| **Custom Connector on CC** (BYO plugin) | Confluent | You (upload a plugin JAR/zip) | Connector config + plugin upload. No worker config. Subject to plugin size caps, sensitive-config rules, and historically limited networking modes (e.g., PrivateLink support varies; > ⚠️ unverified — confirm current CC Custom Connector + PrivateLink support before committing). |
| **Self-managed Connect Distributed** | You (VMs / Kubernetes / CFK) | You (any plugin you can install on `plugin.path`) | Everything — worker config, internal topics, converters, SMT chains, REST API exposure, security, monitoring. The full OSS surface. |

The FSI default is fully-managed: vendor consolidation via one Confluent contract covers the breadth of source/sink connectors (the [FSI vendor-backing rule](../patterns/fsi-canon-overlay-for-confluent-skills.md) treats this as a strict policy, not a preference). Custom Connector is the "no fully-managed match exists but I still don't want to run workers" middle ground. Self-managed is the escape hatch when you need full control — usually for KIP-618 exactly-once source semantics with operator transparency, custom SMTs, in-your-network egress, or an on-prem source where the worker must sit next to the source system.

### Converter pipeline (architectural detail)

A source task emits a `SourceRecord` carrying an internal `Schema` and a value. The configured `value.converter` (and `key.converter`) serialize that to bytes for the producer. A sink task receives `SinkRecord` instances after the configured converter deserializes from the topic. The converter is the seam to **Schema Registry**: `io.confluent.connect.avro.AvroConverter`, `io.confluent.connect.protobuf.ProtobufConverter`, and `io.confluent.connect.json.JsonSchemaConverter` all integrate with SR via `value.converter.schema.registry.url`. The framework itself is schema-aware (so SMTs can reason about field names and types), but it is the converter that decides whether records hit the wire as Avro+SR or raw JSON.

Mismatch is silent: if a topic was produced with Avro but a sink is configured `value.converter=org.apache.kafka.connect.json.JsonConverter`, the sink task fails to deserialize and either errors out or fills the DLQ depending on `errors.tolerance`.

### Exactly-once source (KIP-618) at the concept level

Source connectors are at-least-once by default — the framework commits source-system offsets back to `offset.storage.topic` *after* the producer publishes, so a worker crash between the publish and the offset commit can replay records. KIP-618 (Apache Kafka 3.3+) adds exactly-once *source* semantics by giving each source task a transactional producer plus a configurable transaction boundary, so the produce-and-commit-offset becomes a single atomic Kafka transaction.

Three things make this material at the architecture level:

1. **It requires self-managed Connect.** CC fully-managed connectors do not expose `exactly.once.source.support` — the worker-level toggle and per-connector `transaction.boundary` are operator-controlled knobs.
2. **It only covers the produce side.** Sink connectors have always been exactly-once-capable through the source's offset commit + idempotent consumer pattern; EOS source closes the gap between source-system extraction and the Kafka topic.
3. **It is Kafka-internal scope.** The transactional guarantee ends at the Kafka topic; downstream consumer idempotency (outbox, upsert) is still your problem. See `concepts/exactly-once-semantics.md` for the broader EOS surface.

### Source vs sink connector lifecycle

Source and sink connectors look symmetric in the framework but their failure modes differ.

- **Source connector**: framework polls the source system → emits records → producer publishes → framework commits source offset. Failure between publish and offset commit replays. Source-specific configs: `poll.interval.ms`, `batch.max.rows` (JDBC), `snapshot.mode` (Debezium), `heartbeat.interval.ms` (Postgres CDC — critical, the replication slot LSN doesn't advance without it).
- **Sink connector**: framework subscribes to topic via consumer group → batches records → calls `put(records)` on the sink task → on success, framework commits the consumer offset. Failure during `put()` replays the same batch. Sink-specific configs: `consumer.override.max.poll.records`, `flush.size` (object-store sinks), `batch.size` (JDBC sink).

The sink consumer group is owned by the framework, identified as `connect-<connector-name>`. You do not get to share it across connectors, but you can override `consumer.override.*` per connector to tune fetch behavior.

### When the framework choice matters

Most Connect work — and most FSI Connect work — fits comfortably in fully-managed. The deployment-model decision becomes load-bearing in three cases:

1. **No managed match** — your source/sink isn't in the CC catalog and isn't covered by Custom Connector's runtime constraints. Self-managed is the only option.
2. **EOS source matters at the framework boundary** — you can't accept downstream-side idempotency as the answer (regulatory replay constraints, ledgers, audit). KIP-618 source EOS only ships in self-managed today.
3. **Network locality** — the source must sit inside your VPC/on-prem network and the connector can't reach it from CC, *or* PrivateLink limits on Custom Connector are blocking. Self-managed Connect deployed close to the source is the canonical answer.

Otherwise: fully-managed first, Custom Connector second, self-managed only when forced.

## Related

- [Kafka Connect Deployment Models — Pattern](../patterns/connect-deployment-models.md) — operational decision matrix, performance tuning, EOS configuration, triage table
- [Dead Letter Queue Design](../patterns/dead-letter-queue-design.md) — DLQ topic design and `errors.deadletterqueue.*` configuration
- [Exactly-Once Semantics](exactly-once-semantics.md) — KIP-618 source mechanics, broader EOS surface
- [Schema Registry Best Practices](schema-registry-best-practices.md) — converter/SR integration
- [CDC Source Connector Setup](cdc-source-connector-setup.md) — connector-specific configuration for the major CDC sources
- [Network Connectivity by Cluster Tier](network-connectivity-by-tier.md) — Custom Connector + PrivateLink interactions
- [FSI Canon Overlay for Confluent Agent Skills](../patterns/fsi-canon-overlay-for-confluent-skills.md) — vendor-consolidation rule that drives the FSI fully-managed default
