---
title: Kafka Streams Config Baseline
tags: [kafka-streams, configuration, tuning, fsi, confluent-agent-skills]
sources: [raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/config-baseline.md]
related: [patterns/producer-config-fsi, patterns/consumer-config-fsi, concepts/kafka-streams-architecture, concepts/kafka-streams-production-hardening, concepts/exactly-once-semantics, concepts/warpstream-config-overrides]
confidence: high
last_updated: 2026-05-16
last_validated: 2026-05-16
source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4
upstream_path: skills/kafka-streams-programming/references/config-baseline.md
---

# Kafka Streams Config Baseline

## Summary

Canonical configuration baseline for new Kafka Streams (KS) applications. Every generated app starts with this set; pattern-specific overrides (EOS, stateful tuning, WarpStream) layer on top. Covers core properties (identity, serdes, rebalance protocol, error handling), the four security patterns (SASL_SSL/PLAIN, SCRAM, mTLS, OAUTHBEARER), per-environment specifics (AK/CP/CC/WarpStream), default-serde selection, topic-management rules, and exactly-once configuration.

Sourced from `confluentinc/agent-skills@91d1871e` (Apache-2.0) — upstream maintains an eval gate at 90%+ pass before merge, so this article is `confidence: high` via source attestation rather than per-claim MCP re-validation. Trip-wire micro-articles in `wiki/concepts/` carry full MCP validation.

## Detail

### Core properties

```properties
# Application identity
application.id=<user-provided-or-generated>
client.id=<application.id>

# Cluster connection
bootstrap.servers=<from-user>

# Schema Registry
schema.registry.url=<from-user>
auto.register.schemas=true   # Set to false in production

# Default serdes — required for internal topics (repartition, changelog)
default.key.serde=org.apache.kafka.common.serialization.Serdes$StringSerde
# Default value serde — use the Confluent Schema Registry serde matching the user's schema format:
#   Avro:        io.confluent.kafka.streams.serdes.avro.SpecificAvroSerde
#   Protobuf:    io.confluent.kafka.streams.serdes.protobuf.KafkaProtobufSerde
#   JSON Schema: io.confluent.kafka.streams.serdes.json.KafkaJsonSchemaSerde
default.value.serde=<set-based-on-schema-format>

# Rebalance protocol (KIP-1071) — requires AK 4.2+/CP 8.2+.
# CC rollback: comment out to fall back to classic protocol.
# Standby/warm-up replicas and static membership REQUIRE the classic protocol.
group.protocol=streams

# Explicit naming — prevents state loss on topology changes
ensure.explicit.internal.resource.naming=true

# Error handling
default.deserialization.exception.handler=org.apache.kafka.streams.errors.LogAndContinueExceptionHandler
production.exception.handler=org.apache.kafka.streams.errors.DefaultProductionExceptionHandler
task.timeout.ms=300000

# Producer defaults (acks=all is the default since KS 3.0)
compression.type=lz4

# Monitoring
metrics.recording.level=INFO

# Recommended starting defaults
num.stream.threads=1            # Scale based on throughput needs
commit.interval.ms=30000        # 30 s default for at-least-once
# IMPORTANT: Do NOT set commit.interval.ms for exactly_once_v2 apps.
# EOS defaults to 100 ms internally and relies on this for correctness — OMIT the line entirely.
```

### Security patterns

#### SASL_SSL with PLAIN (CC always, AK/CP optional)

```properties
security.protocol=SASL_SSL
sasl.mechanism=PLAIN
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required \
  username='<KEY>' password='<SECRET>';
```

#### SASL_SSL with SCRAM-SHA-256

```properties
security.protocol=SASL_SSL
sasl.mechanism=SCRAM-SHA-256
sasl.jaas.config=org.apache.kafka.common.security.scram.ScramLoginModule required \
  username='<USER>' password='<PASSWORD>';
```

#### mTLS

```properties
security.protocol=SSL
ssl.keystore.location=/path/to/client.keystore.jks
ssl.keystore.password=<password>
ssl.key.password=<password>
ssl.truststore.location=/path/to/client.truststore.jks
ssl.truststore.password=<password>
```

mTLS + RBAC is the canonical FSI posture — never username/password in regulated environments.

#### OAUTHBEARER (CP RBAC/MDS)

```properties
security.protocol=SASL_SSL
sasl.mechanism=OAUTHBEARER
sasl.login.callback.handler.class=io.confluent.kafka.clients.plugins.auth.token.TokenUserLoginCallbackHandler
sasl.jaas.config=org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required \
  username='<USER>' password='<PASSWORD>' metadataServerUrls='<MDS_URL>';
```

#### SR Basic Auth

```properties
basic.auth.credentials.source=USER_INFO
basic.auth.user.info=<SR_KEY>:<SR_SECRET>
```

Manual serde configuration (pass SR auth to `.configure()`):

```java
Map<String, String> srConfig = Map.of(
    "schema.registry.url", srUrl,
    "basic.auth.credentials.source", "USER_INFO",
    "basic.auth.user.info", srKey + ":" + srSecret);
serde.configure(srConfig, false);
```

### Environment-specific configuration

| Env | Connection | Schema Registry | CLI |
|---|---|---|---|
| Apache Kafka (open source) | PLAINTEXT, optional SASL_SSL/mTLS | `http://localhost:8081` (no auth default) | `kafka-topics.sh`, etc. |
| Confluent Platform (self-managed) | PLAINTEXT (dev) or SASL_SSL/SCRAM/mTLS/OAUTHBEARER (prod) | `http://localhost:8081`, basic auth or RBAC token | `$CONFLUENT_HOME/bin/` |
| Confluent Cloud (managed) | SASL_SSL + PLAIN (always) | Basic auth (always) | `confluent` CLI |
| WarpStream | SASL_SSL + PLAIN or PLAINTEXT | Separate SR service | Standard Kafka CLI + `warpstream` CLI |

**Confluent Cloud:**

```properties
bootstrap.servers=<pkc-xxxxx.region.provider.confluent.cloud:9092>
# + SASL_SSL PLAIN
schema.registry.url=<https://psrc-xxxxx.region.provider.confluent.cloud>
# + SR basic auth
```

**WarpStream-specific overrides (layered on core properties):**

```properties
bootstrap.servers=<warpstream-agent-endpoint:9092>

# Disable idempotence for better WarpStream throughput.
# EOS (exactly_once_v2) enables idempotence internally — see warpstream-optimization.
producer.enable.idempotence=false
producer.max.in.flight.requests.per.connection=1000

# Larger batches amortize object-storage write latency
producer.batch.size=100000
producer.linger.ms=100
producer.buffer.memory=128000000
producer.max.request.size=64000000
producer.request.timeout.ms=30000

# Large fetch sizes — WarpStream appears as a single broker
consumer.fetch.max.bytes=50242880
consumer.max.partition.fetch.bytes=50242880
consumer.fetch.max.wait.ms=10000
# Do NOT set consumer.fetch.min.bytes — unsupported by WarpStream

# Reduce metadata refresh frequency
metadata.max.age.ms=60000

# Zone-aware routing to avoid cross-AZ costs
client.id=<application.id>,ws_az=<availability-zone>
```

See [WarpStream Config Overrides](warpstream-config-overrides.md) for the trip-wire on which standard Kafka knobs WarpStream silently ignores (`fetch.min.bytes`, `replication.factor`).

### Default serde selection

| Schema format | Default value serde | Dependency |
|---|---|---|
| Avro | `io.confluent.kafka.streams.serdes.avro.SpecificAvroSerde` | `kafka-streams-avro-serde` |
| Protobuf | `io.confluent.kafka.streams.serdes.protobuf.KafkaProtobufSerde` | `kafka-streams-protobuf-serde` |
| JSON Schema | `io.confluent.kafka.streams.serdes.json.KafkaJsonSchemaSerde` | `kafka-streams-json-schema-serde` |

Default key serde is `Serdes.StringSerde` unless the user has non-String keys.

### Topic management rules

- **Source topics:** user-managed; must exist before app start.
- **Changelog topics:** auto-created by KS; `compact` for non-windowed, `compact,delete` for windowed.
- **Repartition topics:** auto-created with infinite retention. **Don't set retention — causes data loss.**
- **Output topics:** pre-create before deploying to production.
- **DLQ topics** (KIP-1034): pre-create; named `<application.id>-<source-topic>-dlq`.

Production clusters typically have `auto.create.topics.enable=false` (CC always does). Source, output, DLQ topics must be created manually. Changelog and repartition topics still auto-create via the admin client.

### Monitoring

```properties
# Key metrics:
# - kafka.streams:type=stream-metrics,client-id=*
#     alive-stream-threads (should equal num.stream.threads)
#     failed-stream-threads (should be 0)
# - kafka.streams:type=stream-thread-metrics,thread-id=*
#     process-rate, commit-rate
# - kafka.streams:type=stream-task-metrics,thread-id=*,task-id=*
#     active-process-ratio (target > 0.5)
# - Stateful apps also monitor:
#     kafka.streams:type=stream-state-metrics: store operation latency
#     org.rocksdb:type=statistics: SST file sizes, compaction stats
```

Expose via JMX for Prometheus/Grafana.

### EOS configuration

> **WarpStream:** EOS (`exactly_once_v2`) has measurable throughput cost on WarpStream. It enables idempotent producers internally, capping in-flight requests at 5. Combined with WarpStream's higher produce latency, this reduces throughput and may produce `KAFKA_STORAGE_ERROR` retries. Prefer `at_least_once` with downstream deduplication when possible. See [exactly_once_v2 WarpStream throughput cost](exactly-once-v2-warpstream-throughput-cost.md).

Required:

```properties
processing.guarantee=exactly_once_v2   # NEVER exactly_once (v1 deprecated)
```

Do NOT set:

```properties
# commit.interval.ms — EOS overrides to 100 ms internally for correctness. OMIT entirely.
```

Transaction timeout:

```properties
# Default 10 s. Common values:
#   60 s   — most stateful apps
#   300 s  — slow lookups or large state
#   900 s  — extreme cases
transaction.timeout.ms=60000
```

Properties EOS enforces automatically (do not override):

| Property | Enforced | Why |
|---|---|---|
| `acks` | `all` | All ISR replicas must ack |
| `enable.idempotence` | `true` | Required for transactional producers |
| `retries` | `2147483647` | Transactional producers retry indefinitely |
| `max.in.flight.requests.per.connection` | `5` | Max allowed for idempotent producers |

EOS + resilience:

```properties
num.standby.replicas=1
replication.factor=3
consumer.max.poll.interval.ms=600000
consumer.session.timeout.ms=45000
```

EOS checklist:

1. `processing.guarantee=exactly_once_v2` (not v1).
2. `commit.interval.ms` is NOT set.
3. `transaction.timeout.ms` ≥ worst-case processing time.
4. `num.standby.replicas=1` for resilience.
5. `replication.factor=3` for internal topics.
6. Downstream consumers use `isolation.level=read_committed`.
7. Broker: `transaction.state.log.replication.factor=3`, `min.isr=2`.
8. On CC: app runs at least once per 7 days (transactional ID expiry).
9. `consumer.max.poll.interval.ms ≥ transaction.timeout.ms`.

### Performance tuning — high-impact parameters

> **WarpStream:** The defaults below are for standard Kafka. WarpStream requires significantly larger batches, higher linger, and larger fetch sizes — see the WarpStream environment section above and [WarpStream Config Overrides](warpstream-config-overrides.md).

| Parameter | Default | Tuning |
|---|---|---|
| `producer.batch.size` | 16384 | Strong + throughput correlation. Increase for high-volume. |
| `producer.linger.ms` | 0 | Moderate + throughput. 5-50 ms to allow batching. |
| `consumer.fetch.min.bytes` | 1 | Moderate + throughput at cost of latency. |
| `consumer.max.poll.records` | 500 | Tune to control processing time per poll. |
| `commit.interval.ms` | 30000 | At-least-once only. Larger = more reprocessing on failure. |
| `cache.max.bytes.buffering` | 10485760 | Increasing reduces writes to state stores and changelog. |
| `num.stream.threads` | 1 | ≤ CPU cores; max useful = `input partitions / instances`. |
| `producer.compression.type` | none | `lz4` or `snappy` reduces network bandwidth. |

### RocksDB tuning for stateful apps

```java
public class TunedRocksDBConfig implements RocksDBConfigSetter {
    @Override
    public void setConfig(String storeName, Options options, Map<String, Object> configs) {
        options.setCompactionStyle(CompactionStyle.UNIVERSAL);          // write-heavy
        options.setWriteBufferSize(64 * 1024 * 1024L);                  // 64 MB (default 16 MB)
        options.setMaxWriteBufferNumber(4);                              // default 3
        options.setMaxBackgroundJobs(4);                                 // default 2
        options.setCompressionType(CompressionType.LZ4_COMPRESSION);
    }
    @Override
    public void close(String storeName, Options options) {}
}
```

**`BoundedMemoryRocksDBConfig`** — when you have many stores, the default per-store allocation (~98 MB each) adds up. Share a single block cache across all stores:

```properties
rocksdb.config.setter=org.apache.kafka.streams.state.internals.BoundedMemoryRocksDBConfig
rocksdb.block.cache.size=536870912    # 512 MB total, shared
rocksdb.write.buffer.size=16777216    # 16 MB per write buffer
rocksdb.max.write.buffers=2           # 2 buffers per store (default 3 — lower = less memory)
```

State-restoration tuning:

```properties
restore.consumer.fetch.max.bytes=52428800              # 50 MB
restore.consumer.max.partition.fetch.bytes=10485760    # 10 MB
```

## Related

- [Kafka Streams Architecture](kafka-streams-architecture.md) — runtime model that informs config choices
- [Kafka Streams Production Hardening](kafka-streams-production-hardening.md) — error handlers, health checks, JVM options
- [FSI Producer Configuration](../patterns/producer-config-fsi.md) — paired producer-side baseline
- [FSI Consumer Configuration](../patterns/consumer-config-fsi.md) — paired consumer-side baseline
- [Exactly-Once Semantics](exactly-once-semantics.md) — EOS foundations
- [WarpStream Config Overrides](warpstream-config-overrides.md) — silently-ignored knobs on WarpStream

---

*Source: confluentinc/agent-skills@91d1871e · skills/kafka-streams-programming/references/config-baseline.md · Ingested 2026-05-16 · Apache-2.0*
