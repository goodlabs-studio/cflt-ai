---
title: OCI Streaming → Splunk Sink (Self-Managed Connect) — Deployment & Operations Runbook
subtitle: OCI Audit/Cloud Guard events → OCI Streaming (Kafka) → self-managed Connect → Splunk HEC
audience: Platform / SOC engineering (owners), OCI tenancy admins (SCH + Streaming), Splunk admins (HEC)
validated: 2026-07-29 against confluent-docs (Splunk Sink Connector overview + delivery/DLQ/HEC-ack/health-check behavior) + local canon (dead-letter-queue-design, connect-deployment-models, audit-log-siem-integration, topic-naming). OCI-side steps are expert guidance — confluent-docs has no OCI Streaming coverage; confirm against current OCI docs.
confidence: medium
companion: ../../wiki/patterns/oci-audit-events-to-splunk.md
related-canon: patterns/oci-audit-events-to-splunk.md, patterns/dead-letter-queue-design.md, patterns/connect-deployment-models.md, patterns/audit-log-siem-integration.md
---

# OCI Streaming → Splunk Sink (Self-Managed Connect)

**Purpose:** Stand up and operate a self-managed Kafka Connect pipeline that consumes OCI
Audit / Cloud Guard security events **directly from OCI Streaming's Kafka endpoint** and
sinks them to Splunk via HTTP Event Collector (HEC). No intermediate Confluent cluster.

> **Delivery reality (read first).** This pipeline is **at-least-once** end to end. OCI
> Streaming offers no Kafka transactions/EOS; Splunk HEC is at-least-once. Completeness is
> achieved by **dedup on the OCI event OCID**, not by exactly-once. Do not promise EOS.
> See the [companion pattern](../../wiki/patterns/oci-audit-events-to-splunk.md).

> **Why self-managed.** The fully-managed Confluent Cloud Splunk sink can only read a
> Confluent Cloud cluster — it cannot point at an external OCI bootstrap. Direct OCI→Splunk
> is *always* self-managed Connect. The Splunk sink plugin is open source (no Enterprise
> license). *(MCP-confirmed.)*

---

## 0. Prerequisites

- **OCI tenancy access** to enable Audit (on by default), Cloud Guard, Logging, and to
  create a **Service Connector Hub (SCH)** connector and an **OCI Streaming** stream +
  stream pool.
- **OCI auth token** for the service/user that Connect will authenticate as (this is the
  Kafka SASL password — OCI Streaming does **not** support mTLS to Kafka clients).
- **Connect host** — an OCI VM or OKE cluster to run the self-managed Connect worker
  (co-locate in the same region as the stream pool to avoid egress and latency).
- **Splunk HEC** — an enabled HEC input with a token, target index, and (for FSI) TLS on.
  If HEC is behind a proxy/CDN, `/services/collector/health` must allow **unauthenticated**
  `GET` (see §6, startup health check). *(MCP-confirmed behavior.)*
- **Splunk sink plugin** installed on every Connect worker:
  `confluent connect plugin install splunk/kafka-connect-splunk:latest`
  (or download the ZIP from Confluent Hub).

---

## 1. OCI side — route events into a stream

1. **Enable Cloud Guard** and confirm Audit logging is active for the target compartments.
2. **Send events to Logging** — ensure Audit and Cloud Guard problem/detector events land
   in an OCI **Log Group** you can reference from SCH.
3. **Create the OCI Streaming stream(s).** Prefer **one stream per event class** rather than
   one firehose, so Splunk sourcetype routing stays clean downstream:
   - `oci-audit-events`
   - `oci-cloudguard-events`
   - (optionally) `oci-vcn-flow` etc.
   Size partitions against **peak** audit volume — incident storms and mass RBAC changes
   are the sizing driver, not steady state.
4. **Create the Service Connector Hub connector:** source = Logging (the log groups above),
   target = the OCI Streaming stream(s). SCH is the only supported way to move Audit events
   onto a stream; it cannot target an external Confluent cluster.

---

## 2. Connect worker — point at OCI Streaming

OCI Streaming is the Connect cluster's Kafka. Configure the **worker** (`connect-distributed.properties`)
to authenticate to OCI Streaming with SASL_SSL + PLAIN. The username format is
`<tenancy-name>/<username>/<stream-pool-ocid>`; the password is the **OCI auth token**.

```properties
# --- OCI Streaming as the Connect backing cluster ---
bootstrap.servers = cell-1.streaming.<region>.oci.oraclecloud.com:9092
security.protocol  = SASL_SSL
sasl.mechanism     = PLAIN
sasl.jaas.config   = org.apache.kafka.common.security.plain.PlainLoginModule required \
  username="<tenancy>/<user>/<stream-pool-ocid>" \
  password="<oci-auth-token>";

group.id           = oci-splunk-connect
# Connect internal topics live on OCI Streaming's Kafka Connect Harness — pre-create these
# streams in the pool (OCI Streaming does not auto-create Connect internal topics):
config.storage.topic  = oci-splunk-connect-configs
offset.storage.topic  = oci-splunk-connect-offsets
status.storage.topic  = oci-splunk-connect-status
config.storage.replication.factor = 1
offset.storage.replication.factor = 1
status.storage.replication.factor = 1

# Audit payloads are JSON — pass through as strings, no schema.
key.converter   = org.apache.kafka.connect.storage.StringConverter
value.converter = org.apache.kafka.connect.storage.StringConverter
```

> **OCI Streaming limits to plan for:** no transactions/EOS, no log compaction, and
> connection/partition/throughput caps per stream pool. Consumer groups are supported via
> the Kafka compat layer. Internal Connect topics must be **pre-created** as streams; OCI
> Streaming will not create them on demand.

---

## 3. Splunk Sink Connector config

Static `topics` list (required for per-topic index/sourcetype routing — `topics.regex`
disables that routing). *(MCP-confirmed.)*

```properties
name               = oci-audit-splunk-sink
connector.class    = com.splunk.kafka.connect.SplunkSinkConnector
tasks.max          = 2

# Static list → positional 1:1 mapping to splunk.indexes / splunk.sourcetypes below.
topics             = oci-audit-events,oci-cloudguard-events

# --- Splunk HEC endpoint ---
splunk.hec.uri     = https://hec.splunk.example.com:8088
splunk.hec.token   = <HEC_TOKEN>
splunk.hec.ssl.validate.certs = true          # FSI: never disable cert validation
splunk.hec.raw     = false                     # use /event endpoint (allows enrichment/metadata)

# --- Positional routing: topic[i] -> index[i] -> sourcetype[i] ---
splunk.indexes     = oci_audit,oci_cloudguard
splunk.sourcetypes = oci:audit,oci:cloudguard

# --- HEC acknowledgement: gate offset commit on Splunk indexing ack (audit completeness) ---
# Prevents data loss on Splunk-side failures; costs throughput. Correct trade for a SIEM.
splunk.hec.ack.enabled       = true
splunk.hec.ack.poll.interval = 10
splunk.hec.ack.poll.threads  = 2
splunk.hec.event.timeout     = 300

# --- Dead Letter Queue for records Splunk rejects (malformed / oversized) ---
errors.tolerance                                 = all
errors.deadletterqueue.topic.name                = oci-splunk-sink.dlq
errors.deadletterqueue.topic.replication.factor  = 1     # OCI Streaming; adjust to pool policy
errors.deadletterqueue.context.headers.enable    = true  # always — else you see failures but can't diagnose
errors.log.enable                                = true
errors.log.include.messages                      = false # do not log audit payloads (PII)
```

Notes (all MCP-validated against the Splunk Sink Connector docs):

- **At-least-once only** — there is no exactly-once mode; dedup downstream (§7).
- **`splunk.hec.ack.enabled=true`** makes the connector poll Splunk for indexing ack before
  committing the Kafka offset. Turn it on for audit; expect lower throughput.
- **Positional routing requires the static `topics` list.** With `topics.regex`, the
  `splunk.indexes`/`splunk.sources`/`splunk.sourcetypes` properties are ignored and events
  use the HEC token's default index/sourcetype.
- **DLQ context headers** (`__connect.errors.*`) carry topic/partition/offset + exception
  detail. See [Dead Letter Queue Design](../../wiki/patterns/dead-letter-queue-design.md).

---

## 4. Deploy

```bash
# Start the worker (systemd unit / container on the OCI host or OKE)
connect-distributed connect-distributed.properties

# Register the sink
curl -s -X PUT -H 'Content-Type: application/json' \
  http://localhost:8083/connectors/oci-audit-splunk-sink/config \
  -d @oci-audit-splunk-sink.json
```

---

## 5. Verify (do this before declaring done)

1. **Connector RUNNING, tasks RUNNING:**
   `curl -s localhost:8083/connectors/oci-audit-splunk-sink/status | jq '.connector.state, .tasks[].state'`
   → all `RUNNING`. A task in `FAILED` with a 401/403 on `/services/collector/health` means
   the HEC health check is being blocked by a proxy/CDN (see §6).
2. **Events reaching Splunk:** in Splunk search
   `index=oci_audit sourcetype=oci:audit | head 20` — confirm audit records arrive.
3. **Count reconciliation:** compare the OCI Streaming committed-offset advance for
   `group.id=oci-splunk-connect` against Splunk ingest count over the same window. They
   should track (allowing for at-least-once duplicates, never a shortfall).
4. **DLQ is empty (or explains itself):** consume `oci-splunk-sink.dlq`; any records here
   are Splunk rejections — inspect `__connect.errors.exception.message`.
5. **Ack mode working:** with `splunk.hec.ack.enabled=true`, offsets should commit only
   after Splunk acks. Kill Splunk HEC briefly in a test and confirm offsets stop advancing
   (records are retried, not dropped).

---

## 6. Failure modes & fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| Task FAILED at startup, `401`/`403` on `/services/collector/health` | HEC behind proxy/CDN that authenticates all paths; the connector's startup health check is **unauthenticated** | Allowlist unauthenticated `GET /services/collector/health` in the proxy/CDN *(MCP-confirmed behavior)* |
| Config exception at startup, index count mismatch | `topics` and `splunk.indexes` counts differ | Make them 1:1, or supply a single index for all topics |
| Events land in the wrong/default index | `topics.regex` used → metadata routing ignored | Switch to an explicit `topics` list *(MCP-confirmed)* |
| Consumer lag grows on the stream | HEC ack polling throttling throughput; or under-provisioned tasks | Raise `tasks.max` (≤ partition count), tune `splunk.hec.ack.poll.threads`, or accept the ack-mode throughput cost |
| Gaps in Splunk during an incident burst | OCI Streaming throughput/partition cap hit | Increase stream partitions; confirm SCH is keeping up on the OCI side |
| Duplicates in Splunk after a Connect restart | Expected — at-least-once redelivery | Dedup on OCI event OCID (§7); this is not a bug |
| `SASL authentication failed` to OCI Streaming | Expired OCI auth token, or wrong `username` format | Regenerate auth token; username must be `<tenancy>/<user>/<stream-pool-ocid>` |

---

## 7. Operations

- **Dedup strategy (required):** every OCI audit record carries a unique event OCID
  (`id`) + `eventTime`. Configure Splunk dedup on that field (or a scheduled dedup search)
  since the pipeline is at-least-once. This is the completeness mechanism — not EOS.
- **Monitor:** consumer lag on `group.id=oci-splunk-connect`; connector/task state; DLQ
  message rate (>0 sustained = Splunk-side rejections needing attention); HEC ack timeouts.
- **Retention:** keep the OCI Streaming stream retention **longer** than any downstream
  stage so the stream is a replay anchor. Give the DLQ longer retention than the source.
- **Token rotation:** the OCI auth token is a credential with an expiry — rotate on
  schedule and update the worker `sasl.jaas.config`; a silent expiry stalls the whole feed.
- **Security review notes (FSI):** (1) the OCI→Connect leg is SASL/PLAIN over TLS only, no
  mTLS — document this boundary; (2) `errors.log.include.messages=false` so audit payloads
  are never written to Connect logs; (3) restrict the HEC token to the intended indexes.

---

## 8. When to insert a Confluent hub instead

Keep this pipeline direct (OCI Streaming → self-managed Connect → Splunk) **unless** you
need one of: Flink normalization / Splunk CIM mapping / PII redaction, Schema Registry
governance on the audit stream, fan-out to more than just Splunk, or mTLS + RBAC + Confluent
audit logs as the security boundary. In those cases, bridge OCI Streaming → Confluent with
MirrorMaker 2 / self-managed Connect first, then sink — see the
[companion pattern](../../wiki/patterns/oci-audit-events-to-splunk.md). Otherwise the
Confluent hop is redundant infrastructure.
