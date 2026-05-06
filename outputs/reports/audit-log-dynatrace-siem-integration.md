---
title: Audit Log SIEM Integration — Splunk to Dynatrace Migration
date: 2026-04-30
query: "capturing audit logs in dynatrace — auth failures, RBAC denials, config changes, access transparency"
wiki_sources: [concepts/fsi-data-streaming-platform, concepts/fsi-compliance, concepts/consumer-lag-monitoring]
claims_checked: 7
claims_corrected: 0
claims_unverifiable: 0
---

# Audit Log SIEM Integration — Splunk to Dynatrace Migration

## TL;DR

Confluent Cloud auth failures and security events live in the audit log (`confluent-audit-log-events` topic), not the Metrics API. The Dynatrace CC extension only pulls operational metrics. To replicate Splunk's security alerting in Dynatrace, deploy an HTTP Sink Connector from the audit log topic to Dynatrace's Log Ingest API. Run two instances: high-priority for security events (SOC feed), lower-priority for operational audit (change trail).

## Analysis

### The Two-Channel Problem

Confluent Cloud monitoring splits across two independent data planes:
- **Metrics API** → operational health (throughput, lag, connectors) → Dynatrace CC extension handles this natively
- **Audit Log** → security events (auth, RBAC, config changes, access transparency) → requires a Kafka Connect sink pipeline

Splunk typically consumes both via sink connectors or HEC. Dynatrace has a native extension for the first channel but nothing for the second.

### 14 Alert Categories in the Audit Log

Auth failures, RBAC/ACL denials, topic create/delete, ACL modifications, config changes, Schema Registry auth/ops, Flink auth/RBAC, API key lifecycle, cluster/env changes, RBAC role bindings, IP filter violations, and Confluent staff access (access-transparency). Full filter table in the wiki article.

### Recommended Architecture

HTTP Sink Connector on Confluent Cloud Connect (or self-managed) reading `confluent-audit-log-events` and POSTing to Dynatrace `/api/v2/logs/ingest`. Two instances for SLA separation. Pre-filter via ksqlDB or Flink SQL for complex predicates on nested JSON fields.

### Key Constraints

- 7-day retention on audit log topic
- Dedicated cluster with separate API credentials (OrganizationAdmin required)
- Auth failures only logged when connection reaches a resource
- 5-minute offset on Dynatrace CC extension for metrics (separate concern)

## Decision Framework

- **If migrating Splunk → Dynatrace for CC monitoring** → Deploy Dynatrace CC extension for operational metrics (direct swap) + HTTP Sink Connector pipeline for audit log events (new plumbing)
- **If only need operational metrics in Dynatrace** → Dynatrace CC extension alone is sufficient, no topic pipeline needed
- **If need real-time SOC alerting on auth failures** → High-priority connector instance with `batch.max.size=1` to Dynatrace Log Ingest
- **If need compliance audit trail** → Lower-priority batched connector instance; ensure retention exceeds 7-day audit log window

## Caveats

- No native Dynatrace sink connector exists on Confluent Hub — HTTP Sink Connector requires manual payload shaping
- Access-transparency events (Confluent staff access) are CC-only, no equivalent in CP/CFK
- High-throughput clusters can generate significant audit event volume — monitor sink connector lag

---

*Validated against Confluent docs via MCP (2026-04-30). 7 claims checked, 0 corrected, 0 unverifiable.*
