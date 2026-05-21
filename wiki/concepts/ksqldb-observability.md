---
title: ksqlDB Observability — CC and Self-Managed
tags: [observability ksqldb jmx mbean confluent-cloud confluent-platform cfk metrics-api kafka-streams fsi]
sources:
  - https://docs.confluent.io/cloud/current/monitoring/metrics-api.html
  - https://docs.confluent.io/platform/current/ksqldb/operate-and-deploy/monitoring.html
  - https://docs.confluent.io/platform/current/streams/monitoring.html
related:
  - concepts/observability-metrics-mapping
  - concepts/fsi-data-streaming-platform
  - concepts/consumer-lag-monitoring
  - concepts/kafka-streams-architecture
  - concepts/kafka-streams-debugging
  - patterns/dead-letter-queue-design
  - concepts/sla-tiers
confidence: medium
last_updated: 2026-05-20
last_validated: 2026-05-20
---

# ksqlDB Observability — CC and Self-Managed

## Summary

ksqlDB is a SQL streaming engine that compiles statements to Kafka Streams topologies and runs them inside a long-lived JVM (the ksqlDB server). The observability story therefore has two layers: ksqlDB-specific metrics (query state, restart counts, push/pull query latency, CFU-like compute units on CC) and the underlying Kafka Streams runtime metrics (thread state, RocksDB state stores, commit-and-flush cycle). CC managed ksqlDB exposes a focused set through the Metrics API under `io.confluent.kafka.ksql/*` (MCP-confirmed 2026-05-20); self-managed ksqlDB on CP/CFK exposes the richer JMX MBean tree under `io.confluent.ksql.metrics:*` plus the standard `kafka.streams:*` tree. This article documents both, the deployment-model gap, and the alert patterns aligned to FSI tiers.

## Detail

### Confluent Cloud — Metrics API surface

CC ksqlDB exposes 10 metrics through the Metrics API (MCP-confirmed 2026-05-20):

| CC Metric | Type | What it measures |
|---|---|---|
| `io.confluent.kafka.ksql/committed_offset_lag` | Gauge | How far behind the source topic the ksqlDB persistent query is — the primary freshness signal |
| `io.confluent.kafka.ksql/consumed_total_bytes` | Counter | Cumulative bytes read from upstream topics |
| `io.confluent.kafka.ksql/offsets_processed_total` | Counter | Cumulative offsets advanced — pair with `offset_lag` for catch-up rate |
| `io.confluent.kafka.ksql/processing_errors_total` | Counter | Cumulative errors during record processing (deserialization, SQL eval, sink write) |
| `io.confluent.kafka.ksql/produced_total_bytes` | Counter | Cumulative bytes written to sink topics |
| `io.confluent.kafka.ksql/query_restarts` | Counter | Persistent query restart count — stability indicator |
| `io.confluent.kafka.ksql/query_saturation` | Gauge | Fraction of compute capacity in use (0.0 = idle, 1.0 = saturated) |
| `io.confluent.kafka.ksql/storage_utilization` | Gauge | Fraction of state-store storage in use |
| `io.confluent.kafka.ksql/streaming_unit_count` | Gauge | Current CSU (Confluent Streaming Unit) allocation |
| `io.confluent.kafka.ksql/task_stored_bytes` | Gauge | State-store bytes on disk per task |

Group by `resource.ksql.id` (cluster), `query_id` (per-query), or `task_id` (per-task) as supported. See [Observability Metrics Mapping](observability-metrics-mapping.md) for cross-provider query syntax.

### Self-managed CP / CFK — ksqlDB-specific JMX

ksqlDB-specific MBeans live under `io.confluent.ksql.metrics:type=*`. The server JMX port defaults to the value set in `KSQL_JMX_OPTS` — typically `9999` for CP, configurable per deployment.

| MBean (ksqlDB-specific) | What it measures |
|---|---|
| `io.confluent.ksql.metrics:type=ksql-engine,*` | Engine-level: active persistent queries, num-active-queries, num-persistent-queries, error-queries |
| `io.confluent.ksql.metrics:type=_confluent-ksql-default_query_<id>,*` | Per-query: messages-consumed-per-sec, messages-produced-per-sec, messages-consumed-total, error-rate, query-status |
| `io.confluent.ksql.metrics:type=ksql-queries,*` | Aggregate query metrics — running-queries, rebalancing-queries, failed-queries |
| `io.confluent.ksql.metrics:type=pull-queries,*` | Pull-query (interactive) latency, request rate |
| `io.confluent.ksql.metrics:type=push-queries,*` | Push-query subscriber count, byte throughput |

> ⚠️ unverified — the exact attribute names per MBean (e.g., `num-active-queries` vs `running-queries`) were not fully surfaced in the 2026-05-20 MCP fetch of `platform/current/ksqldb/operate-and-deploy/monitoring.html` (the page references the underlying Kafka Streams metrics doc rather than exhaustively enumerating ksqlDB-specific attributes). Validate against your CP release's ksqlDB JMX tree with `jconsole` before authoring production alert rules.

### Self-managed — the Kafka Streams runtime underneath

Because each ksqlDB persistent query compiles to a Kafka Streams topology, every Streams MBean applies as well. See [Kafka Streams Architecture](kafka-streams-architecture.md) for the threading model. The full `kafka.streams:type=*` namespace:

| MBean | What it measures |
|---|---|
| `kafka.streams:type=stream-metrics,client-id=*` | Top-level client state: state, alive-stream-threads, version |
| `kafka.streams:type=stream-thread-metrics,thread-id=*` | Per-StreamThread: poll-latency-avg, process-latency-avg, commit-latency-avg, punctuate-latency-avg, blocked-time-ns-total, thread-start-time |
| `kafka.streams:type=stream-task-metrics,thread-id=*,task-id=*` | Per-task: process-rate, process-latency-avg, commit-rate, dropped-records-rate, active-process-ratio |
| `kafka.streams:type=stream-processor-node-metrics,thread-id=*,task-id=*,processor-node-id=*` | Per-operator: process-rate, suppression-emit-rate, late-record-drop-rate |
| `kafka.streams:type=stream-state-metrics,thread-id=*,task-id=*,store-id=*` | Per-store: put-rate, fetch-rate, restore-rate, suppression-buffer-* |
| `kafka.streams:type=stream-record-cache-metrics,thread-id=*,task-id=*,record-cache-id=*` | Cache hit-ratio, eviction-rate |

These are particularly useful for diagnosing stuck ksqlDB queries — high `blocked-time-ns-total`, high `late-record-drop-rate`, or a `dropped-records-rate > 0` on a query that should have headroom all point at execution-side problems the ksqlDB-level metrics won't surface cleanly.

### Deployment-model coverage gap

| Diagnostic question | Self-managed (JMX + Streams) | CC managed |
|---|---|---|
| "Is the query up?" | `ksql-engine.num-active-queries` + per-query `query-status` | `query_restarts` counter + `streaming_unit_count` > 0 |
| "Is it falling behind?" | Per-query `messages-consumed-per-sec` vs upstream `MessagesInPerSec` (broker) | `committed_offset_lag` |
| "Are there errors?" | Per-query `error-rate` + Streams `dropped-records-rate` | `processing_errors_total` (cumulative; wrap in rate) |
| "Why did it restart?" | Streams `state` transitions + ksqlDB server logs | `query_restarts` counter (gives count, not cause) |
| "Is state-store IO healthy?" | `stream-state-metrics.{put-rate, fetch-rate, restore-rate}` | `task_stored_bytes` + `storage_utilization` — capacity only, not IO patterns |
| "Are pull queries slow?" | `pull-queries.request-latency-avg` | Not directly exposed |
| "Are push queries flooded?" | `push-queries.subscriber-count` + Streams `late-record-drop-rate` | Not directly exposed |

CC managed gives you the dashboard-level health view; deeper diagnostics (per-operator profiling, state-store IO patterns, pull-query latency tracking) require self-managed JMX. For FSI tenants where ksqlDB is in a regulated workflow, this asymmetry argues for self-managed on CP/CFK in DR-tier deployments.

### Alert patterns (per SLA tier)

| Signal | Critical | Standard | Best-effort |
|---|---|---|---|
| `query_restarts` rate > 0 sustained 10 min | P2 | P2 | P3 |
| `committed_offset_lag` (CC) or per-query `messages-behind` (self-managed) | tier-aware: critical < 1k, standard < 10k, best-effort < 100k records | | |
| `processing_errors_total` rate > 0 sustained 5 min | P2 | P2 | P3 |
| `query_saturation` > 0.85 sustained 15 min (CC) | P2 (scale CSUs) | P3 | informational |
| `storage_utilization` > 0.80 (CC) or per-task disk usage % (self-managed) | P2 (state-store bloat) | P2 | P3 |
| `pull-queries.request-latency-avg` p99 > 500 ms (self-managed only) | P2 | P3 | informational |
| Streams `dropped-records-rate > 0` (self-managed only) | P2 (likely DLQ-worthy) | P2 | P3 |

See [SLA Tiers](sla-tiers.md) for tier definitions. Pair restart-rate alerts with log ingestion (Splunk / Loki) for root-cause context — restart count alone doesn't tell you which deserialization or sink-write triggered it.

### Error handling and DLQ routing

ksqlDB processing errors fall into three buckets, each with a different observability surface:

1. **Deserialization errors** (bad upstream record) — surfaced as `processing_errors_total` (CC) / `dropped-records-rate` (Streams JMX). Route to DLQ via `processing.guarantee` + `default.deserialization.exception.handler` config. See [Dead Letter Queue Design](../patterns/dead-letter-queue-design.md).
2. **SQL evaluation errors** (NULL handling, divide-by-zero, type cast failure) — surfaced as `error-rate` on per-query JMX. Handle in SQL with explicit `WHERE … IS NOT NULL` / `CASE WHEN` guards rather than dropping at runtime.
3. **Sink write errors** (downstream topic unavailable) — surfaced as Streams `producer-record-error-rate`. Pair with the producer's [FSI canon](../patterns/producer-config-fsi.md) (`acks=all`, `enable.idempotence=true`) for reliability.

### Where this article does not cover

- ksqlDB query authoring patterns (SQL-level — see ksqlDB tutorials)
- Kafka Streams runtime details ([Kafka Streams Architecture](kafka-streams-architecture.md), [Production Hardening](kafka-streams-production-hardening.md), [Debugging](kafka-streams-debugging.md))
- ksqlDB security configuration (mTLS, RBAC — see ksqlDB security docs)
- CC ksqlDB billing and CSU sizing (see [CC Cluster Tiers](cc-cluster-tiers.md))

## Related

- [Observability Metrics Mapping](observability-metrics-mapping.md) — cross-provider query syntax for ksqlDB metrics
- [FSI Data Streaming Platform](fsi-data-streaming-platform.md) — ksqlDB as a platform component
- [Consumer Lag Monitoring](consumer-lag-monitoring.md) — ksqlDB queries are consumers; commit lag overlaps
- [Kafka Streams Architecture](kafka-streams-architecture.md) — runtime model under every persistent query
- [Kafka Streams Debugging](kafka-streams-debugging.md) — diagnostic counterpart for stuck queries
- [Dead Letter Queue Design](../patterns/dead-letter-queue-design.md) — deserialization-error DLQ pattern
- [SLA Tiers](sla-tiers.md) — alert thresholds per FSI tier
