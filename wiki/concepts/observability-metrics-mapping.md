---
title: Observability Metrics Mapping — CC Cloud, JMX, and Six Providers
tags: [observability metrics-api jmx prometheus dynatrace splunk datadog newrelic instana cross-provider fsi]
sources:
  - raw/repos/fsi-dsp/observability/metrics-mapping.md
  - https://docs.confluent.io/cloud/current/monitoring/metrics-api.html
  - https://docs.confluent.io/cloud/current/monitoring/metrics-reference.html
related:
  - concepts/fsi-data-streaming-platform
  - concepts/sla-tiers
  - concepts/consumer-lag-monitoring
  - patterns/audit-log-siem-integration
  - patterns/dr-cluster-linking
confidence: medium
last_updated: 2026-05-20
last_validated: 2026-05-20
---

# Observability Metrics Mapping — CC Cloud, JMX, and Six Providers

## Summary

Every observability provider expresses the same underlying Confluent telemetry differently. This article is the canonical mapping spine: for each load-bearing Confluent Cloud (CC) Metrics API metric and its self-managed JMX MBean counterpart, it lists the equivalent query in Grafana (PromQL), Dynatrace (DQL), Datadog, Splunk (SPL), New Relic (NRQL), and IBM Instana. Use it to (a) verify cross-provider dashboard parity when migrating, (b) write tier-aware alerts that translate cleanly across stacks, and (c) close the CC-vs-self-managed coverage gap that the [FSI Data Streaming Platform](fsi-data-streaming-platform.md) observability templates assume but never spell out in one place.

## Detail

### How CC Metrics API maps to provider query syntax

CC publishes telemetry through the [Metrics API](https://docs.confluent.io/cloud/current/monitoring/metrics-api.html). Metric names follow `io.confluent.<component>/<metric_name>` (e.g., `io.confluent.kafka.server/consumer_lag_offsets`). In Prometheus-flavored stacks (Grafana, Datadog, New Relic) the namespace dots and slashes become underscores: `io.confluent.flink/num_records_out` → `io_confluent_flink_num_records_out`. JMX MBeans for self-managed clusters expose the same telemetry under `kafka.server:type=…`, `kafka.connect:type=…`, etc. — see [Confluent Platform Broker JMX](confluent-platform-broker-jmx.md) for the broker MBean reference. The Connect-specific JMX reference lives in the root-level `Connect_Dynatrace_Monitoring_Guide.md`.

### Cluster health

| Metric (CC Metrics API) | JMX (self-managed) | Grafana (PromQL) | Dynatrace (DQL) | Datadog | Splunk (SPL) | New Relic (NRQL) | Instana |
|---|---|---|---|---|---|---|---|
| `io.confluent.kafka.server/active_connection_count` | `kafka.server:type=socket-server-metrics,name=connection-count` | `confluent_kafka_server_active_connection_count{kafka_id="$CLUSTER_ID"}` | `timeseries v = avg(confluent_kafka_server.active_connection_count), by:{kafka_id}` | `confluent_kafka_server.active_connection_count{kafka_id:$CLUSTER_ID}` | `index=kafka sourcetype=confluent_metrics metric_name="active_connection_count"` | `SELECT average(active_connection_count) FROM ConfluentCloudMetric WHERE kafka_id = '$CLUSTER_ID'` | `metrics("active_connection_count").filter("kafka_id","$CLUSTER_ID")` |
| `io.confluent.kafka.server/request_count` | `kafka.network:type=RequestMetrics,name=RequestsPerSec,request=*` | `rate(confluent_kafka_server_request_count{kafka_id="$CLUSTER_ID"}[5m])` | `timeseries v = rate(confluent_kafka_server.request_count, time:5m), by:{kafka_id}` | `rate:confluent_kafka_server.request_count{*}.as_rate()` | `\| timechart span=5m rate(request_count)` | `SELECT rate(sum(request_count), 5 MINUTES) FROM ConfluentCloudMetric` | `metrics("request_count").rate(300)` |
| `io.confluent.kafka.server/received_bytes` | `kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec` | `rate(confluent_kafka_server_received_bytes{kafka_id="$CLUSTER_ID"}[5m])` | `timeseries v = rate(confluent_kafka_server.received_bytes, time:5m)` | `rate:confluent_kafka_server.received_bytes{*}.as_rate()` | `\| timechart rate(received_bytes)` | `SELECT rate(sum(received_bytes), 5 MINUTES) FROM ConfluentCloudMetric` | `metrics("received_bytes").rate(300)` |
| `io.confluent.kafka.server/sent_bytes` | `kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec` | `rate(confluent_kafka_server_sent_bytes{kafka_id="$CLUSTER_ID"}[5m])` | `timeseries v = rate(confluent_kafka_server.sent_bytes, time:5m)` | `rate:confluent_kafka_server.sent_bytes{*}.as_rate()` | `\| timechart rate(sent_bytes)` | `SELECT rate(sum(sent_bytes), 5 MINUTES) FROM ConfluentCloudMetric` | `metrics("sent_bytes").rate(300)` |
| `io.confluent.kafka.server/retained_bytes` | `kafka.log:type=Log,name=Size,topic=*,partition=*` | `confluent_kafka_server_retained_bytes{kafka_id="$CLUSTER_ID"}` | `timeseries v = max(confluent_kafka_server.retained_bytes), by:{topic}` | `confluent_kafka_server.retained_bytes{*}` | `\| stats latest(retained_bytes) by topic` | `SELECT latest(retained_bytes) FROM ConfluentCloudMetric FACET topic` | `metrics("retained_bytes").groupBy("topic")` |
| (JMX-only) | `kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions` | `kafka_server_replica_manager_under_replicated_partitions` | `timeseries v = max(kafka.server.replica_manager.under_replicated_partitions)` | `kafka.server.replica_manager.under_replicated_partitions{*}` | `index=kafka sourcetype=jmx metric_name="under_replicated_partitions"` | `SELECT latest(under_replicated_partitions) FROM KafkaBrokerSample` | `metrics("under_replicated_partitions")` |

> ⚠️ unverified — `io.confluent.kafka.server/partition_count` and `io.confluent.kafka.server/successful_authentication_count` exist in the source mapping but were not surfaced in the 2026-05-20 MCP fetch of the Metrics API descriptor. Validate against the current [Metrics Reference](https://docs.confluent.io/cloud/current/monitoring/metrics-reference.html) before use.

### Consumer lag

| Metric (CC Metrics API) | JMX (self-managed) | Grafana (PromQL) | Dynatrace (DQL) |
|---|---|---|---|
| `io.confluent.kafka.server/consumer_lag_offsets` | `kafka.consumer:type=consumer-fetch-manager-metrics,client-id=*,name=records-lag-max` (client-side); broker-side emitter introduced CP 7.5+ | `confluent_kafka_server_consumer_lag_offsets{topic=~"$DOMAIN_PREFIX.*"}` | `timeseries lag = avg(confluent_kafka_server.consumer_lag_offsets), by:{consumer_group_id, topic}, from:now()-1h, interval:1m` |
| Consumer group state | `kafka.consumer:type=consumer-coordinator-metrics,client-id=*,name=assigned-partitions` (client-side) | `kafka_consumergroup_state` | `timeseries v = latest(kafka.consumer_group.state), by:{consumer_group}` |

See [Consumer Lag Monitoring](consumer-lag-monitoring.md) for the per-provider lag-monitoring deep dive (Burrow, Kafka Lag Exporter, time-based vs offset-based alerting).

### Connect status

Connect's connector and task state is **not** exposed through CC Metrics API for fully-managed connectors. The cross-provider pattern is to scrape the Connect REST API (`/connectors`, `/connectors/{name}/status`) via the provider's HTTP-monitor or scripted-input mechanism, then alert on the JSON state field. For self-managed Connect, JMX MBeans are richer — see the root-level `Connect_Dynatrace_Monitoring_Guide.md` and `Connect_DQL_Dashboard_Config.md` for the full JMX reference (`kafka.connect:type=connector-metrics`, `…connector-task-metrics`, `…task-error-metrics`, etc.).

| Endpoint | Grafana | Dynatrace | Datadog | Splunk | New Relic | Instana |
|---|---|---|---|---|---|---|
| `GET $CONNECT_REST_URL/connectors` | HTTP JSON datasource | HTTP check | HTTP check | Scripted input | Flex integration | HTTP endpoint |
| `GET $CONNECT_REST_URL/connectors/{name}/status` | HTTP JSON datasource | HTTP check | HTTP check | Scripted input | Flex integration | HTTP endpoint |
| `io.confluent.kafka.connect/received_records` | `rate(confluent_kafka_connect_received_records[5m])` | `timeseries v = rate(confluent_kafka_connect.received_records, time:5m), by:{connector_id}` | `rate:confluent_kafka_connect.received_records{*}.as_rate()` | `\| timechart rate(received_records)` | `SELECT rate(sum(received_records), 5 MINUTES) FROM ConfluentCloudMetric` | `metrics("received_records").rate(300)` |

### DR readiness (Cluster Linking)

| Metric (CC Metrics API) | Description |
|---|---|
| `io.confluent.kafka.server/cluster_link_destination_response_bytes` | Bytes received at the destination side of a cluster link (MCP-confirmed family member). |
| Mirror offset lag (records) | Derived per topic on the destination cluster. |
| Mirror lag in seconds (derived) | `offset_lag / received_records.as_rate()` — the time-based view alerts use for tier-aware RPO tracking. |
| Cluster link status | Active/inactive state of each configured link. |

> ⚠️ unverified — the source mapping cites `io.confluent.kafka.server/cluster_link_mirror_topic_offset_lag` as the canonical mirror-lag metric. The 2026-05-20 MCP descriptor surfaced `cluster_link_destination_response_bytes` but not `cluster_link_mirror_topic_offset_lag` by that exact name. The metric exists in the CL family but the exact identifier should be revalidated against the live tenant before using it in alert expressions.

For the full DR observability pattern (RPO/RTO dashboards, failover signals, per-SLA-tier thresholds), see [Cluster Linking](patterns/dr-cluster-linking.md) and `patterns/cluster-linking-observability.md` (pending in this expansion).

### Flink jobs

CC Flink metrics are exposed via the CC Metrics API under the `io.confluent.flink/*` namespace. **The Metrics API does not expose a checkpoint duration metric** — Apache Flink's `checkpointAlignmentTime` JMX metric is not available in CC Flink. Use `pending_records` as a backpressure proxy and `num_records_out` rate for throughput.

| Metric (CC Metrics API) | Description | Grafana (PromQL) | Dynatrace (DQL) |
|---|---|---|---|
| `io.confluent.flink/num_records_in` | Records consumed by statement | `io_confluent_flink_num_records_in{resource_type="flink_statement"}` | `timeseries avg(io.confluent.flink.num_records_in), by:{statement_name}` |
| `io.confluent.flink/num_records_out` | Records produced by statement | `io_confluent_flink_num_records_out{resource_type="flink_statement"}` | `timeseries avg(io.confluent.flink.num_records_out), by:{statement_name}` |
| `io.confluent.flink/pending_records` | Backpressure proxy (records pending processing) | `io_confluent_flink_pending_records{resource_type="flink_statement"}` | `timeseries max(io.confluent.flink.pending_records), by:{statement_name}` |
| `io.confluent.flink/compute_pool_utilization` | CFU utilization across the compute pool (MCP-confirmed 2026-05-20) | `io_confluent_flink_compute_pool_utilization{resource_type="flink_compute_pool"}` | `timeseries avg(io.confluent.flink.compute_pool_utilization), by:{compute_pool_name}` |
| `io.confluent.flink/statement_status` | Current statement state (RUNNING / FAILED / STOPPED) | `io_confluent_flink_statement_status` | `timeseries latest(io.confluent.flink.statement_status), by:{statement_name}` |

> ⚠️ unverified — the source mapping references `io.confluent.flink/current_cfu` and `io.confluent.flink/max_cfu` as separate metrics. The 2026-05-20 MCP fetch surfaced `compute_pool_utilization` as the canonical Flink CFU metric; the current_cfu/max_cfu pair may have been consolidated into the single utilization metric. Validate against [Metrics Reference](https://docs.confluent.io/cloud/current/monitoring/metrics-reference.html) when writing new dashboards.

### Schema Registry and ksqlDB

CC exposes a Schema Registry metric (`io.confluent.kafka.schema_registry/schema_count`) and a richer ksqlDB metric set (`io.confluent.kafka.ksql/committed_offset_lag`, `consumed_total_bytes`, `offsets_processed_total`, `processing_errors_total`, `produced_total_bytes`, `query_restarts`, `query_saturation`, `storage_utilization`, `streaming_unit_count`, `task_stored_bytes`). Both are MCP-confirmed 2026-05-20. Provider deep dives live in `schema-registry-observability.md` and `ksqldb-observability.md` (pending in this expansion).

### Provider decision matrix

| Pick | When |
|---|---|
| **Grafana + Prometheus** | Already running Prometheus; PromQL fluency in team; cost-sensitive; need open-source alerting and dashboard portability across tenants. |
| **Dynatrace** | Buying observability as a managed service; want Davis AI auto-anomaly and root-cause correlation across Kafka + OneAgent JVM + downstream systems; FSI customer with mTLS + RBAC enterprise contract. |
| **Splunk** | Already the SIEM of record; audit logs already flow there (see [Audit Log SIEM Integration](../patterns/audit-log-siem-integration.md)); want one query language across security + metrics. |
| **Datadog** | Multi-cloud, multi-vendor environment beyond Confluent; want tag-based correlation across infra/APM/logs; tolerant of per-host pricing. |
| **New Relic** | NRQL fluency; entity-centric workflows; cost predictable on ingest-based model. |
| **IBM Instana** | IBM stack alignment (LinuxONE, IBM Cloud, IBM Z); want APM correlation across mainframe-adjacent workloads. |

### Provider ingestion endpoints

| Provider | Endpoint | Auth |
|---|---|---|
| Grafana/Prometheus | CC Metrics API Prometheus export: `https://api.telemetry.confluent.cloud/v2/metrics/cloud/export` | Basic auth (CC API key/secret) |
| Dynatrace | `{ENV_URL}/api/v2/metrics/ingest` | API token, `metrics.ingest` scope |
| Datadog | `https://api.datadoghq.com/api/v1/series` | API key + App key |
| Splunk | `https://{HOST}:8088/services/collector` (HEC) | HEC token |
| New Relic | `https://metric-api.newrelic.com/metric/v1` | Ingest license key |
| IBM Instana | `https://{HOST}/api/custom-dashboards` | API token |

## Related

- [FSI Data Streaming Platform](fsi-data-streaming-platform.md) — observability templates context across six deployment models
- [SLA Tiers](sla-tiers.md) — alert thresholds map to FSI SLA tiers (critical / standard / best-effort / compliance)
- [Consumer Lag Monitoring](consumer-lag-monitoring.md) — provider-specific lag-monitoring deep dive
- [Audit Log SIEM Integration](../patterns/audit-log-siem-integration.md) — security-side observability complementing this operational spine
- [DR — Cluster Linking](../patterns/dr-cluster-linking.md) — consumes the CL mirror lag metrics in this spine
