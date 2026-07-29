---
title: OCI Audit/Security Events to Splunk via OCI Streaming
tags: [kafka connect oci oracle splunk siem security audit fsi self-managed]
sources:
  - https://docs.confluent.io/kafka-connectors/splunk-sink/current/overview.html
  - https://docs.confluent.io/cloud/current/connectors/cc-splunk-sink.html
related: [patterns/audit-log-siem-integration, patterns/connect-deployment-models, patterns/dead-letter-queue-design, patterns/fsi-exactly-once, patterns/topic-naming]
confidence: medium
last_updated: 2026-07-29
last_validated: 2026-07-29
---

# OCI Audit/Security Events to Splunk via OCI Streaming

## Summary

Oracle Cloud Infrastructure (OCI) Audit and Cloud Guard emit security and administrative events that an FSI SOC needs in Splunk. The clean path is **OCI Audit → Service Connector Hub → OCI Streaming → self-managed Kafka Connect (Splunk Sink) → Splunk HEC**. The key insight that shapes the whole design: **OCI Streaming *is* a Kafka endpoint** (Kafka-wire-compatible), not something that feeds a separate Kafka — so you consume from it directly with a standard Kafka Connect worker and sink straight to Splunk. No intermediate Confluent cluster is required for the data to move. The dominant trade-off is delivery semantics: OCI Streaming (no EOS) and Splunk HEC (at-least-once) cap the pipeline at **at-least-once**, so completeness comes from deduplication on the OCI event OCID, not from exactly-once.

> **Validation status.** The Confluent-side facts (Splunk Sink Connector delivery guarantee, HEC acknowledgement, DLQ support, index/sourcetype routing, health-check behavior) are validated against `confluent-docs`. The OCI-side facts (Service Connector Hub targets, OCI Streaming Kafka compatibility and its limits) are expert knowledge — `confluent-docs` has **no** OCI Streaming coverage and Confluent ships no OCI connector. Treat the OCI leg as design guidance to confirm against current OCI docs.

## Pattern

### Architecture

```
OCI Audit + Cloud Guard ─▶ OCI Logging ─▶ Service Connector Hub (SCH)
                                                    │  (SCH's only streaming target is OCI Streaming)
                                                    ▼
                                        OCI Streaming  ── Kafka bootstrap endpoint
                                                    │
                                                    │  self-managed Kafka Connect worker
                                                    │  (consumes OCI Streaming directly, SASL_SSL + PLAIN,
                                                    │   OCI auth token as password)
                                                    ▼
                                        Splunk Sink Connector ─▶ Splunk HEC ─▶ index
```

### Why the shape is (mostly) forced

Two constraints eliminate the alternatives before you start:

1. **Service Connector Hub cannot write to an external Confluent cluster.** SCH targets are limited to OCI-native services (Streaming, Functions, Object Storage, Logging, Monitoring, Notifications). Getting audit events onto a stream *requires* OCI Streaming as the first hop — you cannot have SCH produce directly to a Confluent bootstrap. (Producing via an OCI Function is possible but loses buffering and replay; do not use it for audit volume.)
2. **Cluster Linking and MirrorMaker 2's Confluent-to-Confluent path do not apply** — OCI Streaming is not Confluent. Because it is Kafka-*wire*-compatible, you treat it as a **generic Kafka source** and consume it with any Kafka client, including a Kafka Connect worker running the Splunk sink.

### "OCI Streaming IS Kafka" — consume directly

OCI Streaming exposes a Kafka bootstrap URL and speaks the Kafka protocol. There is no handoff to a second Kafka. The Splunk Sink Connector is an ordinary Kafka Connect sink and does not care that the broker is Oracle's rather than Apache's, so you point a Connect worker's `bootstrap.servers` at the OCI Streaming endpoint and it consumes the audit stream like any topic. OCI Streaming also provides a **Kafka Connect Harness** (the backing config/offset/status topics) so the Connect worker can store its state on OCI Streaming itself.

### Self-managed Connect is mandatory here

The fully-managed Confluent Cloud Splunk Sink Connector only consumes from a Confluent Cloud cluster — it **cannot** be pointed at an external OCI Streaming bootstrap. Therefore a direct OCI→Splunk pipeline is *always* **self-managed** Kafka Connect: you run the worker (on an OCI VM or OKE) with the open-source Splunk plugin. The Splunk Sink Connector is open source and requires no Confluent Enterprise license. See [Connect Deployment Models](connect-deployment-models.md).

### Splunk Sink Connector essentials (MCP-validated)

- **At-least-once delivery** — the connector guarantees records are delivered at least once; there is **no exactly-once mode**.
- **HEC acknowledgement mode** — the connector can poll Splunk for indexing acknowledgement *before* committing the Kafka offset. **Enable this for audit data** (`splunk.hec.ack.enabled=true`): it prevents data loss at the cost of ingestion throughput. This is the correct trade for a SIEM feed.
- **Dead Letter Queue** — the connector supports a Connect DLQ for records Splunk rejects; wire it up (`errors.tolerance=all` + a DLQ topic + context headers). See [Dead Letter Queue Design](dead-letter-queue-design.md).
- **Index/sourcetype routing is positional** — `topics` maps 1:1 in order to `splunk.indexes` (and `splunk.sources`/`splunk.sourcetypes`). One index for many topics routes everything there; a mismatched count throws a config exception at startup.
- **Caveat — `topics.regex` disables metadata routing.** When you use `topics.regex` instead of a static `topics` list, `splunk.indexes`/`splunk.sources`/`splunk.sourcetypes` are **ignored** and events fall back to the HEC token's default metadata. Use an explicit `topics` list when you need per-topic sourcetype routing.
- **Caveat — startup health check.** The connector sends an *unauthenticated* `GET /services/collector/health` to each `splunk.hec.uri` at startup. If Splunk sits behind a proxy/CDN (e.g. CloudFront) that authenticates all paths, this returns 401/403 and the connector fails to start. Allowlist `/services/collector/health` for unauthenticated access.

### Delivery semantics — the honest end-to-end

End-to-end this is **at-least-once**, full stop. OCI Streaming's Kafka layer offers no transactions/EOS, and Splunk HEC is at-least-once, so no amount of Confluent EOS in the middle would buy exactly-once. For regulatory completeness:

- **Deduplicate on the OCI event OCID + `eventTime`** — every OCI audit record carries a unique `id`/event OCID; use it as the dedup discriminant (in Splunk, or in a stream-processing stage if one exists).
- **Reconcile by count** — compare records at SCH/OCI Streaming against the Splunk index rather than trusting the pipeline.
- **Keep the raw OCI Streaming stream as the replay anchor** with retention longer than any downstream stage.

## When to Use

- OCI Audit and/or Cloud Guard events must land in Splunk for SOC monitoring or compliance.
- The requirement is literally "OCI security events in Splunk" and you do **not** need stream processing, schema governance, or fan-out — in which case skip any Confluent cluster and sink directly from OCI Streaming with self-managed Connect (fewer moving parts, one Kafka, one operational surface).
- You already operate self-managed Connect on OCI compute and want to add an audit egress.

## Caveats

- **Add a Confluent hub only if it earns the hop.** Inserting Confluent between OCI Streaming and Splunk is justified *only* when you need Flink normalization/CIM mapping/PII redaction, Schema Registry governance on the audit stream, fan-out to more than just Splunk, or mTLS + RBAC + Confluent audit logs as the security boundary. Otherwise it is redundant infrastructure.
- **Security boundary on the OCI leg.** OCI Streaming offers only **SASL/PLAIN over TLS** to Kafka clients (auth token as password) — no mTLS. Flag this explicitly in an FSI review; you regain mTLS + RBAC only if/when data lands in Confluent.
- **No exactly-once.** Do not promise EOS for this pipeline. Design dedup + reconciliation instead (see Delivery semantics).
- **OCI Streaming Kafka-compat limits.** No transactions, no log compaction, and connection/throughput/partition caps apply. Validate stream throughput against peak audit event volume; audit bursts (mass RBAC changes, incident storms) are the sizing driver.
- **Managed Splunk sink ≠ OCI.** The Confluent Cloud managed Splunk sink runs on AWS/Azure/GCP, not OCI, and cannot read an external OCI bootstrap. Direct-from-OCI is self-managed only.
- **This is a different source than Confluent Cloud audit logs.** For forwarding *Confluent Cloud's own* `confluent-audit-log-events` to a SIEM, see [Audit Log SIEM Integration](audit-log-siem-integration.md) — that is a separate pipeline with its own constraints (7-day retention, dedicated audit cluster credentials).

## Related

- [Audit Log SIEM Integration](audit-log-siem-integration.md) — the sibling pattern for forwarding Confluent Cloud's *own* audit log to a SIEM (different source, different constraints)
- [Connect Deployment Models](connect-deployment-models.md) — why this pipeline must be self-managed Connect
- [Dead Letter Queue Design](dead-letter-queue-design.md) — configuring the Splunk sink DLQ and retention for rejected records
- [FSI Exactly-Once](fsi-exactly-once.md) — why at-least-once + dedup is the achievable target for cross-vendor audit pipelines
- [Topic Naming](topic-naming.md) — naming conventions for the landed OCI event streams
