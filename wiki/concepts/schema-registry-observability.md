---
title: Schema Registry Observability — CC and Self-Managed
tags: [observability schema-registry jmx mbean confluent-cloud confluent-platform cfk metrics-api fsi]
sources:
  - https://docs.confluent.io/platform/current/schema-registry/monitoring.html
  - https://docs.confluent.io/cloud/current/monitoring/metrics-api.html
related:
  - concepts/schema-registry-best-practices
  - concepts/schema-evolution-strategies
  - concepts/observability-metrics-mapping
  - patterns/fsi-governance-automation
  - concepts/fsi-compliance
confidence: high
last_updated: 2026-05-20
last_validated: 2026-05-20
---

# Schema Registry Observability — CC and Self-Managed

## Summary

Schema Registry (SR) carries the governance contract for every topic — its availability and latency directly bound producer/consumer health, and silent failures (failed compatibility checks, leader-election flap, schema-bloat) translate into application-layer incidents minutes to hours later. The observable surface differs sharply between Confluent Cloud (one Metrics API metric: `schema_count`) and self-managed CP/CFK (three JMX MBeans: `kafka.schema.registry:type=jetty-metrics`, `…master-slave-role`, `…jersey-metrics` with per-endpoint attributes). This article documents both surfaces, the alert patterns that catch the failure modes [Schema Registry Best Practices](schema-registry-best-practices.md) and [Schema Evolution Strategies](schema-evolution-strategies.md) describe, and the deployment-model gap to budget around.

## Detail

### Self-managed CP / CFK — JMX MBean tree

Self-managed SR exposes three MBeans under the `kafka.schema.registry:type=*` namespace. Override JMX defaults via `SCHEMA_REGISTRY_JMX_OPTS` (authentication is disabled by default in Kafka — apply mTLS + auth before exposing to non-loopback).

**MBean: `kafka.schema.registry:type=jetty-metrics` — HTTP server health**

| Attribute | Type | Signal |
|---|---|---|
| `busy_thread_count` | Gauge | Number of worker threads currently servicing requests |
| `connections-accepted-rate` | Rate | New connection accept rate |
| `connections-active` | Gauge | Currently open connections |
| `connections-closed-rate` | Rate | Connection close rate |
| `connections-opened-rate` | Rate | Connection open rate |
| `request_queue_size` | Gauge | Depth of unhandled-request queue — saturation indicator |
| `request-latency-avg` | Gauge (ms) | Average request latency across all endpoints |
| `thread_pool_usage` | Gauge (fraction) | Fraction of jetty worker pool consumed |

**MBean: `kafka.schema.registry:type=master-slave-role` — leader role**

| Attribute | Type | Signal |
|---|---|---|
| `master-slave-role` | Gauge | `1` if this SR node is the elected master (write-eligible), `0` if a replica/slave |

Cluster invariant: exactly one node should report `master-slave-role = 1` at a time. Sum across nodes; alert on != 1.

**MBean: `kafka.schema.registry:type=jersey-metrics` — per-endpoint API metrics**

Each REST endpoint (e.g., `/subjects/{subject}/versions`, `/schemas/ids/{id}`, `/compatibility/subjects/{subject}/versions/latest`) emits a parallel attribute set, plus a global aggregate with no prefix.

| Attribute (per endpoint, plus global) | Signal |
|---|---|
| `<endpoint>.request-byte-rate` | Bytes/second of incoming requests |
| `<endpoint>.request-error-rate` | HTTP-error responses per second — registration failures, compatibility-rejection, auth-fail |
| `<endpoint>.request-latency-avg` | Mean request latency (ms) |
| `<endpoint>.request-latency-max` | Max request latency (ms) |
| `<endpoint>.request-rate` | HTTP requests per second |
| `<endpoint>.request-size-avg` | Mean request size (bytes) |
| `<endpoint>.request-size-max` | Max request size (bytes) |
| `<endpoint>.response-byte-rate` | Bytes/second of outgoing responses |
| `<endpoint>.response-rate` | HTTP responses per second |
| `<endpoint>.response-size-avg` | Mean response size (bytes) |

The endpoint dimension is the load-bearing observability primitive: a spike in `request-error-rate` on `POST /subjects/{subject}/versions` tells you compatibility checks are rejecting registrations; a spike on the same endpoint's `request-latency-avg` tells you SR is becoming the producer-startup bottleneck. Pair both with the corresponding `request-rate` to distinguish "more requests" from "same requests, worse".

### Confluent Cloud — Metrics API surface

CC SR exposes a much narrower surface — confirmed MCP 2026-05-20:

| CC Metrics API metric | What it measures | Notes |
|---|---|---|
| `io.confluent.kafka.schema_registry/schema_count` | Total registered schema versions across all subjects on the SR cluster | Useful for capacity planning and detecting schema-bloat anti-patterns (e.g., a producer with `auto.register.schemas=true` looping on a non-deterministic schema generator) |

CC does **not** expose `request-error-rate`, `request-latency-avg`, or `master-slave-role` equivalents through the Metrics API. The compatibility-check failure signal lives in producer/consumer client metrics and CC's own audit log (see [Audit Log SIEM Integration](../patterns/audit-log-siem-integration.md)).

### Deployment-model coverage gap

| Diagnostic question | Self-managed (JMX) | CC managed |
|---|---|---|
| "Is SR up and reachable?" | `jetty-metrics.connections-active`, `busy_thread_count` | Synthetic HTTP monitor against `https://<env>.confluent.cloud/sr/.../subjects` |
| "Is SR slow?" | `jetty-metrics.request-latency-avg`, `<endpoint>.request-latency-max` | Producer-side `kafka.producer:type=producer-metrics,client-id=*,name=record-send-rate` drop + manual correlation |
| "Are registrations failing?" | `jersey-metrics.<endpoint>.request-error-rate` on `POST /subjects/.../versions` | Audit log events for failed compatibility checks (KIP-style) + producer client error logs |
| "Are we leader-electing?" | `master-slave-role` cluster sum != 1 | Not applicable (CC managed) |
| "Are we approaching capacity?" | Per-MBean memory + schema_count via REST API | `io.confluent.kafka.schema_registry/schema_count` |
| "Did a compatibility mode change?" | Audit log of REST API `PUT /config/{subject}` calls | Audit log event (`schema_registry_config_updated`) |

For CC tenants where deeper SR observability matters (FSI compliance reporting), the compensating pattern is to instrument *consumers* of the SR REST API: a wrapper that scrapes endpoint latency + error counts before delegating to the Confluent client, exporting Prometheus/DQL metrics from the wrapper. Not as good as native JMX, but closes the gap for the load-bearing endpoints.

### JMX exporter rule excerpt

Self-managed SR with Prometheus JMX exporter:

```yaml
hostPort: "{{SR_HOST}}:5555"
lowercaseOutputName: true
lowercaseOutputLabelNames: true
rules:
  - pattern: 'kafka.schema.registry<type=master-slave-role><>master-slave-role'
    name: schema_registry_master_slave_role
    type: GAUGE
    help: "1 if this node is the elected master, 0 if replica"
  - pattern: 'kafka.schema.registry<type=jetty-metrics><>connections-active'
    name: schema_registry_jetty_connections_active
    type: GAUGE
  - pattern: 'kafka.schema.registry<type=jetty-metrics><>request-latency-avg'
    name: schema_registry_jetty_request_latency_avg_ms
    type: GAUGE
  - pattern: 'kafka.schema.registry<type=jetty-metrics><>busy_thread_count'
    name: schema_registry_jetty_busy_thread_count
    type: GAUGE
  - pattern: 'kafka.schema.registry<type=jersey-metrics><>(.+)\.request-rate'
    name: schema_registry_jersey_request_rate
    type: GAUGE
    labels: { endpoint: "$1" }
  - pattern: 'kafka.schema.registry<type=jersey-metrics><>(.+)\.request-error-rate'
    name: schema_registry_jersey_request_error_rate
    type: GAUGE
    labels: { endpoint: "$1" }
  - pattern: 'kafka.schema.registry<type=jersey-metrics><>(.+)\.request-latency-avg'
    name: schema_registry_jersey_request_latency_avg_ms
    type: GAUGE
    labels: { endpoint: "$1" }
```

### Alert patterns

| Signal | Threshold | Tier | Why |
|---|---|---|---|
| Sum of `master-slave-role` across nodes != 1 | Immediate | P1 (all tiers) | Split-brain or leader gap — registrations stall |
| `jersey-metrics.<POST /subjects/*>.request-error-rate > 0` sustained 5 min | P2 | Critical | Compatibility checks rejecting — producer rollouts blocked |
| `jersey-metrics.global.request-latency-avg > 500 ms` sustained 5 min | P2 | Critical | SR is becoming producer-startup bottleneck |
| `jetty-metrics.busy_thread_count / max threads > 0.8` sustained 10 min | P2 | Standard | Thread saturation; tune `kafkastore.connection.url` parallelism or scale out |
| `schema_count` growth rate suddenly > 10×baseline | P3 | All | Misconfigured producer with `auto.register.schemas=true` on non-deterministic schemas — see [Schema Registry Best Practices](schema-registry-best-practices.md) |
| Compatibility mode change event in audit log | P3 / informational | Critical | Governance signal — should align to a PR/change-ticket |

> ⚠️ unverified — CC managed SR's exact rate-limit thresholds (per-tenant SR API quotas) are not publicly documented in a parseable form. Operate against the Confluent Cloud Schema Registry overview SLAs and budget for 429-response handling in critical-tier producers.

### CC alternative: client-side SR latency wrapper

Where CC observability is too thin (FSI compliance / production-incident postmortems), wrap the Schema Registry REST client. Pseudo-shape:

```python
# Sketch — the wrapper exports Prometheus metrics on each call
class InstrumentedSchemaRegistryClient(SchemaRegistryClient):
    def register(self, subject, schema):
        start = time.monotonic()
        try:
            schema_id = super().register(subject, schema)
            sr_request_seconds.labels(endpoint='register', status='200').observe(time.monotonic() - start)
            return schema_id
        except RestException as exc:
            sr_request_seconds.labels(endpoint='register', status=str(exc.http_code)).observe(time.monotonic() - start)
            raise
```

This is the only way to get per-endpoint latency + error rate from a CC SR client. Apply at the FSI Producer / Consumer base class layer so every app inherits it. Pair with [FSI Governance Automation](../patterns/fsi-governance-automation.md) for Terraform-driven Compatibility settings.

## Related

- [Schema Registry Best Practices](schema-registry-best-practices.md) — operational surface the alerts here govern
- [Schema Evolution Strategies](schema-evolution-strategies.md) — compatibility-check policy driving the compatibility-error alert
- [Observability Metrics Mapping](observability-metrics-mapping.md) — cross-provider query syntax for SR metrics
- [FSI Governance Automation](../patterns/fsi-governance-automation.md) — Terraform module locks Compatibility per tier
- [FSI Compliance](fsi-compliance.md) — SR observability requirements for audit reporting
