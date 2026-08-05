---
title: Azure Blob Storage Source (Generalized Mode) → Kafka — Self-Managed Connect on AKS Runbook
subtitle: Ingest arbitrary files from ADLS Gen2 / Blob Storage into a Kafka topic (mode=GENERIC)
audience: Platform / integration engineers (owners), Azure storage admins (SAS scoping)
validated: 2026-08-05 against confluent-docs (Azure Blob Storage Source — Generalized overview + Configuration Reference) + local canon (connect-deployment-models, dead-letter-queue-design, producer-config-fsi). Connector is proprietary/licensed (30-day trial, then Confluent enterprise license).
confidence: high
companion: adls-gen2-parquet-archive-connect-runbook.md
related-canon: patterns/connect-deployment-models.md, patterns/dead-letter-queue-design.md, patterns/producer-config-fsi.md
---

# Azure Blob Storage Source (Generalized Mode) → Kafka — Self-Managed Connect on AKS

**Purpose:** Stand up a self-managed Kafka Connect pipeline on AKS that reads files from an
ADLS Gen2 / Azure Blob Storage container into a Kafka topic, using the **Generalized** flavor
of the Azure Blob Storage Source connector.

> **Pick the right mode first.** The connector class
> `io.confluent.connect.azure.blob.storage.AzureBlobStorageSourceConnector` ships two modes,
> selected by the `mode` property (default `RESTORE_BACKUP`):
> - **`RESTORE_BACKUP`** — re-ingests data that the Blob **Sink** connector previously exported;
>   with matching format/partitioner it can preserve original partitioning/ordering. Replay / DR only.
> - **`GENERIC`** (generalized) — reads **any** file naming convention in the container, as long as
>   the content is a supported format (JSON, Avro, Byte Array). **This is the ingest path — use it.**
> *(MCP-confirmed 2026-08-05.)*

> **This is always self-managed Connect.** A managed Confluent Cloud connector can't run against
> your own AKS cluster; run distributed Connect workers on AKS with the plugin installed on every
> worker. See [Connect Deployment Models](../../wiki/patterns/connect-deployment-models.md).

---

## 0. Prerequisites

- **Distributed Connect on AKS**, plugin installed on every worker; Connect internal topics
  (`config`/`offset`/`status`) at RF 3.
  - Install: `confluent connect plugin install confluentinc/kafka-connect-azure-blob-storage-source:latest`
    then restart each worker so the plugin path takes effect.
  - Requirements: CP 4.0.0+/Kafka 1.0.0+, Java 8.
- **ADLS Gen2 / Blob Storage account + container** reachable from the AKS node subnet — for FSI,
  a **private endpoint to the blob sub-resource** (not the public endpoint).
- **Auth material** — a **scoped, short-lived SAS token** (preferred) or the account key. See §4 —
  there is **no managed-identity / Entra Workload Identity path** for this connector.
- **License** — 30-day trial, then a Confluent enterprise license (`confluent.license` / the
  `_confluent-command` topic). This is a licensed, vendor-supported connector (satisfies the FSI
  vendor-backing rule) — budget the subscription.

---

## 1. Connector configuration (generalized ingest)

```properties
name=adls-source-orders-ingest
connector.class=io.confluent.connect.azure.blob.storage.AzureBlobStorageSourceConnector
tasks.max=2

mode=GENERIC                                   # selects generalized mode (default is RESTORE_BACKUP)

# --- where, and which files map to which topic ---
azblob.account.name=<account>                  # 3-24 chars
azblob.container.name=<container>              # 3-63 chars
store.url=https://<account>.blob.core.windows.net/<container>   # BLOB endpoint (see §3)
topics.dir=incoming                            # folder prefix; DEFAULT is "topics" — if your files
                                               #   are not under topics/ you MUST set this, or nothing is read
topic.regex.list=orders.raw:.*\.json           # <topic>:<regex>; unmatched files ignored; first match wins
azblob.poll.interval.ms=60000                  # poll for new/removed folders
task.batch.size=10                             # files assigned per task per pass (default 10)

# --- format: use the CloudStorage* generalized classes (NOT azure.blob.*.JsonFormat) ---
format.class=io.confluent.connect.cloud.storage.source.format.CloudStorageJsonFormat
value.converter=org.apache.kafka.connect.json.JsonConverter
value.converter.schemas.enable=false

# --- auth: prefer a scoped, short-lived SAS over the account key; externalize via ConfigProvider ---
azblob.sas.token=${file:/mnt/secrets/adls:sas}
# azblob.account.key=...                        # alternative — avoid in FSI

# --- error handling: route parse failures instead of failing the task ---
behavior.on.error=log                          # fail (default) | ignore | log
parse.error.topic.prefix=adls-source-error     # -> adls-source-error-${connectorName}

# --- first-run cutoff (ONLY applied when no offsets exist yet for this connector name) ---
file.discovery.starting.timestamp=1754352000000   # epoch ms; skip files created before this

# --- canon: durable internal producer (source connectors honor producer.override.*) ---
producer.override.acks=all
producer.override.enable.idempotence=true
producer.override.compression.type=lz4

# --- license topic ---
confluent.topic.bootstrap.servers=kafka:9092
confluent.topic.replication.factor=3
```

**Format classes** (`format.class`, generalized) — all validated:

| Content | Class |
|---|---|
| JSON (line-delimited, record-separator, or concatenated) | `io.confluent.connect.cloud.storage.source.format.CloudStorageJsonFormat` |
| Avro container files | `io.confluent.connect.cloud.storage.source.format.CloudStorageAvroFormat` |
| Raw bytes (split on `format.bytearray.separator`, default newline) | `io.confluent.connect.cloud.storage.source.format.CloudStorageByteArrayFormat` |

> The generalized-overview *quick start* shows `format.class=io.confluent.connect.azure.blob.storage.format.json.JsonFormat` — that disagrees with the Configuration Reference, which lists the `CloudStorage*` classes as the valid values. **Use the `CloudStorage*` classes.** *(Doc inconsistency, MCP-observed 2026-08-05.)*

---

## 2. The gotchas that will actually bite you (all MCP-validated)

1. **Offsets are keyed to the connector NAME, not the container.** Deleting a connector and reusing
   the same name **resumes** progress (it will *not* reprocess from the start); a **new container
   requires a new connector name**; reconfiguring an existing connector to point at a new container
   will **not** read that container from the beginning. Treat the connector name as immutable and
   name it per-container-per-purpose.
2. **No reload on rename or overwrite.** A file renamed after it was read, or re-uploaded with new
   content under the same name, is **not re-read**. This is an append-*new*-files model — it does not
   watch for mutations. If your producer overwrites files in place, this connector is the wrong tool.
3. **`topics.dir` defaults to `topics/`** and the connector **ignores every object not under it**.
   The common "No new files ready after scan task…" failure is almost always `topics.dir` pointing at
   the wrong prefix, or a `topic.regex.list` that matches nothing.
4. **At-least-once delivery** — after a task restart the last few records may be reprocessed. Dedupe
   downstream on a stable record key.
5. **`file.discovery.starting.timestamp` only applies when no offsets are stored** for the connector
   name — it lets a *new* connector skip old files; it will not retroactively move a running one.

---

## 3. ADLS Gen2 endpoint & AKS specifics

- **ADLS Gen2 is read via the BLOB endpoint** (`store.url = https://<account>.blob.core.windows.net/<container>`),
  not the `dfs`/`abfss` endpoint. Hierarchical-namespace (HNS) accounts are readable over the blob
  endpoint; validate listing behavior/performance on a large HNS container before go-live.
- **Network:** private endpoint to the ADLS **blob** sub-resource; the AKS node subnet must resolve
  and reach it. If egress is via a proxy, the connector supports `azblob.proxy.url` / `azblob.proxy.user`
  / `azblob.proxy.password`.
- **Secret handling:** put the SAS in a Kubernetes Secret and inject via a Connect `ConfigProvider`
  (`FileConfigProvider`, as `${file:/mnt/secrets/adls:sas}` above) — never inline it in the connector JSON.
- **Tuning knobs:** `azblob.connection.timeout.ms` (default 30000 — raise for large files),
  `record.batch.max.size` (default 200), `azblob.retry.retries` (default 3).

---

## 4. Auth — the FSI reality

This connector supports **only two auth methods**: `azblob.account.key` or `azblob.sas.token`.
There is **no managed-identity / Entra Workload Identity option** — a genuine FSI gap to flag.

- **Preferred:** a **container-scoped, read+list-only, short-lived SAS**, rotated on a schedule.
- **Avoid** the account key (it is the streaming-platform equivalent of a shared root credential —
  against canon for regulated environments).
- **Field-level encryption:** if payloads carry PII, the connector supports **CSFLE**
  (`csfle.enabled=true`) — enable rather than relying on transport encryption alone.

---

## 5. Delivery semantics & error routing

- **At-least-once** (see §2.4) — dedupe downstream.
- **Parse-error routing (not a Connect DLQ).** Kafka Connect's KIP-298 DLQ is **sink-only**, so it
  does not apply here. Instead this connector has its own mechanism: with `behavior.on.error=log`
  (or `ignore`), a malformed/unparseable file is written to `${parse.error.topic.prefix}-${connectorName}`
  and processing continues, rather than failing the task (the default `fail`). Monitor that topic.

---

## 6. Verify (before declaring done)

1. **Plugin present** — `GET /connector-plugins` lists `AzureBlobStorageSourceConnector`.
2. **Auth reachable** — from a worker pod, confirm the SAS can list the container over the blob endpoint.
3. **Happy path** — drop a test `*.json` under `incoming/`; connector + task `RUNNING`; records arrive
   on `orders.raw`.
4. **Error path** — drop a malformed file; confirm it lands on `adls-source-error-adls-source-orders-ingest`
   and the task stays `RUNNING` (not `FAILED`).
5. **Durability** — restart a worker mid-ingest; confirm no loss (at-least-once) and downstream dedupe holds.

---

## 7. Failure modes & fixes

| Symptom | Cause | Fix |
|---|---|---|
| `No new files ready after scan task…` | `topics.dir` wrong, or `topic.regex.list` matches nothing | Point `topics.dir` at the real prefix; fix the regex (`<topic>:<regex>`) |
| Nothing ingested, no error | Files are under the default `topics/` assumption but live elsewhere; or all files pre-date `file.discovery.starting.timestamp` | Set `topics.dir`; check the starting-timestamp cutoff |
| Re-uploaded / renamed file not picked up | By design — no reload on rename/overwrite | Write *new* filenames; don't mutate in place |
| New container reads nothing from the start | Offsets tied to the old connector name | Use a **new connector name** for a new container |
| Task `FAILED` on a bad file | `behavior.on.error=fail` (default) | Set `behavior.on.error=log` + `parse.error.topic.prefix` |
| Duplicates downstream after restart | Expected (at-least-once) | Dedupe on a stable key |
| Connector won't start after 30 days | Trial license expired | Add a valid `confluent.license` / enterprise subscription |

---

## 8. Operations

- **Naming discipline:** connector name = the offset key. One name per container-per-purpose; never
  reuse a name across containers expecting a fresh read.
- **Schema/SR posture:** arbitrary JSON files have no registered schema, so records land schemaless
  (`JsonConverter`, `schemas.enable=false`). To reach canon (Avro/Protobuf + Schema Registry),
  **schematize downstream** (Flink/ksqlDB) rather than at the connector.
- **SAS rotation:** short-lived, container-scoped SAS rotated on schedule; update the k8s Secret —
  a silent SAS expiry stalls ingest.
- **Monitoring:** connector/task state; lag of the parse-error topic (sustained growth = upstream is
  emitting malformed files); ADLS list latency on HNS containers.
- **Scaling:** raise `tasks.max` (up to file/folder parallelism) and `task.batch.size` for large backfills.
