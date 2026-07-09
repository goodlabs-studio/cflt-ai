---
title: Archival Storage for Long-Retention Topics (Confluent Cloud on Azure)
tags: [kafka confluent-cloud azure tiered-storage retention archival adls tableflow connect fsi]
sources: [raw/articles/Archival Storage for Long-Retention Topics.md]
related: [concepts/cc-cluster-tiers, concepts/tableflow-iceberg-delta, patterns/tableflow-changelog-mode-immutability, concepts/schema-registry-best-practices, patterns/dr-cluster-linking, concepts/exactly-once-semantics]
confidence: high
last_updated: 2026-07-06
last_validated: 2026-07-06
---

# Archival Storage for Long-Retention Topics (Confluent Cloud on Azure)

## Summary

Confluent Cloud retained storage is priced for streaming throughput and fast replay, not cold retention. The pattern: keep only an explicit **replay window** hot on Confluent Cloud (sized via the topic's total `retention.ms`), and land everything older as open-format files (Parquet/Avro) in Azure Data Lake Storage Gen2 — via a managed ADLS Gen2 Sink connector or Tableflow — where Azure-internal redundancy provides durability at a fraction of the streaming rate. The trade-off: cold data is a **re-ingestion** away, not a Kafka seek, so the design trades replay latency for an order-of-magnitude storage cost reduction. The ADLS copy — not Confluent's own tiered layer — is the compliance system of record.

> **Validation status (confidence: high).** Validated 2026-07-06 against `confluent-docs`: CC topic-config reference (no user-facing `local.retention.*`; `retention.ms`/`retention.bytes` editable), CC Azure Data Lake Storage Gen2 Sink connector (class + config keys), and Tableflow storage (Iceberg + Delta on ADLS Gen2 BYOS). Two config corrections from the source draft applied (see Caveats). Illustrative $/TB rates are not MCP-validated — replace with contracted figures.

## Pattern

### Cloud vs. Platform — the knob that changes

On **Confluent Platform** you set `local.retention.ms` to size the hot tail directly. **Confluent Cloud does not expose `local.retention.*`** — it manages the local↔tiered split internally. On Cloud your only levers are:

1. The topic's **total** `retention.ms` / `retention.bytes` (governs local **+** tiered — when it fires, data is genuinely gone from Confluent), and
2. How quickly a **sink connector or Tableflow** lands data in ADLS.

Size the replay window through (1); build the durable archive through (2). Confluent's tiered storage keeps data in Kafka log format bound by the topic's retention — it is a **replay accelerator, not an archive**.

### retention.ms and retention.bytes

Two independent **deletion** ceilings; a segment is evicted when it crosses **either**, whichever hits first:

- **`retention.ms`** — maximum age; a closed segment is evicted this long after it rolls.
- **`retention.bytes`** — maximum size per partition; oldest segments evicted once the partition exceeds it. `-1` disables size-based eviction.

So `retention.bytes = -1` + `retention.ms = 7d` means **age is the only active limit** — the window never silently shrinks on high-volume days. It does not mean storage is infinite; it means size is not the constraint.

### Reference architecture

1. **Hot tail (0 → replay window).** CC topic; set total `retention.ms` to the replay window. Confluent manages the local↔tiered offload beneath it. (Tiered/infinite storage is available on Standard, Enterprise, and Dedicated — **not Basic**; see [CC Cluster Tiers](../concepts/cc-cluster-tiers.md).)
2. **Cold archive (window → full retention).** A fully-managed **Azure Data Lake Storage Gen2 Sink** connector — or **Tableflow** materializing the topic to Iceberg/Delta — writes Parquet/Avro to ADLS Gen2 with **time-based partitioning**, running from day one (archive populated in parallel with the hot tail, not at expiry). This is the compliance system of record.
3. **Lifecycle tiering.** An ADLS lifecycle policy ages blobs Hot → Cool → Archive by partition date. Azure-side, independent of Confluent.
4. **Schema durability.** Register schemas in CC Schema Registry with `FULL` / `FULL_TRANSITIVE` compatibility so cold data stays self-describing and replayable years later ([Schema Registry Best Practices](../concepts/schema-registry-best-practices.md)).

### Configuration reference

Three knobs, three places — topic retention (CC), sink connector (CC), lifecycle policy (Azure). Skeletons, not drop-in modules; validate provider/connector schemas before applying.

**1. Topic retention — the replay window (CC):**

```hcl
resource "confluent_kafka_topic" "orders" {
  kafka_cluster { id = confluent_kafka_cluster.main.id }
  topic_name       = "orders"
  partitions_count = 12
  config = {
    "retention.ms"   = "604800000"  # 7-day replay window
    "retention.bytes" = "-1"        # age is the only limit
    "cleanup.policy" = "delete"
  }
}
```

**2. Sink connector — continuous copy to ADLS (CC):**

```hcl
resource "confluent_connector" "adls_sink" {
  environment   { id = confluent_environment.main.id }
  kafka_cluster { id = confluent_kafka_cluster.main.id }
  config_sensitive = {
    "azure.datalake.gen2.access.key" = var.adls_access_key
  }
  config_nonsensitive = {
    "connector.class"                  = "AzureDataLakeGen2Sink"
    "name"                             = "orders-adls-archive"
    "topics"                           = "orders"
    "azure.datalake.gen2.account.name" = azurerm_storage_account.archive.name
    "topics.dir"                       = "topics"
    "output.data.format"               = "PARQUET"
    "partitioner.class"                = "TimeBasedPartitioner"  # REQUIRED for path.format/time.interval to apply
    "path.format"                      = "'year'=YYYY/'month'=MM/'day'=dd/'hour'=HH"
    "time.interval"                    = "HOURLY"
    "flush.size"                       = "10000"
    "kafka.auth.mode"                  = "SERVICE_ACCOUNT"
    "kafka.service.account.id"         = confluent_service_account.sink.id
    "tasks.max"                        = "2"
  }
}
```

Time-based partitioning is what turns a future replay into a **bounded prefix scan** (`topic/year=2026/month=02/day=03/`) instead of a full-lake read. **`partitioner.class = "TimeBasedPartitioner"` is mandatory** — `path.format` and `time.interval` are ignored under the default partitioner, silently collapsing the directory layout the replay design depends on.

**3. Lifecycle policy — Hot → Cool → Archive (Azure):** `azurerm_storage_account` (Standard, `StorageV2`, `is_hns_enabled = true` → ADLS Gen2) + `azurerm_storage_management_policy` aging block blobs by `days_since_creation` (e.g. Cool @ 30, Archive @ 180). Pure Azure-side; Confluent is unaware.

### Unit economics (1 TB logical, illustrative list rates)

| Platform | Copies billed | ~$/TB/mo | Basis |
|---|---|---|---|
| CC retained storage | 1 (managed meter) | ~$80–120 | Streaming-tier retained storage |
| ADLS Gen2 Hot | 1 logical | ~$23 | Standard GPv2 block blob |
| ADLS Gen2 Cool | 1 logical | ~$13 | Lifecycle-aged |
| ADLS Gen2 Archive | 1 logical | ~$1 | Cold, retrieval latency |

CC retained storage is a **single managed meter — not a per-replica RF multiplier**. A DR cluster via [Cluster Linking](../patterns/dr-cluster-linking.md) is an opt-in second managed cluster; model its retained storage as a separate line, not a blanket 2× on the primary.

**Replay-window cost** scales linearly with the window: `hot_logical_TB = ingest_per_day_TB × replay_window_days`; a 30-day tier costs 10× a 3-day tier. Keeping the window tight is the single highest-leverage cost decision.

### Replaying from cold storage

Once data ages past `retention.ms` it survives only as ADLS files; replay is **re-ingestion**, not a seek.

- **Path A — ADLS Gen2 Source connector.** Scope to the partition prefixes covering the window, rehydrate any Archive-tier blobs to Hot/Cool first (minutes–hours; they can't be read in place), and produce into a **dedicated replay topic** (e.g. `orders.replay`) to avoid colliding with live traffic. Consumers read `EARLIEST` on the replay topic (original offsets won't match) and must handle replayed events idempotently.
- **Path B — Tableflow / Iceberg.** If landed via Tableflow, query the window in place with any Iceberg-aware engine (Flink, Spark, Trino, Databricks, Synapse) and re-produce only the rows you need — far cheaper than replaying whole partitions.

Replayed records carry a **new produce-timestamp** unless the sink persisted original event time; if event-time ordering matters, carry it as a field. Per-partition order survives only if the sink partitioned consistently and the source reads in order; cross-partition global ordering is not guaranteed.

## When to Use

- Long/regulatory retention (OFAC/AML up to 7 years) where most data is never re-consumed directly from the cluster.
- Streaming workloads with a well-defined operational replay window (commonly **3–7 days** for FSI) beyond which access is rare and latency-tolerant.
- When a cheap, queryable, open-format compliance system of record is required outside Kafka's retention accounting.

## Caveats

- **`store.kafka.keys` / `store.kafka.headers` are not valid ADLS Gen2 Sink properties** (they are S3-Sink properties; absent from both the CC managed and CP self-managed references). The managed ADLS Gen2 archive captures the value payload; do not rely on key/header round-tripping for Path A fidelity. Carry anything you need to reconstruct (key, event-time) into the value payload.
- **`partitioner.class = "TimeBasedPartitioner"` is required** for the time-based directory layout — see config note above.
- **`behavior.on.null.values`** (CP self-managed default `fail`) is not shown in the CC quickstart config surface — confirm it's exposed on the managed connector before relying on `ignore` to skip tombstones.
- **Tiered storage is not universal across CC tiers** — Basic clusters do not offer it. Confirm the cluster tier ([CC Cluster Tiers](../concepts/cc-cluster-tiers.md)).
- **Tiered "eviction" is deletion** — when `retention.ms`/`retention.bytes` fire, data is gone from Confluent (local and tiered). The ADLS copy must exist *before* expiry, which is why the sink runs from day one.
- **Replay is not free** — ADLS read/transaction charges, Archive-tier rehydration fees + latency, and CC ingress + retained-storage cost for re-produced traffic. Budget it as occasional and scope tightly by prefix. Avoid lifecycle-aging **Tableflow/Iceberg table files** to Archive unless you're prepared to pause query access to those partitions; scope Archive tiering to raw connector-landed files.
- **Connector/provider schemas drift** — validate `confluentinc/confluent` and `hashicorp/azurerm` schemas (especially sink auth and `path.format`) before applying.

## Related

- [CC Cluster Tiers](../concepts/cc-cluster-tiers.md) — which tiers offer tiered/infinite storage (Basic does not)
- [Tableflow: Iceberg & Delta](../concepts/tableflow-iceberg-delta.md) — Path B archive as a queryable table
- [Tableflow Changelog Mode & Immutability](../patterns/tableflow-changelog-mode-immutability.md) — semantics of the materialized table
- [Schema Registry Best Practices](../concepts/schema-registry-best-practices.md) — FULL/FULL_TRANSITIVE for self-describing cold data
- [DR via Cluster Linking](../patterns/dr-cluster-linking.md) — the opt-in second cluster, modeled as a separate cost
- [Exactly-Once Semantics](../concepts/exactly-once-semantics.md) — why replayed traffic needs idempotent downstream handling
